import pandas as pd
import os
import numpy as np
import copy
from .spacetime import Time, Place, Spacetime

here, this_filename = os.path.split(__file__)
countries = pd.read_csv(f"{here}/../data/countries.csv", index_col=0).fillna("")

class Author:

    def __init__(self, **kwargs):

        self.data = copy.deepcopy(kwargs)
        for key in ["birth", "death", "floruit"]:
            if self.data.get(key) is not None:
                self.data[key] = Spacetime(time=Time(self.data[key].get("time")), place=Place(self.data[key].get("place")))

    def dates(self, abbreviate=True, html=False):
    
        has_birth = self.data.get("birth") is not None
        has_death = self.data.get("death") is not None
    
        html = "place" if html else None
        
        if has_birth:
            if has_death:
                kwargs = {
                    "specify_ad": (self.birth.time.era != self.death.time.era),
                    "abbreviate": abbreviate,
                }
                
                return f"{self.birth.string(kwargs=kwargs, html=html)} – {self.death.string(kwargs=kwargs, html=html)}"
            return f"born {self.birth.string(html=html)}"
        else:
            return ""


    def html_description(self, flags=True):

        parts = []

        html_flags = self.flag_emojis(html=True)
        html_dates = self.dates(html="place")

        if self.name:
            parts.append(f'<a href="{self.link}">{self.name}</a>')

        if html_flags and flags:
            parts.append(html_flags)

        if html_dates:
            parts.append(html_dates)

        return " ".join(parts)


    @property
    def default_language(self):
        languages = self.data.get("language", [])
        if languages:
            return languages[-1]
        return None

    @property
    def nationality(self):
        return self.data.get("nationality", [])
    
    @property
    def demonym(self):
        if self.nationality:
            return "-".join([countries.loc[country, "demonym"] for country in self.nationality])
        return ""
    
    def flag_emojis(self, html=False):
        if self.nationality:
            emojis = [countries.loc[country, "emoji"] for country in self.nationality]
            s = "".join(emojis)
            if html:
                s = f'<span title="{self.demonym}">{s}</span>'
            return s
        return ""

    def __repr__(self):
        return f"Author({self.data})"
        
    def __getattr__(self, attr):

        if attr in self.data:
            return self.data[attr]
        
        if attr in ["link", "name"]:
            return ""

        else:
            raise KeyError(f"No attribute '{attr}'.")
