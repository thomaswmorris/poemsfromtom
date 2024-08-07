import os
import pandas as pd

here, this_filename = os.path.split(__file__)
flags = pd.read_csv(f"{here}/flags.csv", index_col=0)