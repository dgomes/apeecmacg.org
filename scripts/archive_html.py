"""Small HTML tree for the archived WordPress export; standard library only."""
from html import escape
from html.parser import HTMLParser

VOID = set('area base br col embed hr img input link meta param source track wbr'.split())


class Node:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []

    def all(self, tag=None, cls=None):
        for child in self.children:
            if isinstance(child, Node):
                if (tag is None or child.tag == tag) and (cls is None or cls in child.attrs.get('class', '').split()):
                    yield child
                yield from child.all(tag, cls)

    def first(self, tag=None, cls=None):
        return next(self.all(tag, cls), None)

    def text(self):
        return ''.join(c.text() if isinstance(c, Node) else c for c in self.children)

    def inner(self):
        return ''.join(c.html() if isinstance(c, Node) else escape(c, quote=False) for c in self.children)

    def html(self):
        attrs = ''.join(' ' + k + ('="' + escape(v, quote=True) + '"' if v is not None else '') for k, v in self.attrs.items())
        return '<' + self.tag + attrs + '>' + ('' if self.tag in VOID else self.inner() + '</' + self.tag + '>')


class Tree(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.current = self.root
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        node = self.current
        while node.parent is not None:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


BLOCKS = set('address article aside blockquote br caption dd div dl dt figcaption figure footer h1 h2 h3 h4 h5 h6 header hr li main nav ol p pre section table tbody td th thead tr ul'.split())


def normalized_text(node):
    def rendered_text(element):
        if not isinstance(element, Node):
            return element
        text = ''.join(rendered_text(child) for child in element.children)
        return ' ' + text + ' ' if element.tag in BLOCKS else text
    return ' '.join(rendered_text(node).split())
