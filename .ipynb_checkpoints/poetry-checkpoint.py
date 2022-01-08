import regex as re
import glob
import json
import time
import smtplib
import numpy as np
import pandas as pd
import github as gh
from io import StringIO

from datetime import datetime
from dateutil.easter import *
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Poetizer:
    def __init__(self,use_repo=False):
                
        self.dict = {}
        self.username = 'poemsfromtom@gmail.com'
        self.use_repo = use_repo

        # these are secret!!! go away!!!
        self.password = 'becauseidonothopetoturnagain'
        if not self.use_repo:
            self.history = pd.read_csv('history.csv',index_col=0)
        else:
            self.token = "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"
            self.g = gh.Github(self.token)
            self.repo = self.g.get_user().get_repo('poetry')
            self.repo_history_contents = self.repo.get_contents('history.csv')
            self.history = pd.read_csv(StringIO(self.repo_history_contents.decoded_content.decode()),index_col=0)

        self.poets, self.titles, self.pt_keys = [], [], []
        fns = np.sort([fn for fn in glob.glob('./_json/*.json')])
        for fn in fns:
            with open(fn, 'r+') as f:
                _dict = json.load(f)
            tag, name, birth, death, link = _dict['metadata'].split('|')
            self.dict[tag] = _dict
            for title in list(_dict):
                if not title=='metadata':
                    self.poets.append(tag)
                    self.titles.append(title)
                    self.pt_keys.append((tag,title)) 
                
        self.n_pt = len(self.pt_keys)
        self.likelihood = None
        
        self.weekdays  = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        self.months    = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
        self.seasons   = ['winter', 'summer', 'autumn', 'spring']
        
        self.kw_dict = {}
        self.kw_dict['winter']           = ['snow', 'frost', 'cold', 'midwinter']
        self.kw_dict['spring']           = ['~flower','~flowers','~tulips']
        self.kw_dict['summer']           = []
        self.kw_dict['autumn']           = ['~fall', 'leaves']
        
        self.kw_dict['valentine']        = ['valentine','~to my']
        self.kw_dict['palm sunday']      = ['~donkey']
        self.kw_dict['good friday']      = ['~paschal','~crucifixion']
        self.kw_dict['easter vigil']     = ['~hell']
        self.kw_dict['pentacost']        = ['~holy spirit']
        self.kw_dict['lent']             = ['~sin', '~sorrow', '~sadness']
        self.kw_dict['independence day'] = ['~america']
        self.kw_dict['halloween']        = ['goblin']
        self.kw_dict['christmas eve']    = ['~christmas','~nativity']
        self.kw_dict['christmas']        = ['~christmas','~nativity']
        
        self.holidays = ['no holiday']
        [self.holidays.append(holiday) for holiday in map(self.get_holiday,datetime(2022,1,1).timestamp()+86400*np.arange(365)) if not holiday in self.holidays]
        
        self.liturgies = ['ordinary time']
        [self.liturgies.append(liturgy) for liturgy in map(self.get_liturgy,datetime(2022,1,1).timestamp()+86400*np.arange(365)) if not liturgy in self.liturgies]

    def get_weekday(self,t=time.time()):
            return self.weekdays[datetime.fromtimestamp(t).weekday()]
        
    def get_month(self,t=time.time()):
            return self.months[datetime.fromtimestamp(t).month-1]
        
    def get_season(self,t=time.time()):
            month = datetime.fromtimestamp(t).month
            if 3 <= month < 6:  return 'spring' 
            if 6 <= month < 9:  return 'summer' 
            if 9 <= month < 12: return 'autumn' 
            return 'winter'

    def get_holiday(self,t=time.time()):

        dt = datetime.fromtimestamp(t)
        yd = dt.timetuple().tm_yday
        if dt.month==1 and dt.day==1: return 'new year'
        easter_yd = easter(dt.year).timetuple().tm_yday 
        
        if yd == easter_yd - 46: return 'ash wednesday'
        if yd == easter_yd - 7: return 'palm sunday'
        if yd == easter_yd - 3: return 'holy thursday'
        if yd == easter_yd - 2: return 'good friday'
        if yd == easter_yd - 1: return 'easter vigil'
        if yd == easter_yd: return 'easter'
        if yd == easter_yd + 39: return 'ascension'
        if yd == easter_yd + 42: return 'pentacost'
        
        
        if (dt.month,dt.day)==(2,14):  return 'valentine'
        #if (dt.month,dt.day)==(3,25):  return 'annunciation'
        if (dt.month,dt.day)==(7,4):   return 'independence day'
        if (dt.month,dt.day)==(10,31): return 'halloween'
        if (dt.month,dt.day)==(11,(3-datetime(dt.year,11,1).weekday())%7+22): return 'thanksgiving' # fourth thursday of november
        if (dt.month,dt.day)==(12,24): return 'christmas eve'
        if (dt.month,dt.day)==(12,25): return 'christmas'
        
        
        if (dt.month,dt.day)==(3,21): return 'spring'
        if (dt.month,dt.day)==(6,21): return 'summer'
        if (dt.month,dt.day)==(9,21): return 'autumn'
        if (dt.month,dt.day)==(12,21): return 'winter'
        #if self.get_liturgy(t-86400) == 'epiphany' and self.get_liturgy(t) == 'ordinary time': return 'baptism'
        return 'no holiday'

    def get_liturgy(self,t=time.time()):
        dt = datetime.fromtimestamp(t)
        yd = dt.timetuple().tm_yday
        easter_yd    = easter(dt.year).timetuple().tm_yday 
        christmas_yd = datetime(dt.year,12,25).timetuple().tm_yday 
        if 0 < easter(dt.year).timetuple().tm_yday - dt.date().timetuple().tm_yday < 46: return 'lent'
        if -42 < easter(dt.year).timetuple().tm_yday - dt.date().timetuple().tm_yday <= 0: return 'easter'
        if christmas_yd - (22 + datetime(dt.year,12,25).weekday()) <= yd < christmas_yd: return 'advent'
        if 2 <= yd < 9: return 'epiphany'
        return 'ordinary time'
    
    def string_contains_phrase(self, string, phrase, ordered=False):
        return np.all([len(re.findall(f'[^a-z]{w}[^a-z]',string.lower().join([' ',' ']))) > 0 for w in [w.strip('~') for w in phrase.split()]])
    
    
        re.sub(r'\~(.*)',r'\1','~fall')
    def list_contextual(self,exclude=[]):
        for discriminator, label in zip([self.seasons, self.weekdays, self.months, self.holidays, self.liturgies],
                                        ['SEASONS', 'WEEKDAYS', 'MONTHS', 'HOLIDAYS', 'LITURGIES']):
            if label in exclude: continue
            print(f'\n=========\n{label}\n=========')
            for kw in discriminator:
                if not kw in list(self.kw_dict): 
                    self.kw_dict[kw] = []
                print(f'\n{kw} (' + ', '.join(self.kw_dict[kw]) + ')\n-----------+-----------')
                for i,(_poet,_title) in enumerate(self.pt_keys):
                    if np.any([self.string_contains_phrase(_title,_kw) for _kw in [kw,*self.kw_dict[kw]]]):
                        print(f'{_poet:<10} | {_title:}')
                        
    def get_stats(self,force_rows=True,force_cols=True):
        
        if force_rows: pd.set_option('display.max_rows', None)
        if force_cols: pd.set_option('display.max_columns', None)
        self.stats = pd.DataFrame(columns=['name','birth','death','n_poems','times_sent','last_sent'])
        for _poet in list(self.dict):
            
            tag, name, birth, death, link = self.dict[_poet]['metadata'].split('|')
            elapsed = (time.time() - self.history['timestamp'][self.history['poet']==_poet].max()) / 86400# if _poet in self.history['poet'] else None
            self.stats.loc[_poet] = name, birth, death, len(self.dict[_poet]) - 1, (self.history['poet']==_poet).sum(), np.round(elapsed,1)
            
        self.stats.index.name = f'{np.sum([len(self.dict[_poet]) - 1 for _poet in list(self.dict)])} poems from {len(self.dict)} poets'
        return self.stats

    
    def titleize(self,string):

        words_to_not_capitalize = ['a','an','and','the','with','about','among','for','over',
                                   'in','on','of','by','to','from','but','is','that','than','near']
        delims = [': ','\"',' ','O\'']
        string = re.sub(r'\ \_[0-9]+\_','',string).lower()
        for delim in delims:  
            words = string.split(delim)
            for i,s in enumerate(words):
                if (not len(s) > 0) or (s in ['\"','\'']):
                    continue
                if (i in [0,len(words)-1]) or not (s in words_to_not_capitalize): 
                    i_cap = list(re.finditer('[^\"\']',s))[0].start()
                    words[i] = words[i][:i_cap] + words[i][i_cap].capitalize() + words[i][i_cap+1:]
                else: 
                    pass
            string = delim.join(words)

        string = re.sub(r'\'S ','\'s ',string)
        return string
    

    def load_poem(self,
                  poet='random',
                  title='random',
                  when=time.time(),
                  min_length=0,
                  max_length=100000,
                  poet_latency=0,
                  title_latency=0,
                  contextual=False,
                  tag_historical='',
                  read_historical=False,
                  write_historical=False,
                  verbose=True,
                  very_verbose=False,
                  html_color='Black'):

        self.poem = None
        
        if (not poet in self.poets) and (not poet=='random'):
            raise(Exception(f'The poet \"{poet}\" is not in the database!'))
        if (not title in self.titles) and (not title=='random'):
            raise(Exception(f'The title \"{title}\" is not in the database!'))
        if (not (poet,title) in self.pt_keys) and (not poet=='random') and (not title=='random'):
            raise(Exception(f'The poem \"{title}\" poet \"{poet}\" is not in the database!'))
            
        # apply multipliers accordingly; so that poems titled "christmas" aren't sent in june, or poems titled "sunday" aren't sent on thursday
        #if self.likelihood == None:
        self.likelihood = np.ones(self.n_pt) / self.n_pt 
        for _poet in list(self.dict):
            self.likelihood[_poet==np.array(self.poets)] = 1 / np.sum(_poet==np.array(self.poets))
        if contextual:
            context_keywords = [self.get_season(when), self.get_weekday(when), self.get_month(when), self.get_holiday(when), self.get_liturgy(when)]
            if verbose: print('keywords:',context_keywords)
            for discriminator, context_kw, multiplier, label in zip([self.seasons, self.weekdays, self.months, self.holidays, self.liturgies],
                                                                    context_keywords,
                                                                    [4,7,12,1e10,1e2],
                                                                    ['SEASONS', 'WEEKDAYS', 'MONTHS', 'HOLIDAYS', 'LITURGIES']):
                
                for kw in discriminator: # for all the possible values of this discriminator...
                    if not kw in list(self.kw_dict): 
                        self.kw_dict[kw] = []
                    for i_pt,(_poet,_title) in enumerate(self.pt_keys): 
                        #if np.any([self.string_contains_phrase(_title,_kw) for _kw in [kw,*self.kw_dict[kw]]]):
                        for _kw in [kw, *self.kw_dict[kw]]:
                            if self.string_contains_phrase(_title,_kw):
                                if kw == context_kw:
                                    self.likelihood[i_pt] *= multiplier
                                    if very_verbose: print(_kw, _poet, _title, multiplier)
                                elif not (((label == 'HOLIDAYS') and (kw in self.seasons)) or '~' in _kw): self.likelihood[i_pt] = 0

        pop_poets  = self.poets.copy()
        pop_titles = self.titles.copy()
        pop_likelihood = list(self.likelihood)
        
        while (len(pop_titles) > 0) and (self.poem == None):
            
            p = np.array(pop_likelihood) / np.sum(pop_likelihood)
            _index = np.random.choice(np.arange(len(p)),p=p)
            _poet, _title, _likelihood = pop_poets.pop(_index), pop_titles.pop(_index), pop_likelihood.pop(_index)

            if not (_poet==poet) and not (poet=='random'):
                continue 
            if not (_title==title) and not (title=='random'):
                continue
            if not (min_length <= len(self.dict[_poet][_title].split()) <= max_length):
                continue
            
            if read_historical and _likelihood < 1e6:
                if (poet=='random'):
                    if _poet in list(self.history['poet']): 
                        ELAPSED = when - self.history['timestamp'][self.history['poet']==_poet].max()
                        if ELAPSED < poet_latency * 86400 :
                            print(f'poet \"{_poet}\" was sent too recently! ({ELAPSED/86400:.02f} days ago)')
                            continue # if the poem was sent too recently 

                if (title=='random'):
                    if _title in list(self.history['title']):
                        ELAPSED = when - self.history['timestamp'][self.history['title']==_title].max()
                        if ELAPSED < title_latency * 86400 :
                            print(f'title \"{_title}\" was sent too recently! ({ELAPSED/86400:.02f} days ago)')
                            continue # if the poet was sent too recently 
                        
            self.poet = _poet; self.title = _title
            self.poem = self.dict[self.poet][self.title]
            break
    
        # If we exit the loop, and don't have a poem:
        if self.poem == None:
            raise(Exception(f'No poem with the requirements was found in the database!'))

        # Put the attributes of the poem into the class
        self.tag, self.name, self.birth, self.death, self.link = self.dict[self.poet]['metadata'].split('|')
        output = f'chose poem \"{self.title}\" by {self.name}'
    
        if write_historical:
            now = int(time.time()); now_date, now_time = datetime.fromtimestamp(now).isoformat()[:19].split('T')
            self.history.loc[len(self.history)] = self.poet, self.title, tag_historical, now_date, now_time, now
            if not self.use_repo:
                self.history.to_csv('history.csv')
                output += ' (wrote to local history)'
            else:
                f = self.repo.update_file('history.csv', 'poem log', self.history.to_csv(), sha=self.repo_history_contents.sha, branch='master')
                output += ' (wrote to repo)'
            
        if verbose: print(output)

        # Make an html version (for nicely formatted emails)
        html_body = '\n' + self.poem
        html_body = html_body.replace('—', '-')
        html_body = html_body.replace(' ', '&nbsp;')
        html_body = html_body.replace('\n', '<br>')
        html_body = html_body.replace('--', '&#8211;')
        
        while html_body.count('_') > 1:
            try:
                s,e = [match.start() for match in re.finditer('\_',html_body)][:2]
                html_body = html_body[:s]   + '<i>' + html_body[s+1:]
                html_body = html_body[:e+2] + '</i>' + html_body[e+1+2:]
            except:
                html_body.replace('_','')

        self.header = f'\"{self.titleize(self.title)}\" by {self.name}'
        self.poem_html = f"""
        <html>
        <h2 style="font-family:Garamond; color:{html_color}; font-size: 24px; margin-bottom:0; margin : 0; padding-top:0;">{self.titleize(self.title)}</h2>
          <p style="font-family:Garamond; color:{html_color}; font-size: 18px; margin-bottom:0; margin : 0; padding-top:0;"><i>by 
          <a href="{self.link}">{self.name}</a></i> ({self.birth}&#8211;{self.death})</p>
          <hr>
            <p style="font-family:Garamond; color:{html_color}; font-size: 18px; margin-bottom:0; margin : 0; padding-top:0">{html_body}
            </p>
        </html>
        """     

    def send(self, html, recipient, subject=''):
        message = MIMEMultipart('alternative')
        message.attach(MIMEText(html, 'html'))
        message['From']    = self.username
        message['To']      = recipient
        message['Subject'] = subject

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(self.username, self.password)
        server.send_message(message)
        server.quit()

    def send_poem(self, recipient, tag=''):
        self.send(self.poem_html, recipient, subject=tag+': '+self.header)

    def send_history(self, recipient, n=10):
        self.send(self.history.iloc[-n:].to_html(), recipient, subject=f'HISTORY for {datetime.fromtimestamp(int(time.time())).isoformat()}')
    
    def send_stats(self, recipient):
        self.send(self.get_stats.to_html(), recipient, subject=f'STATS for {datetime.fromtimestamp(int(time.time())).isoformat()}')
        
#poetizer = Poetizer()
#poetizer.load_poem(poet='random',title='random')
#poetizer.load_poem(poet='random',title='CHANGING OF THE GUARD')
#poetizer.load_poem(poet='merton',title='random')
#poetizer.load_poem(poet='random',title='random',min_length=500)