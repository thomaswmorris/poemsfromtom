import os
import json
import pandas as pd

from ..objects import Author

here, this_filename = os.path.split(__file__)
flags = pd.read_csv(f"{here}/flags.csv", index_col=0)


with open(f"{here}/poems.json", "r+") as f:
    poems = json.load(f)

authors = []
for author_key, d in poems.items():
    authors.append(Author(key=author_key, **d["metadata"]))