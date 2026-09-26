from poems import Curator

import os
import pandas as pd

def test_apply_history():

    curator = Curator()
    history = pd.read_csv(os.environ["POEMS_HISTORY_PATH"])
    curator.catalog.apply_history(history, verbose=True)