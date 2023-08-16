import poems 


def test_dates():
    print()
    curator = poems.Curator()
    for author in ["bob-dylan", "t-s-eliot", "dante-alighieri", "horace", "ovid", "sappho"]:
        poem = curator.get_poem(author=author, verbose=False)
        print(f'{author:>16}: {poem.author.dates}')

    print(curator.poems)