"""
Understand what's blocking an issue.
"""


if __name__ == '__main__':
    from sys import argv
    from blockers import main
    raise SystemExit(main(*argv[1:]))

from functools import partial
import itertools
import networkx

import issuelib


NOT_FOUND = object()


def build_issue_graph(client, issue, follow_links=None):
    """
    Build a graph of linked issues, starting at 'issue'.
    """
    queue = [issue]
    g = networkx.DiGraph()
    while queue:
        head, queue = queue[0], queue[1:]

        g.add_node(head.key, issue=head.raw)

        for dest_key, outward, link_type in iter_links(head):

            if follow_links and link_type not in follow_links:
                continue

            if dest_key not in g:
                dest = client.issue(dest_key)
                g.add_node(dest_key, issue=dest.raw)
                queue.append(dest)

            if outward:
                g.add_edge(head.key, dest_key, link_type=link_type)
            else:
                g.add_edge(dest_key, head.key, link_type=link_type)

    return g


def iter_links(issue):
    """
    Iterate over issue links.

    For each link, yield (key, outward, link_type), where 'key' is the ticket
    key (e.g. FLOC-2008), 'outward' is the direction of the link, and
    'link_type' is the name of the type of link (e.g. 'Blocks').
    """
    links = getattr(issue.fields, 'issuelinks', ())
    for link in links:
        if getattr(link, 'inwardIssue', NOT_FOUND) is NOT_FOUND:
            dest_key = link.outwardIssue.key
            outward = True
        else:
            dest_key = link.inwardIssue.key
            outward = False
        yield dest_key, outward, link.type.name


def ancestors_dag(graph, root):
    """
    Return a directed, acyclic graph of all the ancestors of 'root'.
    """
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


def main(issue_key):
    client = issuelib.client()
    # XXX: IO
    base_issue = client.issue(issue_key)
    g = build_issue_graph(client, base_issue, follow_links=['Blocks'])
    g = ancestors_dag(g, issue_key)
    print_tree(issue_key, partial(format_issue, g), g.predecessors)
