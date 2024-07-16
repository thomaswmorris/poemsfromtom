from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Author():
    """Author dataclass"""
    tag: str
    name: str
    birth: dict
    death: dict
    gender: str
    religion: str
    nationality: str
    language: str
    flag: str
    link: str
    favorite: bool
    n_poems: str
    tags: list = field(default_factory=list)

    @property
    def dates(self):
        """
        Convert birth and death to a string.
        """
        # this assumes no one born before Christ is still alive
        if not self.death: 
            if not self.birth:
                return ""
            else:
                return f"(born {self.birth['year']})"
        
        birth_string = f"{'c. ' if 'circa' in self.birth else ''}{abs(self.birth['year'])}"
        death_string = f"{'c. ' if 'circa' in self.death else ''}{abs(self.death['year'])}"

        if self.birth["year"] < 0: 
            if self.death["year"] < 0: 
                death_string += " BC"
            else: 
                birth_string += " BC"
                death_string += " AD"

        return f"({birth_string} – {death_string})"
