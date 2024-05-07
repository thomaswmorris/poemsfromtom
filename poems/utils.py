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

HOLIDAYS = yaml.safe_load(pathlib.Path(f"{here}/holidays.yml").read_text())
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

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
    year_dayay = dt.timetuple().tm_yday
    if year_dayay < get_solstice_or_equinox_year_day(year, "spring"):
        return "winter"
    if year_dayay < get_solstice_or_equinox_year_day(year, "summer"):
        return "spring"
    if year_dayay < get_solstice_or_equinox_year_day(year, "autumn"):
        return "summer"
    if year_dayay < get_solstice_or_equinox_year_day(year, "winter"):
        return "autumn"
    return "winter"


def get_holiday(t=None):

    dt = get_utc_datetime(t)
    year_day = dt.timetuple().tm_yday

    year, month, day, weekday = dt.year, MONTHS[dt.month-1], dt.day, WEEKDAYS[dt.weekday()]

    # these are relative to easter
    easter_offset = year_day - easter(dt.year).timetuple().tm_yday 
    if easter_offset in HOLIDAYS["easter_offset"].keys():
        return HOLIDAYS["easter_offset"][easter_offset]

    # these shouldn't override anything important
    if month == "march":
        if year_day == get_solstice_or_equinox_year_day(year, "spring"):
            return "spring_equinox"
    if month == "june":
        if year_day == get_solstice_or_equinox_year_day(year, "summer"):
            return "summer_solstice"
    if month == "september":
        if year_day == get_solstice_or_equinox_year_day(year, "autumn"):
            return "autumn_equinox"
    if month == "december":
        if year_day == get_solstice_or_equinox_year_day(year, "winter"):
            return "winter_solstice"
    
    christmas_day = datetime(dt.year,12,25)
    advent_sunday_year_day = christmas_day.timetuple().tm_yday - (22 + christmas_day.weekday())   

    # these are relative to advent
    if year_day == advent_sunday_year_day: 
        return "advent_sunday"
    if year_day == advent_sunday_year_day - 7: 
        return "christ_the_king"

    # these are floating holidays
    weekday_count = int((day - 1) / 7) + 1
    if (month, weekday, weekday_count) == ("february", "monday", 3):  
        return "presidents_day" 
    if (month, weekday, weekday_count) == ("may", "sunday", 2):  
        return "mothers_day"
    if (month, weekday, weekday_count) == ("june", "sunday", 3):  
        return "fathers_day"
    if (month, weekday, weekday_count) == ("september", "monday", 1):  
        return "labor_day"
    if (month, weekday, weekday_count) == ("october", "monday", 2):  
        return "columbus_day"
    if (month, weekday, weekday_count) == ("november", "thursday", 4): 
        return "thanksgiving"

    # these are weird
    if (month, weekday) == ("january", "sunday") and (day > 6) and (day <= 13): 
        return "baptism" # first sunday after epiphany
    if (month, weekday) == ("may", "monday") and (get_utc_datetime(t + 7 * 86400).month == 6): 
        return "memorial_day" # last monday of may

    if day in HOLIDAYS["dates"][month].keys():
        return HOLIDAYS["dates"][month][day]

    return "none"


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
    if advent_sunday_year_day <= year_day < christmas_year_day: 
        return "advent"
    return "ordinary time"

def get_advent_sunday_year_day(year):
    christmas_year_day = datetime(year,12,25).timetuple().tm_yday 
    return christmas_year_day - (22 + datetime(year,12,25).weekday())


def get_month_epoch(t=None):
    dt = get_utc_datetime(t)
    if dt.day < 11: return "early"
    if dt.day < 21: return "middle"
    return "late"

def get_year_day(t=ttime.time()):
    return get_utc_datetime(t).timetuple().tm_yday

def send_email(username, password, html, recipient, subject=""):

        message = MIMEMultipart("alternative")
        message["From"]    = username
        message["To"]      = recipient
        message["Subject"] = subject
        message.attach(MIMEText(html, "html"))
        
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(username, password)
        server.send_message(message)
        server.quit()

def add_italic_tags(text):
    """
    Converts to HTML italic format.
    """
    sections = []
    for i, section in enumerate(text.split("_")):
        if i % 2 == 1:
            section = "<i>" + re.sub("\n", "</i>\n<i>", section) + "</i>"
            section.replace("<i></i>", "")
        sections.append(section)
    return "".join(sections)

# def convert_to_html_lines(text):
#     """
#     Converts to HTML italic format.
#     """
#     html_lines = []
#     for line in text.split("\n"):
#         if len(line) == 0:
#             html_lines.append('<div class="poem-line-blank">&#8203</div>')
#         elif line[:2] == "> ":
#             html_lines.append(f'<div class="poem-line-title">{line}</div>')
#         elif line.strip().strip("_")[0] in ["“", "‘", "’"]:
#             html_lines.append(f'<div class="poem-line-punc-start">{line}</div>')
#         else:
#             html_lines.append(f'<div class="poem-line">{line}</div>')
            
#     return add_italic_tags("\n".join(html_lines))



# def text_to_html_lines(text):

#     text = text.replace("--", "&#8212;") # convert emdashes
#     text = add_italic_tags(text)

#     parsed_lines = []
#     for line in text.split("\n"):
#         if len(line) > 0:
#             parsed_lines.append(f'<div class="poem-line">{line.strip()}</div>')
#         else:
#             parsed_lines.append(f'<div class="poem-line-blank">&#8203;</div>')

#     return "\n".join(parsed_lines)