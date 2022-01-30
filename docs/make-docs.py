

from datetime import datetime
import calendar
import pandas as pd
import sys
sys.path.insert(1, 'poetry/')
from poetry import Poetizer
import os


history  = pd.read_csv('history.csv',index_col=0)
poetizer = Poetizer()

dt_now = datetime.now()

with open('docs/index.html','w+') as f:
    f.write(f'''
    <html>
    <head>
        <title>HTML Meta Tag</title>
        <meta http-equiv = "refresh" content="0; url=https://thomaswmorris.github.io/poetry/{dt_now.year:02}/{dt_now.month:02}/{dt_now.day:02}" />
    </head>
    <body>
        <p>Redirecting to another URL</p>
    </body>
    </html>
    ''')

ys, ms, ds = [], [], []
for loc in history.index:

    y, m, d = history.loc[loc,'date'].split('-')

    dt = datetime(int(y),int(m),int(d),7,0,0) 
    dt_prev = datetime.fromtimestamp(dt.timestamp() - 86400)
    dt_next = datetime.fromtimestamp(dt.timestamp() + 86400)

    if not os.path.isdir(f'docs/{y}'):         os.mkdir(f'docs/{y}')
    if not os.path.isdir(f'docs/{y}/{m}'):     os.mkdir(f'docs/{y}/{m}')
    if not os.path.isdir(f'docs/{y}/{m}/{d}'): os.mkdir(f'docs/{y}/{m}/{d}')

    nice_fancy_date = f'{poetizer.weekdays[dt.weekday()].capitalize()}, {calendar.month_name[dt.month]} {dt.day:02} {dt.year}'
    poetizer.load_poem(poet=history.loc[loc,'poet'], title=history.loc[loc,'title'])

    html_header = f'''
        <html>
            <h2 style="font-family:Garamond; color:Black; font-size: 16px; margin-bottom:0; margin : 0; padding-top:0;">
            <a href="https://thomaswmorris.github.io/poetry/{dt_prev.year:02}/{dt_prev.month:02}/{dt_prev.day:02}">previous</a>
            <a href="https://thomaswmorris.github.io/poetry/{dt_next.year:02}/{dt_next.month:02}/{dt_next.day:02}">next</a>
            <p style="font-family:Garamond; color:Black; font-size: 16px; margin-bottom:0; margin : 0; padding-top:0">{nice_fancy_date}
            </p>
            <br>
        </h2>
        </html>
        '''

    with open(f'docs/{y}/{m}/{d}/index.html','w+') as f:
        f.write(html_header + poetizer.poem_html)



