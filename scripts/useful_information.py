"""Split the archived guide at explicit, reviewed topic boundaries without losing text."""
import hashlib
import json
from archive_html import Tree, Node, normalized_text


def split_guide(root, meta, html, document):
    topics = json.loads((root / 'data/useful_information.json').read_text())
    nodes = Tree(html).root.children
    boundaries = []
    for topic in topics:
        matches = [i for i, node in enumerate(nodes)
                   if isinstance(node, Node) and normalized_text(node) == topic['start']]
        if len(matches) != 1:
            raise ValueError('Ambiguous guide boundary: ' + topic['start'])
        boundaries.append(matches[0])
    if boundaries != sorted(boundaries):
        raise ValueError('Guide topics are out of source order')
    groups = [nodes[:boundaries[0]]] + [nodes[a:b] for a, b in zip(boundaries, boundaries[1:] + [len(nodes)])]
    parts = []
    bodies = []
    for i, group in enumerate(groups):
        container = Node()
        container.children = group
        body = container.inner()
        text = normalized_text(container)
        bodies.append(text)
        if i == 0:
            hub_body = body
            url = meta['url']
        else:
            topic = topics[i - 1]
            url = meta['url'] + topic['slug'] + '/'
            child_meta = {key: meta[key] for key in ('date', 'lastmod', 'source', 'type') if key in meta}
            child_meta.update(title=topic['title'], url=url, guide=True)
            document('pages/367/' + topic['slug'] + '/index.html', child_meta, body)
        parts.append({'url': url, 'text_sha256': hashlib.sha256(text.encode()).hexdigest()})
    if ' '.join(bodies) != normalized_text(Tree(html).root):
        raise ValueError('Guide split changed source text')
    meta['guide_index'] = True
    # A branch bundle lets the six topic bundles coexist with the guide landing page.
    old_leaf = root / 'content/pages/367/index.html'
    if old_leaf.exists():
        old_leaf.unlink()
    return hub_body, parts
