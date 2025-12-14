import ephem, pathlib, pytz, os, yaml

from dateutil.easter import easter
from dataclasses import dataclass
from datetime import datetime

import time as ttime
import numpy as np
import pandas as pd

here, this_filename = os.path.split(__file__)

holidays = pd.read_csv(f"{here}/data/holidays.csv")
forced_holidays = list(holidays.loc[holidays.forced].name.values)

MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


@dataclass
class Context():

    timestamp: float
    ctime: str = ""
    season: str = ""
    liturgy: str = ""
    holidays: str = ""

    def __post_init__(self):

        self.datetime    = datetime.fromtimestamp(self.timestamp).astimezone(pytz.utc)
        self.ctime       = self.datetime.ctime()
        self.season      = get_season(self.timestamp)
        self.liturgy     = get_liturgy(self.timestamp)
        self.holidays    = get_holidays(self.timestamp)
        self.month_epoch = get_month_epoch(self.timestamp)
        self.year_epoch  = get_year_epoch(self.timestamp)
        self.year_day    = self.datetime.timetuple().tm_yday
        self.weekday     = WEEKDAYS[self.datetime.weekday()]
        
    @classmethod
    def now(cls):
        return cls(timestamp=np.round(ttime.time(), 6))

    @property
    def year(self):
        return self.datetime.year

    @property
    def month(self):
        return MONTHS[self.datetime.month - 1]

    @property
    def day(self):
        return self.datetime.day

    @property
    def isoformat(self):
        return self.datetime.isoformat()

    @property
    def pretty_date(self):
        return timestamp_to_pretty_date(self.timestamp)

    def to_dict(self):
        return  {"timestamp": self.timestamp, 
                     "ctime": self.ctime, 
                    "season": self.season, 
                   "liturgy": self.liturgy, 
                   "holiday": self.holidays, 
                      "year": self.year,
                "year_epoch": self.year_epoch,
                     "month": self.month,
               "month_epoch": self.month_epoch,
                       "day": self.day,
                  "year_day": self.year_day, 
                   "weekday": self.weekday, 
               }


def get_utc_datetime(when=None):
    when = when if when is not None else ttime.time()
    return datetime.fromtimestamp(when).astimezone(pytz.utc)

def get_context_dict(when=None):
    t = when if when is not None else ttime.time()
    return Context(timestamp=t).to_dict()

def timestamp_to_pretty_date(t):
    dt = datetime.fromtimestamp(t, tz=pytz.utc)
    return f"{WEEKDAYS[dt.weekday()].capitalize()} {MONTHS[dt.month-1].capitalize()} {int(dt.day)}, {int(dt.year)}"



def get_season(t=None):
    dt = get_utc_datetime(t)
    year = dt.year
    year_day = dt.timetuple().tm_yday

    winter_start_yday = datetime(year, 12, 1).timetuple().tm_yday
    winter_end_yday   = datetime(year, 3, 1).timetuple().tm_yday

    spring_start_yday = datetime(year, 4, 1).timetuple().tm_yday
    spring_end_yday   = datetime(year, 6, 1).timetuple().tm_yday

    summer_start_yday = datetime(year, 6, 21).timetuple().tm_yday
    summer_end_yday   = datetime(year, 9, 1).timetuple().tm_yday

    autumn_start_yday = datetime(year, 10, 1).timetuple().tm_yday
    autumn_end_yday   = datetime(year, 12, 1).timetuple().tm_yday

    if (year_day < winter_end_yday) or (year_day >= winter_start_yday):
        return "winter"
    if spring_start_yday <= year_day < spring_end_yday:
        return "spring"
    if summer_start_yday <= year_day < summer_end_yday:
        return "summer"
    if autumn_start_yday <= year_day < autumn_end_yday:
        return "autumn"
    return "interseason"


def get_holidays(t=None):

    res = []

    dt = get_utc_datetime(t)
    year_day = dt.timetuple().tm_yday

    year, month, day, weekday = dt.year, MONTHS[dt.month-1], dt.day, WEEKDAYS[dt.weekday()]
    easter_offset = year_day - easter(dt.year).timetuple().tm_yday 

    mask = (holidays.month == month) & (holidays.day == day)
    mask |= (holidays.easter_offset == easter_offset)

    res.extend(holidays.loc[mask].name.values)


    # these shouldn't override anything important
    if month == "march":
        if year_day == get_solstice_or_equinox_year_day(year, "spring"):
            res.append("spring_equinox")
    if month == "june":
        if year_day == get_solstice_or_equinox_year_day(year, "summer"):
            res.append("summer_solstice")
    if month == "september":
        if year_day == get_solstice_or_equinox_year_day(year, "autumn"):
            res.append("autumn_equinox")
    if month == "december":
        if year_day == get_solstice_or_equinox_year_day(year, "winter"):
            res.append("winter_solstice")
    
    christmas_day = datetime(dt.year,12,25)
    advent_sunday_year_day = christmas_day.timetuple().tm_yday - (22 + christmas_day.weekday())   

    # these are relative to advent
    if year_day == advent_sunday_year_day: 
        res.append("advent_sunday")
    if year_day == advent_sunday_year_day - 7: 
        res.append("christ_the_king")
    if year_day == advent_sunday_year_day + 14: 
        res.append("gaudate_sunday")

    # these are floating holidays
    weekday_count = int((day - 1) / 7) + 1
    if (month, weekday, weekday_count) == ("february", "monday", 3):  
        res.append("presidents_day")
    if (month, weekday, weekday_count) == ("may", "sunday", 2):  
        res.append("mothers_day")
    if (month, weekday, weekday_count) == ("june", "sunday", 3):  
        res.append("fathers_day")
    if (month, weekday, weekday_count) == ("september", "monday", 1):  
        res.append("labor_day")
    if (month, weekday, weekday_count) == ("october", "monday", 2):  
        res.append("columbus_day")
    if (month, weekday, weekday_count) == ("november", "thursday", 4): 
        res.append("thanksgiving")

    # these are weird
    if (month, weekday) == ("january", "sunday") and (day > 6) and (day <= 13): 
        res.append("baptism") # first sunday after epiphany
    if (month, weekday) == ("may", "monday") and (get_utc_datetime(t + 7 * 86400).month == 6): 
        res.append("memorial_day") # last monday of may

    if (year_day > christmas_day.timetuple().tm_yday) and (weekday == "sunday"): 
        res.append("holy_family") # sunday after christmas
    if (month, day) == ("december", 30) and christmas_day.weekday() == "sunday":
        res.append("holy_family") # if christmas is a sunday then december 30

    return res

def get_solstice_or_equinox_year_day(year, season):
    if season == "spring":
        return ephem.next_spring_equinox((year,1,1)).datetime().timetuple().tm_yday
    elif season == "summer":
        return ephem.next_summer_solstice((year,1,1)).datetime().timetuple().tm_yday
    elif season == "autumn":
        return ephem.next_autumnal_equinox((year,1,1)).datetime().timetuple().tm_yday
    elif season == "winter":
        return ephem.next_winter_solstice((year,1,1)).datetime().timetuple().tm_yday

def get_liturgy(t=ttime.time()):
    dt = get_utc_datetime(t)
    year_day = dt.timetuple().tm_yday
    easter_year_day = easter(dt.year).timetuple().tm_yday 
    christmas_year_day = datetime(dt.year,12,25).timetuple().tm_yday
    advent_sunday_year_day = christmas_year_day - (22 + datetime(dt.year,12,25).weekday())   

    if year_day <= 5 or year_day >= christmas_year_day: 
        return "christmastide"
    if 3 < easter_year_day - dt.date().timetuple().tm_yday <= 46: 
        return "lent"
    if 0 <= easter_year_day - dt.date().timetuple().tm_yday < 3: 
        return "triduum"
    if -39 < easter_year_day - dt.date().timetuple().tm_yday <= 0: 
        return "eastertide"
    if datetime(dt.year,10,31).timetuple().tm_yday <= year_day <= datetime(dt.year,11,2).timetuple().tm_yday: 
        return "allhallowtide"
    if advent_sunday_year_day <= year_day < christmas_year_day: 
        return "advent"
    return "ordinary_time"

def get_advent_sunday_year_day(year):
    christmas_year_day = datetime(year,12,25).timetuple().tm_yday 
    return christmas_year_day - (22 + datetime(year,12,25).weekday())

def get_year_epoch(t=None):
    month = get_utc_datetime(t).month
    if month < 5: return "early"
    if month < 9: return "middle"
    return "late"

def get_month_epoch(t=None):
    dt = get_utc_datetime(t)
    if dt.day < 11: return "early"
    if dt.day < 21: return "middle"
    return "late"

def get_year_day(t=ttime.time()):
    return get_utc_datetime(t).timetuple().tm_yday
