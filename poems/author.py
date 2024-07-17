from dataclasses import dataclass, field
from .utils import date_to_string_parts

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

    def dates(self, month_and_day=True):
        """
        Convert birth and death to a string.
        """
        # this assumes no one born before Christ is still alive

        birth = self.birth or {}
        death = self.death or {}
        
        birth_parts = date_to_string_parts(birth, month_and_day)
        death_parts = date_to_string_parts(death, month_and_day)

        if ("BC" in birth_parts) and ("BC" not in death_parts):
            death_parts.insert(0, "AD")

        if "circa" in birth:
            birth_parts.insert(0, "c.")
        if "circa" in death:
            death_parts.insert(0, "c.")

        birth_string = " ".join(birth_parts)
        death_string = " ".join(death_parts)

        if not death:
            if not birth:
                return ""
            return f"(born {birth_string})"

        return f"({birth_string} – {death_string})"
