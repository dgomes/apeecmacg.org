#!/usr/bin/env python3
"""Validate archive coverage, preserved article text, local links, and asset hashes."""
import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from archive_html import Tree, normalized_text

ROOT = Path(__file__).resolve().parents[1]


def validate(destination):
    destination = destination.resolve()
    report = json.loads((ROOT / 'migration/report.json').read_text())
    errors = []
    documents = {}
    for path in destination.rglob('*.html'):
        documents[path] = Tree(path.read_text()).root
    for page in report['pages']:
        path = destination / page['url'].lstrip('/') / 'index.html'
        tree = documents.get(path)
        if tree is None:
            errors.append({'kind': 'missing_page', 'url': page['url']})
            continue
        # Blog is a listing, and its original editorial body is empty.
        if not page['characters']:
            continue
        parts = page.get('parts', [{'url': page['url'], 'text_sha256': page['text_sha256']}])
        texts = []
        for part in parts:
            part_tree = documents.get(destination / part['url'].lstrip('/') / 'index.html')
            content = part_tree.first(cls='entry-content') if part_tree else None
            text = normalized_text(content) if content else ''
            texts.append(text)
            if content is None or hashlib.sha256(text.encode()).hexdigest() != part['text_sha256']:
                errors.append({'kind': 'text_mismatch', 'url': part['url']})
        if hashlib.sha256(' '.join(texts).encode()).hexdigest() != page['text_sha256']:
            errors.append({'kind': 'split_text_coverage_mismatch', 'url': page['url']})
    for asset in report['assets']:
        path = destination / asset['url'].lstrip('/')
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != asset['sha256']:
            errors.append({'kind': 'asset_mismatch', 'url': asset['url']})
    for listing in report['archive_listings']:
        path = destination / listing['url'].lstrip('/') / 'index.html'
        if not path.is_file():
            errors.append({'kind': 'missing_legacy_listing', 'url': listing['url']})
    # Search and RSS must enumerate content, not empty generated archive pages.
    index = json.loads((destination / 'index.json').read_text())
    expected = {part['url'] for p in report['pages'] if p['url'] != '/blog/'
                for part in p.get('parts', [{'url': p['url']}])}
    if {p['url'] for p in index} != expected:
        errors.append({'kind': 'search_coverage_mismatch'})
    rss = ET.fromstring((destination / 'feed/index.xml').read_text())
    rss_items = rss.findall('./channel/item')
    if len(rss_items) != report['summary']['posts']:
        errors.append({'kind': 'rss_coverage_mismatch'})
    for item in rss_items:
        url = urlsplit(item.findtext('link')).path
        page = next((p for p in report['pages'] if p['url'] == url), None)
        if page is None or item.findtext('title') != page['title']:
            errors.append({'kind': 'rss_entry_mismatch', 'url': url})
    # The home highlights only news; the complete news and sales lists stay separate.
    classified_urls = set()
    news_urls = set()
    for source in (ROOT / 'content/posts').glob('*/index.html'):
        meta = json.JSONDecoder().raw_decode(source.read_text())[0]
        (classified_urls if 'Classificados' in meta.get('category', []) else news_urls).add(meta['url'])

    def preview_urls(path):
        tree = documents.get(path)
        return [article.first('h2').first('a').attrs['href']
                for article in tree.all('article', 'post-preview')] if tree else []

    home_urls = preview_urls(destination / 'index.html')
    if len(home_urls) != min(3, len(news_urls)) or not set(home_urls) <= news_urls:
        errors.append({'kind': 'home_news_mismatch'})
    for prefix, expected_urls in [('blog', news_urls), ('category/classificados', classified_urls)]:
        listing_urls = preview_urls(destination / prefix / 'index.html')
        for path in sorted((destination / prefix / 'page').glob('*/index.html')):
            listing_urls.extend(preview_urls(path))
        if set(listing_urls) != expected_urls or len(listing_urls) != len(expected_urls):
            errors.append({'kind': 'editorial_listing_mismatch', 'listing': prefix})
    links_checked = 0
    broken = set()
    external_media = set()
    for path, tree in documents.items():
        page_url = '/' + str(path.relative_to(destination)).removesuffix('index.html')
        for node in tree.all():
            for attr in ('href', 'src', 'poster', 'data'):
                value = node.attrs.get(attr)
                if not value or value.startswith(('mailto:', 'tel:', 'data:', 'javascript:')):
                    continue
                parts = urlsplit(urljoin('https://apeecmacg.org' + page_url, value))
                if parts.hostname not in {'apeecmacg.org', 'www.apeecmacg.org'}:
                    if attr in {'src', 'poster', 'data'}:
                        external_media.add(value)
                    continue
                target = destination / unquote(parts.path).lstrip('/')
                if target.is_dir():
                    target = target / 'index.html'
                links_checked += 1
                if not target.is_file():
                    broken.add((page_url, value))
                elif parts.fragment and target.suffix == '.html' and target in documents:
                    ids = {n.attrs.get('id') for n in documents[target].all()}
                    if unquote(parts.fragment) not in ids:
                        broken.add((page_url, value))
    for page, link in sorted(broken):
        errors.append({'kind': 'broken_link', 'page': page, 'link': link})
    # CSS assets are checked separately because HTML traversal does not see font URLs.
    for css in destination.rglob('*.css'):
        for value in re.findall(r'url\([\'"]?([^\)\'\"]+)', css.read_text()):
            if value.startswith('/') and not (destination / value.lstrip('/')).is_file():
                errors.append({'kind': 'missing_css_asset', 'url': value})
    result = {'pages_checked': len(report['pages']), 'uploaded_files_checked': len(report['assets']),
              'rendered_html_files': len(documents), 'search_entries_checked': len(index), 'rss_posts_checked': len(rss_items), 'local_links_checked': links_checked,
              'news_posts_checked': len(news_urls), 'classified_posts_checked': len(classified_urls),
              'external_media': sorted(external_media), 'errors': errors}
    (ROOT / 'migration/validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return bool(errors)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    sys.exit(validate(parser.parse_args().destination))
