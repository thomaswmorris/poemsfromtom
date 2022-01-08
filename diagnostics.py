import time
from apscheduler.schedulers.blocking import BlockingScheduler
from poetry import Poetizer

poetizer = Poetizer()
schedule = BlockingScheduler(timezone='America/New_York')

import argparse, sys
parser = argparse.ArgumentParser()
parser.add_argument('--address', type=str, help='Where to send the poem',default='testserv.txt')
parser.add_argument('--what', type=str, help='What diagnostic to send', default='')
parser.add_argument('--hour', type=str, help='Hour of the day to send', default=7)

args = parser.parse_args()
@schedule.scheduled_job('cron', day_of_week='mon,tue,wed,thu,fri,sat,sun', hour=args.hour)
def send_diagnostic():

    if args.what == 'history': poetizer.send_history(args.address,n=15)
    if args.what == 'stats': poetizer.send_stats(args.address)

send_diagnostic()
schedule.start()

    


    





