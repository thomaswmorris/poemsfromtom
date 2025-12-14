import numpy as np

import json
import os
import pathlib
import yaml

from pandas import DataFrame
from .context import Context
from .objects import Poem, Author
from .utils import make_author_stats

import logging
logger = logging.getLogger("poems")

here, this_file = os.path.split(__file__)

CONTEXT_WEIGHTS = yaml.safe_load(pathlib.Path(f"{here}/data/weights.yml").read_text())

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

                context_keywords = poem["metadata"].get("context", {})

                poem_tags = [*author_tags, *context_keywords.values(), *poem["metadata"].get("tags", [])]

                entries[index] = {
                                  "author": author, 
                                  "title": title,
                                  "context": context_keywords,
                                  "tags": poem_tags, 
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
    def context(self):
        return self._context if hasattr(self, "_context") else Context.now()
    
    @property
    def poem_contexts(self):
        c = {}
        for category in CONTEXT_WEIGHTS.keys():
            c[category] = [context.get(category, None) for context in self.df.context]
        return c

    def copy(self):
        return Catalog(filepath=self.filepath)

    def apply_context(self, context: Context, forced=[], verbose=False):

        if self.contextual:
            self.reset()

        self._context = context
        context_dict = context.to_dict()

        poem_contexts = self.poem_contexts # of the catalog

        for category in CONTEXT_WEIGHTS.keys():
            if not category in context_dict.keys(): 
                continue

            for keyword, weight in CONTEXT_WEIGHTS[category].items():

                mask = np.array([c==keyword for c in poem_contexts[category]])

                if (keyword in context_dict[category] if category == "holiday" else keyword == context_dict[category]): 
                    if keyword in forced:
                        if verbose:
                            logger.info(f"FORCING CONTEXT: {category}='{keyword}'")
                        multiplier = 1e18
                    else:
                        multiplier = weight
                else: 
                    multiplier = 0
                
                self.df.loc[mask, "likelihood"] *= multiplier

        self.contextual = True

        self.df.loc[:, "probability"] = self.df.likelihood / self.df.likelihood.sum()

    
    def apply_history(self, history: DataFrame, cooldown: int = 7 * 86400, manage_attrition: bool = False, verbose: bool = False):

        timestamp = Context.now().timestamp

        author_stats = make_author_stats(history, self)

        last_occurence = DataFrame(columns=["timestamp"], dtype=float)
        for _, entry in history.iterrows():
            last_occurence.loc[entry.author, "timestamp"] = entry.timestamp
        
        last_occurence = last_occurence.sort_values("timestamp")

        indices_to_drop = []
        treated_authors = []
        dropped_authors = []

        for _, entry in history.iterrows():

            author_mask = self.df.author == entry.author

            res = self.df.loc[author_mask & (self.df.title==entry.title)]

            if not len(res):
                logger.warning(f"Could not remove poem '{entry.title}' by '{entry.author}'.")

            indices_to_drop.extend(res.index)

            # apply to all poems by this author, if not done for this author yet:
            if entry.author not in dropped_authors:

                if entry.timestamp > timestamp - cooldown:
                    indices_to_drop.extend(self.df.loc[author_mask].index)
                    dropped_authors.append(entry.author)

            if manage_attrition:
                if entry.author not in treated_authors:
                    self.df.loc[author_mask, "likelihood"] *= 1 - author_stats.loc[entry.author, "attrition"]
                    treated_authors.append(entry.author)

        if verbose:
            logger.info(f"Dropped authors {dropped_authors}")


        self.df.loc[indices_to_drop, "likelihood"] = 0

    def __repr__(self):
        return self.df.__repr__()

    def _repr_html_(self):
        return self.df._repr_html_()
        
    def construct_poem(self, author, title):
        return Poem(key=title, author=Author(**self.data[author]["metadata"]), context=self.context, **self.data[author]["poems"][title])
