"""Supplemental consistency checks; these do not verify scientific claims."""
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse
ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / 'data/papers.json').read_text(encoding='utf-8'))
seen = {'arxiv': {}, 'doi': {}, 'title': {}}
errors = []
for p in data['papers']:
    values = {'arxiv': re.sub(r'v\d+$', '', p['arxiv'].strip().lower()),'doi': re.sub(r'^https?://(?:dx\.)?doi.org/', '', p['doi'].strip().lower()),'title': re.sub(r'[\W_]+', '', unicodedata.normalize('NFKC', p['title']).casefold())}
    for field, value in values.items():
        if not value: continue
        if value in seen[field]: errors.append(f'{p["id"]}: duplicate {field} with {seen[field][value]}')
        seen[field][value] = p['id']
    for src in p['sources']:
        parsed = urlparse(src['url'])
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc: errors.append(f'{p["id"]}: invalid source URL')
        lm=re.search(r'\\bv(\\d+)\\b',src.get('label',''),re.I);um=re.search(r'arxiv\\.org/(?:html|pdf|abs)/\\d{4}\\.\\d{4,5}v(\\d+)',src['url'],re.I)
        if lm and um and lm.group(1)!=um.group(1): errors.append(f'{p["id"]}: source label {src["label"]!r} disagrees with URL version v{um.group(1)}')
state = json.loads((ROOT / 'maintenance/state/state.json').read_text(encoding='utf-8'))
if state['lastStatus'] not in {'not_run', 'success', 'partial', 'failed'}: errors.append('Invalid maintenance status')
if errors: raise SystemExit('\n'.join(errors))
print(f'PASS: {len(data["papers"])} records; unique canonical identifiers/titles; maintenance status valid.')
print('No claim is made about source availability, research accuracy or exhaustive coverage.')
