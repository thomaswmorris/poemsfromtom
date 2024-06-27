from dataclasses import dataclass, field

@dataclass
class Author():
    """Author dataclass"""
    tag: str
    name: str
    birth: str
    death: str
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
                return f"(born {self.birth})"

        birth_is_circa = True if "~" in self.birth else False
        death_is_circa = True if "~" in self.death else False
        
        b_numeric = int(self.birth.strip("~"))
        d_numeric = int(self.death.strip("~"))

        birth_string, death_string = str(abs(b_numeric)), str(abs(d_numeric))

        birth_string = f'{"c. " if birth_is_circa else ""}{abs(b_numeric)}'
        death_string = f'{"c. " if death_is_circa else ""}{abs(d_numeric)}'

        if b_numeric < 0: 
            if d_numeric < 0: 
                death_string += " BC"
            else: 
                birth_string += " BC"
                death_string += " AD"

        return f"({birth_string} -- {death_string})"
