from poems import Curator



test_titles = ["roads-go-ever-ever-on", "gods-acres", "sonnet-101"]

def test_dates():
    curator = Curator()

    for title in test_titles:
        poem = curator.get_poem(title=title, verbose=False)
        print(poem.html_header())
        print(poem.html_footer())
