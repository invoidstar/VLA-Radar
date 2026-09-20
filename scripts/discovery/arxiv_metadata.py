"""Strict, small official abstract-page fallback; never infer dates from the ID."""
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import re
from html.parser import HTMLParser
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

class AbstractPage(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}; self.parts = []; self.hrefs = []; self.hidden = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in {'script','style'}: self.hidden += 1
        if tag == 'meta' and a.get('name'):
            self.meta.setdefault(a['name'].lower(), []).append(a.get('content',''))
        if tag == 'a' and a.get('href'): self.hrefs.append(a['href'])
        if tag in {'br','div','tr','h2','p'}: self.parts.append(' ')
    def handle_endtag(self, tag):
        if tag in {'script','style'}: self.hidden = max(0,self.hidden-1)
        if tag in {'td','div','tr','h2','p'}: self.parts.append(' ')
    def handle_data(self, text):
        if not self.hidden: self.parts.append(text)

def parse_abstract(html, expected_id):
    p = AbstractPage(); p.feed(html)
    ident = (p.meta.get('citation_arxiv_id') or [''])[0]
    if re.sub(r'v\d+$','',ident) != expected_id:
        raise ValueError('Abstract page does not identify the requested arXiv paper')
    title = ' '.join((p.meta.get('citation_title') or [''])[0].split())
    if not title: raise ValueError('Missing official citation title')
    text = ' '.join(' '.join(p.parts).split())
    if 'Submission history' not in text: raise ValueError('Missing version history; refusing to infer dates')
    history = text.split('Submission history',1)[1]
    versions = {}
    pattern = r'\[v(\d+)\]\s*([A-Za-z]{3},\s*\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}\s+(?:UTC|GMT))'
    for version, stamp in re.findall(pattern,history):
        versions[int(version)] = parsedate_to_datetime(stamp).date().isoformat()
    if 1 not in versions: raise ValueError('No explicit v1 submission date')
    latest = max(versions)
    if versions[latest] < versions[1]: raise ValueError('Invalid version chronology')
    def field(label):
        m=re.search(re.escape(label)+r':\s*(.*?)(?=Subjects:|Journal reference:|DOI:|Report number:|Cite as:|Submission history|$)',text)
        return m[1].strip()[:1000] if m else ''
    dois = set()
    for u in p.hrefs:
        parsed=urlparse(u)
        if parsed.hostname in {'doi.org','dx.doi.org'}:
            d=parsed.path.lstrip('/')
            if d.startswith('10.') and not d.lower().startswith('10.48550/arxiv'): dois.add(d)
    return {'arxiv':expected_id,'title':title,'version':f'v{latest}',
            'firstArxivAt':versions[1],'latestArxivAt':versions[latest],
            'doi':next(iter(dois)) if len(dois)==1 else '',
            'journalRef':field('Journal reference'),'comment':field('Comments'),
            'provider':'arxiv-abstract','source':f'https://arxiv.org/abs/{expected_id}'}
