import time
import numpy as np
import pandas as pd
import poetry
from io import StringIO
import threading
from datetime import datetime


import argparse, sys
parser = argparse.ArgumentParser()
parser.add_argument('--username', type=str, help='Email address from which to send the poem',default='')
parser.add_argument('--password', type=str, help='Email password',default='')
parser.add_argument('--recipient', type=str, help='Where to send the poem',default='poemsfromtom@gmail.com')
parser.add_argument('--repo_lsfn', type=str, help='Where to send the poem',default='')
parser.add_argument('--author', type=str, help='Which poet to send', default='random')
parser.add_argument('--title', type=str, help='Which title to send', default='random')
parser.add_argument('--repo', type=str, help='Which GH repository to load', default='')
parser.add_argument('--token', type=str, help='GH token', default='')
parser.add_argument('--context', type=bool, help='Whether to send contextual poems', default=False)
parser.add_argument('--rh', type=bool, help='Whether to consider past poems sent', default=False)
parser.add_argument('--wh', type=bool, help='Whether to consider this poem in the future', default=False)
parser.add_argument('--type', type=str, help='What tag to write to the history with', default='')
parser.add_argument('--subj_tag', type=str, help='Email subject prefix', default='')
parser.add_argument('--hour', type=str, help='Hour of the day to send', default=7)
parser.add_argument('--vv', type=bool, help='Very verbose', default=False)

args = parser.parse_args()

# Initialize the curator
curator = poetry.Curator()

when = time.time() if not args.type == 'test' else time.time() + 365 * 86400 * np.random.uniform()

subject = args.subj_tag if not args.subj_tag == '' else datetime.fromtimestamp(when).isoformat()[:10]

# Choose a poem that meets the supplied conditions
poem = curator.load_poem(
                            author=args.author, 
                            title=args.title, 
                            repo_name=args.repo,
                            repo_token=args.token,
                            when=time.time(), 
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

if not args.repo_lsfn == '':

    contents = curator.repo.get_contents(args.repo_lsfn, ref='master')
    entries  = pd.read_csv(StringIO(contents.decoded_content.decode()),index_col=0)

else: 
    
    entries = pd.DataFrame(columns=['name','email'])
    for recipient in args.recipient.split(','):
        entries.loc[len(entries)] = '*', recipient

def f(*arguments):

    poetry.send_poem(*arguments)
    a,b = email.split('@'); print(f'sent to {name:<18} | {a:>24} @ {b:<20}')

for name, email in zip(entries['name'],entries['email']):

    t = threading.Thread(target=f, args=(poem, args.username, args.password, email, subject))
    t.start()


    


    





