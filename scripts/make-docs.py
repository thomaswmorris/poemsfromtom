from datetime import datetime
import time as ttime
import github as gh
import pytz, re, sys
sys.path.insert(0, '../poems')
import poems

import argparse, sys
parser = argparse.ArgumentParser()
parser.add_argument('--github_repo_name', type=str, help='Which GH repository to load', default='')
parser.add_argument('--github_token', type=str, help='GH token', default='')
args = parser.parse_args()

# Initialize the curator
curator = poems.Curator()
curator.load_github_repo(github_repo_name=args.github_repo_name, github_token=args.github_token)
curator.read_history(filename='data/poems/daily-history.csv', from_repo=True)

dt_last = datetime.fromtimestamp(curator.history.iloc[-1].timestamp).astimezone(pytz.utc)
last_date, last_time = dt_last.isoformat()[:19].split('T')
print(f'today is {last_date} {last_time}')

index_html = f'''<html>
<head>
<meta http-equiv="refresh" content="0; url={dt_last.year:02}-{dt_last.month:02}-{dt_last.day:02}"/>
</head>
</html>'''

random_html = '''<html>
<script>
function randomDate(start, end) {
var date = new Date(+start + Math.random() * (end - start));
return date;}'''

random_html += f'''
window.location.href = randomDate(new Date(2021, 10, 22), new Date({dt_last.year}, {dt_last.month-1}, {dt_last.day})).toISOString().slice(0, 10)
</script>
</html>'''

elems = []

blob = curator.repo.create_git_blob(index_html, "utf-8")
elems.append(gh.InputGitTreeElement(path='docs/poems/index.html', mode='100644', type='blob', sha=blob.sha))

blob = curator.repo.create_git_blob(random_html, "utf-8")
elems.append(gh.InputGitTreeElement(path='docs/poems/random.html', mode='100644', type='blob', sha=blob.sha))

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

ys, ms, ds = [], [], []

print(f"writing docs for n={len(curator.history)} poems")

for index, entry in curator.history.iterrows():

    y, m, d = entry.date.split('-')

    dt = datetime(int(y), int(m), int(d), 12, 0, 0, tzinfo=pytz.utc) 
    dt_prev = datetime.fromtimestamp(dt.timestamp() - 86400)
    dt_next = datetime.fromtimestamp(dt.timestamp() + 86400)
    
    poem = curator.get_poem(author=entry.author, 
                            title=entry.title, 
                            context={'timestamp' : dt.timestamp()},
                            verbose=False)

    prev_string = f'<li class="nav-item left"><a class="nav-link" href="/poems/{dt_prev.year:02}-{dt_prev.month:02}-{dt_prev.day:02}">«previous</a></li>' if index != curator.history.index[0] else ''

    next_string = f'<li class="nav-item left"><a class="nav-link" href="/poems/{dt_next.year:02}-{dt_next.month:02}-{dt_next.day:02}">next»</a></li>' if index != curator.history.index[-1] else ''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{poem.nice_fancy_date}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="stylesheet" href="/css/style.css">
</head>
<header style="background-image: url('/assets/images/bg/pissaro-pontoise.jpeg')"></header>
<nav>
    <ul>
        <li><a href="/">home</a></li>
        <li><a href="/music">music</a></li>
        <li><a href="/poems">poems</a></li>    
        <li><a href="/xw">crosswords</a></li>
        <li><a href="/blog">blog</a></li>
    </ul>
    <ul>
        {prev_string}
        <li class="nav-item left"><a class="nav-link" href="/poems/random">random</a></li>
        {next_string}
    </ul>
</nav>
<body>
{poem.html}
</body>
</html>
'''

    filepath = f'docs/poems/{y}-{m}-{d}.html'
    try: 
        contents = curator.repo.get_contents(filepath, ref='master').decoded_content.decode()
    except: 
        contents = None
    if html != contents:
        print(f'OVERWRITE #{index:>03} {y}/{m}/{d} {poem.author:>12} {poem.title}')
    else:
        print(f'          #{index:>03} {y}/{m}/{d} {poem.author:>12} {poem.title}')
        continue
    
    blob = curator.repo.create_git_blob(html, "utf-8")
    elems.append(gh.InputGitTreeElement(path=filepath, mode='100644', type='blob', sha=blob.sha))
    
    if len(elems) >= 64: 
        commit_elements(elems)
        elems = []
        ttime.sleep(30) # just chill out, github doesn't like rapid commits

commit_elements(elems)