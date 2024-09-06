from poems import Context, Curator
from datetime import datetime
import pytz

def test_holiday_context():

    t = datetime(2024, 3, 31, tzinfo=pytz.utc).timestamp()

    curator = Curator()
    context = Context(timestamp=t)
    curator.catalog.apply_context(context, forced=['easter_sunday'], verbose=True)
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