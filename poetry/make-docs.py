from datetime import datetime
import calendar
import pandas as pd
import github as gh
import sys; sys.path.insert(1, 'poetry/')
import numpy as np
from poetry import Poetizer
from context_utils import get_month, get_weekday, get_day, get_holiday, get_season, get_liturgy
import os
from io import StringIO

import argparse, sys
parser = argparse.ArgumentParser()
parser.add_argument('--username', type=str, help='Email address from which to send the poem',default='')
parser.add_argument('--password', type=str, help='Email password',default='')
parser.add_argument('--recipient', type=str, help='Where to send the poem',default='poemsfromtom@gmail.com')
parser.add_argument('--repo_lsfn', type=str, help='Where to send the poem',default='')
parser.add_argument('--poet', type=str, help='Which poet to send', default='random')
parser.add_argument('--title', type=str, help='Which title to send', default='random')
parser.add_argument('--repo', type=str, help='Which GH repository to load', default='')
parser.add_argument('--token', type=str, help='GH token', default='')
parser.add_argument('--context', type=bool, help='Whether to send contextual poems', default=False)
parser.add_argument('--rh', type=bool, help='Whether to consider past poems sent', default=False)
parser.add_argument('--wh', type=bool, help='Whether to consider this poem in the future', default=False)
parser.add_argument('--hist_tag', type=str, help='What tag to write to the history with', default='')
parser.add_argument('--subj_tag', type=str, help='Email subject prefix', default='')
parser.add_argument('--hour', type=str, help='Hour of the day to send', default=7)

args = parser.parse_args()

# Initialize the poetizer
poetizer = Poetizer()

print(args.repo, args.token)

# Choose a poem that meets the supplied conditions
poetizer.load_history(repo_name=args.repo, repo_token=args.token) # This automatically loads the repo as well
history = poetizer.history.copy()

dt_now = datetime.fromtimestamp(history.iloc[-1]['timestamp'])
now_date, now_time = dt_now.isoformat()[:19].split('T')
print(f'today is {now_date} {now_time}')
home_index = f'''
    <html>
    <head>
        <title></title>
        <meta http-equiv = "refresh" content="0; url=https://thomaswmorris.github.io/poems/{dt_now.year:02}/{dt_now.month:02}/{dt_now.day:02}" />
    </head>
    </html>
    '''

ymds = []
for i, loc in enumerate(history.index):
    y, m, d = history.loc[loc,'date'].split('-')
    ymds.append(f'{y:0>2}/{m:0>2}/{d:0>2}')

random_index = f'''
    <html>
        <title> </title>
        <script>
        var ymds = [{','.join([f'"{ymd}"' for ymd in ymds])}];
        window.location.href = "https://thomaswmorris.github.io/poems/" + ymds[Math.floor(Math.random() * ymds.length)];
        </script>
    </html>
    '''

poets_index = '<html><title>poets</title><br>\n'
for _poet in sorted(np.unique(history['poet'])):

    tag, name, birth, death, nationality, link = poetizer.data[_poet]['metadata'].values()
    title_list = history.sort_values('title').loc[history['poet']==_poet, 'title']
    date_list  = history.sort_values('title').loc[history['poet']==_poet, 'date']

    poets_index += f'''\n\n<p style="font-size: 30px;">{name} 
    <span style="font-family:Garamond; color:Black; font-size: 20px; margin-bottom:0; margin : 0; padding-top:0;">
    ({birth}&#8212;{death}) {poetizer.html_flags[nationality]}'''
    
    for title, date in zip(title_list, date_list):

        y, m, d = date.split('-')
        poets_index += f'\n<br><i><a href="https://thomaswmorris.github.io/poems/{y}/{m}/{d}">{poetizer.titleize(title)}</a></i>'
        
    poets_index += '\n<br><br></span></p>'

poets_index += '\n<html>'

####### 

archive_index = '<html><title>archive</title><br>\n'
_m = '0'
for index, entry in history.iterrows():

    poet, title, type, date, time, timestamp = entry
    tag, name, birth, death, nationality, link = poetizer.data[poet]['metadata'].values()

    y, m, d = date.split('-')

    if not m == _m:
        archive_index += f'\n<br><h2 style="font-size: 24px;">{get_month(timestamp).capitalize()} {y}</h2>'
        _m = m


    poetizer.load_poem(poet=poet, title=title, when=timestamp, verbose=False)

    archive_index += f'\n<i><p style="font-size: 18px;">{int(get_day(timestamp))} &#8212; '
    archive_index += f'<a href="https://thomaswmorris.github.io/poems/{y}/{m}/{d}">{poetizer.titleize(title)}</a>'
    archive_index += f' by <a href="{link}">{name}</a></i></p>'

archive_index += '\n<html>'

#######

blob  = poetizer.repo.create_git_blob(home_index, "utf-8")
elems = [gh.InputGitTreeElement(path='docs/index.html', mode='100644', type='blob', sha=blob.sha)]

blob  = poetizer.repo.create_git_blob(random_index, "utf-8")
elems.append(gh.InputGitTreeElement(path='docs/random/index.html', mode='100644', type='blob', sha=blob.sha))

blob  = poetizer.repo.create_git_blob(poets_index, "utf-8")
elems.append(gh.InputGitTreeElement(path='docs/poets/index.html', mode='100644', type='blob', sha=blob.sha))

blob  = poetizer.repo.create_git_blob(archive_index, "utf-8")
elems.append(gh.InputGitTreeElement(path='docs/archive/index.html', mode='100644', type='blob', sha=blob.sha))

n_history = len(history)
ys, ms, ds = [], [], []

for i, loc in enumerate(history.index):

    y, m, d = history.loc[loc,'date'].split('-')

    dt = datetime(int(y),int(m),int(d),7,0,0) 
    dt_prev = datetime.fromtimestamp(dt.timestamp() - 86400)
    dt_next = datetime.fromtimestamp(dt.timestamp() + 86400)
    
    poetizer.load_poem(poet=history.loc[loc,'poet'], title=history.loc[loc,'title'], when=history.loc[loc,'timestamp'], verbose=False)

    print(y, m, d, poetizer.poet, poetizer.title)

    prev_string = f'<a href="https://thomaswmorris.github.io/poems/{dt_prev.year:02}/{dt_prev.month:02}/{dt_prev.day:02}">«previous</a>' if i > 0 else ''
    next_string = f'<a href="https://thomaswmorris.github.io/poems/{dt_next.year:02}/{dt_next.month:02}/{dt_next.day:02}">next»</a>' if i < n_history - 1 else ''
    rand_string = f'<a href="https://thomaswmorris.github.io/poems/random">random</a>'
    poet_string = f'<a href="https://thomaswmorris.github.io/poems/poets">poets</a>'
    arch_string = f'<a href="https://thomaswmorris.github.io/poems/archive">archive</a>'

    html_header = f'''
        <html>
        <title>{poetizer.nice_fancy_date}</title>
            <p style="font-family:Garamond; color:Black; font-size: 18px; margin-bottom:0; margin : 0; padding-top:0;">
            <i><b>{prev_string}&nbsp;{poet_string}&nbsp;{rand_string}&nbsp;{arch_string}&nbsp;{next_string}</b>
            <br>{poetizer.nice_fancy_date}</i></p>
            <br>
        </html>
        '''
    index_fn = f'docs/{y}/{m}/{d}/index.html'

    try:
        index = poetizer.repo.get_contents(index_fn,ref='master').decoded_content.decode()
    except:
        index = None

    if html_header + poetizer.poem_html == index:
        continue

    blob = poetizer.repo.create_git_blob(html_header + poetizer.poem_html, "utf-8")
    elems.append(gh.InputGitTreeElement(path=index_fn, mode='100644', type='blob', sha=blob.sha))

    print(f'wrote to {index_fn}')

head_sha  = poetizer.repo.get_branch('master').commit.sha
base_tree = poetizer.repo.get_git_tree(sha=head_sha)

tree   = poetizer.repo.create_git_tree(elems, base_tree)
parent = poetizer.repo.get_git_commit(sha=head_sha) 

commit = poetizer.repo.create_git_commit(f'update logs {now_date} {now_time}', tree, [parent])
master_ref = poetizer.repo.get_git_ref('heads/master')
master_ref.edit(sha=commit.sha)


