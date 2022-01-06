import time
from datetime import datetime

import smtplib

from email.mime.multipart import MIMEMultipart
import sys

import regex as re


subject_tag = 'Poem of the Day | '
poet  = 'random'
title = 'random'

#if len(sys.argv) == 2:
    
#    this_program, address, poet, title = sys.argv
    
import argparse, sys

parser = argparse.ArgumentParser()
parser.add_argument('--address', type=str, help='Where to send the poem',default='listserv.txt')
parser.add_argument('--poet', type=str, help='Which poet to send', default='random')
parser.add_argument('--title', type=str, help='Which poem to send', default='random')

args = parser.parse_args()

address   = args.address
get_poet  = args.poet
get_title = args.title

from poetry import Poetizer
poetizer = Poetizer()

poetizer.load_poem(poet=args.poet, title=args.title, when=time.time(), min_length=12, max_length=2000, 
poet_latency=28, title_latency=400, contextual=True, read_historical=True, write_historical=True)

print()
print(datetime.now().isoformat(),poetizer.poet,poetizer.title)
print(64*'#')
print()

with open(address,'r+') as f:
    listserv = f.read()
entries = [entry for entry in listserv.split('\n') if len(entry) > 0]
for entry in entries:
    
    name, email = entry.split(' : ')

    done = False; fails = 0
    
    
    while (not done) and (fails < 12):
        try:
            poetizer.send_poem(email,tag='Poem of the Day: ')
            done = True
            a,b = email.split('@'); print(f'sent to {name:<18} | {a:>24} @ {b:<20}')
        except:
            time.sleep(600)
            fails += 1

    


    





