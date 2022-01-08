import warnings
def ignore_deprecated():
    warnings.warn("deprecated", DeprecationWarning)

with warnings.catch_warnings():
    warnings.simplefilter("ignore"); ignore_deprecated()

import time
from apscheduler.schedulers.blocking import BlockingScheduler
from poetry import Poetizer

poetizer = Poetizer()
schedule = BlockingScheduler()

import argparse, sys
parser = argparse.ArgumentParser()
parser.add_argument('--address', type=str, help='Where to send the poem',default='testserv.txt')
parser.add_argument('--poet', type=str, help='Which poet to send', default='random')
parser.add_argument('--title', type=str, help='Which title to send', default='random')
parser.add_argument('--context', type=bool, help='Whether to send contextual poems', default=False)
parser.add_argument('--rh', type=bool, help='Whether to consider past poems sent', default=False)
parser.add_argument('--wh', type=bool, help='Whether to consider this poem in the future', default=False)
parser.add_argument('--tag', type=str, help='Email subject prefix', default='Poem of the Day')
parser.add_argument('--hour', type=str, help='Hour of the day to send', default=7)

args = parser.parse_args()
@schedule.scheduled_job('cron', day_of_week='mon,tue,wed,thu,fri,sat,sun', hour=args.hour)
#@schedule.scheduled_job('interval', minutes=1, max_instances=10)
def send_daily_poem():
    print(f'This job is run every day at {args.hour}:00UTC')
    if '.txt' in args.address:
        with open(args.address,'r+') as f:
            entries = [entry for entry in f.read().split('\n') if len(entry) > 0]
    else: entries = [': ' + args.address]

    # Choose a poem that meets the supplied conditions
    poetizer.load_poem(
        poet=args.poet, 
        title=args.title, 
        when=time.time(), 
        min_length=12, 
        max_length=2000, 
        poet_latency=28, 
        title_latency=400, 
        contextual=args.context, 
        read_historical=args.rh, 
        write_historical=args.wh,
        verbose=True,
        )

    for entry in entries:
        name, email = entry.split(' : ')
        done = False; fails = 0
        while (not done) and (fails < 12):
            try:
                poetizer.send_poem(email,tag=args.tag)
                done = True
                a,b = email.split('@'); print(f'sent to {name:<18} | {a:>24} @ {b:<20}')
            except Exception as e:
                print(e)
                time.sleep(60)
                fails += 1

#send_daily_poem()
schedule.start()

    


    





