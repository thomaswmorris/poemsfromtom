from datetime import datetime
import time as ttime
import github as gh
import pytz, re, sys
sys.path.insert(0, '../poetry')
import poetry

import argparse, sys
parser = argparse.ArgumentParser()
parser.add_argument('--github_repo_name', type=str, help='Which GH repository to load', default='')
parser.add_argument('--github_token', type=str, help='GH token', default='')
args = parser.parse_args()

# Initialize the curator
curator = poetry.Curator()
curator.load_github_repo(github_repo_name=args.github_repo_name, github_token=args.github_token)
curator.read_history(filename='poems/history.csv', from_repo=True)
history = curator.history.copy()

history['strip_title'] = [re.sub(r'^(THE|AN|A)\s+', '', title) for title in history['title']]

dt_last = datetime.fromtimestamp(curator.history.iloc[-1].timestamp).astimezone(pytz.utc) #fromtimestamp(history.iloc[-1]['timestamp']).astimezone(pytz.utc)
last_date, last_time = dt_last.isoformat()[:19].split('T')
print(f'today is {last_date} {last_time}')

home_html = f'''
    <html>
    <head>
        <title></title>
        <meta http-equiv="refresh" content="0; url={dt_last.year:02}-{dt_last.month:02}-{dt_last.day:02}"/>
    </head>
    </html>
    '''

ymds = []
for i, entry in curator.history.iterrows():
    y, m, d = entry.date.split('-')
    ymds.append(f'{y:0>2}-{m:0>2}-{d:0>2}')

random_html = f'''
    <html>
        <title> </title>
        <script>
        var ymds = [{','.join([f'"{ymd}"' for ymd in ymds])}];
        window.location.href = ymds[Math.floor(Math.random() * ymds.length)];
        </script>
    </html>
    '''

#######

def commit_elements(elements):

    print(f'\ncommitting {len(elements)} elements...\n')

    now = datetime.now(tz=pytz.utc)
    now_date, now_time = now.isoformat()[:19].split('T') 

    head_sha  = curator.repo.get_branch('master').commit.sha
    base_tree = curator.repo.get_git_tree(sha=head_sha)

    tree   = curator.repo.create_git_tree(elements, base_tree)
    parent = curator.repo.get_git_commit(sha=head_sha) 

    commit = curator.repo.create_git_commit(f'update logs {now_date} {now_time}', tree, [parent])
    master_ref = curator.repo.get_git_ref('heads/master')
    master_ref.edit(sha=commit.sha)

blob  = curator.repo.create_git_blob(home_html, "utf-8")
elems = [gh.InputGitTreeElement(path='poems/index.html', mode='100644', type='blob', sha=blob.sha)]

blob  = curator.repo.create_git_blob(random_html, "utf-8")
elems.append(gh.InputGitTreeElement(path='poems/random.html', mode='100644', type='blob', sha=blob.sha))

n_history = len(history)
ys, ms, ds = [], [], []

for i, entry in curator.history.iterrows():

    y, m, d = entry.date.split('-')

    dt = datetime(int(y), int(m), int(d), 12, 0, 0, tzinfo=pytz.utc) 
    dt_prev = datetime.fromtimestamp(dt.timestamp() - 86400)
    dt_next = datetime.fromtimestamp(dt.timestamp() + 86400)
    
    poem = curator.get_poem(author=entry.author, 
                            title=entry.title, 
                            context={'timestamp' : dt.timestamp()},
                            verbose=False)

    print(f'{y}-{m}-{d} {poem.author:>12} {poem.title}')

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

    filepath = f'poems/{y}-{m}-{d}.html'
    try:    contents = curator.repo.get_contents(filepath, ref='master').decoded_content.decode()
    except: contents = None
    if html == contents:
        continue
    
    blob = curator.repo.create_git_blob(html, "utf-8")
    elems.append(gh.InputGitTreeElement(path=filepath, mode='100644', type='blob', sha=blob.sha))
    print(f'creating file {filepath}')
    print(32*'#')

    if len(elems) >= 64: 
        commit_elements(elems)
        elems = []
        ttime.sleep(60) # just chill out, github doesn't like rapid commits

commit_elements(elems)