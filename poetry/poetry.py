import re, pytz, json, smtplib
import time as ttime
import numpy as np
import pandas as pd
import github as gh
from io import StringIO

from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from context_utils import get_month, get_weekday, get_day, get_holiday, get_season, get_liturgy

class Poetizer:

    def __init__(self):
                        
        with open('data.json', 'r+') as f:
            self.data = json.load(f)

        with open(f'context.json', 'r+') as f:
            self.context = json.load(f)
        
        self.sml_kws = [kw for c in ['season', 'month', 'liturgy'] for kw in self.context[c]]
        self.kw_mult = {'season':4, 'weekday':7, 'month':12, 'day':30, 'liturgy':16, 'holiday':1e16}

        poets, titles, keywords, lengths = [], [], [], []
        self.poems = pd.DataFrame(columns=['poet', 'title', 'keywords', 'likelihood', 'word_count'])
        for _poet in self.data.keys():
            for _title in self.data[_poet]['poems'].keys():

                poets.append(_poet)
                titles.append(_title)
                keywords.append(self.data[_poet]['poems'][_title]['keywords'])
                lengths.append(len(self.data[_poet]['poems'][_title]['body'].split()))

        self.poems['poet'] = poets
        self.poems['title'] = titles
        self.poems['keywords'] = keywords
        self.poems['likelihood'] = 1
        self.poems['word_count'] = lengths

        self.archive_poems = self.poems.copy()
        self.history = None

        self.html_flags = {'american' : '&#127482&#127480', 
                        'argentinian' : '&#127462&#127479',
                           'austrian' : '&#127462&#127481',
                         'australian' : '&#127462&#127482',
                            'belgian' : '&#127463&#127466',
                            'bengali' : '&#127463&#127465',
                           'canadian' : '&#127464&#127462',
                            'chilean' : '&#127464&#127473',
                              'cuban' : '&#127464&#127482',
                              'czech' : '&#127464&#127487',
                            'english' : '&#127988&#917607&#917602&#917605&#917614&#917607&#917631',
                             'french' : '&#127467&#127479',
                             'german' : '&#127465&#127466',
                           'georgian' : '&#127468&#127466',
                              'greek' : '&#127468&#127479',
                         'guatemalan' : '&#127468&#127481',
                          'hungarian' : '&#127469&#127482',
                              'irish' : '&#127470&#127466',
                            'israeli' : '&#127470&#127473',
                            'italian' : '&#127470&#127481',
                           'jamaican' : '&#127471&#127474',
                           'lebanese' : '&#127473&#127463',
                            'maltese' : '&#127474&#127481',
                         'nicaraguan' : '&#127475&#127470',
                          'norwegian' : '&#127475&#127476',
                            'persian' : '&#127470&#127479',
                           'peruvian' : '&#127477&#127466',
                             'polish' : '&#127477&#127473',
                         'portuguese' : '&#127477&#127481',
                            'russian' : '&#127479&#127482',
                       'saint lucian' : '&#127473&#127464',
                           'scottish' : '&#127988&#917607&#917602&#917619&#917603&#917620&#917631',
                            'serbian' : '&#127479&#127480',
                            'spanish' : '&#127466&#127480',
                      'south african' : '&#127487&#127462',
                            'swedish' : '&#127480&#127466',
                              'swiss' : '&#127464&#127469',
                         'vietnamese' : '&#127483&#127475', 
                              'welsh' : '&#127988&#917607&#917602&#917623&#917612&#917619&#917631',
                                   '' : '',
        }

    def get_keywords(self, when=ttime.time()):
        return [get_season(when), get_weekday(when), get_month(when), get_day(when),get_liturgy(when), get_holiday(when)]          

    def titleize(self,string):

        with open('poetry/minor-words.txt','r') as f:
            words_to_not_capitalize = f.read().split('\n')

        

        delims = [': ', '\"', ' ', 'O\'', '-', '(']
        string = re.sub(r'\ \_[0-9]+\_','',string).lower()
        for delim in delims:  
            words = string.split(delim)
            for i, s in enumerate(words):
                
                if (not len(s) > 0) or (s in ['\"','\'']):
                    continue

                if (i in [0,len(words)-1]) or not ((s in words_to_not_capitalize) and not delim == '-'): 
                    i_cap = list(re.finditer('[^\"\']',s))[0].start()
                    words[i] = words[i][:i_cap] + words[i][i_cap].capitalize() + words[i][i_cap+1:]

                if np.isin(list(s),['I','V','X']).all():
                    words[i] = s.upper()

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
            self.repo_history_contents = self.repo.get_contents('poems/history.csv',ref='master')
            self.rhistory = pd.read_csv(StringIO(self.repo_history_contents.decoded_content.decode()),index_col=0)
            self.history  = self.rhistory.loc[self.rhistory['type']!='test']
            self.history.index = np.arange(len(self.history.index))

        else:
            try:
                self.history = pd.read_csv('poems/history.csv',index_col=0)
            except Exception as e:
                self.history = pd.DataFrame(columns=['poet','title','type','date','time','timestamp'])
                print(f'{e}\ncould not find history.csv')

    def make_stats(self,order_by=None, ascending=True,force_rows=True,force_cols=True):

        if self.history is None: raise(Exception('No history has been loaded!'))
        
        if force_rows: pd.set_option('display.max_rows', None)
        if force_cols: pd.set_option('display.max_columns', None)
        self.stats = pd.DataFrame(columns=['name','birth','death','n_poems','times_sent','days_since_last_sent'])
        for _poet in np.unique(np.append(self.poems['poet'], self.history['poet'])):
            
            tag, name, birth, death, nationality, link = self.data[_poet]['metadata'].values()
            elapsed = (ttime.time() - self.history['timestamp'][self.history['poet']==_poet].max()) / 86400 # if _poet in self.history['poet'] else None
            self.stats.loc[_poet] = name, birth, death, len(self.data[_poet]['poems']), (self.history['poet']==_poet).sum(), np.round(elapsed,1)
            
        if not order_by is None:
            self.stats = self.stats.sort_values(by=order_by, ascending=ascending)

    def load_poem(self,
                  poet='random',
                  title='random',
                  when=ttime.time(),
                  min_length=0,
                  max_length=100000,
                  title_latency=0,
                  context=False,
                  force_context=False,
                  repo_name='',
                  repo_token='',
                  tag_historical='',
                  read_historical=False,
                  write_historical=False,
                  verbose=True,
                  very_verbose=False,
                  include_flags=False,
                  html_color='Black'):

        self.poems = self.archive_poems.copy()

        try: self.when = float(when)
        except: 
            try: self.when = when.timestamp()
            except: 
                try: self.when = datetime(*[int(x) for x in when.split('-')],12,0,0).timestamp()
                except: raise(Exception(f'\'when\' argument must be timestamp or datetime object'))
            
        self.body = ''
        self.history = None

        if read_historical or write_historical:

            self.load_history(repo_name=repo_name, repo_token=repo_token)
            self.make_stats(order_by=['times_sent', 'days_since_last_sent'], ascending=(False,True))
            
            for index, entry in self.history.iterrows():
                if ttime.time() - entry['timestamp'] < title_latency * 86400:
                    try:
                        i = self.poems.index[np.where((self.poems['poet']==entry['poet']) & (self.poems['title']==entry['title']))[0][0]]
                        if very_verbose: 
                            _poet, _title = self.poems.loc[i, ['poet', 'title']]
                            print(f'removing poem {_title} by {_poet}')
                        self.poems.drop(i, inplace=True)
                    except:
                        print('error handling entry {entry}')


        self.poems.loc[self.poems['word_count'] > max_length, 'likelihood'] = 0
    
        if not poet == 'random': self.poems.loc[self.poems['poet'] != poet, 'likelihood'] = 0
        if not title == 'random': self.poems.loc[self.poems['title'] != title, 'likelihood'] = 0

        if not self.poems['likelihood'].sum() > 0:
            raise(Exception(f'The poem \"{title}\" by \"{poet}\" is not in the database!'))

        for _poet in np.unique(self.poems['poet']):
            
            # weight by the number of poems the poet has 
            # if the poet was sent a lot, exponentially discount him
            # if the poet was sent recently, exponentially discount him

            self.poems.loc[_poet==self.poems['poet'], 'likelihood'] *= 1 / np.sum(_poet==self.poems['poet'])

            if not self.history is None:

                ts_weight = np.exp(.5 * np.log(.5) * self.stats.loc[_poet, 'times_sent']) # twice is a weight of 0.5
                dsls = self.stats.loc[_poet, 'days_since_last_sent']
                if np.isnan(dsls): dsls = 1e3
                dsls_weight = 1 / (1 + np.exp(-.1 * (dsls - 56))) # after eight weeks, the weight is 0.5
                if very_verbose: print(f'{_poet:<12} has been weighted by {ts_weight:.03f} * {dsls_weight:.03f} = {ts_weight * dsls_weight:.03f}')
                self.poems.loc[_poet==self.poems['poet'], 'likelihood'] *= ts_weight * dsls_weight
            
        if context:

            if force_context: self.poems.loc[[len(kws) == 0 for kws in self.poems['keywords']], 'likelihood'] = 0

            self.poems.loc[:, 'likelihood'] *= np.array([4.0 if 'tight' in kws else 1.0 for kws in self.poems['keywords']])

            desired_context = self.get_keywords(self.when)
            if verbose: print('keywords:', desired_context)

            for icat, category in enumerate(self.context.keys()):
                for possibility in self.context[category]:

                    m = np.array([possibility in kws for kws in self.poems['keywords']])
                    if possibility == desired_context[icat]:
                        self.poems.loc[m,'likelihood'] *= self.kw_mult[category]
                        if very_verbose: print(f'weighted {int(m.sum())} poems with context {possibility}')

                    # if we want to use 'spring' as a holiday for the first day of spring, then we need to not
                    # exclude that keyword when it is not that holiday. this translates well; if the holiday is 
                    # also a season, month, or liturgy, then we do not  
                    
                    else:
                        if category == 'holiday' and possibility in self.sml_kws: continue
                        self.poems.loc[m, 'likelihood'] *= 0
                        if very_verbose: print(f'disallowed {int(m.sum())} poems with context {possibility}')

        if very_verbose: print(f'choosing from {len(self.poems)} poems')
        self.poems['p'] = self.poems['likelihood'] / np.sum(self.poems['likelihood'])
        if very_verbose: print(self.poems.sort_values('p',ascending=False).iloc[:10][['poet','title','keywords','p']])
        loc = np.random.choice(self.poems.index, p=self.poems['p'])

        self.poet, self.title = self.poems.loc[loc,['poet', 'title']]
        self.body = self.data[self.poet]['poems'][self.title]['body']
    
        # If we exit the loop, and don't have a poem:
        if self.body == '':
            raise(Exception(f'No poem with the requirements was found in the database!'))

        # Put the attributes of the poem into the class
        self.tag, self.name, self.birth, self.death, self.nationality, self.link = self.data[self.poet]['metadata'].values()
        output = f'chose poem \"{self.title}\" by {self.name}'

        self.dt_when = datetime.fromtimestamp(self.when,tz=pytz.timezone('America/New_York'))
        self.ts_when = self.dt_when.timestamp()
    
        if write_historical:
            
            when_date, when_time = self.dt_when.isoformat()[:19].split('T')
            self.history.loc[len(self.history)] = self.poet, self.title, tag_historical, when_date, when_time, int(ttime.time())
            self.make_stats(order_by=['times_sent', 'days_since_last_sent'], ascending=(False,True))

            if very_verbose: print(self.stats)

            if not repo_name == '':

                hist_blob = self.repo.create_git_blob(self.history.to_csv(), "utf-8")
                stat_blob = self.repo.create_git_blob(self.stats.to_csv(), "utf-8")
                poem_blob = self.repo.create_git_blob(self.archive_poems[['poet', 'title', 'keywords', 'word_count']].to_csv(), "utf-8")

                hist_elem = gh.InputGitTreeElement(path='history.csv', mode='100644', type='blob', sha=hist_blob.sha)
                stat_elem = gh.InputGitTreeElement(path='stats.csv', mode='100644', type='blob', sha=stat_blob.sha)
                #poem_elem = gh.InputGitTreeElement(path='poems.csv', mode='100644', type='blob', sha=poem_blob.sha)
                
                head_sha  = self.repo.get_branch('master').commit.sha
                base_tree = self.repo.get_git_tree(sha=head_sha)

                tree   = self.repo.create_git_tree([hist_elem, stat_elem], base_tree)
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

        paddings = re.findall('\n+( *)', self.body)
        nmp = len(min(paddings, key=len))
        if nmp > 0:
            for padding in sorted(paddings,key=len):
                self.body = re.sub(padding, padding[:-nmp], self.body)

        # Make an html version (for nicely formatted emails)
        html_body = '\n' + self.body
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
        self.nice_fancy_date = f'{get_weekday(self.ts_when).capitalize()} '\
                             + f'{get_month(self.ts_when).capitalize()} {self.dt_when.day}, {self.dt_when.year}'
        
        self.header = f'“{self.titleize(self.title)}” by {self.name}'

        flag_ish = f' {self.html_flags[self.nationality]}' if include_flags else ''

        self.html_body = html_body
        self.flag_ish  = flag_ish
        
        self.poem_html = f"""
        <html>
        <h2 style="font-family:Garamond; color:{html_color}; font-size: 30px; margin-bottom:0; margin : 0; padding-top:0;">{self.titleize(self.title)}</h2>
            <p style="font-family:Garamond; color:{html_color}; font-size: 20px; margin-bottom:0; margin : 0; padding-top:0;"><i>by 
            <a href="{self.link}">{self.name}</a> ({self.birth}&#8212;{self.death})</i>{flag_ish}</p>
            <hr style="width:25%;text-align:left;margin-left:0";color:black;background-color:black">
            <p style="font-family:Garamond; color:{html_color}; font-size: 20px; margin-bottom:0; margin : 0; padding-top:0">{html_body}
            </p>
            <br>
        </html>
        """     

        self.email_html = self.poem_html + '''
        <html>
            <br>
            <p style="font-family:Garamond; color:{html_color}; font-size: 20px; margin-bottom:0; margin : 0; padding-top:0"> 
            <a href="https://thomaswmorris.com/poems">archive</a>
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