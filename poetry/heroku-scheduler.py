import time as ttime
import pandas as pd
import numpy as np
from apscheduler.schedulers.blocking import BlockingScheduler
from poetry import Poetizer
from multiprocessing import Process
from datetime import datetime
import os
from io import StringIO

schedule = BlockingScheduler(timezone='America/New_York')

import argparse, sys
parser = argparse.ArgumentParser()
parser.add_argument('--recipient', type=str, help='Where to send the poem',default='poemsfromtom@gmail.com')
parser.add_argument('--repo_lsfn', type=str, help='Where to send the poem',default='')
parser.add_argument('--poet', type=str, help='Which poet to send', default='random')
parser.add_argument('--title', type=str, help='Which title to send', default='random')
parser.add_argument('--type', type=str, help='What kind of proc', default='test')
parser.add_argument('--context', type=bool, help='Whether to send contextual poems', default=False)
parser.add_argument('--rh', type=bool, help='Whether to consider past poems sent', default=False)
parser.add_argument('--wh', type=bool, help='Whether to consider this poem in the future', default=False)
parser.add_argument('--subj_tag', type=str, help='Email subject prefix', default='')
parser.add_argument('--hour', type=str, help='Hour of the day to send', default=7)
args = parser.parse_args()

@schedule.scheduled_job('cron', day_of_week='mon,tue,wed,thu,fri,sat,sun', hour=args.hour)
def send_daily_poem():

    print(f'\nThis job is run every day at {args.hour} EST')

    # Load the poetizer
    poetizer = Poetizer()

    when = ttime.time()
    subject = args.subj_tag
    if args.type == 'test':
        when = datetime.fromtimestamp(ttime.time() + np.random.uniform(low=0,high=365) * 86400).timestamp()
        date, time = datetime.fromtimestamp(when).isoformat().split('T') 
        print(date)
        subject = args.subj_tag + f'{date\\}: '
    
    # Choose a poem that meets the supplied conditions
    poetizer.load_poem(
        poet=args.poet, 
        title=args.title, 
        repo_name='poems',
        repo_token=os.environ['GITHUB_TOKEN'],
        when=when, 
        min_length=100, 
        max_length=2000, 
        title_latency=800, 
        context=args.context, 
        tag_historical=args.type,
        write_historical=args.wh,
        read_historical=args.rh, 
        verbose=True,
    )

    def f(username, password, name, email, tag):
        done, fails = False, 0
        while (not done) and (fails < 12):
            try:
                poetizer.send_poem(username, password, email, tag); done = True
                a,b = email.split('@'); print(f'sent to {name:<18} | {a:>24} @ {b:<20}')
            except Exception as e:
                print(e); fails += 1; ttime.sleep(1)
 
    if not args.repo_lsfn == '':
        contents = poetizer.repo.get_contents(args.repo_lsfn, ref='master')
        entries  = pd.read_csv(StringIO(contents.decoded_content.decode()),index_col=0)
    else: 
        entries = pd.DataFrame(columns=['name','email'])
        for recipient in args.recipient.split(','):
            entries.loc[len(entries)] = '*', recipient

    for name, email in zip(entries['name'],entries['email']):
        p = Process(target=f, args=('poemsfromtom@gmail.com', os.environ['PFT_PW'], name, email, subject))
        p.start()
        p.join()

schedule.start()