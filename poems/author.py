from dataclasses import dataclass, field
from .utils import date_to_string_parts

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
    flag: str = None
    link: str = None
    favorite: bool = False
    n_poems: str = None
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
