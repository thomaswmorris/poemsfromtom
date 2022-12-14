import re, os, pytz, smtplib
import numpy as np
import time as ttime
from datetime import datetime
from dateutil.easter import easter
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

base, this_filename = os.path.split(__file__)

def get_utc_datetime(t=None):
    if t is None: t = ttime.time()
    return datetime.fromtimestamp(t).astimezone(pytz.utc)

def get_weekday(t=None):
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return weekdays[get_utc_datetime(t).weekday()]

def get_month(t=None):
    months = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
    return months[get_utc_datetime(t).month-1]

def get_day(t=None):
    return f'{get_utc_datetime(t).day:02}'

def get_season(t=None):

    year = get_utc_datetime(t).year
    yday = get_utc_datetime(t).timetuple().tm_yday

    spring = datetime(year, 3, 20).timetuple().tm_yday
    summer = datetime(year, 6, 21).timetuple().tm_yday
    autumn = datetime(year, 9, 23).timetuple().tm_yday
    winter = datetime(year, 12, 21).timetuple().tm_yday

    if (spring <= yday < summer):  return 'spring' 
    if (summer <= yday < autumn):  return 'summer' 
    if (autumn <= yday < winter):  return 'autumn' 
    return 'winter'

# def get_sunday():

def get_holiday(t=None):

    dt = get_utc_datetime(t)
    yd = dt.timetuple().tm_yday
    
    # these are easter things, which supercede all others
    easter_yd = easter(dt.year).timetuple().tm_yday 
    if yd == easter_yd - 47: return 'mardi_gras'
    if yd == easter_yd - 46: return 'ash_wednesday'
    if yd == easter_yd - 7:  return 'palm_sunday'
    if yd == easter_yd - 3:  return 'holy_thursday'
    if yd == easter_yd - 2:  return 'good_friday'
    if yd == easter_yd - 1:  return 'holy_saturday'
    if yd == easter_yd:      return 'easter_sunday'
    if yd == easter_yd + 7:  return 'divine_mercy_sunday'
    if yd == easter_yd + 39: return 'ascension'
    if yd == easter_yd + 49: return 'pentecost'
    if yd == easter_yd + 56: return 'trinity_sunday'
    if yd == easter_yd + 60: return 'corpus_christi'
    if yd == easter_yd + 68: return 'sacred_heart'

    # these are on specific dates 
    if (dt.month, dt.day) == (1, 1):   return 'new_years_day'
    if (dt.month, dt.day) == (1, 6):   return 'epiphany'

    if (dt.month, dt.day) == (2, 2):   return 'candlemas'
    if (dt.month, dt.day) == (2, 14):  return 'saint_valentine'

    if (dt.month, dt.day) == (3, 17):  return 'saint_patrick'
    if (dt.month, dt.day) == (3, 19):  return 'saint_joseph'
    if (dt.month, dt.day) == (3, 25):  return 'annunciation'

    if (dt.month, dt.day) == (6, 19):  return 'juneteenth'
    if (dt.month, dt.day) == (6, 24):  return 'john_the_baptist'
    if (dt.month, dt.day) == (6, 29):  return 'peter_and_paul'
    
    if (dt.month, dt.day) == (7, 4):   return 'independence_day'
    if (dt.month, dt.day) == (7, 4):   return 'independence_day'

    if (dt.month, dt.day) == (8, 6):   return 'transfiguration'
    if (dt.month, dt.day) == (8, 25):  return 'assumption'

    if (dt.month, dt.day) == (10, 31): return 'halloween'
    
    if (dt.month, dt.day) == (11, 1):  return 'all_saints'
    if (dt.month, dt.day) == (11, 2):  return 'all_souls'
    if (dt.month, dt.day) == (11, 11): return 'veterans_day'
    
    if (dt.month, dt.day) == (12, 8):  return 'immaculate_conception'
    if (dt.month, dt.day) == (12, 24): return 'christmas_eve'
    if (dt.month, dt.day) == (12, 25): return 'christmas_day'
    if (dt.month, dt.day) == (12, 31): return 'new_years_eve'

    # these are weird
    if (get_liturgy(t - 86400) != 'advent') & (get_liturgy(t) == 'advent'): return 'advent_sunday'
    if get_holiday(t + 7 * 86400) == 'advent_sunday': return 'christ_the_king'

    # these are weirder
    if (dt.month, dt.weekday()) == (5, 0) and (get_utc_datetime(t + 7 * 86400).month == 6): return 'memorial_day' # last monday of may
    if (dt.month, dt.weekday()) == (9, 0) and (get_utc_datetime(t - 7 * 86400).month == 8): return 'labor_day' # first monday of september
    if (dt.month, dt.day) == (11, (3 - datetime(dt.year, 11, 1).weekday()) % 7 + 22): return 'thanksgiving' # fourth thursday of november
    
    return 'no holiday'

def get_liturgy(t=ttime.time()):
    
    dt = get_utc_datetime(t)
    yd = dt.timetuple().tm_yday
    easter_yd = easter(dt.year).timetuple().tm_yday 
    christmas_yd = datetime(dt.year,12,25).timetuple().tm_yday 

    if yd <= 5 or yd >= christmas_yd: return 'christmastide'
    if 0 < easter_yd - dt.date().timetuple().tm_yday <= 46: 
        if not dt.weekday() == 0: return 'lent'
    if -39 < easter_yd - dt.date().timetuple().tm_yday <= 0: return 'eastertide'
    if christmas_yd - (22 + datetime(dt.year,12,25).weekday()) <= yd < christmas_yd: return 'advent'
    return 'ordinary time'

def get_context(when=None):
    if when is None: when = ttime.time()
    return {
            'weekday' : get_weekday(when), 
              'month' : get_month(when), 
                'day' : get_day(when),
             'season' : get_season(when), 
            'liturgy' : get_liturgy(when), 
            'holiday' : get_holiday(when),
          'timestamp' : when,
            }

context_categories = [key for key in get_context(0).keys() if not key == 'timestamp']
context_multipliers = {}
sample_times = datetime(2020,1,1,12).timestamp() + 86400 * np.arange(366)
for category in context_categories:
    samples = np.array([get_context(t)[category] for t in sample_times])
    context_multipliers[category] = {}
    for keyword in np.unique(samples):
        context_multipliers[category][keyword] = np.round(len(samples) / np.sum(keyword==samples), 3)

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

def titleize(string):

    with open(f'{base}/minor-words.txt','r') as f:
        words_to_not_capitalize = f.read().split('\n')

    delims = [': ', '\“', ' ', 'O’', '-', '(']
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
    text  = re.sub(r'_([\s\S]*?)_', r'<i>\1</i>', text) # convert italic notation

    lines = [line if len(line) > 0 else '&nbsp;' for line in text.split('\n')]
    html  = '\n'.join([f'<div style="text-align:left" align="center">\n\t{line}\n</div>' for line in lines])

    return html