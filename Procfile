daily: python poetry/heroku-scheduler.py --type 'daily' --repo_lsfn 'listserv.csv' --context true --rh true --wh true --subj_tag 'Poem of the Day: ' --hour '7'; python poetry/make-docs.py --repo 'poems' --token_from_heroku true

test: python poetry/heroku-scheduler.py --type 'test' --repo_lsfn 'testserv.csv' --context true --rh true --wh true --subj_tag '(TEST) ' --hour '0-6,8-23'; python poetry/make-docs.py --repo 'poems' --token_from_heroku true
