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
        if "time" not in self.metadata:
            return ""
        year, m, day = [self.metadata["time"].get(attr) for attr in ["year", "month", "day"]]
        x = ""
        if m:
            month = m.capitalize()
            if day:
                x += f"{month} {day}, "
            else:
                x += f"{month} "
        if year:
            x += f"{year}"

        if "approximate" in self.metadata["time"]:
            x = f"circa {x}"

        return x.strip()

    def spacetime(self, html=True):
        parts = []
        if "location" in self.metadata:
            parts.append(self.metadata["location"])
        if self.pretty_date:
            parts.append(self.pretty_date)
        return ". ".join(parts)

    def source(self, html=True):
        parts = []
        source = self.metadata.get("source")
        if source:
            if "link" in source:
                parts.append(f'<a href="{source["link"]}">{source["title"]}</a>')
            else:
                parts.append(f"{source['title']}")
            if "published" in source:
                year = source['published']['year']
                if source.get("type") in ["magazine"]:
                    parts.append(f"({source['published']['month'].capitalize()} {year})")
                else:
                    parts.append(f"({year})")
            return " ".join(parts)
        return ""

    @property
    def language(self) -> str:
        return self.metadata.get("language")

    @property
    def translator(self) -> str:
        return self.metadata.get("translator")

    @property
    def translation(self) -> str:
        if self.language is None:
            return None
        if self.language.lower() == "english":
            return None
        else:
            translation = f"Translated from the {self.language.capitalize()}"
            if self.translator is not None:
                translation += f" by {self.translator}"
            return translation

    def email_subject(self, mode="daily"):
        if mode == "daily":
            return f"Poem of the Day: {self.title_by_author}"
        if mode == "test":
            return f"TEST ({self.context.pretty_date}): {self.title_by_author} {self.keywords}"
        else:
            raise ValueError("'mode' must be one of ['daily', 'test'].")

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

    


    def html_header(self, flags=True):
        html_description = self.author.html_description(flags=flags, html=True)
        if html_description:
            header = f'<div id="poem-description">{self.title} by {html_description}</div>'
        else:
            header = f'<div id="poem-description">{self.title}</div>'

        if self.translation:
            header += f'\n<div id="poem-translation"><i>{self.translation}</i></div>'

        return header
    
    def html_footer(self, archive_link=False):
        parts = []
        if self.spacetime(html=True):
            parts.append(f'<i>{self.spacetime(html=True)}.</i>')
        if self.source(html=True):
            parts.append(f'from <i>{self.source(html=True)}</i>')
        if archive_link:
            parts.append('<a href="https://thomaswmorris.com/poems">daily poems archive</a>')
        return "\n<br>".join(parts)
            
    @property
    def email_html(self):
        return f'''<!DOCTYPE html>
<html lang="en">
<section style="text-align: left; max-width: 960px; font-family: Baskerville; font-size: 18px;">
<section id="header" style="padding-bottom: 32px;">
{self.html_header(flags=False)}
</section>
<section id="body" style="padding-bottom: 32px;">
{self.html_body()}
</section>
<section id="footer" style="padding-bottom: 32px;">
{self.html_footer(archive_link=True)}
</section>
</html>
'''