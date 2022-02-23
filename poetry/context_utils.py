from dateutil.easter import *
from datetime import datetime
import time as ttime

def get_weekday(t=ttime.time()):
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return weekdays[datetime.fromtimestamp(t).weekday()]

def get_month(t=ttime.time()):
    months = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
    return months[datetime.fromtimestamp(t).month-1]

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
    
    if (dt.month,dt.day)==(6,24):  return 'midsummer'
    if (dt.month,dt.day)==(7,4):   return 'independence day'
    if (dt.month,dt.day)==(9,8):   return 'immaculate conception'
    if (dt.month,dt.day)==(10,31): return 'halloween'
    if (dt.month,dt.day)==(11,1):  return 'all saints'
    if (dt.month,dt.day)==(11,11): return 'veteran\'s day'
    
    if (dt.month,dt.day)==(12,24): return 'christmas eve'
    if (dt.month,dt.day)==(12,25): return 'christmas'
    if (dt.month,dt.day)==(12,31): return 'new year\'s eve'

    # these are weird 

    if (dt.month,dt.weekday())==(5,0) and (get_month(t+7*86400)=='june'): return 'memorial day' # last monday of may
    if (dt.month,dt.day)==(11,(3-datetime(dt.year,11,1).weekday())%7+22): return 'thanksgiving' # fourth thursday of november

    # a changing month or season is a holiday

    if get_month(t) != get_month(t - 86400): return get_month(t)
    if get_season(t) != get_season(t - 86400): return get_season(t)

    return 'no holiday'

def get_liturgy(t=ttime.time()):
    
    dt = datetime.fromtimestamp(t)
    yd = dt.timetuple().tm_yday
    easter_yd    = easter(dt.year).timetuple().tm_yday 
    christmas_yd = datetime(dt.year,12,25).timetuple().tm_yday 

    if yd <= 5 or yd >= christmas_yd: return 'christmas'

    if 0 < easter(dt.year).timetuple().tm_yday - dt.date().timetuple().tm_yday <= 46: return 'lent'
    if -42 < easter(dt.year).timetuple().tm_yday - dt.date().timetuple().tm_yday <= 0: return 'easter'
    if christmas_yd - (22 + datetime(dt.year,12,25).weekday()) <= yd < christmas_yd: return 'advent'
    return 'ordinary time'