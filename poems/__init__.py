import json, os, pytz, re
import time as ttime
import numpy as np
import pandas as pd
import github as gh
from io import StringIO
from datetime import datetime
from .utils import Context

from .objects import Poem, Author

class PoemNotFoundError(Exception):
    pass

here, this_file = os.path.split(__file__)

with open(f"{here}/poems.json", "r+") as f:
    db = json.load(f)

with open(f"{here}/weights.json", "r+") as f:
    CONTEXT_WEIGHTS = json.load(f)

authors = {author:Author(**db[author]["metadata"]) for author in db.keys()}

def _construct_poem(author, title, context=None, timestamp=None):
    return Poem(author=Author(**db[author]["metadata"]), **db[author]["poems"][title], context=context, timestamp=timestamp)

class Curator():

    def __init__(self):
                        
        authors, titles, keywords, translators, lengths = [], [], [], [], []
        self.catalog = pd.DataFrame(columns=["author", "title", "keywords", "translator", "likelihood", "word_count"])
        for author in db.keys():
            for title in db[author]["poems"].keys():
                authors.append(author)
                titles.append(title)
                metadata = db[author]["poems"][title]["metadata"]
                keywords.append(metadata["keywords"] if "keywords" in metadata.keys() else {})
                translators.append(metadata["translator"] if "translator" in metadata.keys() else None)
                lengths.append(len(db[author]["poems"][title]["body"].split()))

        self.catalog.loc[:, "author"] = authors
        self.catalog.loc[:, "title"] = titles
        self.catalog.loc[:, "keywords"] = keywords
        self.catalog.loc[:, "translator"] = translators
        self.catalog.loc[:, "likelihood"] = 1.
        self.catalog.loc[:, "word_count"] = lengths

        self.unique_authors = np.sort(np.unique(self.catalog.author))
        self.archive_poems  = self.catalog.copy()
        self.history = None


    def get_poem(
                self,
                author=None,
                title=None,
                context=None,
                weight_schemes=["context"],
                forced_contexts=[],
                verbose=False,
                very_verbose=False,
                timestamp=None,
                ):

        if timestamp is None:
            timestamp = Context.now().timestamp

        verbose = verbose or very_verbose
        self.catalog = self.archive_poems.copy()

        if context is None:
            context = Context(timestamp=timestamp).to_dict()
        
        if "timestamp" in context.keys():
            timestamp = context["timestamp"]

        if author and title: 
            if title in db[author]["poems"].keys():
                return _construct_poem(author=author, title=title, context=context, timestamp=timestamp)
            else:
                raise PoemNotFoundError(f"There is no poem \"{title}\" by \"{author}\" in the database.")

        # if author is supplied, get rid of poems not by that author
        if author: 
            self.catalog.loc[self.catalog.author != author, "likelihood"] = 0
            if not len(self.catalog) > 0:
                raise PoemNotFoundError(f"There are no poems by author \"{author}\" in the database.")

        # if JUST the title is supplied, do this (why would you ever do this? but we should support it anyway)
        if title: 
            self.catalog.loc[self.catalog.title != title, "likelihood"] = 0
            if not len(self.catalog) > 0:
                raise PoemNotFoundError(f"There is no poem called \"{title}\" by any author in the database.")

        if "history" in weight_schemes:
            if not hasattr(self, "history"): 
                raise Exception("There is no history for the weight scheme.")

            for _, entry in self.history.iterrows():
                try:
                    loc = self.catalog.index[np.where((self.catalog.author==entry.author)&(self.catalog.title==entry.title))[0][0]]
                    # self.catalog.drop(loc, inplace=True)
                    self.catalog.loc[loc, "likelihood"] = 0
                    #if verbose: print(f"removed {entry.title} by {entry.author}")
                except:
                    print(f"error handling entry {entry}")

            for uauthor in self.unique_authors:
                
                ### weigh by number of poems so that every poet is equally likely (unless you have few poems left) 
                #times_sent_weight = np.exp(.25 * np.log(.5) * self.stats.times_sent.loc[uauthor]) # four times sent is a weight of 0.5
                days_since_last_sent_weight = 1 / (1 + np.exp(-.25 * (self.stats.days_since_last_sent.fillna(365).loc[uauthor] - 42))) # after six weeks, the weight is 0.5
                total_weight = days_since_last_sent_weight # * times_sent_weight

                #if verbose: print(f"weighted {uauthor:<12} by {times_sent_weight:.03f} * {days_since_last_sent_weight:.03f} = {total_weight:.03f}")
                self.catalog.loc[uauthor==self.catalog.author, "likelihood"] *= total_weight

            if verbose: print("applying \"history\" weighting scheme")

        if "author" in weight_schemes:
            for uauthor in self.unique_authors:
                self.catalog.loc[uauthor==self.catalog.author, "likelihood"] /= np.sum(uauthor==self.catalog.author)
            if verbose: print("applying \"author\" weighting scheme")

        if "remaining" in weight_schemes:
            for uauthor in self.unique_authors:
                n = np.sum(uauthor == self.catalog.author)
                if not n > 0: continue
                self.catalog.loc[uauthor == self.catalog.author, "likelihood"] *= 1 + np.log(n)
            if verbose: print("applying \"remaining\" weighting scheme")
            
        if "context" in weight_schemes:

            if verbose: print(f"using context {context}")
            if verbose: print(f"forcing contexts {forced_contexts}")

            exclude = np.array([kwdict["type"]=="exclude" if "type" in kwdict.keys() else False for kwdict in self.catalog.keywords])
            self.catalog.loc[exclude, "likelihood"] = 0

            if verbose: print(f"omitting {exclude.sum()} poems")

            # if the category is "statistical", then we weight to be uniform in the long run (i.e. *= 4 for seasons and *= 12 for months)
            # if the category is forced, then we multiply by some arbitrarily large number. we don"t multiply (~category) by 0 because this
            # would throw an error if there were no suitable poems, so this is a bit more flexible for workflows and things. 

            for category in CONTEXT_WEIGHTS.keys():
                if not category in context.keys(): 
                    continue
                for keyword in CONTEXT_WEIGHTS[category].keys():
                    has_keyword = np.array([keyword==kwdict[category] if category in kwdict.keys() else False for kwdict in self.catalog.keywords])
                    if not has_keyword.sum() > 0: 
                        continue

                    if keyword == context[category]: 
                        if keyword in forced_contexts:
                            multiplier = 1e18
                        else:
                            multiplier = CONTEXT_WEIGHTS[category][keyword]  
                    else: 
                        multiplier = 0

                    # if we want to use "spring" as a holiday for the first day of spring, then we need to not
                    # exclude that keyword when it is not that holiday. this translates well; if the holiday is 
                    # also a season, month, or liturgy, then we do not do anything
                    
                    self.catalog.loc[has_keyword, "likelihood"] *= multiplier
                    if very_verbose: print(f"weighted {int(has_keyword.sum()):>3} poems with {category} = {keyword} by {multiplier}")

            if not self.catalog["likelihood"].sum() > 0:
                raise PoemNotFoundError(f"No poem with the given context")

        self.catalog["probability"] = self.catalog.likelihood / self.catalog.likelihood.sum()
        if very_verbose: 
            print(f"choosing from {len(self.catalog)} poems; the 20 most likely are:")
            print(self.catalog.sort_values("probability", ascending=False)[["author","title","keywords","probability"]].iloc[:20])
        chosen_loc = np.random.choice(self.catalog.index, p=self.catalog.probability)
        chosen_author, chosen_title = self.catalog.loc[chosen_loc, ["author", "title"]]
        
        if verbose: 
            print(f"chose poem \"{chosen_title}\" by {chosen_author}")

        poem = _construct_poem(author=chosen_author, title=chosen_title, context=context, timestamp=timestamp)

        now = datetime.now(tz=pytz.utc)

        if self.history is not None:
            self.history.loc[len(self.history)+1] = chosen_author, chosen_title, *now.isoformat()[:19].split("T"), int(now.timestamp())

        return poem

    

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
        self.stats = pd.DataFrame(columns=["name", "nationality","birth","death","n_poems","n_times_sent","days_since_last_sent"])

        for author in db.keys():

            name = db[author]["metadata"]["name"]
            birth = db[author]["metadata"]["birth"]
            death = db[author]["metadata"]["death"]
            nationality = db[author]["metadata"]["nationality"]
            n_poems = db[author]["metadata"]["n_poems"]

            elapsed = (ttime.time() - self.history["timestamp"][self.history.author==author].max()) / 86400 
            n_times_sent = (self.history["author"]==author).sum()
            
            self.stats.loc[author] = name, nationality, birth, death, n_poems, n_times_sent, np.round(elapsed,1)
            
        self.stats = self.stats.sort_values(by=["n_times_sent", "n_poems", "name"], ascending=False)

        if not order_by is None:
            self.stats = self.stats.sort_values(by=order_by, ascending=ascending)

            
            
            


  