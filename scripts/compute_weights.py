import datetime, os, yaml
base, this_file = os.path.split(__file__)

import numpy as np
from tqdm import tqdm

from datetime import datetime
from poems.context import Context

here, this_file = os.path.split(__file__)
sample_times = datetime(2021, 12, 21, 12).timestamp() + 86400 * np.arange(10000)

categories =  ["weekday", "month", "day", "season", "liturgy", "holiday", "month_epoch", "year_epoch"]
COUNTS = {category:{} for category in categories}
pbar = tqdm(sample_times)
for t in pbar:
    c = Context(t).to_dict()
    pbar.set_postfix(ctime=c["ctime"])
    for category in categories:
        value = c[category]
        for keyword in (value if isinstance(value, list) else [value]):
            if keyword not in COUNTS[category]:
                COUNTS[category][keyword] = 0
            COUNTS[category][keyword] += 1

MULTIPLIERS = {}
for category in COUNTS:
    MULTIPLIERS[category] = {}
    for keyword in COUNTS[category]:
        MULTIPLIERS[category][keyword] = round(len(sample_times) / COUNTS[category][keyword], 2)

with open(f"{here}/../poems/data/weights.yml", "w+", encoding="utf8") as f:
    yaml.dump(MULTIPLIERS, f, default_flow_style=False)