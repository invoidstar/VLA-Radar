from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[3]
STAGE=ROOT/'maintenance/audits/staging'

def load(name):
    return json.loads((STAGE/name).read_text(encoding='utf-8'))

papers=[]
for pid in ('p121','p122','p124'):
    meta=load(pid+'-meta.json')
    sections=[]
    for part in ('a','b','c'):
        path=STAGE/(pid+'-sections-'+part+'.json')
        if path.exists():
            sections.extend(json.loads(path.read_text(encoding='utf-8')))
    meta['note']['sections']=sections
    papers.append(meta)

manifest=json.loads((ROOT/'catalog/manifest.json').read_text(encoding='utf-8'))
known=set(manifest['paperOrder'])
for rec in papers:
    pid=rec['paper']['id']
    if pid not in known:
        (ROOT/'catalog/papers'/f'{pid}.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        manifest['paperOrder'].insert(0,pid)
        known.add(pid)
manifest['updatedAt']='2026-10-04'
(ROOT/'catalog/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('staged papers:', ', '.join(p['paper']['id'] for p in papers))
