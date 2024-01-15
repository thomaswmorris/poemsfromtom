import ephem, re, pytz, smtplib
import numpy as np
import time as ttime
from datetime import datetime
from dateutil.easter import easter
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import yaml
import pathlib
import os
from dataclasses import dataclass

here, this_filename = os.path.split(__file__)

HOLIDAYS = yaml.safe_load(pathlib.Path(f'{here}/holidays.yml').read_text())
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']

WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']



def get_utc_datetime(when=None):
    when = when if when is not None else ttime.time()
    return datetime.fromtimestamp(when).astimezone(pytz.utc)

def get_context_dict(when=None):
    t = when if when is not None else ttime.time()
    return Context(timestamp=t).to_dict()

@dataclass
class Context():
    timestamp: int
    ctime: str = ''
    season: str = ''
    liturgy: str = ''
    holiday: str = ''

    def __post_init__(self):

        self.datetime    = datetime.fromtimestamp(self.timestamp).astimezone(pytz.utc)
        self.ctime       = self.datetime.ctime()
        self.season      = get_season(self.timestamp)
        self.liturgy     = get_liturgy(self.timestamp)
        self.holiday     = get_holiday(self.timestamp)
        self.month_epoch = get_month_epoch(self.timestamp)
        self.year_day    = self.datetime.timetuple().tm_yday
        self.weekday     = WEEKDAYS[self.datetime.weekday()]
        
    @classmethod
    def now(cls):
        return cls(timestamp=int(ttime.time()))

    @property
    def year(self):
        return self.datetime.year

    @property
    def month(self):
        return MONTHS[self.datetime.month - 1]

    @property
    def day(self):
        return self.datetime.day

    def to_dict(self):
        return  {'timestamp': self.timestamp, 
                     'ctime': self.ctime, 
                    'season': self.season, 
                   'liturgy': self.liturgy, 
                   'holiday': self.holiday, 
                      'year': f'{self.year:04}',
                     'month': f'{self.month:02}',
                       'day': f'{self.day:02}',
                  'year_day': self.year_day, 
                   'weekday': self.weekday, 
               'month_epoch': self.month_epoch}

def dates_string(birth, death):
    '''
    Convert birth and death to a string.
    '''
    # this assumes no one born before Christ is still alive
    if not death: 
        if not birth:
            return ''
        else:
            return f'(born {birth})'

    birth_is_circa = True if '~' in birth else False
    death_is_circa = True if '~' in death else False
    
    b_numeric = int(birth.strip('~'))
    d_numeric = int(death.strip('~'))

    birth_string, death_string = str(abs(b_numeric)), str(abs(d_numeric))

    birth_string = f'{"c. " if birth_is_circa else ""}{abs(b_numeric)}'
    death_string = f'{"c. " if death_is_circa else ""}{abs(d_numeric)}'

    if b_numeric < 0: 
        birth_string += ' BC'
        if d_numeric < 0: 
            death_string += ' BC'
        else: 
            death_string += ' AD'

    return f'({birth_string} -- {death_string})'


def get_season(t=None):
    dt = get_utc_datetime(t)
    year = dt.year
    yday = dt.timetuple().tm_yday
    if yday < get_solstice_or_equinox_year_day(year, 'spring'):
        return 'winter'
    if yday < get_solstice_or_equinox_year_day(year, 'summer'):
        return 'spring'
    if yday < get_solstice_or_equinox_year_day(year, 'autumn'):
        return 'summer'
    if yday < get_solstice_or_equinox_year_day(year, 'winter'):
        return 'autumn'
    return 'winter'


def get_holiday(t=None):

    dt = get_utc_datetime(t)
    yd = dt.timetuple().tm_yday

    year, month, day, weekday = dt.year, dt.month, dt.day, dt.weekday()

    # how many of this weekday have there been in this month before?
    weekday_count = int((day - 1) / 7)
    
    # these are easter things, which supersede all others
    easter_offset = yd - easter(dt.year).timetuple().tm_yday 

    if easter_offset in HOLIDAYS['easter'].keys():
        return HOLIDAYS['easter'][easter_offset]

    if day in HOLIDAYS['dates'][month].keys():
        return HOLIDAYS['dates'][month][day]
    
    elif (month, weekday, weekday_count) == (2, 0, 2):  return 'presidents_day' # third monday of february
    elif (month, weekday, weekday_count) == (5, 6, 1):  return 'mothers_day' # second sunday of may
    elif (month, weekday, weekday_count) == (6, 6, 2):  return 'fathers_day' # third sunday of june
    elif (month, weekday, weekday_count) == (9, 0, 0):  return 'labor_day' # first monday of september
    elif (month, weekday, weekday_count) == (11, 3, 3): return 'thanksgiving' # fourth thursday of november

    # these are weird
    elif (month, weekday) == (1, 6) and (day > 6) and (day <= 13): return 'baptism' # first sunday after epiphany
    elif (month, weekday) == (5, 0) and (get_utc_datetime(t + 7 * 86400).month == 6): return 'memorial_day' # last monday of may
    elif (get_liturgy(t - 86400) != 'advent') & (get_liturgy(t) == 'advent'): return 'advent_sunday'
    elif get_holiday(t + 7 * 86400) == 'advent_sunday': return 'christ_the_king'

    # not important
    elif yd == get_solstice_or_equinox_year_day(year, 'spring'): return 'spring_equinox'
    elif yd == get_solstice_or_equinox_year_day(year, 'summer'): return 'summer_solstice'
    elif yd == get_solstice_or_equinox_year_day(year, 'autumn'): return 'autumn_equinox'
    elif yd == get_solstice_or_equinox_year_day(year, 'winter'): return 'winter_solstice'

    return 'none'


def get_solstice_or_equinox_year_day(year, season):
    if season == 'spring':
        return ephem.next_spring_equinox((year,1,1)).datetime().timetuple().tm_yday
    elif season == 'summer':
        return ephem.next_summer_solstice((year,1,1)).datetime().timetuple().tm_yday
    elif season == 'autumn':
        return ephem.next_autumnal_equinox((year,1,1)).datetime().timetuple().tm_yday
    elif season == 'winter':
        return ephem.next_winter_solstice((year,1,1)).datetime().timetuple().tm_yday

def get_liturgy(t=ttime.time()):
    dt = get_utc_datetime(t)
    yd = dt.timetuple().tm_yday
    easter_yd = easter(dt.year).timetuple().tm_yday 
    christmas_yd = datetime(dt.year,12,25).timetuple().tm_yday 
    if yd <= 5 or yd >= christmas_yd: 
        return 'christmastide'
    if 3 < easter_yd - dt.date().timetuple().tm_yday <= 46: 
        return 'lent'
    if 0 < easter_yd - dt.date().timetuple().tm_yday <= 3: 
        return 'triduum'
    if -39 < easter_yd - dt.date().timetuple().tm_yday <= 0: 
        return 'eastertide'
    if christmas_yd - (22 + datetime(dt.year,12,25).weekday()) <= yd < christmas_yd: 
        return 'advent'
    return 'ordinary time'

def get_month_epoch(t=None):
    dt = get_utc_datetime(t)
    if dt.day < 11: return 'early'
    if dt.day < 21: return 'middle'
    return 'late'

def get_year_day(t=ttime.time()):
    return get_utc_datetime(t).timetuple().tm_yday

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


# raw:

# monospace:

# html: 




def uppercase_title(text):
    '''
    Capitalizes the part in quotes.
    '''
    prefix, title, suffix = re.search(r'(.*)“(.*)”(.*)', text).groups(0)
    return f'{prefix}“{title.upper()}”{suffix}'

# def add_italic_tags(text):
#     '''
#     Converts to HTML italic format.
#     '''

#     for span in re.findall(r'(_[\w\W]+?_)', text): 
#         text = re.sub(fr'{span}', re.sub(r'\n', r'_\n_', fr'{span}'), text) # add italic around all line breaks
#     text = re.sub(r'_([\w\W]*?)_', r'<i>\1</i>', text) # convert to html italic notation

#     return text

def add_italic_tags(text):
    '''
    Converts to HTML italic format.
    '''
    sections = []
    for i, section in enumerate(text.split('_')):
        if i % 2 == 1:
            section = '<i>' + re.sub('\n', '</i>\n<i>', section) + '</i>'
            section.replace('<i></i>', '')
        sections.append(section)
    return ''.join(sections)

def convert_to_html_lines(text):
    '''
    Converts to HTML italic format.
    '''
    html_lines = []
    for line in text.split('\n'):
        if len(line) == 0:
            html_lines.append('<div class="poem-line-blank">&#8203</div>')
        elif line.strip().strip('_')[0] in ['“', '‘', '’']:
            html_lines.append(f'<div class="poem-line-punc-start">{line}</div>')
        else:
            html_lines.append(f'<div class="poem-line">{line}</div>')
            
    return add_italic_tags('\n'.join(html_lines))



def text_to_html_lines(text):

    text = text.replace('--', '&#8212;') # convert emdashes
    text = add_italic_tags(text)

    parsed_lines = []
    for line in text.split('\n'):
        if len(line) > 0:
            parsed_lines.append(f'<div class="poem-line">{line.strip()}</div>')
        else:
            parsed_lines.append(f'<div class="poem-line-blank">&#8203;</div>')

    return '\n'.join(parsed_lines)