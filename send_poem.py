from poetry import Poetizer
poetizer = Poetizer()

def send_daily_poem():
    print(f'This job is run every day at {args.hour}:00.')
    with open(args.address,'r+') as f:
        entries = [entry for entry in f.read().split('\n') if len(entry) > 0]

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
        )

    for entry in entries:
        name, email = entry.split(' : ')
        done = False; fails = 0
        while (not done) and (fails < 12):
            try:
                poetizer.send_poem(email,tag=args.tag + ': ')
                done = True
                a,b = email.split('@'); print(f'sent to {name:<18} | {a:>24} @ {b:<20}')
            except:
                time.sleep(60)
                fails += 1


    


    





