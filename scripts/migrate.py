#!/usr/bin/env python3
"""Deterministically import the complete archived site without network dependencies."""
import argparse
import hashlib
import json
import re
import zipfile
from html import unescape
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit, urlunsplit
from archive_html import Tree, Node, normalized_text
from useful_information import split_guide

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {'apeecmacg.org', 'www.apeecmacg.org'}


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding='utf-8')


def document(path, meta, body=''):
    write(ROOT / 'content' / path, json.dumps(meta, ensure_ascii=False, indent=2) + '\n\n' + body.strip() + '\n')


def migrate(archive):
    report = {'archive': archive.name, 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
              'pages': [], 'archive_listings': [], 'excluded': [], 'assets': [], 'url_repairs': [], 'warnings': []}
    with zipfile.ZipFile(archive) as z:
        files = {n[len('public_static/'):]: n for n in z.namelist()
                 if n.startswith('public_static/') and not n.endswith('/') and not PurePosixPath(n).name.startswith('._')}
        if 'index.html' not in files:
            raise SystemExit('Expected public_static/index.html in archive')
        if any('..' in PurePosixPath(n).parts or n.startswith('/') for n in files):
            raise SystemExit('Unsafe archive path')
        trees = {n: Tree(z.read(full).decode('utf-8-sig')).root for n, full in sorted(files.items()) if n.endswith('.html') and not n.startswith('wp-json/')}
        api_metadata = {}
        for kind in ['posts', 'pages']:
            name = 'wp-json/wp/v2/' + kind + '/index.html'
            if name in files:
                api_metadata.update({item['id']: item for item in json.loads(z.read(files[name]))})
        imported_ids = set()
        path_map = {}
        ids = {}
        for source, tree in trees.items():
            body = tree.first('body')
            classes = body.attrs.get('class', '').split() if body else []
            if 'wp-singular' not in classes or 'paged' in classes:
                continue
            article = tree.first('article')
            title = article.first(cls='entry-title') if article else None
            entry = article.first(cls='entry-content') if article else None
            if not title or entry is None:
                raise ValueError('Missing article content: ' + source)
            uid = article.attrs['id']
            if uid in imported_ids:
                raise ValueError('Duplicate canonical entry: ' + uid)
            imported_ids.add(uid)
            url = '/' + source.removesuffix('index.html')
            path_map[source] = url
            ids[uid.removeprefix('post-')] = url
        repairs = set()

        def rewrite(value, source):
            value = unescape(value)
            if 'usp=sf_linkFORhttps://' in value:
                new = value.split('FORhttps://', 1)[0]
                repairs.add((value, new))
                value = new
            parts = urlsplit(value)
            if parts.hostname in {'i0.wp.com', 'i1.wp.com', 'i2.wp.com'}:
                path = re.sub(r'^/(?:www\.)?apeecmacg\.org', '', parts.path)
                if path != parts.path:
                    return unquote(path)
            if parts.hostname in HOSTS or (not parts.netloc and not parts.scheme):
                path = unquote(parts.path)
                if path.endswith('/index.html'):
                    path = path[:-10]
                if not path and parts.query:
                    match = re.search(r'(?:^|&)(?:p|page_id)=(\d+)', parts.query)
                    if match and match[1] in ids:
                        return ids[match[1]] + ('#' + parts.fragment if parts.fragment else '')
                return urlunsplit(('', '', path, parts.query, parts.fragment))
            return value

        def clean(node, source):
            for child in list(node.children):
                if not isinstance(child, Node):
                    continue
                if child.tag in {'script', 'style'}:
                    node.children.remove(child)
                    report['warnings'].append({'source': source, 'removed_active_element': child.tag})
                    continue
                # This inherited label hides the visible link text from screen readers.
                if child.attrs.get('aria-label', '').strip() == '(opens in a new tab)':
                    del child.attrs['aria-label']
                for attr in list(child.attrs):
                    if attr.startswith('on') or attr in {'srcset', 'sizes', 'data-recalc-dims'}:
                        del child.attrs[attr]
                    elif attr in {'href', 'src', 'poster', 'data'}:
                        child.attrs[attr] = rewrite(child.attrs[attr] or '', source)
                if child.tag == 'img':
                    child.attrs['loading'] = 'lazy'
                    child.attrs['decoding'] = 'async'
                clean(child, source)

        # Keep all uploads, including attachments not referenced by an individual article.
        for name, full in sorted(files.items()):
            if name.startswith('wp-content/uploads/'):
                dest = ROOT / 'static' / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                data = z.read(full)
                dest.write_bytes(data)
                report['assets'].append({'source': name, 'url': '/' + name, 'sha256': hashlib.sha256(data).hexdigest()})
        for source, url in path_map.items():
            tree = trees[source]
            article = tree.first('article')
            entry = article.first(cls='entry-content')
            before = normalized_text(entry)
            clean(entry, source)
            if normalized_text(entry) != before:
                raise ValueError('Text changed during import: ' + source)
            post = 'type-post' in article.attrs.get('class', '').split()
            title = normalized_text(article.first(cls='entry-title'))
            meta = {'title': title, 'url': url, 'source': source, 'wordpress_id': int(article.attrs['id'][5:])}
            api = api_metadata.get(meta['wordpress_id'], {})
            if api.get('date_gmt'):
                meta['date'] = api['date_gmt'] + 'Z'
            if api.get('modified_gmt'):
                meta['lastmod'] = api['modified_gmt'] + 'Z'
            stamp = article.first('time')
            if stamp:
                meta['date'] = stamp.attrs['datetime']
                updated = article.first('time', 'updated')
                if updated and 'lastmod' not in meta:
                    meta['lastmod'] = updated.attrs['datetime']
            if post:
                meta['type'] = 'posts'
                meta['category'] = [normalized_text(a) for a in article.all('a') if 'category' in a.attrs.get('rel', '').split()]
                author = article.first(cls='author')
                if author:
                    meta['author'] = [normalized_text(author)]
                tags = [normalized_text(a) for a in article.all('a') if a.attrs.get('rel') == 'tag']
                if tags:
                    meta['tags'] = tags
            else:
                meta['type'] = 'pages'
            images = list(entry.all('img'))
            if images:
                meta['image'] = images[0].attrs.get('src')
            comments = tree.first(cls='comment-list')
            html = entry.inner()
            if comments:
                clean(comments, source)
                html += '<section class="archived-comments"><h2>Comentários</h2>' + comments.html() + '</section>'
            if url == '/blog/':
                dest = 'posts/_index.html'
                meta['type'] = 'posts'
                meta['aliases'] = ['/page/' + str(i) + '/' for i in range(1, 6)] + ['/blog/page/' + str(i) + '/' for i in range(3, 6)]
            else:
                dest = ('posts/' if post else 'pages/') + str(meta['wordpress_id']) + '/index.html'
            parts = None
            if url == '/informacoes-uteis/':
                html, parts = split_guide(ROOT, meta, html, document)
                dest = 'pages/367/_index.html'
                meta['layout'] = 'single'
            document(dest, meta, html)
            report['pages'].append({'source': source, 'destination': 'content/' + dest, 'url': url, 'id': meta['wordpress_id'],
                                    'kind': 'post' if post else 'page', 'title': title, 'text_sha256': hashlib.sha256(before.encode()).hexdigest(),
                                    'characters': len(before), 'images': len(images), 'comments': bool(comments)})
            if parts:
                report['pages'][-1]['parts'] = parts
        # Preserve substantive sidebar text, contacts, and links without copying WP runtime.
        widgets = []
        for widget in trees['index.html'].all('section', 'widget_text'):
            clean(widget, 'index.html#sidebar')
            widgets.append({'title': normalized_text(widget.first(cls='widget-title')), 'html': widget.first(cls='textwidget').inner()})
        write(ROOT / 'data' / 'sidebar.json', json.dumps(widgets, ensure_ascii=False, indent=2) + '\n')
        # Recreate date archives. Other archive types are Hugo taxonomies/pagination.
        for source, tree in trees.items():
            if source in path_map:
                continue
            match = re.fullmatch(r'(\d{4}(?:/\d{2}){0,2})/index.html', source)
            if match:
                prefix = match[1]
                document('archives/' + prefix.replace('/', '-') + '/index.html', {'title': 'Arquivo · ' + prefix.replace('/', ' / '),
                         'url': '/' + prefix + '/', 'layout': 'archive', 'archive_prefix': prefix,
                         'aliases': ['/' + n.removesuffix('index.html') for n in trees if re.fullmatch(re.escape(prefix) + r'/page/\d+/index.html', n)]})
                report['archive_listings'].append({'source': source, 'url': '/' + prefix + '/', 'kind': 'date', 'destination': 'content/archives/' + prefix.replace('/', '-') + '/index.html'})
            elif source == '404.html':
                report['excluded'].append({'source': source, 'reason': 'Replaced by theme 404 page; no unique editorial content'})
            elif source.startswith('feed/'):
                report['excluded'].append({'source': source, 'reason': 'Feed duplicate; Hugo RSS generated at /feed/index.xml'})
            else:
                report['archive_listings'].append({'source': source, 'url': '/' + source.removesuffix('index.html'), 'kind': 'listing'})
        # Ensure every article appearing in a listing has an imported canonical entry.
        listed = {a.attrs.get('id') for t in trees.values() for a in t.all('article') if a.attrs.get('id', '').startswith('post-')}
        missing = sorted(listed - imported_ids)
        if missing:
            raise ValueError('Listing content missing canonical import: ' + ', '.join(missing))
        api_counts = {}
        for kind in ['posts', 'pages', 'comments', 'media']:
            name = 'wp-json/wp/v2/' + kind + '/index.html'
            entries = json.loads(z.read(files[name])) if name in files else []
            api_counts[kind] = len(entries)
            if kind in {'posts', 'pages'}:
                for item in entries:
                    if str(item['id']) not in ids:
                        raise ValueError('API content missing from import: ' + str(item['id']))
            if kind == 'comments' and entries:
                raise ValueError('API comments require review before marking import complete')
        report['api_entries_checked'] = api_counts
        report['url_repairs'] = [{'original': a, 'replacement': b} for a, b in sorted(repairs)]
        report['summary'] = {'posts': sum(p['kind'] == 'post' for p in report['pages']), 'pages': sum(p['kind'] == 'page' for p in report['pages']),
                             'uploaded_files': len(report['assets']), 'html_files_in_archive': len(trees) + sum(n.endswith('.html') and n.startswith('wp-json/') for n in files),
                             'canonical_articles_in_listings': len(listed), 'missing_canonical_articles': missing}
    write(ROOT / 'migration' / 'report.json', json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report['summary'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', nargs='?', type=Path, default=ROOT / 'public_static.zip')
    migrate(parser.parse_args().archive)
