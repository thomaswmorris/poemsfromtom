from poems import Context, Curator, forced_holidays
from datetime import timedelta
import arrow

from poems.context import holidays

def test_liturgys():

    t = arrow.get().timestamp()

    for _ in range(1000):

        t += 86400

        context = Context(timestamp=t)

        for holiday in context.holidays:
            if holiday not in holidays.name.values:
                raise ValueError(f"Bad holiday '{holiday}'.")


def test_holiday_context():

    t = arrow.get(f"{2024}-03-31").timestamp()

    curator = Curator()
    context = Context(timestamp=t)
    curator.catalog.apply_context(context, forced=forced_holidays, verbose=True)
    poem = curator.get_poem(verbose=True)

    assert poem.keywords['holiday'] == 'easter_sunday'


def test_month_context():

    t = arrow.get(f"{2024}-10-15").timestamp()

    curator = Curator()
    context = Context(timestamp=t)
    curator.catalog.apply_context(context, forced=['october'], verbose=True)
    poem = curator.get_poem(verbose=True)

    assert poem.keywords['month'] == 'october'

def test_liturgy_context():

    t = arrow.get(f"{2024}-02-15").timestamp()

    curator = Curator()
    context = Context(timestamp=t)
    curator.catalog.apply_context(context, forced=['lent'], verbose=True)
    poem = curator.get_poem(verbose=True)

    assert poem.keywords['liturgy'] == 'lent'