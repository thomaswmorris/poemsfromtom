import json
import time as ttime
import numpy as np
import pandas as pd
from datetime import datetime
import argparse, sys, threading
from io import StringIO
sys.path.insert(0, "../poemsfromtom")
import poems
import warnings

parser = argparse.ArgumentParser()
parser.add_argument("--username", type=str, help="Email address from which to send the poem",default="")
parser.add_argument("--password", type=str, help="Email password",default="")
parser.add_argument("--listserv_filename", type=str, help="Where to send the poem",default="")
parser.add_argument("--github_repo_name", type=str, help="Which GH repository to load", default="")
parser.add_argument("--github_token", type=str, help="GH token", default="")
parser.add_argument("--kind", type=str, help="What tag to write to the history with", default="")
args = parser.parse_args()

# Initialize the curator
curator = poems.Curator()
curator.load_github_repo(github_repo_name=args.github_repo_name, github_token=args.github_token)

test = (args.kind == "test")

curator.read_history(filename="data/poems/history-daily.csv", from_repo=True)

when = ttime.time() if not test else ttime.time() + 365 * 86400 * np.random.uniform()

context = poems.utils.Context(timestamp=when).to_dict()

# Choose a poem that meets the supplied conditions
poem = curator.get_poem(
                        context=context, 
                        weight_schemes=["context", "history"],
                        forced_contexts=["holy_thursday", "good_friday", "holy_saturday", "easter_sunday", "christmas_eve", "christmas_day"],
                        verbose=True,
                        very_verbose=test,
                        )


subject = poem.test_email_subject if test else poem.daily_email_subject

contents = curator.repo.get_contents(args.listserv_filename, ref="master")
entries  = pd.read_csv(StringIO(contents.decoded_content.decode()), index_col=0)

def thread_process(poem, username, password, name, email, subject):

    done, fails = False, 0
    while (not done) and (fails < 60):
        try:
            poems.utils.send_email(username, password, poem.email_html, email, subject)
            a, b = email.split("@"); print(f"{datetime.now().isoformat()} | sent to {name:<18} | {a:>24} @ {b:<20}")
            done = True
        except Exception as e:
            print(e); fails += 1; ttime.sleep(60)

for name, email in zip(entries["name"], entries["email"]):

    t = threading.Thread(target=thread_process, args=(poem, args.username, args.password, name, email, subject))
    t.start()
    ttime.sleep(1e0)

# don't record this in the history
if test:
    curator.history.drop(index=curator.history.iloc[-1].name, inplace=True)
    
daily_poems = {}

for index, entry in curator.history.iterrows():
    try:
        p = curator.get_poem(author=entry.author, title=entry.title, when=entry.timestamp)
        daily_poems[str(index)] = {
                                   "date": entry.date,
                                   "author": {
                                             "name": p.author.name,
                                             "link": p.author.link,
                                             "dates": p.author.dates
                                             },
                                   "title": p.title,
                                   "body": p.html_body,
                                   "metadata": p.metadata
                                   }

    except Exception as e:
        warnings.warn(f"Could not find poem for entry {entry}")

curator.write_to_repo(items={
                            "data/poems/history-daily.csv" : curator.history.to_csv(), 
                            "data/poems/author-stats.csv"  : curator.stats.drop(columns=["days_since_last_sent"]).to_csv(),
                            "docs/assets/scripts/data/daily-poems.js" : f"var dailyPoems = {json.dumps(daily_poems, indent=4, ensure_ascii=False)}",
                            }, 
                            verbose=True)