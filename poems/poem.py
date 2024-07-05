from dataclasses import dataclass

from . import utils
from .author import Author
from .context import Context, MONTHS

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
    def keywords(self) -> dict:
        return self.metadata.get("context", {})

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
            month = m.capitalize()
            if day:
                x += f"{month} {day}, "
            else:
                x += f"{month} "
        if year:
            x += f"{year}"

        if "approximate" in self.metadata["date"]:
            x = f"circa {x}"

        return x.strip()

    @property
    def spacetime(self):
        parts = []
        if "location" in self.metadata:
            parts.append(self.metadata["location"])
        if self.pretty_date:
            parts.append(self.pretty_date)
        return ". ".join(parts)

    @property
    def translator(self) -> str:
        return self.metadata.get("translator")

    @property
    def translation(self) -> str:
        return f"Translated by {self.translator}" if self.translator is not None else ""


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
<section id="header" style="padding-bottom: 32px;">
{self.email_header}
</section>
<section id="body" style="padding-bottom: 32px;">
{self.html_body}
</section>
<section id="footer" style="padding-bottom: 32px;">
{self.spacetime}
</section>
<section>
<a href="https://thomaswmorris.com/poems">daily poems archive</a>
</section>
</html>
'''