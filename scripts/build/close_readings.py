"""Source-of-truth adapter for small, license-bounded public paper close-readings."""
from __future__ import annotations
import json,re
from pathlib import Path
from catalog_core import read_catalog

LABELS={'thesis','concept','evidence','concession','method'}
SECTION_RE=re.compile(r'^[a-z][a-z0-9-]*$')
UNIT_RE=re.compile(r'^P[0-9]{3}$')
ORIGINAL_BODY_KEYS={'originalEnglish','englishOriginal','fullEnglish','originalText','pdfImage','base64Image','translation'}
def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def validate(root):
    root=Path(root)
    index=load(root/'catalog/close-readings/index.json')
    if set(index)!={'schemaVersion','updatedAt','items'} or index['schemaVersion']!=1:raise ValueError('close reading index schema')
    manifest=load(root/'catalog/manifest.json')
    ids=set(manifest['paperOrder']);seen=set();result_ids=set()
    for p in (root/'catalog/results').glob('r-*.json'):result_ids.add(load(p)['id'])
    available=set()
    for item in index['items']:
        pid=item['paperId']
        if pid in seen or pid not in ids or not re.fullmatch(r'p\d{3,}',pid):raise ValueError('close reading index duplicate/unknown paper')
        seen.add(pid)
        if item['href']!=pid+'/' or item['contentUrl']!='../../data/close-readings/'+pid+'.json':raise ValueError('close reading link mismatch')
        path=root/f'catalog/close-readings/{pid}.json'
        if not path.is_file():raise ValueError('missing source reading '+pid)
        d=load(path)
        if set(d)!={'schemaVersion','paperId','sourceVersion','sourceUrl','analyzedSource','visibility','originalTextStatus','language','updatedAt','title','subtitle','notice','overview','sections','units'} or d['schemaVersion']!=1 or d['paperId']!=pid:raise ValueError('reading schema mismatch '+pid)
        if d['visibility']!='public-commentary-only' or d['originalTextStatus']!='omitted-pending-permission':raise ValueError('reading public reuse permission not established')
        if not d['sourceUrl'].startswith('https://arxiv.org/pdf/'):raise ValueError('untrusted close reading source')
        from urllib.parse import urlparse
        if urlparse(d['sourceUrl']).netloc!='arxiv.org':raise ValueError('invalid source')
        if set(d['overview'])!={'thesis','chain','strong','weak'} or len(d['overview']['chain'])!=5:raise ValueError('reading argument map schema')
        sections=d['sections'];units=d['units'];sids=set();uids=set()
        for s in sections:
            if set(s)!={'id','title','summary','order'} or not SECTION_RE.fullmatch(s['id']) or s['id'] in sids:raise ValueError('duplicate/invalid reading section')
            sids.add(s['id'])
        if [s['order'] for s in sections]!=list(range(len(sections))):raise ValueError('section order')
        for u in units:
            if set(u)!={'id','section','page','dimension','englishKeywords','interpretation','annotation','evidenceRefs'}:raise ValueError('reading unit schema')
            if not UNIT_RE.fullmatch(u['id']) or u['id'] in uids or u['section'] not in sids:raise ValueError('reading unit identity')
            uids.add(u['id'])
            if u['dimension'] not in LABELS or type(u['page'])!=int or not 1<=u['page']<=31:raise ValueError('invalid source page/dimension')
            if not isinstance(u['englishKeywords'],str) or len(u['englishKeywords'])>180 or not u['interpretation'] or not 60<=len(u['interpretation'])<=600:raise ValueError('reading short index and substantive commentary')
            if set(u['annotation'])!={'function','role','critique'} or any(not u['annotation'][k] for k in u['annotation']):raise ValueError('missing commentary reasoning fields')
            if any(x not in result_ids for x in u['evidenceRefs']):raise ValueError('unknown result evidence reference')
            if ORIGINAL_BODY_KEYS & set(u):raise ValueError('unlicensed original paper reproduction field')
            if 'data:image' in json.dumps(u) or '<img' in json.dumps(u):raise ValueError('embedded PDF images are forbidden')
        if len(uids)<8 or len(sids)<8:raise ValueError('full-reading prototype lacks adequate coverage')
        if item['unitCount']!=len(uids) or item['sectionCount']!=len(sids) or item['sourceVersion']!=d['sourceVersion']:raise ValueError('index counts stale')
        available.add(pid)
    extra={p.stem for p in (root/'catalog/close-readings').glob('p*.json')}-available
    if extra:raise ValueError('unindexed reading content '+str(sorted(extra)))
    if not available:raise ValueError('no close-reading prototype')
    return index,available

def outputs(root):
    root=Path(root);idx,ids=validate(root)
    from catalog_core import dumps
    out={'data/close-readings/index.json':dumps(idx)}
    for pid in sorted(ids):out[f'data/close-readings/{pid}.json']=dumps(load(root/f'catalog/close-readings/{pid}.json'))
    return out
