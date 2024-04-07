import poems as poems
from datetime import datetime

def test_holiday_context():

    t = datetime(2024, 3, 31).timestamp()

    curator = poems.Curator()
    context = poems.utils.Context(timestamp=t).to_dict()
    poem = curator.get_poem(context=context, forced_contexts=['easter_sunday'], verbose=True)

    print(poem.date)

    assert poem.metadata['keywords']['holiday'] == 'easter_sunday'


def test_month_context():

    t = datetime(2024, 10, 15).timestamp()

    curator = poems.Curator()
    context = poems.utils.Context(timestamp=t).to_dict()
    poem = curator.get_poem(context=context, forced_contexts=['october'], verbose=True)

    print(poem.date)

    assert poem.metadata['keywords']['month'] == 'october'

def test_liturgy_context():

    t = datetime(2024, 2, 15).timestamp()

    curator = poems.Curator()
    context = poems.utils.Context(timestamp=t).to_dict()
    poem = curator.get_poem(context=context, forced_contexts=['lent'], verbose=True)

    print(poem.date)

    assert poem.metadata['keywords']['liturgy'] == 'lent'