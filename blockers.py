"""
Understand what's blocking an issue.
"""

from functools import partial
import itertools
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
    assert_dag(graph)
    descs = networkx.descendants(graph, root)
    non_descs = set(graph.nodes()) - descs
    non_descs.remove(root)
    new_graph = graph.copy()
    new_graph.remove_nodes_from(non_descs)
    assert_dag(graph)
    return new_graph


def ancestors_dag(graph, root):
    # XXX: This is a clone of descendants_dag. :(
    assert_dag(graph)
    ancestors = networkx.ancestors(graph, root)
    non_ancestors = set(graph.nodes()) - ancestors
    non_ancestors.remove(root)
    new_graph = graph.copy()
    new_graph.remove_nodes_from(non_ancestors)
    assert_dag(new_graph)
    return new_graph


def assert_dag(graph):
    if not networkx.is_directed_acyclic_graph(graph):
        raise AssertionError('Expected %r to be a DAG' % (graph,))


def _dfs_tree(root, get_children, level=0):
    children = get_children(root)
    yield root, level, children
    for child in children:
        for result in _dfs_tree(child, get_children, level + 1):
            yield result


def dfs_predecessor_tree(graph, root):
    assert_dag(graph)
    return _dfs_tree(root, graph.predecessors)


# These have been factored out into jml/tree-fonmat.

FORK = u'\u251c'
LAST = u'\u2514'
VERTICAL = u'\u2502'
HORIZONTAL = u'\u2500'


def _format_tree(node, format_node, get_children, prefix=''):
    children = get_children(node)
    next_prefix = u''.join([prefix, VERTICAL, u'   '])
    for child in children[:-1]:
        yield u''.join(
            [prefix, FORK, HORIZONTAL, HORIZONTAL, u' ', format_node(child)])
        results = _format_tree(child, format_node, get_children, next_prefix)
        for result in results:
            yield result
    if children:
        last_prefix = u''.join([prefix, u'    '])
        last = children[-1]
        yield u''.join(
            [prefix, LAST, HORIZONTAL, HORIZONTAL, u' ', format_node(last)])
        results = _format_tree(last, format_node, get_children, last_prefix)
        for result in results:
            yield result


def format_tree(node, format_node, get_children):
    lines = itertools.chain(
        [format_node(node)],
        _format_tree(node, format_node, get_children),
        [u''],
    )
    return u'\n'.join(lines)


def format_issue(graph, node):
    fields = graph.node[node]['issue']['fields']
    assignee = fields['assignee']
    if assignee:
        assignee_text = u' ({})'.format(assignee['key'])
    else:
        assignee_text = ''
    return u'{}: {} - {}{}'.format(
        node, fields['summary'], fields['status']['name'], assignee_text)


def print_tree(node, format_node, get_children):
    print format_tree(node, format_node, get_children)


def load_graph_from_jira(issue_key):
    client = issuelib.client()
    # XXX: IO
    base_issue = client.issue(issue_key)
    return build_issue_graph(client, base_issue)


def load_graph_from_file(path):
    return networkx.read_gpickle(path)


if __name__ == '__main__':
    issue_key = 'FLOC-2008'
    g = load_graph_from_jira(issue_key)
    # XXX: Useful to be able to save at this point for later processing:
    # networkx.write_gpickle(g, 'FLOC-2008-closure.pickle')
    g = filter_edges(lambda x: x.get('link_type') == 'Blocks', g)
    g = ancestors_dag(g, issue_key)
    # XXX: print this as a tree, highlighting nodes that appear more than once
    print_tree(issue_key, partial(format_issue, g), g.predecessors)
