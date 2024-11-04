import json
import time as ttime
import datetime
import argparse, threading

from numpy import random
from poems import Context, Curator, holidays
from poems import utils

import logging
logger = logging.getLogger("poems")

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

history = utils.read_csv(repo=repo, filepath="poems/history-daily.csv")

when = ttime.time() if args.mode == "daily" else ttime.time() + random.uniform(low=0, high=365 * 86400)
context = Context(timestamp=when)

logger.info(f"using context {context.to_dict()}")

curator.catalog.apply_context(context, forced=holidays.loc[holidays.forced].name.values)
curator.catalog.apply_history(history, verbose=True)

# choose a poem
p = curator.get_poem(very_verbose=True)
curator.catalog.reset()

thread_kwargs = {"username": args.username,
                 "password": args.password,
                 "subject": p.email_subject(mode=args.mode),
                 "content": p.email_html}

listserv = utils.read_csv(repo=repo, filepath=args.listserv_filename)

delta = datetime.timedelta(hours=1)
now = datetime.datetime.now()
if args.mode in ["daily", "hourly-test"]:
    start_time = (now + datetime.timedelta(hours=1)).replace(microsecond=0, second=0, minute=0)
else:
    start_time = (now + datetime.timedelta(minutes=1)).replace(microsecond=0, second=0)

wait_seconds = (start_time - now).seconds + 1
if wait_seconds < 600:
    logger.info(f"Waiting {int(wait_seconds)} seconds.")
    ttime.sleep(wait_seconds)

now = Context.now()

for index, entry in listserv.iterrows():
    t = threading.Thread(target=utils.email_thread, kwargs={**thread_kwargs, "recipient": entry.email})
    t.start()
    ttime.sleep(5e-1)

if args.write_to_repo:

    if args.mode == "daily":
        index = len(history) + 1
        date, time = now.isoformat[:19].split("T")

        history.loc[index, "date"] = date
        history.loc[index, "time"] = time
        history.loc[index, "timestamp"] = now.timestamp
        history.loc[index, "title"] = p.key
        history.loc[index, "author"] = p.author.key

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
            logger.warning(f"Could not find poem for entry {entry.to_dict()}")

    utils.write_to_repo(repo,
                        items={
                            "poems/history-daily.csv": history.to_csv(), 
                            "poems/author-stats.csv": utils.make_author_stats(history, catalog=curator.catalog).to_csv(),
                            "docs/assets/scripts/data/daily-poems.js": f"var dailyPoems = {json.dumps(daily_poems, indent=4, ensure_ascii=False)}",
                        }, 
                        verbose=True)