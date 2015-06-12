"""
Understand what's blocking an issue.
"""

import issuelib


def blocker_ids(issue):
    """
    Immediate blockers of an issue.
    """
    for link in issue.fields.issuelinks:
        if link.type.name == 'Blocks':
            yield link.inwardIssue


if __name__ == '__main__':
    client = issuelib.client()
    base_issue = client.issue('FLOC-2008')
    for i in blocker_ids(base_issue):
        print i
