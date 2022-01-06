import time
from apscheduler.schedulers.blocking import BlockingScheduler
from run import sendMail
from poetry import Poetizer

poetizer = Poetizer()
schedule = BlockingScheduler()

#@schedule.scheduled_job('cron', day_of_week='mon-sun', hour=7)
@schedule.scheduled_job('interval', minutes=1)
def send_daily_poem():
    print('This job is run every day at 7 AM.')

    with open('testserv.txt','r+') as f:
        entries = [entry for entry in f.read().split('\n') if len(entry) > 0]

    # Choose a poem that meets the supplied conditions
    poetizer.load_poem(
        poet='random', 
        title='random', 
        when=time.time(), 
        min_length=12, 
        max_length=2000, 
        poet_latency=28, 
        title_latency=400, 
        contextual=True, 
        read_historical=True, 
        write_historical=True
        )

    for entry in entries:
        name, email = entry.split(' : ')
        done = False; fails = 0
        while (not done) and (fails < 12):
            try:
                poetizer.send_poem(email,tag='Poem of the Day: ')
                done = True
                a,b = email.split('@'); print(f'sent to {name:<18} | {a:>24} @ {b:<20}')
            except:
                time.sleep(60)
                fails += 1
                
schedule.start()

    


    





