import re
import pytz
import glob
import json
import time
import smtplib
import numpy as np
import pandas as pd
import github as gh
from io import StringIO

from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from keyword_utils import get_month, get_weekday, get_holiday, get_season, get_liturgy

class Poetizer:
    def __init__(self):
                        
        self.poems, self.metadata = {}, {}
        self.poets, self.titles, self.pt_keys = [], [], []
        self.ptdf = pd.DataFrame(columns=['poet', 'title', 'keywords'])
        self.content_prefix = ''
        fns = np.sort([fn for fn in glob.glob(self.content_prefix + 'poems/*.json')])

        with open('poems.json', 'r+') as f:
            pt_dict = json.load(f)

        with open(f'keywords.json', 'r+') as f:
            self.keywords = json.load(f)

        self.kw_mult = {'season':4, 'month':12, 'weekday':7, 'liturgy':8, 'holiday':1e16}
        self.kw_list = []
        [[self.kw_list.extend([kw.strip('~') for kw in self.keywords[cat][poss]]) for poss in self.keywords[cat]] for cat in list(self.keywords)]

        for k, v in pt_dict.items():

            tag = v['metadata'].split('|')[0]
            self.metadata[tag] = v['metadata']    
            self.poems[tag] = v['poems']

            for _title in list(v['poems']):
                self.poets.append(tag)
                self.titles.append(_title)
                self.pt_keys.append((tag,_title))
                self.ptdf.loc[len(self.ptdf)] = tag, _title, [kw for kw in self.kw_list if self.string_contains_phrase(_title, kw)]

                

        
                
        self.n_pt = len(self.pt_keys)
        self.likelihood = None
        
    def string_contains_phrase(self, string, phrase, ordered=False, return_counts=False):

        # this checks that a string has, as words, all of the words in phrase in some order
        counts_per_word = np.array([len(re.findall(f'[^a-z]{w}[^a-z]',string.lower().join([' ',' ']))) for w in [w.strip('~') for w in phrase.split()]])
        if return_counts: return counts_per_word
        return (counts_per_word > 0).all()

    def get_keywords(self, when):
        return [get_season(when), get_weekday(when), get_month(when), get_holiday(when), get_liturgy(when)]          
    
    def list_keywords(self):
        for dyd in range(365):
            t  = datetime(2022,1,1).timestamp() + 86400 * (dyd + .5)
            dt = datetime.fromtimestamp(t)
            print(f'{dt.month}/{dt.day}',self.get_keywords(t))

    def titleize(self,string):

        with open('poetry/minor-words.txt','r') as f:
            words_to_not_capitalize = f.read().split('\n')

        delims = [': ', '\"', ' ', 'O\'', '-']
        string = re.sub(r'\ \_[0-9]+\_','',string).lower()
        for delim in delims:  
            words = string.split(delim)
            for i,s in enumerate(words):
                if (not len(s) > 0) or (s in ['\"','\'']):
                    continue
                if (i in [0,len(words)-1]) or not ((s in words_to_not_capitalize) and not delim == '-'): 
                    i_cap = list(re.finditer('[^\"\']',s))[0].start()
                    words[i] = words[i][:i_cap] + words[i][i_cap].capitalize() + words[i][i_cap+1:]
                else: 
                    pass
            string = delim.join(words)

        string = re.sub(r'\'S ','\'s ',string)
        return string

    def load_repo(self,repo_name='',repo_token=''):

        self.repo_name  = repo_name
        self.repo_token = repo_token
        self.g = gh.Github(self.repo_token)
        self.repo = self.g.get_user().get_repo(self.repo_name)
    
    def load_history(self,repo_name='',repo_token=''):

        if not repo_name == '':
            self.load_repo(repo_name, repo_token)
            self.repo_history_contents = self.repo.get_contents('history.csv',ref='master')
            self.rhistory = pd.read_csv(StringIO(self.repo_history_contents.decoded_content.decode()),index_col=0)
            self.history  = self.rhistory.loc[self.rhistory['type']!='test']
            self.history.index = np.arange(len(self.history.index))

        else:
            try:
                self.history = pd.read_csv('history.csv',index_col=0)
            except Exception as e:
                self.history = pd.DataFrame(columns=['poet','title','type','date','time','timestamp'])
                print(f'{e}\ncould not find history.csv')

    

    def make_stats(self,order_by=None, ascending=True,force_rows=True,force_cols=True):
        
        if force_rows: pd.set_option('display.max_rows', None)
        if force_cols: pd.set_option('display.max_columns', None)
        self.stats = pd.DataFrame(columns=['name','birth','death','n_poems','times_sent','days_since_last_sent'])
        for _poet in list(self.poems):
            
            tag, name, birth, death, link = self.metadata[_poet].split('|')
            elapsed = (time.time() - self.history['timestamp'][self.history['poet']==_poet].max()) / 86400 # if _poet in self.history['poet'] else None
            self.stats.loc[_poet] = name, birth, death, len(self.poems[_poet]), (self.history['poet']==_poet).sum(), np.round(elapsed,1)
            
        if not order_by is None:
            self.stats = self.stats.sort_values(by=order_by, ascending=ascending)

    def load_poem(self,
                  poet='random',
                  title='random',
                  when=time.time(),
                  min_length=0,
                  max_length=100000,
                  poet_latency=0,
                  title_latency=0,
                  contextual=False,
                  repo_name='',
                  repo_token='',
                  tag_historical='',
                  read_historical=False,
                  write_historical=False,
                  verbose=True,
                  very_verbose=False,
                  html_color='Black'):

        self.when = when
        self.poem = None
        self.history = None
        if read_historical or write_historical:
            self.load_history(repo_name=repo_name, repo_token=repo_token)
            self.make_stats(order_by=['times_sent', 'days_since_last_sent'], ascending=(False,True))
            for row in self.history.index:
                entry = self.history.loc[row]
                if self.when - entry['timestamp'] < title_latency * 86400:
                    i_pt = np.where((np.array(self.poets)==entry['poet'])&(np.array(self.titles)==entry['title']))[0][0]
                    if very_verbose: print(f'removing poem {self.titles[i_pt]} by {self.poets[i_pt]} at loc {i_pt}')
                    self.poets.pop(i_pt); self.titles.pop(i_pt); self.pt_keys.pop(i_pt); self.n_pt -= 1
        
        if (not poet in self.poets) and (not poet=='random'):
            raise(Exception(f'The poet \"{poet}\" is not in the database!'))
        if (not title in self.titles) and (not title=='random'):
            raise(Exception(f'The title \"{title}\" is not in the database!'))
        if (not (poet,title) in self.pt_keys) and (not poet=='random') and (not title=='random'):
            raise(Exception(f'The poem \"{title}\" poet \"{poet}\" is not in the database!'))
            
        # apply multipliers accordingly; so that poems titled "christmas" aren't sent in june, or poems titled "sunday" aren't sent on thursday
        self.likelihood = np.ones(self.n_pt) / self.n_pt 
        if (not poet == 'random') and (not title == 'random'):
            self.poet  = poet
            self.title = title
            self.poem  = self.poems[self.poet][self.title]

        else:
            for _poet in np.unique(self.poets):
                self.likelihood[_poet==np.array(self.poets)] = 1 / np.sum(_poet==np.array(self.poets))
                if not self.history is None:
                    weight = np.exp(-.25 * self.stats.loc[_poet, 'times_sent'])
                    if very_verbose: print(f'{_poet} has been weighted by {weight}')
                    self.likelihood[_poet==np.array(self.poets)] *= weight

        if contextual:

            context = self.get_keywords(self.when)
            if verbose: print('keywords:', context)

            for cat in list(self.keywords):
                for poss in self.keywords[cat]:
                
                    if poss in context:
                        m = np.array([np.sum([self.string_contains_phrase(t, kw.strip('~')) for kw in self.keywords[cat][poss]]) > 0 for p, t in self.pt_keys])
                        self.likelihood[m] *= 4 * self.kw_mult[cat]
                        if very_verbose: print(f'weighted {m.sum()} poems with context {poss}')
                    
                    else:
                        m = np.array([np.sum([self.string_contains_phrase(t, kw) for kw in self.keywords[cat][poss] if not '~' in kw]) > 0 for p, t in self.pt_keys])
                        self.likelihood[m] *= 0
                        if very_verbose: print(f'disallowed {m.sum()} poems with context {poss}')
 
        pop_likelihood = list(self.likelihood)
        pop_poets  = self.poets.copy()
        pop_titles = self.titles.copy()
            
        while (len(pop_titles) > 0) and (self.poem == None):
            
            p = np.array(pop_likelihood) / np.sum(pop_likelihood)
            _index = np.random.choice(np.arange(len(p)), p=p)
            _poet, _title, _likelihood = pop_poets.pop(_index), pop_titles.pop(_index), pop_likelihood.pop(_index)

            if not (_poet==poet) and not (poet=='random'):
                continue 
            if not (_title==title) and not (title=='random'):
                continue
            if not (min_length <= len(self.poems[_poet][_title].split()) <= max_length):
                continue
            
            self.poet = _poet; self.title = _title
            self.poem = self.poems[self.poet][self.title]
            break
    
        # If we exit the loop, and don't have a poem:
        if self.poem == None:
            raise(Exception(f'No poem with the requirements was found in the database!'))

        # Put the attributes of the poem into the class
        self.tag, self.name, self.birth, self.death, self.link = self.metadata[self.poet].split('|')
        output = f'chose poem \"{self.title}\" by {self.name}'

        self.dt_when = datetime.fromtimestamp(self.when,tz=pytz.timezone('America/New_York'))
        self.ts_when = self.dt_when.timestamp()
    
        if write_historical:
            
            when_date, when_time = self.dt_when.isoformat()[:19].split('T')
            self.history.loc[len(self.history)] = self.poet, self.title, tag_historical, when_date, when_time, self.when
            self.make_stats(order_by=['times_sent', 'days_since_last_sent'], ascending=(False,True))

            if not repo_name == '':

                hist_blob = self.repo.create_git_blob(self.history.to_csv(), "utf-8")
                stat_blob = self.repo.create_git_blob(self.stats.to_csv(), "utf-8")
                poem_blob = self.repo.create_git_blob(self.ptdf.to_csv(), "utf-8")

                hist_elem = gh.InputGitTreeElement(path='history.csv', mode='100644', type='blob', sha=hist_blob.sha)
                stat_elem = gh.InputGitTreeElement(path='stats.csv', mode='100644', type='blob', sha=stat_blob.sha)
                poem_elem = gh.InputGitTreeElement(path='poems.csv', mode='100644', type='blob', sha=poem_blob.sha)
                
                head_sha  = self.repo.get_branch('master').commit.sha
                base_tree = self.repo.get_git_tree(sha=head_sha)

                tree   = self.repo.create_git_tree([hist_elem, stat_elem, poem_elem], base_tree)
                parent = self.repo.get_git_commit(sha=head_sha) 

                commit = self.repo.create_git_commit(f'update logs {when_date} {when_time}', tree, [parent])
                master_ref = self.repo.get_git_ref('heads/master')
                master_ref.edit(sha=commit.sha)
                
                output += ' (wrote to repo)'

            else:
                self.history.to_csv('history.csv')
                self.stats.to_csv('stats.csv')

                output += ' (wrote to local history)'
            
        if verbose: print(output)

        paddings = re.findall('\n+( *)', self.poem)
        nmp = len(min(paddings, key=len))
        if nmp > 0:
            for padding in sorted(paddings,key=len):
                self.poem = re.sub(padding, padding[:-nmp], self.poem)

        # Make an html version (for nicely formatted emails)
        html_body = '\n' + self.poem
        html_body = html_body.replace('—', '-')
        html_body = html_body.replace(' ', '&nbsp;')
        html_body = html_body.replace('\n', '<br>')
        html_body = html_body.replace('--', '&#8212;')
        
        while html_body.count('_') > 1:
            try:
                s,e = [match.start() for match in re.finditer('\_',html_body)][:2]
                html_body = html_body[:s]   + '<i>' + html_body[s+1:]
                html_body = html_body[:e+2] + '</i>' + html_body[e+1+2:]
            except:
                html_body.replace('_','')

        import calendar
        self.nice_fancy_date = f'{get_weekday(self.ts_when).capitalize()}, '\
                             + f'{get_month(self.ts_when).capitalize()} {self.dt_when.day}, {self.dt_when.year}'
        
        self.header = f'“{self.titleize(self.title)}” by {self.name}'
        
        self.poem_html = f"""
        <html>
        <h2 style="font-family:Garamond; color:{html_color}; font-size: 26px; margin-bottom:0; margin : 0; padding-top:0;">{self.titleize(self.title)}</h2>
            <p style="font-family:Garamond; color:{html_color}; font-size: 18px; margin-bottom:0; margin : 0; padding-top:0;"><i>by 
            <a href="{self.link}">{self.name}</a> ({self.birth}&#8212;{self.death})</i> </p>
            <hr style="width:25%;text-align:left;margin-left:0";color:black;background-color:black">
            <p style="font-family:Garamond; color:{html_color}; font-size: 18px; margin-bottom:0; margin : 0; padding-top:0">{html_body}
            </p>
            <br>
        </html>
        """     

        self.email_html = self.poem_html + '''
        <html>
            <br>
            <br>
            <p style="font-family:Garamond; color:{html_color}; font-size: 16px; margin-bottom:0; margin : 0; padding-top:0">Past poems 
            can be found <a href="https://thomaswmorris.github.io/poems">here</a>.
            </p>
        </html>
        '''

    def send(self, username, password, html, recipient, subject=''):

        message = MIMEMultipart('alternative')
        message['From']    = username
        message['To']      = recipient
        message['Subject'] = subject
        message.attach(MIMEText(html, 'html'))

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(username, password)
        server.send_message(message)
        server.quit()

    def send_poem(self, username, password, recipient, tag=''):
        self.send(username, password, self.email_html, recipient, subject=tag+self.header)

    def send_history(self, username, password, recipient, n=10):
        self.send(username, password, self.history.iloc[-n:].to_html(), recipient, subject=f'HISTORY for {datetime.fromtimestamp(int(time.time())).isoformat()}')
    
    def send_stats(self, username, password, recipient):
        self.send(username, password, self.get_stats.to_html(), recipient, subject=f'STATS for {datetime.fromtimestamp(int(time.time())).isoformat()}')
        

        