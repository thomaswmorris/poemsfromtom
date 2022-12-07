import numpy as np
import time as ttime
from datetime import datetime
from dateutil.easter import *

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
    if dt.month==1 and dt.day==1: return 'new_years_day'
    easter_yd = easter(dt.year).timetuple().tm_yday 

    # easter things supercede 

    if yd == easter_yd - 46: return 'ash_wednesday'
    if yd == easter_yd - 7:  return 'palm_sunday'
    if yd == easter_yd - 3:  return 'holy_thursday'
    if yd == easter_yd - 2:  return 'good_friday'
    if yd == easter_yd - 1:  return 'holy_saturday'
    if yd == easter_yd:      return 'easter_sunday'
    if yd == easter_yd + 7:  return 'divine_mercy_sunday'
    if yd == easter_yd + 39: return 'ascension'
    if yd == easter_yd + 49: return 'pentacost'

    # these are on specific dates 
    
    if (dt.month,dt.day)==(1,1):   return 'new_years_day'
    if (dt.month,dt.day)==(1,6):   return 'epiphany'
    if (dt.month,dt.day)==(2,2):   return 'candlemas'
    if (dt.month,dt.day)==(2,14):  return 'valentines_day'
    if (dt.month,dt.day)==(3,25):  return 'annunciation'
    
    if (dt.month,dt.day)==(7,4):   return 'independence_day'
    if (dt.month,dt.day)==(9,8):   return 'immaculate_conception'
    if (dt.month,dt.day)==(10,31): return 'halloween'
    if (dt.month,dt.day)==(11,1):  return 'all_saints'
    if (dt.month,dt.day)==(11,11): return 'veterans_day'
    
    if (dt.month,dt.day)==(12,24): return 'christmas_eve'
    if (dt.month,dt.day)==(12,25): return 'christmas_day'
    if (dt.month,dt.day)==(12,31): return 'new_years_eve'

    # these are weird lmao

    if (dt.month,dt.weekday())==(5,0) and (get_month(t+7*86400)=='june'): return 'memorial day' # last monday of may
    if (dt.month,dt.day)==(11,(3-datetime(dt.year,11,1).weekday())%7+22): return 'thanksgiving' # fourth thursday of november

    # a changing month or season is a holiday 
    # just kidding it's not

    #if get_season(t) != get_season(t - 86400): return f'first day of {get_season(t)}'
    #if get_month(t) != get_month(t - 86400): return f'first day of {get_month(t)}'
    
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

def get_feast(t=ttime.time()):
    
    if yd <= 5 or yd >= christmas_yd: return 'christmastide'
    if 0 < easter_yd - dt.date().timetuple().tm_yday <= 46: 
        if not dt.weekday() == 0: return 'lent'
    if -39 < easter_yd - dt.date().timetuple().tm_yday <= 0: return 'eastertide'
    if christmas_yd - (22 + datetime(dt.year,12,25).weekday()) <= yd < christmas_yd: return 'advent'
    return 'ordinary time'

def get_context(when):
    return {'weekday' : get_weekday(when), 
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
        context_multipliers[category][keyword] = np.round(len(samples) / np.sum(keyword==samples))