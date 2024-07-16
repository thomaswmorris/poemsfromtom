import os, pathlib, yaml
import numpy as np
from .errors import AuthorNotFoundError, PoemNotFoundError
from .catalog import Catalog
from .poem import Author, Poem

here, this_file = os.path.split(__file__)

class Curator():

    def __init__(self, filepath=f"{here}/data/poems.json"):
        self.catalog = Catalog(filepath=filepath)


    def get_author(self, author=None) -> Author:

        all_authors = list(self.catalog.data.keys())

        if author is None:
            author = np.random.choice(all_authors)

        if author in all_authors:
            return Author(tag=author, **self.catalog.data[author]["metadata"])

        raise ValueError(f"No author '{author}'.")

                
    def get_poem(
                self,
                author=None,
                title=None,
                verbose=False,
                very_verbose=False,
                ) -> Poem:

        verbose = verbose or very_verbose
        mask = self.catalog.likelihood > 0

        if author and title:
            if author in self.catalog.data:
                if title in self.catalog.data[author]["poems"]:
                    return self.catalog.construct_poem(author=author, title=title)
                else:
                    raise PoemNotFoundError(f"There is no poem '{title}' by author '{author}' in the database.")
            else: 
                raise AuthorNotFoundError(f"There is no author '{author}' in the database.")
        
        # if author is supplied, get rid of poems not by that author
        if author: 
            mask &= self.catalog.author == author
            if not mask.sum():
                raise PoemNotFoundError(f"There are no poems by author '{author}' in the database.")

        # if JUST the title is supplied, do this (why would you ever do this? but we should support it anyway)
        if title: 
            mask &= self.catalog.title == title
            if not mask.sum():
                raise PoemNotFoundError(f"There is no poem called '{title}' by any author in the database.")
        
        self.catalog.df.loc[~mask, "likelihood"] = 0
        self.catalog.df["probability"] = self.catalog.df.likelihood / self.catalog.df.likelihood.sum()

        if very_verbose: 
            catalog_summary = self.catalog.df.sort_values(["probability", "author"], ascending=[False, False])[["author", "title", "context", "probability"]]
            print(f"choosing from {len(self.catalog.df)} poems; the most likely are:")
            print(catalog_summary.iloc[:20].to_string())
        chosen_loc = np.random.choice(self.catalog.df.index, p=self.catalog.df.probability)
        chosen_author, chosen_title = self.catalog.df.loc[chosen_loc, ["author", "title"]]
        
        if verbose: 
            print(f"chose poem '{chosen_title}' by {chosen_author}")

        self.catalog.reset()

        return self.catalog.construct_poem(author=chosen_author, title=chosen_title)
