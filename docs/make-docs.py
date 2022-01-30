


import pandas as pd
import sys
sys.path.insert(1, 'poetry/')
from poetry import Poetizer
import os


history  = pd.read_csv('history.csv',index_col=0)
poetizer = Poetizer()



ys, ms, ds = [], [], []
for loc in history.index:

    y, m, d = history.loc[loc,'date'].split('-')

    if not os.path.isdir(f'docs/{y}'):         os.mkdir(f'docs/{y}')
    if not os.path.isdir(f'docs/{y}/{m}'):     os.mkdir(f'docs/{y}/{m}')
    if not os.path.isdir(f'docs/{y}/{m}/{d}'): os.mkdir(f'docs/{y}/{m}/{d}')

    poetizer.load_poem(poet=history.loc[loc,'poet'], title=history.loc[loc,'title'])

    with open(f'docs/{y}/{m}/{d}/index.html','w') as f:
        f.write(poetizer.poem_html)



