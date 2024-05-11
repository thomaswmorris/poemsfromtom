from poems import Context, Curator
from datetime import datetime

def test_holiday_context():

    t = datetime(2024, 3, 31).timestamp()

    curator = Curator()
    context = Context(timestamp=t)
    curator.catalog.apply_context(context.to_dict(), forced=['easter_sunday'])
    poem = curator.get_poem(verbose=True)

    assert poem.metadata['keywords']['holiday'] == 'easter_sunday'


def test_month_context():

    t = datetime(2024, 10, 15).timestamp()

    curator = Curator()
    context = Context(timestamp=t)
    curator.catalog.apply_context(context.to_dict(), forced=['october'])
    poem = curator.get_poem(verbose=True)

    assert poem.metadata['keywords']['month'] == 'october'

def test_liturgy_context():

    t = datetime(2024, 2, 15).timestamp()

    curator = Curator()
    context = Context(timestamp=t)
    curator.catalog.apply_context(context.to_dict(), forced=['lent'])
    poem = curator.get_poem(verbose=True)

    assert poem.metadata['keywords']['liturgy'] == 'lent'