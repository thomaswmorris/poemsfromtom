import datetime, json, numpy, os, pandas, sys, yaml
base, this_file = os.path.split(__file__)

sys.path.append(f"/users/tom/repos/poemsfromtom/poems")
import utils

context_categories = [key for key in utils.get_context_dict(0).keys() if not key == "timestamp"]
sample_times = numpy.arange(datetime.datetime(2000, 1, 1, 12).timestamp(), datetime.datetime(2100, 1, 1, 12).timestamp(), 86400)

sampled_context_values = numpy.array([list(utils.get_context_dict(t).values()) for t in sample_times])
sampled_context = pandas.DataFrame(sampled_context_values, columns=utils.get_context_dict().keys())

CONTEXT_MULTIPLIERS = {}
for category in ['weekday', 'month', 'day', 'season', 'liturgy', 'holiday', 'month_epoch']:
    CONTEXT_MULTIPLIERS[category] = {}
    sampled_keywords = sampled_context.loc[:, category]

    ukws = numpy.unique(sampled_keywords)
    if category == "weekday":
        sort = numpy.argsort([numpy.median(sampled_context.loc[sampled_keywords==kw, "year_day"].astype(int)[:7]) for kw in ukws])
    else:
        sort = numpy.argsort([numpy.min(sampled_context.loc[sampled_keywords==kw, "year_day"].astype(int)) for kw in ukws])
    for keyword in ukws[sort]:
        CONTEXT_MULTIPLIERS[category][keyword] = numpy.round(len(sampled_keywords) / numpy.sum(keyword==sampled_keywords), 3)

with open(f'/users/tom/repos/poemsfromtom/poems/weights.json', 'w+', encoding='utf8') as f:
    json.dump(CONTEXT_MULTIPLIERS, f, indent=4, ensure_ascii=False)