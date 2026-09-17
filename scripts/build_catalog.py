"""Deterministically build the legacy export, searchable summaries and lazy details."""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path
from catalog_core import dumps, read_catalog

def outputs(root):
    m,records,tracks,results=read_catalog(root)
    meta={k:m[k] for k in ('updatedAt','title','collection','description','topics')}
    legacy={'schemaVersion':1,**meta,'papers':[r['paper'] for r in records]}
    out={'data/papers.json':dumps(legacy)}; summaries=[]
    for r in records:
        p=r['paper']; content=dumps(r); digest=hashlib.sha256(content.encode()).hexdigest()[:16]
        out[f'data/details/{p["id"]}.json']=content
        summaries.append({**p,'detailUrl':f'data/details/{p["id"]}.json?v={digest}','noteStatus':r['note']['status'],
            'lifecycle':{k:r['publication'][k] for k in ('firstArxivAt','latestArxivVersion','status','lastCheckedAt')}})
    out['data/catalog.json']=dumps({'schemaVersion':1,**meta,'papers':summaries})
    # Keep all evidence/history in the export; UI never ranks candidates or superseded rows.
    out['data/leaderboards.json']=dumps({'schemaVersion':1,'updatedAt':m['updatedAt'],'tracks':tracks,'results':results})
    return out

def build(root,check=False):
    root=Path(root); generated=outputs(root); stale=[]
    for path,text in generated.items():
        f=root/path
        if not f.exists() or f.read_text(encoding='utf-8')!=text:
            stale.append(path)
            if not check: f.parent.mkdir(parents=True,exist_ok=True); f.write_text(text,encoding='utf-8')
    for p in (root/'data/details').glob('p*.json'):
        if str(p.relative_to(root)) not in generated:
            stale.append(str(p.relative_to(root)))
            if not check:p.unlink()
    if check and stale: raise ValueError('Generated files are stale: '+', '.join(stale[:12]))
    print(f'PASS: {len(generated)-3} per-paper detail files; deterministic catalog and protocol-scoped results.')
    return generated
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--check',action='store_true')
    a=ap.parse_args();build(a.root,a.check)
