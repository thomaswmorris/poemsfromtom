import os
import pandas as pd
from dataclasses import dataclass, field

from .utils import date_to_string_parts

here, this_filename = os.path.split(__file__)
flags = pd.read_csv(f"{here}/data/flags.csv", index_col=0)

@dataclass
class Author():
    """Author dataclass"""
    tag: str = None
    name: str = None
    birth: dict = field(default_factory=list)
    death: dict = field(default_factory=list)
    gender: str = None
    education: str = None
    movement: str = None
    religion: str = None
    nationality: str = None
    language: str = None
    flags: str = None
    link: str = None
    favorite: bool = False
    tags: list = field(default_factory=list)

    def __post_init__(self):

        self.flags = []
        for key in self.nationality:
            self.flags.append(flags.loc[key, "emoji"])

    @property
    def demonym(self):
        return "-".join([flags.loc[key, "demonym"] for key in self.nationality])

    @property
    def html_flags(self):
        html_flags = []
        for key in self.nationality:
            html_flags.append(flags.loc[key, "html"])
        if not html_flags:
            return ""
        return f'<span title="{self.demonym}">{"".join(html_flags)}</span>'
    
    def html_description(self, name=True, flags=True, html=True):

        parts = []
        if not self.name:
            return ""
        if name:
            if not self.name:
                parts = [self.name]
            if self.link:
                parts = [f'<a href="{self.link}">{self.name}</a>']            
        if flags and self.html_flags and html:
            parts.append(self.html_flags)
        parts.append(self.dates(html=html))

        return " ".join(parts)

    def birth_or_death_string(self, key, html=False):
        if key not in ["birth", "death"]:
            raise ValueError(f"'{key}' must be either 'birth' or 'death'.")
        bd = getattr(self, key) or {}
        date = bd.get("date", {})
        s = " ".join(date_to_string_parts(date, month_and_day=True))
        if html:
            if bd.get("place"):
                place = ", ".join(list(bd["place"].values()))
                s = f'<span title="{place}">{s}</span>'
        if date.get("circa"):
            prefix = "c. " if not html else '<span title="circa">c. </span>'
            s = prefix + s
        if key == "birth":
            if date.get("floruit"):
                prefix = "fl. " if not html else '<a href="https://en.wikipedia.org/wiki/Floruit">fl.</a> '
                s = prefix + s
        return s
    
    def birth_string(self, html=False):
        return self.birth_or_death_string("birth", html=html)
    
    def death_string(self, html=False):
        return self.birth_or_death_string("death", html=html)
    

    def dates(self, html=False):
        """
        This assumes no one born before Christ is still alive
        """ 

        birth_string = self.birth_string(html=html)
        death_string = self.death_string(html=html)

        if ("BC" in birth_string) and ("BC" not in death_string):
            death_string = "AD" + death_string

        if not death_string:
            if not birth_string:
                return ""
            return f"(born {birth_string})"

        return f"({birth_string} – {death_string})"




