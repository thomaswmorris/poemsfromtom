import numpy as np

import json
import os
import warnings

from pandas import DataFrame
from .context import Context
from .poem import Poem, Author

here, this_file = os.path.split(__file__)

with open(f"{here}/weights.json", "r+") as f:
    CONTEXT_WEIGHTS = json.load(f)

class Catalog():

    def __init__(self, filepath: str):

        self.filepath = filepath
        
        with open(filepath, "r+") as f:
            self.data = json.load(f)

        entries = {}
        index = 0
        
        for author, author_data in self.data.items():
            author_metadata = self.data[author]["metadata"]
            author_tags = author_metadata["tags"]
            for title, poem in author_data["poems"].items():

                context_keywords = poem["metadata"].get("keywords", {})

                entries[index] = {
                                  "author": author, 
                                  "title": title,
                                  "context": context_keywords,
                                  "tags": [*author_tags, *context_keywords.values()], 
                                  "date": poem["metadata"].get("date", None),
                                  "translator": poem["metadata"].get("translator", None),
                                  "word_count": len(poem["body"].split()),
                                 }

                index += 1
                
        self.df = DataFrame(entries).T
        self.df.loc[:, "likelihood"] = 1.0
        
        # self.authors = {author: Author(**self.data[author]["metadata"]) for author in self.data.keys()}

        self.contextual = False

    def __getattr__(self, attr):
        if attr in self.df.columns:
            return self.df.loc[:, attr]
        raise AttributeError(f"No attribute named {attr}.")
    
    def reset(self):
        self.df.likelihood = 1.
        self.contextual = False

    @property
    def contexts(self):
        c = {}
        for category in CONTEXT_WEIGHTS.keys():
            c[category] = [context.get(category, None) for context in self.df.context]
        return c

    def copy(self):
        return Catalog(filepath=self.filepath)

    def apply_context(self, context: dict, forced=[], verbose=False):

        if self.contextual:
            self.reset()

        contexts = self.contexts

        for category in CONTEXT_WEIGHTS.keys():
            if not category in context.keys(): 
                continue

            for keyword, weight in CONTEXT_WEIGHTS[category].items():

                mask = np.array([c==keyword for c in contexts[category]])

                if keyword == context[category]: 
                    if keyword in forced:
                        if verbose:
                            print(f"Forcing context '{keyword}'")
                        multiplier = 1e18
                    else:
                        multiplier = weight
                else: 
                    multiplier = 0
                
                self.df.loc[mask, "likelihood"] *= multiplier

        self.contextual = True

        self.df.loc[:, "probability"] = self.df.likelihood / self.df.likelihood.sum()

    
    def apply_history(self, history: DataFrame, latency: int = 30 * 86400, verbose: bool = False):

        timestamp = Context.now().timestamp

        last_occurence = DataFrame(columns=["timestamp"], dtype=float)
        for index, entry in history.iterrows():
            last_occurence.loc[entry.author, "timestamp"] = entry.timestamp
        
        last_occurence = last_occurence.sort_values("timestamp")

        indices_to_drop = []
        dropped_authors = []

        for _, entry in history.iterrows():

            res = self.df.loc[(self.df.author==entry.author) & (self.df.title==entry.title)]

            if not len(res):
                warnings.warn(f"Could not remove poem '{entry.title}' by '{entry.author}'.")

            indices_to_drop.extend(res.index)

            if entry.timestamp > timestamp - latency:
                if entry.author not in dropped_authors:
                    indices_to_drop.extend(self.df.loc[self.df.author == entry.author].index)
                    dropped_authors.append(entry.author)

        if verbose:
            print(f"Dropped authors {dropped_authors}.")

        self.df.loc[indices_to_drop, "likelihood"] = 0

    def __repr__(self):
        return self.df.__repr__()

    def _repr_html_(self):
        return self.df._repr_html_()
        
    def construct_poem(self, author, title):
        return Poem(tag=title, author=Author(tag=author, **self.data[author]["metadata"]), **self.data[author]["poems"][title])
