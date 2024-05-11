import re, smtplib

import numpy as np
import pandas as pd
import github as gh
import time


from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import StringIO


def email_thread(poem, username, password, name, email, subject):
    done, fails = False, 0
    while (not done) and (fails < 60):
        try:
            send_email(username, password, poem.email_html, email, subject)
            a, b = email.split("@"); print(f"{datetime.now().isoformat()} | sent to {name:<18} | {a:>24} @ {b:<20}")
            done = True
        except Exception as error:
            print(f"{error}\nEncountered error, trying again...")
            fails += 1
            time.sleep(60)

def load_github_repo(github_repo_name=None, github_token=None):
    return gh.Github(github_token).get_user().get_repo(github_repo_name)


def read_csv(filepath, repo=None):
    """
    Read a CSV, maybe from a github repo.
    """
    if repo:
        csv_content = repo.get_contents(filepath, ref="master")
        csv = pd.read_csv(StringIO(csv_content.decoded_content.decode()), index_col=0)
    else:         
        csv = pd.read_csv(filepath, index_col=0)

    return csv


def write_to_repo(repo, items, branch="master", verbose=False):

    elements = []
    for filename, content in items.items():

        blob = repo.create_git_blob(content, "utf-8")
        elements.append(gh.InputGitTreeElement(path=filename, mode="100644", type="blob", sha=blob.sha))
        if verbose: print(f"writing to {github_repo_name}/{filename}")

    head_sha   = repo.get_branch(branch).commit.sha
    base_tree  = repo.get_git_tree(sha=head_sha)
    tree       = repo.create_git_tree(elements, base_tree)
    parent     = repo.get_git_commit(sha=head_sha) 
    commit     = repo.create_git_commit(f"updated logs @ {datetime.now(tz=pytz.utc).isoformat()[:19]}", tree, [parent])
    master_ref = repo.get_git_ref(f"heads/{branch}")
    master_ref.edit(sha=commit.sha)


def make_author_stats(history, catalog=None):

    sort_kwargs = {"by": ["n_times_sent", "days_since_last_sent"], "ascending": [False, True]}

    entries = {}

    timestamp = time.time()
    
    for author in np.unique(history.author):

        if author not in entries:

            author_mask = history.author.values == author
            days_since_last_sent = (timestamp - history.loc[author_mask, "timestamp"].max()) / 86400

            entries[author] = {
                "n_times_sent": sum(author_mask),
                "days_since_last_sent": int(days_since_last_sent),
            }

    stats = pd.DataFrame(entries, dtype=int).T

    if catalog:

        sort_kwargs["by"].append("n_poems")
        sort_kwargs["ascending"].append(False)

        stats.insert(0, "n_poems", 0)

        for author in stats.index:

            stats.loc[author, "n_poems"] = catalog.data[author]["metadata"]["n_poems"]

    return stats.sort_values(**sort_kwargs)


# def make_stats(self, order_by=None, ascending=True, force_rows=True, force_cols=True):

#     if self.history is None: raise(Exception("No history has been loaded!"))
#     if force_rows: pd.set_option("display.max_rows", None)
#     if force_cols: pd.set_option("display.max_columns", None)
#     self.stats = pd.DataFrame(columns=["name", "nationality","birth","death","n_poems","n_times_sent","days_since_last_sent"])

#     for author in db.keys():

#         name = db[author]["metadata"]["name"]
#         birth = db[author]["metadata"]["birth"]
#         death = db[author]["metadata"]["death"]
#         nationality = db[author]["metadata"]["nationality"]
#         n_poems = db[author]["metadata"]["n_poems"]

#         elapsed = (ttime.time() - self.history["timestamp"][self.history.author==author].max()) / 86400 
#         n_times_sent = (self.history["author"]==author).sum()
        
#         self.stats.loc[author] = name, nationality, birth, death, n_poems, n_times_sent, np.round(elapsed,1)
        
#     self.stats = self.stats.sort_values(by=["n_times_sent", "n_poems", "name"], ascending=False)

#     if not order_by is None:
#         self.stats = self.stats.sort_values(by=order_by, ascending=ascending)

        
        

def send_email(username, password, html, recipient, subject=""):

        message = MIMEMultipart("alternative")
        message["From"]    = username
        message["To"]      = recipient
        message["Subject"] = subject
        message.attach(MIMEText(html, "html"))
        
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(username, password)
        server.send_message(message)
        server.quit()

def add_italic_tags(text):
    """
    Converts to HTML italic format.
    """
    sections = []
    for i, section in enumerate(text.split("_")):
        if i % 2 == 1:
            section = "<i>" + re.sub("\n", "</i>\n<i>", section) + "</i>"
            section.replace("<i></i>", "")
        sections.append(section)
    return "".join(sections)

# def convert_to_html_lines(text):
#     """
#     Converts to HTML italic format.
#     """
#     html_lines = []
#     for line in text.split("\n"):
#         if len(line) == 0:
#             html_lines.append('<div class="poem-line-blank">&#8203</div>')
#         elif line[:2] == "> ":
#             html_lines.append(f'<div class="poem-line-title">{line}</div>')
#         elif line.strip().strip("_")[0] in ["“", "‘", "’"]:
#             html_lines.append(f'<div class="poem-line-punc-start">{line}</div>')
#         else:
#             html_lines.append(f'<div class="poem-line">{line}</div>')
            
#     return add_italic_tags("\n".join(html_lines))



# def text_to_html_lines(text):

#     text = text.replace("--", "&#8212;") # convert emdashes
#     text = add_italic_tags(text)

#     parsed_lines = []
#     for line in text.split("\n"):
#         if len(line) > 0:
#             parsed_lines.append(f'<div class="poem-line">{line.strip()}</div>')
#         else:
#             parsed_lines.append(f'<div class="poem-line-blank">&#8203;</div>')

#     return "\n".join(parsed_lines)