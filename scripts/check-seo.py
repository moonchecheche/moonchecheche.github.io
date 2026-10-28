#!/usr/bin/env python3
"""Check rendered Jekyll output using only the Python standard library."""
import json
import pathlib
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

destination = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '_site').resolve()
source = pathlib.Path(__file__).resolve().parents[1]
app = json.loads((source / '_data/app.json').read_text())
origin = app['siteUrl']
alternates = {value['lang']: origin + value['path'] for value in app['locales'].values()}
alternates['x-default'] = origin + '/'
homes = {origin + value['path']: value for value in app['locales'].values()}


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.meta, self.links, self.ids, self.scripts = {}, [], set(), []
        self.html, self.title, self.h1, self.hrefs = {}, '', 0, []
        self.in_title, self.json_script = False, None
        self.feed(text)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'html':
            self.html = attrs
        elif tag == 'title':
            self.in_title = True
        elif tag == 'h1':
            self.h1 += 1
        elif tag == 'meta':
            key = attrs.get('name', attrs.get('property'))
            assert key not in self.meta, f'Duplicate meta tag: {key}'
            self.meta[key] = attrs.get('content', '')
        elif tag == 'link':
            self.links.append(attrs)
        elif tag == 'a':
            self.hrefs.append(attrs.get('href', ''))
        elif tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.json_script = ''
        elif tag == 'img':
            assert 'alt' in attrs, 'Image alt text is missing'
            assert attrs.get('width') and attrs.get('height'), 'Image dimensions are missing'

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        elif tag == 'script' and self.json_script is not None:
            self.scripts.append(json.loads(self.json_script))
            self.json_script = None

    def handle_data(self, text):
        if self.in_title:
            self.title += text
        if self.json_script is not None:
            self.json_script += text


pages, titles, descriptions = {}, set(), set()
for file in sorted(destination.rglob('*.html')):
    text = file.read_text()
    assert '{{' not in text and '{%' not in text, f'{file}: unrendered Liquid'
    page = Page(text)
    canonical_tags = [link['href'] for link in page.links if link.get('rel') == 'canonical']
    assert len(canonical_tags) == 1, f'{file}: expected one canonical'
    canonical = canonical_tags[0]
    assert canonical.startswith(origin + '/'), f'{file}: wrong canonical origin'
    assert canonical not in pages, f'{file}: duplicate canonical'
    url_path = urllib.parse.urlparse(canonical).path
    expected = destination / (url_path.lstrip('/') + 'index.html' if url_path.endswith('/') else url_path.lstrip('/') + '.html')
    assert expected == file, f'{file}: canonical points to another page: {canonical}'
    assert page.h1 == 1, f'{file}: expected one h1'
    assert page.title and page.title not in titles, f'{file}: empty or duplicate title'
    description = page.meta.get('description', '')
    assert description and description not in descriptions, f'{file}: empty or duplicate description'
    assert page.meta.get('og:url') == canonical, f'{file}: Open Graph URL differs'
    assert page.meta.get('og:title') == page.title, f'{file}: Open Graph title differs'
    assert page.meta.get('og:description') == description, f'{file}: Open Graph description differs'
    assert 'noindex' not in page.meta.get('robots', ''), f'{file}: noindex'
    assert page.meta.get('apple-itunes-app') == 'app-id=6755811989'
    assert page.scripts, f'{file}: no JSON-LD'
    graph = page.scripts[0]['@graph']
    webpage = next(node for node in graph if node['@type'] == 'WebPage')
    assert webpage['url'] == canonical and webpage['name'] == page.title
    assert webpage['inLanguage'] == page.html.get('lang')
    if canonical in homes:
        home = homes[canonical]
        assert page.html['lang'] == home['lang'] and page.html['dir'] == home['dir']
        actual_alternates = {link['hreflang']: link['href'] for link in page.links if link.get('rel') == 'alternate'}
        assert actual_alternates == alternates, f'{file}: incomplete hreflang set'
        software = next(node for node in graph if node['@type'] == 'SoftwareApplication')
        assert software['url'] == canonical and software['name'] == home['name']
        assert set(software['installUrl']) == set(app['storeUrls'].values())
        assert set(app['storeUrls'].values()).issubset(page.hrefs), f'{file}: store link missing'
        assert 'aggregateRating' not in software and 'review' not in software, 'Do not invent ratings'
    pages[canonical] = page
    titles.add(page.title)
    descriptions.add(description)

assert set(homes).issubset(pages), 'A localized landing page is missing'
for canonical, page in pages.items():
    for href in page.hrefs:
        url = urllib.parse.urlparse(urllib.parse.urljoin(canonical, href))
        if url.scheme not in ('http', 'https') or url.netloc != urllib.parse.urlparse(origin).netloc:
            continue
        target = urllib.parse.urlunparse(url._replace(fragment='', query=''))
        assert target in pages, f'{canonical}: broken internal page link {href}'
        if url.fragment:
            assert urllib.parse.unquote(url.fragment) in pages[target].ids, f'{canonical}: missing anchor {href}'

tree = ET.parse(destination / 'sitemap.xml')
locations = [node.text for node in tree.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
assert len(locations) == len(set(locations)) and set(locations) == set(pages), 'Sitemap differs from canonical pages'
text_locations = (destination / 'sitemap.txt').read_text().splitlines()
text_locations = [url for url in text_locations if url.strip()]
assert len(text_locations) == len(set(text_locations)) and set(text_locations) == set(pages), 'Text sitemap differs from canonical pages'
robots = (destination / 'robots.txt').read_text()
assert f'Sitemap: {origin}/sitemap.xml' in robots
assert 'Disallow: /' not in robots
assert '12시간 시간별 날씨' not in (destination / 'index.html').read_text()
print(f'PASS: {len(pages)} pages, 17 reciprocal language sets, canonical URLs, JSON-LD, store links, internal links and sitemap.')
