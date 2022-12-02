import re, pytz, json, smtplib
import time as ttime
import numpy as np
import pandas as pd
import github as gh
from io import StringIO
import os

from dateutil.easter import *
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def PoemNotFoundError(Exception):
    pass

base, this_filename = os.path.split(__file__)

html_flags = {'american' : '&#127482&#127480', 
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
                'persian' : '',
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

def get_weekday(t=ttime.time()):
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return weekdays[datetime.fromtimestamp(t).weekday()]

def get_month(t=ttime.time()):
    months = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
    return months[datetime.fromtimestamp(t).month-1]

def get_day(t=ttime.time()):
    return f'{datetime.fromtimestamp(t).day:02}'

def get_season(t=ttime.time()):

    year = datetime.fromtimestamp(t).year
    yday = datetime.fromtimestamp(t).timetuple().tm_yday

    spring = datetime(year, 3, 20).timetuple().tm_yday
    summer = datetime(year, 6, 21).timetuple().tm_yday
    autumn = datetime(year, 9, 23).timetuple().tm_yday
    winter = datetime(year, 12, 21).timetuple().tm_yday

    if (spring <= yday < summer):  return 'spring' 
    if (summer <= yday < autumn):  return 'summer' 
    if (autumn <= yday < winter):  return 'autumn' 
    return 'winter'

def get_holiday(t=ttime.time()):


    dt = datetime.fromtimestamp(t)
    yd = dt.timetuple().tm_yday
    if dt.month==1 and dt.day==1: return 'new year\'s day'
    easter_yd = easter(dt.year).timetuple().tm_yday 

    # easter things supercede 

    if yd == easter_yd - 46: return 'ash wednesday'
    if yd == easter_yd - 7:  return 'palm sunday'
    if yd == easter_yd - 3:  return 'holy thursday'
    if yd == easter_yd - 2:  return 'good friday'
    if yd == easter_yd - 1:  return 'easter vigil'
    if yd == easter_yd:      return 'easter'
    if yd == easter_yd + 7:  return 'divine mercy'
    if yd == easter_yd + 39: return 'ascension'
    if yd == easter_yd + 49: return 'pentacost'

    # these are on specific dates 
    
    if (dt.month,dt.day)==(1,1):   return 'new year\'s day'
    if (dt.month,dt.day)==(1,6):   return 'epiphany'
    if (dt.month,dt.day)==(2,2):   return 'candlemas'
    if (dt.month,dt.day)==(2,14):  return 'valentine\'s day'
    if (dt.month,dt.day)==(3,25):  return 'annunciation'
    
    if (dt.month,dt.day)==(7,4):   return 'independence day'
    if (dt.month,dt.day)==(9,8):   return 'immaculate conception'
    if (dt.month,dt.day)==(10,31): return 'halloween'
    if (dt.month,dt.day)==(11,1):  return 'all saints'
    if (dt.month,dt.day)==(11,11): return 'veteran\'s day'
    
    if (dt.month,dt.day)==(12,24): return 'christmas eve'
    if (dt.month,dt.day)==(12,25): return 'christmas day'
    if (dt.month,dt.day)==(12,31): return 'new year\'s eve'

    # these are weird lmao

    if (dt.month,dt.weekday())==(5,0) and (get_month(t+7*86400)=='june'): return 'memorial day' # last monday of may
    if (dt.month,dt.day)==(11,(3-datetime(dt.year,11,1).weekday())%7+22): return 'thanksgiving' # fourth thursday of november

    # a changing month or season is a holiday

    if get_season(t) != get_season(t - 86400): return get_season(t)
    if get_month(t) != get_month(t - 86400): return get_month(t)
    
    return 'no holiday'

def get_liturgy(t=ttime.time()):
    
    dt = datetime.fromtimestamp(t)
    yd = dt.timetuple().tm_yday
    easter_yd    = easter(dt.year).timetuple().tm_yday 
    christmas_yd = datetime(dt.year,12,25).timetuple().tm_yday 

    if yd <= 5 or yd >= christmas_yd: return 'christmastide'
    if 0 < easter_yd - dt.date().timetuple().tm_yday <= 46: 
        if not dt.weekday() == 0: return 'lent'
    if -39 < easter_yd - dt.date().timetuple().tm_yday <= 0: return 'eastertide'
    if christmas_yd - (22 + datetime(dt.year,12,25).weekday()) <= yd < christmas_yd: return 'advent'
    return 'ordinary time'

def get_context(when):
    return {'season' : get_season(when), 
           'weekday' : get_weekday(when), 
             'month' : get_month(when), 
               'day' : get_day(when),
           'liturgy' : get_liturgy(when), 
           'holiday' : get_holiday(when)
    }

context_categories = get_context(0).keys()
context_multipliers = {}
sample_times = datetime(2020,1,1,12).timestamp() + 86400 * np.arange(366)
for category in context_categories:
    samples = np.array([get_context(t)[category] for t in sample_times])
    context_multipliers[category] = {}
    for keyword in np.unique(samples):
        if category == 'holiday': 
            context_multipliers[category][keyword] = 1e12
            continue
        context_multipliers[category][keyword] = np.round(len(samples) / np.sum(keyword==samples))

def send_email(username, password, html, recipient, subject=''):

        message = MIMEMultipart('alternative')
        message['From']    = username
        message['To']      = recipient
        message['Subject'] = subject
        message.attach(MIMEText(html, 'html'))
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(username, password)
        server.send_message(message)
        server.quit()

#def send_poem(poem, username, password, recipient, tag=''):
#    send_email(username, password, poem.email_html, recipient, subject=f'{tag}: {poem.header}')      

def titleize(string):

    with open(f'{base}/minor-words.txt','r') as f:
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

def text_to_html(text):

    text  = text.replace('--', '&#8212;') # convert emdashes
    text  = re.sub(r'_(.*?)_', r'<i>\1</i>', text) # convert italic notation

    lines = [line if len(line) > 0 else '&nbsp;' for line in text.split('\n')]

    html  = '\n'.join([f'<div style="text-align:left" align="center">\n\t{line}\n</div>' for line in lines])

    return html

class Poem():

    def __init__(self, author, title, when):

        with open(f'{base}/data.json', 'r+') as f:

            data = json.load(f)
            self.title = title
            self.author, self.author_name, self.birth, self.death, self.nationality, self.link = data[author]['metadata'].values()
            self.body, self.keywords = data[author]['poems'][title].values()
            self.when, self.html_flag = when, html_flags[self.nationality]

        self.html_body = f'''<blockquote style="font-family:Baskerville; font-size: 18px" align="left">
        <div style="text-indent: -1em; padding-left:1em;">
        {text_to_html(self.body)}
        </div>
        </blockquote>'''
        self.date_time = datetime.fromtimestamp(when).replace(tzinfo=pytz.utc)
        self.nice_fancy_date = f'{get_weekday(self.when).capitalize()} {get_month(self.when).capitalize()} {self.date_time.day}, {self.date_time.year}'
        
        self.header = f'“{titleize(title)}” by {self.author_name}'

        self.html_header = f'''<p style="font-family:Baskerville; font-size: 18px; line-height: 1.5;">
            <i>{self.nice_fancy_date}</i>
            <br>
            <span style="font-family:Georgia; font-size: 24px;"><b>{titleize(title)}</b></span>
            <i>by <a href="{self.link}">{self.author_name}</a> ({self.birth}&#8212;{self.death})</i></p>
            </p>'''

        self.email_html = f'''<html>
            {self.html_header}
            {self.html_body}
            <p> 
            <a href="thomaswmorris.com/poems">past poems</a>
            </p>
            </html>'''

class Curator():

    def __init__(self):
                        
        with open(f'{base}/data.json', 'r+') as f:
            self.data = json.load(f)

        authors, titles, keywords, lengths = [], [], [], []
        self.poems = pd.DataFrame(columns=['author', 'title', 'keywords', 'likelihood', 'word_count'])
        for _author in self.data.keys():
            for _title in self.data[_author]['poems'].keys():
                authors.append(_author)
                titles.append(_title)
                keywords.append(self.data[_author]['poems'][_title]['keywords'])
                lengths.append(len(self.data[_author]['poems'][_title]['body'].split()))

        self.poems['author'] = authors
        self.poems['title'] = titles
        self.poems['keywords'] = keywords
        self.poems['likelihood'] = 1
        self.poems['word_count'] = lengths

        self.archive_poems = self.poems.copy()
        self.history = None

        

    def get_keywords(self, when=ttime.time()):
        return [get_season(when), get_weekday(when), get_month(when), get_day(when),get_liturgy(when), get_holiday(when)]          


    def load_repo(self,repo_name='', repo_token=''):

        self.repo_name  = repo_name
        self.repo_token = repo_token
        self.g = gh.Github(self.repo_token)
        self.repo = self.g.get_user().get_repo(self.repo_name)
    
    def load_history(self, repo_name='', repo_token=''):

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
                self.history = pd.DataFrame(columns=['author','title','type','date','time','timestamp'])
                print(f'{e}\ncould not find history.csv')

    def make_stats(self,order_by=None, ascending=True,force_rows=True,force_cols=True):

        if self.history is None: raise(Exception('No history has been loaded!'))
        if force_rows: pd.set_option('display.max_rows', None)
        if force_cols: pd.set_option('display.max_columns', None)
        self.stats = pd.DataFrame(columns=['name','birth','death','n_poems','times_sent','days_since_last_sent'])
        for _author in np.unique(np.append(self.poems['author'], self.history['author'])):
            
            tag, name, birth, death, nationality, link = self.data[_author]['metadata'].values()
            elapsed = (ttime.time() - self.history['timestamp'][self.history['author']==_author].max()) / 86400 # if _author in self.history['author'] else None
            self.stats.loc[_author] = name, birth, death, len(self.data[_author]['poems']), (self.history['author']==_author).sum(), np.round(elapsed,1)
            
        if not order_by is None:
            self.stats = self.stats.sort_values(by=order_by, ascending=ascending)

    def get_poem(
                self,
                author='random',
                title='random',
                when=ttime.time(), # this needs to be a timestamp
                context=False,
                force_context=False,
                repo_name='',
                repo_token='',
                tag_historical='',
                read_historical=False,
                write_historical=False,
                verbose=True,
                very_verbose=False,
                ):

        self.poems = self.archive_poems.copy()
        self.when = float(when)
            
        self.body = ''
        self.history = None

        if read_historical or write_historical:

            self.load_history(repo_name=repo_name, repo_token=repo_token)
            self.make_stats(order_by=['times_sent', 'days_since_last_sent'], ascending=(False,True))
            
            for index, entry in self.history.iterrows():
                try:
                    i = self.poems.index[np.where((self.poems['author']==entry['author']) & (self.poems['title']==entry['title']))[0][0]]
                    if very_verbose: 
                        _author, _title = self.poems.loc[i, ['author', 'title']]
                        print(f'removing poem {_title} by {_author}')
                    self.poems.drop(i, inplace=True)
                except:
                    print('error handling entry {entry}')
    
        if not author == 'random': self.poems.loc[self.poems['author'] != author, 'likelihood'] = 0
        if not title == 'random': self.poems.loc[self.poems['title'] != title, 'likelihood'] = 0

        if not self.poems['likelihood'].sum() > 0:
            raise PoemNotFoundError(f'The poem \"{title}\" by \"{author}\" is not in the database!')

        for _author in np.unique(self.poems['author']):
            
            # weigh by the number of poems the author has sent
            # if there are few poems left, discount him
            # if the author was sent a lot, discount him
            # if the author was sent recently, discount him

            self.poems.loc[_author==self.poems['author'], 'likelihood'] *= np.minimum(1., 4. / np.sum(_author==self.poems['author']))

            if not self.history is None:

                ts_weight = np.exp(.25 * np.log(.5) * self.stats.loc[_author, 'times_sent']) # four times sent is a weight of 0.5
                dsls = self.stats.loc[_author, 'days_since_last_sent']
                if np.isnan(dsls): dsls = 1e3
                dsls_weight = 1 / (1 + np.exp(-.1 * (dsls - 42))) # after six weeks, the weight is 0.5
                if very_verbose: print(f'{_author:<12} has been weighted by {ts_weight:.03f} * {dsls_weight:.03f} = {ts_weight * dsls_weight:.03f}')
                self.poems.loc[_author==self.poems['author'], 'likelihood'] *= ts_weight * dsls_weight
            
        if context:

            if force_context: self.poems.loc[[len(kws) == 0 for kws in self.poems['keywords']], 'likelihood'] = 0

            self.poems.loc[:, 'likelihood'] *= np.array([4.0 if 'tight' in kws else 1.0 for kws in self.poems['keywords']])

            context = get_context(self.when)
            if verbose: print(context)

            for category in context_categories:
                for keyword in context_multipliers[category].keys():
                    m = np.array([keyword in _keywords for _keywords in self.poems['keywords']])
                    if keyword == context[category]:
                        self.poems.loc[m, 'likelihood'] *= context_multipliers[category][keyword]
                        if very_verbose: print(f'weighted {int(m.sum())} poems with context {category}: {keyword}')

                    # if we want to use 'spring' as a holiday for the first day of spring, then we need to not
                    # exclude that keyword when it is not that holiday. this translates well; if the holiday is 
                    # also a season, month, or liturgy, then we do not  

                    else:
                        self.poems.loc[m, 'likelihood'] *= 0
                        if very_verbose: print(f'disallowed {int(m.sum())} poems with context {category}: {keyword}')

        if not self.poems['likelihood'].sum() > 0:
            raise PoemNotFoundError(f'No poem with the given context')

        if very_verbose: print(f'choosing from {len(self.poems)} poems')
        self.poems['p'] = self.poems['likelihood'] / np.sum(self.poems['likelihood'])
        if very_verbose: print(self.poems.sort_values('p',ascending=False).iloc[:10][['author','title','keywords','p']])
        loc = np.random.choice(self.poems.index, p=self.poems['p'])

        chosen_author, chosen_title = self.poems.loc[loc, ['author', 'title']]
        print(f'chose poem "{chosen_title}" by {chosen_author}')

        self.dt_when = datetime.fromtimestamp(self.when, tz=pytz.utc)
        self.ts_when = self.dt_when.timestamp()
    
        if write_historical:
            
            when_date, when_time = self.dt_when.isoformat()[:19].split('T')
            self.history.loc[len(self.history)] = chosen_author, chosen_title, tag_historical, when_date, when_time, int(ttime.time())
            self.make_stats(order_by=['times_sent', 'days_since_last_sent'], ascending=(False,True))

            if very_verbose: print(self.stats)
            if not repo_name == '':

                hist_blob = self.repo.create_git_blob(self.history.to_csv(), "utf-8")
                stat_blob = self.repo.create_git_blob(self.stats.to_csv(), "utf-8")

                hist_elem = gh.InputGitTreeElement(path='poems/history.csv', mode='100644', type='blob', sha=hist_blob.sha)
                stat_elem = gh.InputGitTreeElement(path='poems/stats.csv', mode='100644', type='blob', sha=stat_blob.sha)
                
                head_sha  = self.repo.get_branch('master').commit.sha
                base_tree = self.repo.get_git_tree(sha=head_sha)

                tree   = self.repo.create_git_tree([hist_elem, stat_elem], base_tree)
                parent = self.repo.get_git_commit(sha=head_sha) 

                commit = self.repo.create_git_commit(f'updated logs @ {when_date} {when_time}', tree, [parent])
                master_ref = self.repo.get_git_ref('heads/master')
                master_ref.edit(sha=commit.sha)
                
                if verbose: print(f'wrote to repo ({self.repo_name})')

            else:
                self.history.to_csv('history.csv')
                self.stats.to_csv('stats.csv')

                if verbose: print(f'wrote to local history')

        return Poem(chosen_author, chosen_title, when)



  