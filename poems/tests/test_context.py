from poems import Context, Curator, forced_holidays
from datetime import datetime, timedelta
import pytz

from poems.context import holidays

def test_liturgys():

    t = datetime.now()

    for _ in range(1000):

        t += timedelta(days=1)

        context = Context(timestamp=t.timestamp())

        for holiday in context.holidays:
            if holiday not in holidays.name.values:
                raise ValueError(f"Bad holiday '{holiday}'.")


def test_holiday_context():

    t = datetime(2024, 3, 31, tzinfo=pytz.utc).timestamp()

    curator = Curator()
    context = Context(timestamp=t)
    curator.catalog.apply_context(context, forced=forced_holidays, verbose=True)
    poem = curator.get_poem(verbose=True)

    assert poem.keywords['holiday'] == 'easter_sunday'


def test_month_context():

    t = datetime(2024, 10, 15, tzinfo=pytz.utc).timestamp()

    curator = Curator()
    context = Context(timestamp=t)
    curator.catalog.apply_context(context, forced=['october'], verbose=True)
    poem = curator.get_poem(verbose=True)

    assert poem.keywords['month'] == 'october'

def test_liturgy_context():

    t = datetime(2024, 2, 15, tzinfo=pytz.utc).timestamp()

    curator = Curator()
    context = Context(timestamp=t)
    curator.catalog.apply_context(context, forced=['lent'], verbose=True)
    poem = curator.get_poem(verbose=True)

    assert poem.keywords['liturgy'] == 'lent'