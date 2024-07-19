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
        Convert birth_date and death_date to a string.
        """
        # this assumes no one born before Christ is still alive

        birth_date = (self.birth or {}).get("date", {})
        death_date = (self.death or {}).get("date", {})
        
        birth_date_parts = date_to_string_parts(birth_date, month_and_day)
        death_date_parts = date_to_string_parts(death_date, month_and_day)

        if ("BC" in birth_date_parts) and ("BC" not in death_date_parts):
            death_date_parts.insert(0, "AD")

        if "circa" in birth_date:
            birth_date_parts.insert(0, "c.")
        if "circa" in death_date:
            death_date_parts.insert(0, "c.")

        birth_date_string = " ".join(birth_date_parts)
        death_date_string = " ".join(death_date_parts)

        if not death_date:
            if not birth_date:
                return ""
            return f"(born {birth_date_string})"

        return f"({birth_date_string} – {death_date_string})"
