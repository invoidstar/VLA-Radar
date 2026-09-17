"""Validate the public database schema, not the scientific truth of its content."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from datetime import date

ROOT_KEYS = {'schemaVersion', 'updatedAt', 'title', 'collection', 'description', 'topics', 'papers'}
TOPIC_KEYS = {'id', 'name', 'en', 'description', 'color'}
PAPER_KEYS = {'id', 'name', 'title', 'team', 'venue', 'publicationType', 'publicationStatus', 'firstPublished', 'dateNote', 'collectionMonth', 'versionNote', 'topics', 'tags', 'priority', 'contribution', 'findings', 'limitations', 'insight', 'readingFocus', 'evidence', 'evidenceNote', 'hasCautionaryResult', 'sources', 'paperUrl', 'arxiv', 'doi'}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def check_date(value, month_only=False):
    require(isinstance(value, str), 'Date must be text')
    require(bool(re.fullmatch(r'\d{4}-\d{2}' if month_only else r'\d{4}-\d{2}(-\d{2})?', value)), f'Invalid date: {value}')
    date.fromisoformat(value + '-01' if len(value) == 7 else value)

def check_url(value):
    parsed = urlparse(value)
    require(parsed.scheme in ('http','https') and bool(parsed.netloc) and not parsed.username and not parsed.password, f'Invalid public URL: {value}')

def validate(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    require(set(data) == ROOT_KEYS, 'Root fields must match the public schema')
    require(data['schemaVersion'] == 1, 'Unsupported schema version')
    date.fromisoformat(data['updatedAt'])
    topic_ids = set()
    for t in data['topics']:
        require(set(t) == TOPIC_KEYS, 'Unexpected topic fields')
        require(t['id'] not in topic_ids, f'Duplicate topic: {t["id"]}')
        topic_ids.add(t['id'])
    ids = set()
    for p in data['papers']:
        require(set(p) == PAPER_KEYS, f'{p.get("id", "record")}: missing or unexpected public fields')
        require(re.fullmatch(r'p\d{3,}', p['id']) and p['id'] not in ids, f'Invalid or duplicate ID: {p["id"]}')
        ids.add(p['id'])
        for key in PAPER_KEYS - {'firstPublished','topics','tags','sources','hasCautionaryResult'}:
            require(isinstance(p[key], str), f'{p["id"]}.{key}: expected string')
        require(p['name'] and p['title'] and p['contribution'] and p['findings'], f'{p["id"]}: missing essential content')
        if p['firstPublished'] is not None: check_date(p['firstPublished'])
        require(p['firstPublished'] is not None or bool(p['dateNote']), 'Missing date needs an explanatory note')
        check_date(p['collectionMonth'], month_only=True)
        require(p['priority'] in {'deep','selective','overview'}, 'Invalid reading suggestion')
        require(p['evidence'] in {'notes','metadata','checked'}, 'Invalid evidence state')
        require(p['publicationType'] in {'preprint','conference','journal','report'}, 'Invalid publication type')
        require(isinstance(p['hasCautionaryResult'], bool), 'Invalid caution marker')
        require(isinstance(p['topics'],list) and bool(p['topics']) and set(p['topics']) <= topic_ids, 'Invalid research topics')
        require(isinstance(p['tags'],list) and all(isinstance(x,str) for x in p['tags']), 'Invalid tags')
        require(isinstance(p['sources'],list) and bool(p['sources']), 'At least one primary source is required')
        if p['arxiv']:
            require(bool(re.fullmatch(r'\d{2}(?:0[1-9]|1[0-2])\.\d{4,5}', p['arxiv'])), 'Invalid arXiv identifier; a DOI is not an arXiv ID')
        check_url(p['paperUrl'])
        for s in p['sources']:
            require(set(s) == {'label','url'} and isinstance(s['label'],str), 'Unexpected source fields')
            check_url(s['url'])
            if urlparse(s['url']).hostname == 'arxiv.org':
                require(bool(p['arxiv']) and p['arxiv'] in urlparse(s['url']).path, 'arXiv source must match the record identifier')
    print(f'PASS: {len(ids)} papers, {len(topic_ids)} topic groups; public schema and URLs valid.')
    print('This check does not verify research claims or source availability.')

if __name__ == '__main__':
    try:
        validate(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / 'data' / 'papers.json')
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        sys.exit(1)
