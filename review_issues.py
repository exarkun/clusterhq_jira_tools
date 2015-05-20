"""
Find JIRA issues which are currently waiting to be reviewed.
"""

from __future__ import print_function

if __name__ == '__main__':
    from sys import argv
    from review_issues import main
    raise SystemExit(main(*argv[1:]))

import jira.client as jc


def priority(issue):
    for i in range(1, 5):
        if "prio{}".format(i) in issue.fields.labels:
            return -i
    return 0


def main():
    c = jc.JIRA({"server": "https://clusterhq.atlassian.net/"})

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
