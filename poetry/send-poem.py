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
parser.add_argument('--author', type=str, help='Which poet to send', default='random')
parser.add_argument('--title', type=str, help='Which title to send', default='random')
parser.add_argument('--repo', type=str, help='Which GH repository to load', default='')
parser.add_argument('--token', type=str, help='GH token', default='')
parser.add_argument('--context', type=bool, help='Whether to send contextual poems', default=False)
parser.add_argument('--rh', type=bool, help='Whether to consider past poems sent', default=False)
parser.add_argument('--wh', type=bool, help='Whether to consider this poem in the future', default=False)
parser.add_argument('--type', type=str, help='What tag to write to the history with', default='')
parser.add_argument('--vv', type=bool, help='Very verbose', default=False)

args = parser.parse_args()

# Initialize the curator
curator = poetry.Curator()

when = ttime.time() if not args.type == 'test' else ttime.time() + 365 * 86400 * np.random.uniform()

# Choose a poem that meets the supplied conditions
curated_poem = curator.get_poem(
                                author=args.author, 
                                title=args.title, 
                                repo_name=args.repo,
                                repo_token=args.token,
                                when=when, 
                                min_length=10, 
                                max_length=5000, 
                                title_latency=800, 
                                context=args.context, 
                                tag_historical=args.type,
                                write_historical=args.wh,
                                read_historical=args.rh, 
                                verbose=True,
                                very_verbose=args.vv,
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

def f(poem, username, password, name, email, subject):

    done, fails = False, 0
    while (not done) and (fails < 10):
        try:
            poetry.send_email(username, password, poem.email_html, email, subject)
            a, b = email.split('@'); print(f'sent to {name:<18} | {a:>24} @ {b:<20}')
        except Exception as e:
            print(e); fails += 1; ttime.sleep(60)

for name, email in zip(entries['name'], entries['email']):

    t = threading.Thread(target=f, args=(curated_poem, args.username, args.password, name, email, subject))
    t.start()


    


    





