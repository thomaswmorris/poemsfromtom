from datetime import datetime
import calendar
import pandas as pd
import github as gh
import sys; sys.path.insert(1, 'poetry/')
import numpy as np
import poetry
from context_utils import get_month, get_weekday, get_day, get_holiday, get_season, get_liturgy
import os, re
from io import StringIO
import pytz

import argparse, sys
parser = argparse.ArgumentParser()
parser.add_argument('--username', type=str, help='Email address from which to send the poem',default='')
parser.add_argument('--password', type=str, help='Email password',default='')
parser.add_argument('--recipient', type=str, help='Where to send the poem',default='poemsfromtom@gmail.com')
parser.add_argument('--repo_lsfn', type=str, help='Where to send the poem',default='')
parser.add_argument('--author', type=str, help='Which author to send', default='random')
parser.add_argument('--title', type=str, help='Which title to send', default='random')
parser.add_argument('--repo', type=str, help='Which GH repository to load', default='')
parser.add_argument('--token', type=str, help='GH token', default='')
parser.add_argument('--context', type=bool, help='Whether to send contextual poems', default=False)
parser.add_argument('--rh', type=bool, help='Whether to consider past poems sent', default=False)
parser.add_argument('--wh', type=bool, help='Whether to consider this poem in the future', default=False)
parser.add_argument('--hist_tag', type=str, help='What tag to write to the history with', default='')
parser.add_argument('--subj_tag', type=str, help='Email subject prefix', default='')
parser.add_argument('--hour', type=str, help='Hour of the day to send', default=7)
parser.add_argument('--token_from_heroku', type=bool, help='Whether to get token from os env', default=False)

args = parser.parse_args()

if args.token_from_heroku: args.token = os.environ['GITHUB_TOKEN']

def commit_elements(_elems):

    dt_now = datetime.fromtimestamp(history.iloc[-1]['timestamp']).astimezone(pytz.utc)
    now_date, now_time = dt_now.isoformat()[:19].split('T') 

    head_sha  = curator.repo.get_branch('master').commit.sha
    base_tree = curator.repo.get_git_tree(sha=head_sha)

    tree   = curator.repo.create_git_tree(_elems, base_tree)
    parent = curator.repo.get_git_commit(sha=head_sha) 

    commit = curator.repo.create_git_commit(f'update logs {now_date} {now_time}', tree, [parent])
    master_ref = curator.repo.get_git_ref('heads/master')
    master_ref.edit(sha=commit.sha)

# Initialize the curator
curator = poetry.Curator()

print(args.repo, args.token)

# Initialize the curator
curator.load_history(repo_name=args.repo, repo_token=args.token)
history = curator.history.copy()

history['strip_title'] = [re.sub(r'^(THE|AN|A)\s+', '', title) for title in history['title']]

dt_now = datetime.now() #fromtimestamp(history.iloc[-1]['timestamp']).astimezone(pytz.utc)
now_date, now_time = dt_now.isoformat()[:19].split('T')
print(f'today is {now_date} {now_time}')

home_index = f'''
    <html>
    <head>
        <title></title>
        <meta http-equiv="refresh" content="0; url={dt_now.year:02}-{dt_now.month:02}-{dt_now.day:02}"/>
    </head>
    </html>
    '''

ymds = []
for i, entry in curator.history.iterrows():
    y, m, d = entry.date.split('-')
    ymds.append(f'{y:0>2}-{m:0>2}-{d:0>2}')

random_index = f'''
    <html>
        <title> </title>
        <script>
        var ymds = [{','.join([f'"{ymd}"' for ymd in ymds])}];
        window.location.href = ymds[Math.floor(Math.random() * ymds.length)];
        </script>
    </html>
    '''

#######

blob  = curator.repo.create_git_blob(home_index, "utf-8")
elems = [gh.InputGitTreeElement(path='poems/index.html', mode='100644', type='blob', sha=blob.sha)]

blob  = curator.repo.create_git_blob(random_index, "utf-8")
elems.append(gh.InputGitTreeElement(path='poems/random.html', mode='100644', type='blob', sha=blob.sha))

n_history = len(history)
ys, ms, ds = [], [], []

for i, entry in curator.history.iterrows():

    y, m, d = entry.date.split('-')

    dt = datetime(int(y),int(m),int(d),12,0,0,tzinfo=pytz.utc) 
    dt_prev = datetime.fromtimestamp(dt.timestamp() - 86400)
    dt_next = datetime.fromtimestamp(dt.timestamp() + 86400)
    
    poem = curator.load_poem(author=entry.author, title=entry.title, when=entry.timestamp, verbose=False, include_flags=True)

    print(y, m, d, poem.author, poem.title)

    prev_string = f'<li class="nav-item left"><a class="nav-link" href="{dt_prev.year:02}-{dt_prev.month:02}-{dt_prev.day:02}">«Previous</a></li>' if i > 0 else ''
    next_string = f'<li class="nav-item left"><a class="nav-link" href="{dt_next.year:02}-{dt_next.month:02}-{dt_next.day:02}">Next»</a></li>' if i < n_history - 1 else ''
    rand_string = f'<a href="random">random</a>'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head><!DOCTYPE html>
    <meta charset="utf-8">
    <title>{poem.nice_fancy_date}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="stylesheet" href="../assets/css/style.css">
</head>
    <body class="static-layout" background="../assets/images/bg/monet-haystacks.jpg">
        <div class="boxed-page">
            <nav>
                <ul>
                    {prev_string}
                    <li class="nav-item left"><a class="nav-link" href="random">Random</a></li>
                    {next_string}
                    <li class="nav-item right"><a class="nav-link" href="../blog">Blog</a></li>
                    <li class="nav-item right"><a class="nav-link" href="../xw">Crosswords</a></li>
                    <li class="nav-item right"><a class="nav-link" href="../poems">Poems</a></li>    
                    <li class="nav-item right"><a class="nav-link" href="../projects">Projects</a></li>
                    <li class="nav-item right"><a class="nav-link" href="../papers">Papers</a></li>
                    <li class="nav-item right"><a class="nav-link" href="../cv">CV</a></li>
                    <li class="nav-item right"><a class="nav-link" href="..">Home</a></li>
                </ul>
            </nav>
            <section class="bg-white">
                <div class="section-content" style="border-collapse:collapse; padding-left: 5%; padding-right: 5%;">
                    {poem.html_header}
                    {poem.html_body}
                </div>
            </div>
        </section>		
    </body>
</html>
'''

    index_fn = f'poems/{y}-{m}-{d}.html'

    try:    contents = curator.repo.get_contents(index_fn, ref='master').decoded_content.decode()
    except: contents = None

    print(32*'#')

    if html == contents:
        continue

    blob = curator.repo.create_git_blob(html, "utf-8")
    elems.append(gh.InputGitTreeElement(path=index_fn, mode='100644', type='blob', sha=blob.sha))

commit_elements(elems)