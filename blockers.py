"""
Understand what's blocking an issue.
"""

import networkx

import issuelib


NOT_FOUND = object()


def build_issue_graph(client, issue):
    """
    Build a graph of linked issues, starting at 'issue'.
    """
    seen = {}
    queue = [issue]
    g = networkx.DiGraph()
    while queue:
        head, queue = queue[0], queue[1:]
        links = getattr(head.fields, 'issuelinks', ())

        g.add_node(head.key, issue=head.raw)

        for link in links:

            if getattr(link, 'inwardIssue', NOT_FOUND) is NOT_FOUND:
                dest_key = link.outwardIssue.key
                outward = True
            else:
                dest_key = link.inwardIssue.key
                outward = False

            if dest_key not in seen:
                # XXX: IO
                dest = client.issue(dest_key)
                queue.append(dest)

            g.add_node(dest_key, issue=dest.raw)
            link_type = link.type.name
            if outward:
                g.add_edge(dest_key, head.key, link_type=link_type)
            else:
                g.add_edge(head.key, dest_key, link_type=link_type)

        seen[head.key] = head

    return g


if __name__ == '__main__':
    client = issuelib.client()
    # XXX: IO
    base_issue = client.issue('FLOC-2008')
    print build_issue_graph(client, base_issue)
