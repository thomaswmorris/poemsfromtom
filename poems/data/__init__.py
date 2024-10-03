import os
import json
import pandas as pd

from ..objects import Author

here, this_filename = os.path.split(__file__)
countries = pd.read_csv(f"{here}/countries.csv", index_col=0).fillna("")


with open(f"{here}/poems.json", "r+") as f:
    poems = json.load(f)

# author_list = []
# author_entries = {}
# for author_key, author_data in poems.items():
#     author = Author(key=author_key, **author_data["metadata"])
#     author_list.append(author)

#     author_entries[author_key] = {
#                                 "name": author.name,
#                                 "demonym": author.demonym.lower(),
#                                 # "dates": author.dates()[1:-1],
#                                   }
    
# authors = pd.DataFrame(author_entries).T