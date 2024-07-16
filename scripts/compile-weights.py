import datetime, os, yaml
base, this_file = os.path.split(__file__)

import numpy as np
import pandas as pd

from datetime import datetime
from poems.context import Context

context_categories = [key for key in Context(0).to_dict().keys() if not key == "timestamp"]
sample_times = np.arange(datetime(2000, 1, 1, 12).timestamp(), datetime(2400, 1, 1, 12).timestamp(), 86400)

sampled_context_values = np.array([list(Context(t).to_dict().values()) for t in sample_times])
sampled_context = pd.DataFrame(sampled_context_values, columns=Context.now().to_dict().keys())

for col in ["year", "day", "year_day"]:
    sampled_context[col] = pd.to_numeric(sampled_context[col])

CONTEXT_MULTIPLIERS = {}
for category in ['weekday', 'month', 'day', 'season', 'liturgy', 'holiday', 'month_epoch']:
    CONTEXT_MULTIPLIERS[category] = {}
    sampled_keywords = sampled_context.loc[:, category]

    ukws = np.unique(sampled_keywords)
    if category == "weekday":
        sort = np.argsort([np.median(sampled_context.loc[sampled_keywords==kw, "year_day"].astype(int)[:7]) for kw in ukws])
    else:
        sort = np.argsort([np.min(sampled_context.loc[sampled_keywords==kw, "year_day"].astype(int)) for kw in ukws])
    for keyword in ukws[sort]:
        if not isinstance(keyword, str):
            keyword = int(keyword)
        CONTEXT_MULTIPLIERS[category][keyword] = float(np.round(len(sampled_keywords) / np.sum(keyword==sampled_keywords), 3))

with open(f'/users/tom/poems/src/poems/data/weights.yml', 'w+', encoding='utf8') as f:
    yaml.dump(CONTEXT_MULTIPLIERS, f, default_flow_style=False)