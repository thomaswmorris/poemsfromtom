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
parser.add_argument("--username", type=str, help="Email address from which to send the poem", default="")
parser.add_argument("--password", type=str, help="Email password", default="")
parser.add_argument("--listserv_filename", type=str, help="Where to send the poem", default="")
parser.add_argument("--github_repo_name", type=str, help="Which GH repository to load", default="")
parser.add_argument("--github_token", type=str, help="GH token", default="")
parser.add_argument("--mode", type=str, help="What mode to send the poem in", default="test")
parser.add_argument('--write_to_repo', action=argparse.BooleanOptionalAction, default=False)
args = parser.parse_args()

curator = Curator()

repo = utils.load_github_repo(github_repo_name=args.github_repo_name, 
                              github_token=args.github_token)

history = utils.read_csv(repo=repo, filepath="data/poems/history-daily.csv")

when = ttime.time() if args.mode == "daily" else ttime.time() + random.uniform(low=0, high=365 * 86400)
context = Context(timestamp=when)

print(f"using context {context.to_dict()}")

curator.catalog.apply_context(context.to_dict(), forced=["holy_thursday", "good_friday", "holy_saturday", "easter_sunday", "christmas_eve", "christmas_day"])
curator.catalog.apply_history(history, verbose=True)

# choose a poem
p = curator.get_poem(very_verbose=True)
curator.catalog.reset()

thread_kwargs = {"username": args.username,
                 "password": args.password,
                 "subject": p.email_subject(mode=args.mode),
                 "content": p.email_html}

listserv = utils.read_csv(repo=repo, filepath=args.listserv_filename)
for index, entry in listserv.iterrows():
    t = threading.Thread(target=utils.email_thread, kwargs={**thread_kwargs, "recipient": entry.email})
    t.start()
    ttime.sleep(1e0)

if args.write_to_repo:

    if args.mode == "daily":
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
                    "header": p.html_header(),
                    "body": p.html_body(),
                    "footer": p.html_footer(),
                    }

            daily_poems[str(index)] = packet

        except Exception as e:
            warnings.warn(f"Could not find poem for entry {entry}")

    utils.write_to_repo(repo,
                        items={
                            "data/poems/history-daily.csv": history.to_csv(), 
                            "data/poems/author-stats.csv": utils.make_author_stats(history, catalog=curator.catalog).to_csv(),
                            "docs/assets/scripts/data/daily-poems.js": f"var dailyPoems = {json.dumps(daily_poems, indent=4, ensure_ascii=False)}",
                        }, 
                        verbose=True)