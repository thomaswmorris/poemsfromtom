import re, pytz, smtplib, time

import numpy as np
import pandas as pd
import github as gh

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
        if verbose: print(f"writing to {filename}")

    head_sha   = repo.get_branch(branch).commit.sha
    base_tree  = repo.get_git_tree(sha=head_sha)
    tree       = repo.create_git_tree(elements, base_tree)
    parent     = repo.get_git_commit(sha=head_sha) 
    commit     = repo.create_git_commit(f"updated logs @ {datetime.now(tz=pytz.utc).isoformat()[:19]}", tree, [parent])
    master_ref = repo.get_git_ref(f"heads/{branch}")
    master_ref.edit(sha=commit.sha)


def make_author_stats(history, catalog=None):

    sort_kwargs = {"by": ["n_times_sent", "n_poems", "date_last_sent"], "ascending": [False, False, False]}

    timestamp = time.time()

    stats = pd.DataFrame(columns=["n_times_sent", "n_poems", "attrition", "date_last_sent"], dtype="object")
    
    uauthors = np.unique(catalog.author if catalog else history.author)

    for author in uauthors:

        if author not in stats.index.values:
            author_mask = history.author.values == author
            stats.loc[author, "n_times_sent"] = sum(author_mask)

            if author_mask.sum():
                timestamp_last_sent = history.loc[author_mask, "timestamp"].max()
                isoformat_last_sent = datetime.fromtimestamp(timestamp_last_sent).astimezone(pytz.utc).isoformat()
                # days_since_last_sent = (timestamp - timestamp_last_sent) / 86400
                stats.loc[author,"date_last_sent"] = isoformat_last_sent[:10]
                # stats.loc[author,"days_since_last_sent"] = int(np.round(days_since_last_sent))

    if catalog:

        sort_kwargs["by"].append("n_poems")
        sort_kwargs["ascending"].append(False)

        for author in stats.index:

            stats.loc[author, "n_poems"] = catalog.data[author]["metadata"]["n_poems"]
            attrition = stats.loc[author, "n_times_sent"] / stats.loc[author, "n_poems"]
            stats.loc[author, "attrition"] = np.round(attrition, 3)


    return stats.sort_values(**sort_kwargs)

        

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
