"""
A library for interacting with JIRA in a ClusterHQ/Flocker-specific way.
"""

import jira.client as jc


def priority(issue):
    """
    Determine the priority of an issue.

    Priorities are negative numbers with absolute priority derived from the
    absolute value of the number.

    Priorities are currently derived from priority labels "prio1" through
    "prio4".

    :return: An integer giving the priority.
    """
    for i in range(1, 5):
        if "prio{}".format(i) in issue.fields.labels:
            return -i
    return 0


def client():
    """
    Create a JIRA client object.
    """
    return jc.JIRA({"server": "https://clusterhq.atlassian.net/"})
