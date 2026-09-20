"""Deterministic payload budgets, not a claim about a visitor's connection or device."""
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import gzip,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def check(root=ROOT):
    root=Path(root);lib=json.loads((root/'data/library.json').read_text());n=len(lib['papers'])
    forbidden={'sections','sources','readingFocus','evidenceNote','publicationStatus','limitations','insight'}
    for p in lib['papers']:
        if forbidden & p.keys():raise ValueError('Detail/search-only fields leaked into bootstrap')
        if not (root/p['detailUrl']).exists():raise ValueError('Missing hashed detail')
        if p['resultUrl'] and not (root/p['resultUrl']).exists():raise ValueError('Missing paper-result shard')
    sizes={}
    for path in ['data/catalog.json','data/library.json',lib['searchUrl'],lib['boardIndexUrl'],'data/leaderboards.json']:
        b=(root/path).read_bytes();sizes[path]={'bytes':len(b),'gzipBytes':len(gzip.compress(b,mtime=0))}
    light=sizes['data/library.json']['bytes']
    if light>max(32000,n*1800):raise ValueError('Bootstrap per-paper budget exceeded')
    boards=json.loads((root/lib['boardIndexUrl']).read_text())
    if 'results' in boards:raise ValueError('All result rows leaked into board index')
    for t in boards['tracks']:
        shard=json.loads((root/t['resultUrl']).read_text())
        if shard['trackId']!=t['id'] or any(r['trackId']!=t['id'] for r in shard['results']):raise ValueError('Protocol isolation failed')
    return {'papers':n,'budgets':'pass','payloads':sizes,'baseline':'catalog.json is the compatibility full-summary export; library.json is the new startup payload','networkTiming':'not measured; gzip sizes are analytical, actual server encoding may differ'}
if __name__=='__main__':print(json.dumps(check(),ensure_ascii=False,indent=2))
