import json, os, pytz, re
import time as ttime
import numpy as np
import pandas as pd
import github as gh
from io import StringIO

from dataclasses import dataclass

from datetime import datetime
from . import utils

class PoemNotFoundError(Exception):
    pass

base, this_file = os.path.split(__file__)

with open(f"{base}/poem-style.css", "r") as f: 
    CSS = f.read()

with open(f"{base}/poems.json", "r+") as f:
    POEMS = json.load(f)

with open(f"{base}/weights.json", "r+") as f:
    CONTEXT_WEIGHTS = json.load(f)



@dataclass
class Author():
    """Author data class"""
    name: str
    birth: int
    death: int
    nationality: str
    flag: str
    link: str
    favorite: bool
    n_poems: str
    link: str

    @property
    def dates(self) -> str:
        if self.death is None:
            return f"(born {self.birth})"
        if self.birth < 0:
            if self.death < 0:
                return f"({(-self.birth)} BC &#8211; {-self.death} BC)"
            else:
                return f"({(-self.birth)} BC &#8211; {self.death} AD)"
        else:
             return f"({(self.birth)} &#8211; {self.death})"

@dataclass
class Poem():
    author: Author
    title: str
    body: str
    keywords: dict
    when: int

    @property
    def html_title(self) -> str:
        return re.sub("^from", "<i>from</i>", self.title)

    @property
    def date_time(self):
        return datetime.fromtimestamp(self.when).replace(tzinfo=pytz.utc)

    @property
    def nice_fancy_date(self):
        return f"{utils.get_weekday(self.when).capitalize()} {utils.get_month(self.when).capitalize()} {self.date_time.day}, {self.date_time.year}"

    @property
    def html_lines(self):
        return utils.text_to_html_lines(self.body)

    @property        
    def header(self):
        return f"{self.title} by {self.author.name}"

    @property
    def html(self):
        return f'''<section class="poem-section">
<div class="poem-header">
    <div class="poem-date">{self.nice_fancy_date}</div>
    <div>
        <span class="poem-title">{self.html_title}</span>
        by 
        <span class="poem-author"><a href="{self.author.link}">{self.author.name}</a> <i>{self.author.dates}</i> {self.author.flag}</span>
    </div>
</div>
{self.html_lines}
</section>'''

    def email_html(self):
        return f'''<head><!DOCTYPE html>
<style>
{CSS}
</style>
</head>
{self.html.replace(self.author.flag, "")}
<br>
Past poems can be found in the <a href="https://thomaswmorris.com/poems">archive</a>.
</html>
'''


class Curator():

    def __init__(self):
                        
        authors, titles, keywords, lengths = [], [], [], []
        self.poems = pd.DataFrame(columns=["author", "title", "keywords", "likelihood", "word_count"])
        for author in POEMS.keys():
            for title in POEMS[author]["poems"].keys():
                authors.append(author)
                titles.append(title)
                keywords.append(POEMS[author]["poems"][title]["keywords"])
                lengths.append(len(POEMS[author]["poems"][title]["body"].split()))

        self.poems.loc[:, "author"] = authors
        self.poems.loc[:, "title"] = titles
        self.poems.loc[:, "keywords"] = keywords
        self.poems.loc[:, "likelihood"] = 1
        self.poems.loc[:, "word_count"] = lengths

        self.unique_authors = np.sort(np.unique(self.poems.author))
        self.archive_poems  = self.poems.copy()
        self.history = None

    def load_github_repo(self, github_repo_name=None, github_token=None):

        self.github_repo_name  = github_repo_name
        self.github_token = github_token
        self.g = gh.Github(self.github_token)
        self.repo = self.g.get_user().get_repo(self.github_repo_name)

    def read_history(self, filename, from_repo=False):

        if from_repo:
            if not hasattr(self, "repo"):
                raise Exception("The curator has not loaded a github repository.")
            self.repo_history_contents = self.repo.get_contents(filename, ref="master")
            self.history = pd.read_csv(StringIO(self.repo_history_contents.decoded_content.decode()), index_col=0)
                
            
        else:         
            try:
                self.history = pd.read_csv(filename, index_col=0)
            except Exception as e:
                raise Exception(f"{e}\n(Could not load file \"{filename}\")")

        self.make_stats() # order_by=["times_sent", "days_since_last_sent"], ascending=(False, True))

    def write_to_repo(self, items, branch="master", verbose=False):

        elements = []
        for filename, content in items.items():

            blob = self.repo.create_git_blob(content, "utf-8")
            elements.append(gh.InputGitTreeElement(path=filename, mode="100644", type="blob", sha=blob.sha))
            if verbose: print(f"writing to {self.github_repo_name}/{filename}")

        head_sha   = self.repo.get_branch(branch).commit.sha
        base_tree  = self.repo.get_git_tree(sha=head_sha)
        tree       = self.repo.create_git_tree(elements, base_tree)
        parent     = self.repo.get_git_commit(sha=head_sha) 
        commit     = self.repo.create_git_commit(f"updated logs @ {datetime.now(tz=pytz.utc).isoformat()[:19]}", tree, [parent])
        master_ref = self.repo.get_git_ref(f"heads/{branch}")
        master_ref.edit(sha=commit.sha)

    def make_stats(self, order_by=None, ascending=True, force_rows=True, force_cols=True):

        if self.history is None: raise(Exception("No history has been loaded!"))
        if force_rows: pd.set_option("display.max_rows", None)
        if force_cols: pd.set_option("display.max_columns", None)
        self.stats = pd.DataFrame(columns=["name","nationality","birth","death","n_poems","#_of_times_sent","days_since_last_sent"])

        for author in POEMS.keys():

            name = POEMS[author]["metadata"]["name"]
            birth = POEMS[author]["metadata"]["birth"]
            death = POEMS[author]["metadata"]["death"]
            nationality = POEMS[author]["metadata"]["nationality"]
            n_poems = POEMS[author]["metadata"]["n_poems"]

            elapsed = (ttime.time() - self.history["timestamp"][self.history.author==author].max()) / 86400 
            n_sent = (self.history["author"]==author).sum()
            
            self.stats.loc[author] = name, nationality, birth, death, n_poems, n_sent, np.round(elapsed,1)
            
        if not order_by is None:
            self.stats = self.stats.sort_values(by=order_by, ascending=ascending)

    def get_poem(
                self,
                author=None,
                title=None,
                context=None,
                weight_schemes=["context"],
                forced_contexts=[],
                historical_tag=None,
                verbose=True,
                very_verbose=False,
                **kwargs,
                ):

        verbose = verbose or very_verbose
        self.poems = self.archive_poems.copy()

        if context is None:
            context = utils.get_context()

        self.when = ttime.time() 
        if "timestamp" in context.keys():
            self.when = context["timestamp"]

        # if author is supplied, get rid of poems not by that author
        if author is not None: 
            self.poems.loc[self.poems.author != author, "likelihood"] = 0
            if not len(self.poems) > 0:
                raise PoemNotFoundError(f"There are no poems by author \"{author}\" in the database.")

            # if the author AND the title are supplied, then we can end here (either in a return or an error)
            if title is not None: 
                if title in POEMS[author]["poems"].keys():
                    return Poem(author, title, self.when)
                else:
                    raise PoemNotFoundError(f"There is no poem \"{title}\" by \"{author}\" in the database.")

        # if JUST the title is supplied, do this (why would you ever do this? but we should support it anyway)
        if title is not None: 
            self.poems.loc[self.poems.title != title, "likelihood"] = 0
            if not len(self.poems) > 0:
                raise PoemNotFoundError(f"There are no poem \"{title}\" by any author in the database.")

        if "history" in weight_schemes:
            if not hasattr(self, "history"): 
                raise Exception("There is no history for the weight scheme.")

            for _, entry in self.history.iterrows():
                try:
                    loc = self.poems.index[np.where((self.poems.author==entry.author)&(self.poems.title==entry.title))[0][0]]
                    self.poems.drop(loc, inplace=True)
                    #if verbose: print(f"removed {entry.title} by {entry.author}")
                except:
                    print(f"error handling entry {entry}")

            for uauthor in self.unique_authors:
                
                ### weigh by number of poems so that every poet is equally likely (unless you have few poems left) 
                #times_sent_weight = np.exp(.25 * np.log(.5) * self.stats.times_sent.loc[uauthor]) # four times sent is a weight of 0.5
                days_since_last_sent_weight = 1 / (1 + np.exp(-.25 * (self.stats.days_since_last_sent.fillna(365).loc[uauthor] - 21))) # after three weeks, the weight is 0.5
                total_weight = days_since_last_sent_weight # * times_sent_weight

                #if verbose: print(f"weighted {uauthor:<12} by {times_sent_weight:.03f} * {days_since_last_sent_weight:.03f} = {total_weight:.03f}")
                self.poems.loc[uauthor==self.poems.author, "likelihood"] *= total_weight

            if verbose: print("applying \"history\" weighting scheme")

        if "author" in weight_schemes:
            for uauthor in self.unique_authors:
                self.poems.loc[uauthor==self.poems.author, "likelihood"] /= np.sum(uauthor==self.poems.author)
            if verbose: print("applying \"author\" weighting scheme")

        if "remaining" in weight_schemes:
            for uauthor in self.unique_authors:
                n = np.sum(uauthor == self.poems.author)
                if not n > 0: continue
                self.poems.loc[uauthor == self.poems.author, "likelihood"] *= 1 + np.log(n)
            if verbose: print("applying \"remaining\" weighting scheme")
            
        if "context" in weight_schemes:

            if verbose: print(f"using context {context}")
            if verbose: print(f"forcing contexts {forced_contexts}")

            exclude = np.array([kwdict["type"]=="exclude" if "type" in kwdict.keys() else False for kwdict in self.poems.keywords])
            self.poems.loc[exclude, "likelihood"] = 0

            if verbose: print(f"omitting {exclude.sum()} poems")

            # if the category is "statistical", then we weight to be uniform in the long run (i.e. *= 4 for seasons and *= 12 for months)
            # if the category is forced, then we multiply by some arbitrarily large number. we don"t multiply (~category) by 0 because this
            # would throw an error if there were no suitable poems, so this is a bit more flexible for workflows and things. 

            for category in CONTEXT_WEIGHTS.keys():
                if not category in context.keys(): 
                    continue
                for keyword in CONTEXT_WEIGHTS[category].keys():
                    has_keyword = np.array([keyword==kwdict[category] if category in kwdict.keys() else False for kwdict in self.poems.keywords])
                    if not has_keyword.sum() > 0: 
                        continue

                    if keyword == context[category]: 
                        if keyword not in forced_contexts:
                            multiplier = CONTEXT_WEIGHTS[category][keyword]  
                        else:
                            multiplier = 1e12
                    else: 
                        multiplier = 0

                    # if we want to use "spring" as a holiday for the first day of spring, then we need to not
                    # exclude that keyword when it is not that holiday. this translates well; if the holiday is 
                    # also a season, month, or liturgy, then we do not do anything
                    
                    self.poems.loc[has_keyword, "likelihood"] *= multiplier
                    if very_verbose: print(f"weighted {int(has_keyword.sum()):>3} poems with {category} = {keyword} by {multiplier}")

            if not self.poems["likelihood"].sum() > 0:
                raise PoemNotFoundError(f"No poem with the given context")

        self.poems["probability"] = self.poems.likelihood / self.poems.likelihood.sum()
        if very_verbose: 
            print(f"choosing from {len(self.poems)} poems. the 10 most likely are:")
            print(self.poems.sort_values("probability", ascending=False)[["author","title","keywords","probability"]].iloc[:10])
        chosen_loc = np.random.choice(self.poems.index, p=self.poems.probability)
        chosen_author, chosen_title = self.poems.loc[chosen_loc, ["author", "title"]]
        
        if verbose: 
            print(f"chose poem \"{chosen_title}\" by {chosen_author}")

        poem = Poem(author=Author(**POEMS[chosen_author]["metadata"]),
                    title=chosen_title,
                    body=POEMS[chosen_author]["poems"][chosen_title]["body"],
                    keywords=POEMS[chosen_author]["poems"][chosen_title]["keywords"],
                    when=self.when)

        if not historical_tag is None:
            now = datetime.now(tz=pytz.utc)
            self.history.loc[len(self.history)+1] = chosen_author, chosen_title, *now.isoformat()[:19].split("T"), int(now.timestamp())

        return poem

    
            
            
            


  