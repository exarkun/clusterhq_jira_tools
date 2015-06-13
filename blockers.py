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
                g.add_edge(head.key, dest_key, link_type=link_type)
            else:
                g.add_edge(dest_key, head.key, link_type=link_type)

        seen[head.key] = head

    return g


def filter_edges(predicate, graph):
    """
    Create a graph based on 'graph', but only with edges that match
    'predicate'.

    Any nodes that are no longer connected will also be removed.
    """
    nonmatching_edges = (
        (src, dst) for (src, dst) in graph.edges()
        if not predicate(graph[src][dst]))
    new_graph = graph.copy()
    new_graph.remove_edges_from(nonmatching_edges)
    new_graph.remove_nodes_from(networkx.isolates(new_graph))
    return new_graph


if __name__ == '__main__':
    client = issuelib.client()
    # XXX: IO
    base_issue = client.issue('FLOC-2008')
    print build_issue_graph(client, base_issue)
