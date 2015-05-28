"""
Present a list of issues which should probably be worked on next.
"""

from __future__ import print_function

if __name__ == '__main__':
    from sys import argv
    from next_issue import main
    raise SystemExit(main(*argv[1:]))

from issuelib import client, priority

BACKLOGS = [
    "Backlog",
    "Code backlog",
    "Contribution backlog",
    "Design Backlog",
]


def main():
    c = client()

    query = (
        'type != "Story" and '
        'status in ({}) and '
        'sprint in openSprints() '
    ).format(", ".join(repr(backlog) for backlog in BACKLOGS))
    issues = list(c.search_issues(query, maxResults=False))
    issues.sort(key=priority)
    for issue in issues:
        print("{}: {}".format(issue.key, issue.fields.summary))
