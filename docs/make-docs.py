

from datetime import datetime
import pandas as pd
import sys
sys.path.insert(1, 'poetry/')
from poetry import Poetizer
import os


history  = pd.read_csv('history.csv',index_col=0)
poetizer = Poetizer()



ys, ms, ds = [], [], []
for loc in history.index:

    y, m, d = [int(x) for x in history.loc[loc,'date'].split('-')]

    dt = datetime(y,m,d,7,0,0) 
    dt_prev = datetime.fromtimestamp(dt.timestamp() - 86400)
    dt_next = datetime.fromtimestamp(dt.timestamp() + 86400)

    if not os.path.isdir(f'docs/{y}'):         os.mkdir(f'docs/{y}')
    if not os.path.isdir(f'docs/{y}/{m}'):     os.mkdir(f'docs/{y}/{m}')
    if not os.path.isdir(f'docs/{y}/{m}/{d}'): os.mkdir(f'docs/{y}/{m}/{d}')


    poetizer.load_poem(poet=history.loc[loc,'poet'], title=history.loc[loc,'title'])


    html = f'''
    <html>
        <h2 style="font-family:Garamond; color:Black; font-size: 24px; margin-bottom:0; margin : 0; padding-top:0;">
        <a href="thomaswmorris.github.io/poetry/{dt_prev.year}/{dt_prev.month}/{dt_prev.day}">previous</a>
        <a href="thomaswmorris.github.io/poetry/{dt_next.year}/{dt_next.month}/{dt_next.day}">next</a>
        </h2>
    </html>
    '''

    with open(f'docs/{y}/{m}/{d}/index.html','w') as f:
        f.write(html + poetizer.poem_html)



