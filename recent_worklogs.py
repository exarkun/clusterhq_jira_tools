
from __future__ import print_function

if __name__ == '__main__':
    from sys import argv
    from recent_worklogs import main
    raise SystemExit(main(*argv[1:]))

from datetime import datetime, timedelta

from dateutil.parser import parse as parse_datetime

from pytz import utc

from issuelib import client


def main(username="exarkun"):
    username = username.decode("ascii")
    now = datetime.now(tz=utc)

    c = client()

    RECENT_ISSUES = (
        '(issuetype = Bug or issuetype != Bug) and '
        'updated >= -1 '
        'order by updated desc'
    )

    work = {}

    for issue in c.search_issues(RECENT_ISSUES):
        for worklog in c.worklogs(issue=issue.id):
            started = parse_datetime(worklog.started)
            if (now - started) <= timedelta(days=1):
                if worklog.author.name == username:
                    key = (issue.key, issue.fields.summary)
                    work.setdefault(key, []).append(worklog.comment)

    print(u"\n".join(
        u"{}: {} ({})".format(key, summary, u", ".join(comments))
        for ((key, summary), comments)
        in work.items()
    ))
