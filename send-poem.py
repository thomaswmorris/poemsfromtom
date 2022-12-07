import time as ttime
import numpy as np
import pandas as pd
import argparse, poetry, sys, threading
from io import StringIO
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--username', type=str, help='Email address from which to send the poem',default='')
parser.add_argument('--password', type=str, help='Email password',default='')
parser.add_argument('--listserv_filename', type=str, help='Where to send the poem',default='')
parser.add_argument('--github_repo_name', type=str, help='Which GH repository to load', default='')
parser.add_argument('--github_token', type=str, help='GH token', default='')
parser.add_argument('--type', type=str, help='What tag to write to the history with', default='')
args = parser.parse_args()

# Initialize the curator
curator = poetry.Curator()
curator.load_github_repo(github_repo_name=args.github_repo_name, github_token=args.github_token)
curator.read_history(filename='poems/history.csv', from_repo=True, apply_weights=True, verbose=True)

when = ttime.time() if not args.type == 'test' else ttime.time() + 365 * 86400 * np.random.uniform()

context = poetry.utils.get_context(when)

# Choose a poem that meets the supplied conditions
curated_poem = curator.get_poem(
                                context=context, 
                                forced_contexts=['holiday'],
                                historical_tag=args.type,
                                very_verbose=True,
                                )

if args.type == 'test':
    subject = f'(TEST) {curated_poem.nice_fancy_date}: {curated_poem.header}'
elif args.type == 'daily':
    subject = f'Poem of the Day: {curated_poem.header}'
else:
    raise Exception('unhandled type')

if args.listserv_filename == '':
    raise Exception('could not find a listserv')

contents = curator.repo.get_contents(args.listserv_filename, ref='master')
entries  = pd.read_csv(StringIO(contents.decoded_content.decode()), index_col=0)

def thread_process(poem, username, password, name, email, subject):

    done, fails = False, 0
    while (not done) and (fails < 10):
        try:
            poetry.send_email(username, password, poem.email_html, email, subject)
            a, b = email.split('@'); print(f'sent to {name:<18} | {a:>24} @ {b:<20}')
            done = True
        except Exception as e:
            print(e); fails += 1; ttime.sleep(np.random.uniform(low=30,high=120))

for name, email in zip(entries['name'], entries['email']):

    t = threading.Thread(target=thread_process, args=(curated_poem, args.username, args.password, name, email, subject))
    t.start()


    


    





