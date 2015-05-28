"""
Find JIRA issues which are currently waiting to be reviewed.
"""

from __future__ import print_function

if __name__ == '__main__':
    from sys import argv
    from review_issues import main
    raise SystemExit(main(*argv[1:]))

from issuelib import priority, client


def main():
    c = client()

    query = (
        'type != "Story" and '
        'status in ("Design Review Ready", "Code Review Ready")'
    )
    issues = list(c.search_issues(query))
    issues.sort(key=priority)
    for issue in issues:
        p = priority(issue)
        if p:
            prio = "prio{} ".format(-p)
        else:
            prio = ""
        print("{}: {}{}".format(issue.key, prio, issue.fields.summary))
