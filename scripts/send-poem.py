import json
import time as ttime
from datetime import datetime
import argparse, threading
import warnings
import pytz

from numpy import random
from poems import Context, Curator
from poems import utils

parser = argparse.ArgumentParser()
parser.add_argument("--username", type=str, help="Email address from which to send the poem",default="")
parser.add_argument("--password", type=str, help="Email password",default="")
parser.add_argument("--listserv_filename", type=str, help="Where to send the poem",default="")
parser.add_argument("--github_repo_name", type=str, help="Which GH repository to load", default="")
parser.add_argument("--github_token", type=str, help="GH token", default="")
parser.add_argument("--kind", type=str, help="What tag to write to the history with", default="")
parser.add_argument('--write_to_repo', action=argparse.BooleanOptionalAction)
args = parser.parse_args()

test = (args.kind == "test")

curator = Curator()

repo = utils.load_github_repo(github_repo_name=args.github_repo_name, 
                              github_token=args.github_token)

history = utils.read_csv(repo=repo, filepath="data/poems/history-daily.csv")

when = ttime.time() if not test else ttime.time() + random.uniform(low=0, high=365 * 86400)
context = Context(timestamp=when)

print(f"using context {context.to_dict()}")

curator.catalog.apply_context(context.to_dict(), forced=["holy_thursday", "good_friday", "holy_saturday", "easter_sunday", "christmas_eve", "christmas_day"])
curator.catalog.apply_history(history, verbose=True)

# choose a poem 
p = curator.get_poem(verbose=True, very_verbose=test)
curator.catalog.reset()

if test:
    subject = f"TEST ({context.pretty_date}): {p.title_by_author} context={p.keywords}"
else:
    subject = p.daily_email_subject

listserv = utils.read_csv(repo=repo, filepath=args.listserv_filename)

for index, entry in listserv.iterrows():
    t = threading.Thread(target=utils.email_thread, args=(p, args.username, args.password, entry["name"], entry["email"], subject))
    t.start()
    ttime.sleep(1e0)

if not test:
    index = len(history) + 1
    now = Context.now()
    date, time = now.isoformat[:19].split("T")

    history.loc[index, "date"] = date
    history.loc[index, "time"] = time
    history.loc[index, "timestamp"] = int(now.timestamp)
    history.loc[index, "title"] = p.tag
    history.loc[index, "author"] = p.author.tag

daily_poems = {}
for index, entry in history.iterrows():
    try:
        p = curator.get_poem(author=entry.author, title=entry.title)
        c = Context(timestamp=entry.timestamp)

        packet = {
                "date": c.pretty_date,
                "description": p.html_description,
                "translation": f"Translated by {p.translator}" if p.translator else "",
                "spacetime": p.spacetime,
                "body": p.html_body,
                }

        daily_poems[str(index)] = packet

    except Exception as e:
        warnings.warn(f"Could not find poem for entry {entry}")

if args.write_to_repo:
    utils.write_to_repo(repo,
                        items={
                            "data/poems/history-daily.csv": history.to_csv(), 
                            "data/poems/author-stats.csv": utils.make_author_stats(history, catalog=curator.catalog).to_csv(),
                            "docs/assets/scripts/data/daily-poems.js": f"var dailyPoems = {json.dumps(daily_poems, indent=4, ensure_ascii=False)}",
                        }, 
                        verbose=True)