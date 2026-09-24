"""Apply a public, source-checked batch on a release branch. No network or Git writes."""
from __future__ import annotations
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import argparse, hashlib, re
from pathlib import Path
from datetime import date
from catalog_core import load, write, read_catalog, validate_record, validate_track, validate_result, require, load_resources, public_url
from build_catalog import build
from reproducibility import validate_reproducibility_data
from maintenance_queue import plan
ROOT=Path(__file__).resolve().parents[2]

def prepare_resources(root,paper_ids,updates):
    require(isinstance(updates,dict),'resources must be an object')
    merged={pid:dict(value) for pid,value in load_resources(root,paper_ids).items()}
    for pid,change in updates.items():
        require(pid in paper_ids,'Resource update references unknown paper: '+pid)
        require(isinstance(change,dict) and change and set(change)<={'project','code'},pid+': resource update must contain project/code')
        item=dict(merged.get(pid,{}))
        for kind,value in change.items():
            if value is None:item.pop(kind,None)
            else:item[kind]=public_url(value)
        require(len(set(item.values()))==len(item),pid+': duplicate resource URL')
        if item:merged[pid]=item
        else:merged.pop(pid,None)
    return {'schemaVersion':1,'papers':{pid:merged[pid] for pid in sorted(merged)}}
def prepare_reproducibility(root,paper_ids,updates):
    require(isinstance(updates,dict),'reproducibility must be an object')
    current=load(root/'catalog/reproducibility.json')
    merged={**current,'papers':{pid:dict(value) for pid,value in current['papers'].items()}}
    for pid,change in updates.items():
        require(pid in paper_ids,'Reproducibility update references unknown paper: '+pid)
        require(isinstance(change,dict),pid+': reproducibility audit must be an object')
        merged['papers'][pid]=change
    validate_reproducibility_data(merged,paper_ids)
    return {'schemaVersion':merged['schemaVersion'],'dimensions':merged['dimensions'],'statuses':merged['statuses'],
            'papers':{pid:merged['papers'][pid] for pid in sorted(merged['papers'])}}

def apply(root,path):
    b=load(path)
    required={'id','date','summary','notes','tracks','results'};allowed=required|{'resources','reproducibility'}
    require(required<=set(b)<=allowed,'Unexpected batch fields')
    require(re.fullmatch(r'[a-z0-9-]+',b['id']),'Invalid batch ID');date.fromisoformat(b['date'])
    lp=root/'maintenance/state/applied-batches.json';ledger=load(lp) if lp.exists() else {'schemaVersion':1,'batches':[]}
    digest=hashlib.sha256(path.read_bytes()).hexdigest();old=next((x for x in ledger['batches'] if x['id']==b['id']),None)
    if old:
        require(old['sha256']==digest,'Applied batch cannot be rewritten');print('Already applied:',b['id']);return False
    m,recs,tracks,results=read_catalog(root);byid={r['paper']['id']:r for r in recs}
    resource_updates=b.get('resources',{});resource_data=prepare_resources(root,set(byid),resource_updates)
    repro_updates=b.get('reproducibility',{});repro_data=prepare_reproducibility(root,set(byid),repro_updates)
    require(len(b['notes'])==len({n['paperId'] for n in b['notes']}),'Duplicate note')
    for n in b['notes']:
        require(set(n)=={'paperId','expectedVersion','note'},'Unexpected note fields');require(n['paperId'] in byid,'Only existing papers')
        r=byid[n['paperId']];require(r['note']['version']==n['expectedVersion'],'Concurrent note change: '+n['paperId'])
        r['note']=n['note'];validate_record(r)
        require(n['note']['status']=='expanded','Incomplete note in completed batch')
        require(len(n['note']['sections'])>=8,'Need eight sourced sections')
        require(sum(len(s['body']) for s in n['note']['sections'])>=1400,'Note too short')
    tm={t['id']:t for t in tracks}
    for t in b['tracks']:
        validate_track(t);require(t['id'] not in tm,'Track overwrite');tm[t['id']]=t
    ids={r['id'] for r in results}
    for r in b['results']:
        validate_result(r,set(byid),tm);require(r['id'] not in ids,'Duplicate result');ids.add(r['id'])
    for n in b['notes']:write(root/f'catalog/papers/{n["paperId"]}.json',byid[n['paperId']])
    if resource_updates:write(root/'catalog/resources.json',resource_data)
    if repro_updates:write(root/'catalog/reproducibility.json',repro_data)
    write(root/'catalog/benchmarks.json',{'schemaVersion':1,'tracks':list(tm.values())})
    for r in b['results']:write(root/f'catalog/results/{r["id"]}.json',r)
    m['updatedAt']=b['date'];write(root/'catalog/manifest.json',m)
    ledger['batches'].append({'id':b['id'],'sha256':digest,'date':b['date'],'notes':[n['paperId'] for n in b['notes']],'tracks':[t['id'] for t in b['tracks']],'results':len(b['results']),'resources':sorted(resource_updates),'reproducibility':sorted(repro_updates)});write(lp,ledger)
    log=root/'CHANGELOG.md';log.write_text(f'## {b["date"]} — {b["id"]}\n\n{b["summary"]}\n\n'+log.read_text(encoding='utf-8'),encoding='utf-8')
    build(root);plan(root);print('Applied',b['id']);return True
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('batch',type=Path);a=p.parse_args();apply(ROOT,a.batch)
