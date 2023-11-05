import ephem, re, pytz, smtplib
import numpy as np
import time as ttime
from datetime import datetime
from dateutil.easter import easter
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def get_context(x=None):
    when = get_utc_datetime(x).timestamp() if x is not None else ttime.time()
    return {
               "year" : get_year(when), 
           "year_day" : get_year_day(when),
            "weekday" : get_weekday(when), 
              "month" : get_month(when), 
                "day" : get_day(when),
        "month_epoch" : get_month_epoch(when),
             "season" : get_season(when), 
            "liturgy" : get_liturgy(when), 
            "holiday" : get_holiday(when),
          "timestamp" : when,
            }


def get_utc_datetime(when=None):
    if type(when) == str: 
        when = datetime.fromisoformat(when).replace(tzinfo=pytz.utc).timestamp()
    if when is None: 
        when = ttime.time()
    return datetime.fromtimestamp(when).astimezone(pytz.utc)

def get_weekday(t=None):
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    return weekdays[get_utc_datetime(t).weekday()]

def get_year(t=None):
    return f"{get_utc_datetime(t).year:04}"

def get_month(t=None):
    months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
    return months[get_utc_datetime(t).month-1]

def get_day(t=None):
    return f"{get_utc_datetime(t).day:02}"

def get_season(t=None):
    year = get_utc_datetime(t).year
    yday = get_utc_datetime(t).timetuple().tm_yday
    if yday < get_solstice_or_equinox_year_day(year, "spring"):
        return "winter"
    if yday < get_solstice_or_equinox_year_day(year, "summer"):
        return "spring"
    if yday < get_solstice_or_equinox_year_day(year, "autumn"):
        return "summer"
    if yday < get_solstice_or_equinox_year_day(year, "winter"):
        return "autumn"
    return "winter"

def get_holiday(t=None):
    dt = get_utc_datetime(t)
    yd = dt.timetuple().tm_yday

    year, month, day, weekday = dt.year, dt.month, dt.day, dt.weekday()

    # how many of this weekday have there been in this month before?
    weekday_count = int((day - 1) / 7)
    
    # these are easter things, which supersede all others
    easter_yd = easter(dt.year).timetuple().tm_yday 
    if yd == easter_yd - 47: return "mardi_gras"
    elif yd == easter_yd - 46: return "ash_wednesday"
    elif yd == easter_yd - 7:  return "palm_sunday"
    elif yd == easter_yd - 3:  return "holy_thursday"
    elif yd == easter_yd - 2:  return "good_friday"
    elif yd == easter_yd - 1:  return "holy_saturday"
    elif yd == easter_yd:      return "easter_sunday"
    elif yd == easter_yd + 7:  return "divine_mercy"
    elif yd == easter_yd + 39: return "ascension"
    elif yd == easter_yd + 49: return "pentecost"
    elif yd == easter_yd + 56: return "trinity_sunday"
    elif yd == easter_yd + 60: return "corpus_christi"
    elif yd == easter_yd + 68: return "sacred_heart_of_jesus"
    elif yd == easter_yd + 69: return "immaculate_heart_of_mary"
    
    elif (month, weekday, weekday_count) == (2, 0, 2):  return "presidents_day" # third monday of february
    elif (month, weekday, weekday_count) == (5, 6, 1):  return "mothers_day" # second sunday of may
    elif (month, weekday, weekday_count) == (6, 6, 2):  return "fathers_day" # third sunday of june
    elif (month, weekday, weekday_count) == (9, 0, 0):  return "labor_day" # first monday of september
    elif (month, weekday, weekday_count) == (11, 3, 3): return "thanksgiving" # fourth thursday of november

    # these are weird
    elif (month, weekday) == (5, 0) and (get_utc_datetime(t + 7 * 86400).month == 6): return "memorial_day" # last monday of may

    # these are weird
    elif (get_liturgy(t - 86400) != "advent") & (get_liturgy(t) == "advent"): return "advent_sunday"
    elif get_holiday(t + 7 * 86400) == "advent_sunday": return "christ_the_king"

    # these are on specific dates 
    elif (month, day) == (1, 1):   return "new_years_day"
    elif (month, day) == (1, 2):   return "saint_basil"
    elif (month, day) == (1, 3):   return "holy_name_of_jesus"
    elif (month, day) == (1, 6):   return "epiphany"
    elif (month, day) == (1, 20):  return "saint_agnes_eve"
    elif (month, day) == (1, 21):  return "saint_agnes"
    elif (month, day) == (1, 24):  return "saint_francis_de_sales"
    elif (month, day) == (1, 25):  return "conversion_of_saint_paul"
    elif (month, day) == (1, 28):  return "saint_thomas_aquinas"
    elif (month, day) == (1, 31):  return "saint_john_bosco"

    elif (month, day) == (2, 2):   return "candlemas"
    elif (month, day) == (2, 11):  return "our_lady_of_lourdes"
    elif (month, day) == (2, 14):  return "saint_valentine"
    elif (month, day) == (2, 22):  return "chair_of_peter"
    elif (month, day) == (2, 29):  return "leap_day"

    elif (month, day) == (3, 7):   return "saints_perpetua_and_felicity"
    elif (month, day) == (3, 8):   return "saint_john_of_god"
    elif (month, day) == (3, 17):  return "saint_patrick"
    elif (month, day) == (3, 19):  return "saint_joseph"
    elif (month, day) == (3, 25):  return "annunciation"

    elif (month, day) == (4, 1):   return "april_fools"
    elif (month, day) == (4, 5):   return "saint_vincent_ferrer"
    elif (month, day) == (4, 11):  return "saint_stanislaus"
    elif (month, day) == (4, 21):  return "saint_anselm"
    elif (month, day) == (4, 23):  return "saint_george"
    elif (month, day) == (4, 25):  return "saint_mark"
    elif (month, day) == (4, 29):  return "saint_catherine_of_siena"

    elif (month, day) == (5, 1):   return "may_day"
    elif (month, day) == (5, 3):   return "saints_philip_and_james"
    elif (month, day) == (5, 13):  return "our_lady_of_fatima"
    elif (month, day) == (5, 14):  return "saint_matthias"
    elif (month, day) == (5, 26):  return "saint_philip_neri"
    elif (month, day) == (5, 31):  return "visitation"

    elif (month, day) == (6, 13):  return "saint_anthony"
    elif (month, day) == (6, 19):  return "juneteenth"
    elif (month, day) == (6, 23):  return "saint_johns_eve"
    elif (month, day) == (6, 24):  return "saint_john_the_baptist"
    elif (month, day) == (6, 29):  return "saints_peter_and_paul"
    
    elif (month, day) == (7, 1):   return "saint_junipero_serra"
    elif (month, day) == (7, 3):   return "saint_thomas_the_apostle"
    elif (month, day) == (7, 4):   return "independence_day"
    elif (month, day) == (7, 6):   return "saint_maria_goretti"
    elif (month, day) == (7, 11):  return "saint_benedict"
    elif (month, day) == (7, 15):  return "saint_bonaventure"
    elif (month, day) == (7, 16):  return "our_lady_of_mount_carmel"
    elif (month, day) == (7, 17):  return "saint_alexis"
    elif (month, day) == (7, 22):  return "saint_mary_magdalene"
    elif (month, day) == (7, 25):  return "saint_james"
    elif (month, day) == (7, 31):  return "saint_ignatius_of_loyola"

    elif (month, day) == (8, 1):   return "lammas"
    elif (month, day) == (8, 6):   return "transfiguration"
    elif (month, day) == (8, 8):   return "saint_dominic"
    elif (month, day) == (8, 10):  return "saint_lawrence"
    elif (month, day) == (8, 14):  return "saint_maximilian_kolbe"
    elif (month, day) == (8, 15):  return "assumption"
    elif (month, day) == (8, 22):  return "coronation"
    elif (month, day) == (8, 24):  return "saint_bartholomew"
    elif (month, day) == (8, 27):  return "saint_monica"
    elif (month, day) == (8, 28):  return "saint_augustine"
    elif (month, day) == (8, 28):  return "beheading_of_john_the_baptist"

    elif (month, day) == (9, 3):   return "saint_gregory_the_great"
    elif (month, day) == (9, 8):   return "marymas"
    elif (month, day) == (9, 12):  return "holy_name_of_mary"
    elif (month, day) == (9, 13):  return "saint_john_chrysostom"
    elif (month, day) == (9, 14):  return "holy_cross"
    elif (month, day) == (9, 15):  return "our_lady_of_sorrows"
    elif (month, day) == (9, 19):  return "our_lady_of_la_salette"
    elif (month, day) == (9, 21):  return "saint_matthew"
    elif (month, day) == (9, 23):  return "saint_padre_pio"
    elif (month, day) == (9, 29):  return "michaelmas"
    elif (month, day) == (9, 30):  return "saint_jerome"

    elif (month, day) == (10, 1):  return "saint_therese_of_lisieux"
    elif (month, day) == (10, 2):  return "guardian_angels"
    elif (month, day) == (10, 4):  return "saint_francis"
    elif (month, day) == (10, 7):  return "our_lady_of_the_rosary"
    elif (month, day) == (10, 15): return "saint_teresa_of_avila"
    elif (month, day) == (10, 16): return "saint_hedwig"
    elif (month, day) == (10, 17): return "saint_ignatius_of_antioch"
    elif (month, day) == (10, 18): return "saint_luke"
    elif (month, day) == (10, 22): return "saint_john_paul"
    elif (month, day) == (10, 28): return "saints_simon_and_jude"
    elif (month, day) == (10, 31): return "halloween"
    
    elif (month, day) == (11, 1):  return "all_saints"
    elif (month, day) == (11, 2):  return "all_souls"
    elif (month, day) == (11, 3):  return "saint_malachy"
    elif (month, day) == (11, 8):  return "blessed_duns_scotus"
    elif (month, day) == (11, 10): return "saint_leo_the_great"
    elif (month, day) == (11, 11): return "veterans_day"
    elif (month, day) == (11, 15): return "saint_albert"
    elif (month, day) == (11, 21): return "presentation_of_mary"
    elif (month, day) == (11, 22): return "saint_cecilia"
    elif (month, day) == (11, 30): return "saint_andrew"
    
    elif (month, day) == (12, 3):  return "saint_francis_xavier"
    elif (month, day) == (12, 6):  return "saint_nicholas"
    elif (month, day) == (12, 7):  return "saint_ambrose"
    elif (month, day) == (12, 8):  return "immaculate_conception"
    elif (month, day) == (12, 9):  return "saint_juan_diego"
    elif (month, day) == (12, 10): return "our_lady_of_loreto"
    elif (month, day) == (12, 12): return "our_lady_of_guadalupe"
    elif (month, day) == (12, 13): return "saint_lucia"
    elif (month, day) == (12, 14): return "saint_john_of_the_cross"
    elif (month, day) == (12, 24): return "christmas_eve"
    elif (month, day) == (12, 25): return "christmas_day"
    elif (month, day) == (12, 26): return "saint_stephen"
    elif (month, day) == (12, 27): return "saint_john_the_apostle"
    elif (month, day) == (12, 28): return "holy_innocents"
    elif (month, day) == (12, 29): return "saint_thomas_becket"
    elif (month, day) == (12, 31): return "new_years_eve"

    # not important
    elif yd == get_solstice_or_equinox_year_day(year, "spring"): return "spring_equinox"
    elif yd == get_solstice_or_equinox_year_day(year, "summer"): return "summer_solstice"
    elif yd == get_solstice_or_equinox_year_day(year, "autumn"): return "autumn_equinox"
    elif yd == get_solstice_or_equinox_year_day(year, "winter"): return "winter_solstice"


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
    yd = dt.timetuple().tm_yday
    weekday = dt.weekday()
    easter_yd = easter(dt.year).timetuple().tm_yday 
    christmas_yd = datetime(dt.year,12,25).timetuple().tm_yday 
    if yd <= 5 or yd >= christmas_yd: 
        return "christmastide"
    if 3 < easter_yd - dt.date().timetuple().tm_yday <= 46: 
        return "lent"
    if 0 < easter_yd - dt.date().timetuple().tm_yday <= 3: 
        return "triduum"
    if -39 < easter_yd - dt.date().timetuple().tm_yday <= 0: 
        return "eastertide"
    if christmas_yd - (22 + datetime(dt.year,12,25).weekday()) <= yd < christmas_yd: 
        return "advent"
    return "ordinary time"

def get_month_epoch(t=ttime.time()):
    day = int(get_day(t=t))
    if day < 11: return "early"
    if day < 21: return "middle"
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


# raw:

# monospace:

# html: 




def uppercase_title(text):
    """
    Capitalizes the part in quotes.
    """
    prefix, title, suffix = re.search(r"(.*)“(.*)”(.*)", text).groups(0)
    return f"{prefix}“{title.upper()}”{suffix}"

# def add_italic_tags(text):
#     """
#     Converts to HTML italic format.
#     """

#     for span in re.findall(r"(_[\w\W]+?_)", text): 
#         text = re.sub(fr"{span}", re.sub(r"\n", r"_\n_", fr"{span}"), text) # add italic around all line breaks
#     text = re.sub(r"_([\w\W]*?)_", r"<i>\1</i>", text) # convert to html italic notation

#     return text

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

def convert_to_html_lines(text):
    """
    Converts to HTML italic format.
    """
    html_lines = []
    for line in text.split("\n"):
        if len(line) == 0:
            html_lines.append('''<div class="opus-line-blank">&#8203</div>''')
        elif line.strip().strip("_")[0] in ["“", "‘", "’"]:
            html_lines.append(f'''<div class="opus-line-punc-start">{line}</div>''')
        else:
            html_lines.append(f'''<div class="opus-line">{line}</div>''')
            
    return add_italic_tags("\n".join(html_lines))



def text_to_html_lines(text):

    text = text.replace("--", "&#8212;") # convert emdashes
    text = add_italic_tags(text)

    parsed_lines = []
    for line in text.split("\n"):
        if len(line) > 0:
            parsed_lines.append(f'<div class="opus-line">{line.strip()}</div>')
        else:
            parsed_lines.append(f'<div class="opus-line-blank">&#8203;</div>')

    return "\n".join(parsed_lines)