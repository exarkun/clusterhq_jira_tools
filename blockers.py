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


def descendants_dag(graph, root):
    # XXX: There must be a standard name for this sort of thing.
    if not networkx.is_directed_acyclic_graph(graph):
        raise ValueError('%r is not DAG' % (graph,))
    descs = networkx.descendants(graph, root)
    non_descs = set(graph.nodes()) - descs
    non_descs.remove(root)
    new_graph = graph.copy()
    new_graph.remove_nodes_from(non_descs)
    if not networkx.is_directed_acyclic_graph(new_graph):
        raise AssertionError('Expected %r to be a DAG' % (new_graph,))
    return new_graph


def ancestors_dag(graph, root):
    # XXX: This is a clone of descendants_dag. :(
    if not networkx.is_directed_acyclic_graph(graph):
        raise ValueError('%r is not DAG' % (graph,))
    ancestors = networkx.ancestors(graph, root)
    non_ancestors = set(graph.nodes()) - ancestors
    non_ancestors.remove(root)
    new_graph = graph.copy()
    new_graph.remove_nodes_from(non_ancestors)
    if not networkx.is_directed_acyclic_graph(new_graph):
        raise AssertionError('Expected %r to be a DAG' % (new_graph,))
    return new_graph


if __name__ == '__main__':
    issue_key = 'FLOC-2008'
    client = issuelib.client()
    # XXX: IO
    base_issue = client.issue(issue_key)
    g = build_issue_graph(client, base_issue)
    # XXX: Useful to be able to save at this point for later processing:
    # networkx.write_gpickle(g, 'FLOC-2008-closure.pickle')
    g = filter_edges(lambda x: x.get('link_type') == 'Blocks', g)
    g = ancestors_dag(g, issue_key)
    # XXX: print this as a tree, highlighting nodes that appear more than once
    print g
