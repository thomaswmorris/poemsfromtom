from dataclasses import dataclass, field

from . import utils
from .context import Context, MONTHS

@dataclass
class Author():
    """Author dataclass"""
    tag: str
    name: str
    birth: str
    death: str
    gender: str
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

@dataclass
class Poem():
    """Poem dataclass"""
    tag: str
    author: Author
    title: str
    body: str
    metadata: dict
    context: Context = None

    def __post_init__(self):
        if self.context is None:
            self.context = Context.now()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.title_by_author})"

    @property
    def translator(self) -> str:
        return self.metadata["translator"] if "translator" in self.metadata else ""

    @property
    def keywords(self) -> dict:
        return self.metadata["keywords"] if "keywords" in self.metadata else {}

    @property
    def title_by_author(self):
        if self.author.name:
            return f"{self.title} by {self.author.name}"
        else:
            return f"{self.title}"

    @property
    def pretty_date(self):
        if "date" not in self.metadata:
            return ""
        year, m, day = [self.metadata["date"].get(attr) for attr in ["year", "month", "day"]]
        x = ""
        if m:
            month = MONTHS[m-1].capitalize()
            if day:
                x += f"{month} {day}, "
            else:
                x += f"{month} "
        if year:
            x += f"{year}"

        return x.strip()

    @property
    def spacetime(self):
        parts = []
        if self.pretty_date:
            parts.append(self.pretty_date)
        if "location" in self.metadata:
            parts.append(self.metadata["location"])
        return ". ".join(parts) or ""

    @property
    def test_email_subject(self):
        return f"TEST ({self.context.pretty_date}): {self.title_by_author} {self.keywords}"

    @property
    def daily_email_subject(self):
        return f"Poem of the Day: {self.title_by_author}"

    @property
    def html_description(self):

        if self.author.name:
            description = f'{self.title} by <a href="{self.author.link}">{self.author.name}</a> {self.author.dates.replace("--", "&ndash;")}'
        else:
            description = self.title

        return description

    @property
    def html_body(self):
        body_text = self.body.replace("--", "&#8212;") # convert emdashes
        body_text = utils.add_italic_tags(body_text)

        parsed_lines = []

        for line in body_text.split("\n"):
            if len(line) == 0:
                parsed_lines.append(f'<div class="poem-line-blank">&#8203;</div>')
            elif line[:2] == "# ":
                parsed_lines.append(f'<div class="poem-line-title">{line[2:]}</div>')
            elif line[:2] == "> ":
                parsed_lines.append(f'<div class="poem-line-dialogue">{line[2:]}</div>')
            # elif line[0] == "“":
            #     parsed_lines.append(f'<div class="poem-line-double-quote-start">{line}</div>')
            # elif line[0] == "‘":
            #     parsed_lines.append(f'<div class="poem-line-single-quote-start">{line}</div>')
            # elif line[0] == "’":
            #     parsed_lines.append(f'<div class="poem-line-apostrophe-start">{line}</div>')
            else:
                parsed_lines.append(f'<div class="poem-line">{line.strip()}</div>')

        return "\n".join(parsed_lines)

    # @property        
    # def html_date(self):
    #     return f'<div><i>{self.context.pretty_date}</i></div>'



    @property
    def email_header(self):

        if self.author.name:
            description = f'<div>{self.title} by <a href="{self.author.link}">{self.author.name}</a> {self.author.dates.replace("--", "&ndash;")}</div>'
        else:
            description = f'<div>{self.title}</div>'

        if "translator" in self.metadata:
            description += f'\n<div><i>Translated by {self.translator}</i></div>'

        return description
            
    @property
    def email_html(self):
        return f'''<!DOCTYPE html>
<html lang="en">
<section style="text-align: left; max-width: 960px; font-family: Baskerville; font-size: 18px;">
<section style="padding-bottom: 32px;">
{self.email_header}
</section>
<section style="padding-bottom: 32px;">
{self.html_body}
</section>
<section>
<a href="https://thomaswmorris.com/poems">daily poems archive</a>
</section>
</html>
'''