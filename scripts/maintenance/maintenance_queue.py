"""Write a deterministic public work queue. A queue is not a completed audit."""
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
from datetime import date
from pathlib import Path
import argparse
from catalog_core import load, read_catalog, today, write

def plan(root,limit=8):
    m,records,tracks,results=read_catalog(root);now=today()
    def priority(r):
        n=r['note'];return (0 if n['status']=='needs_review' else 1 if n['status']=='legacy' else 2,{'deep':0,'selective':1,'overview':2}[r['paper']['priority']],n['verifiedAt'] or '',r['paper']['id'])
    out={'schemaVersion':1,'plannedAt':now,'notes':[{'paperId':r['paper']['id'],'reason':r['note']['status'],'readVersion':r['note']['version'],'latestVersion':r['publication']['latestArxivVersion']} for r in sorted(records,key=priority)[:limit]],
         'metadata':{'allArxiv':True,'withoutArxiv':[r['paper']['id'] for r in records if not r['paper']['arxiv']]},
         'remainingNotes':sum(r['note']['status']!='expanded' for r in records),
         'sourceHealth':'check_sources.py: check up to 100 URLs overdue by 30 days; continue until full cycle complete',
         'quarterlyReview':f'{now[:4]}-Q{(int(now[5:7])-1)//3+1}',
         'instructions':'For each selected note read primary methods, contributions, experiment protocol, ablations, limitations; cite each section. Discovery/metadata/notes/results have independent completion semantics. No private research context.'}
    write(Path(root)/'maintenance/state/work-queue.json',out);return out
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);ap.add_argument('--limit',type=int,default=8);a=ap.parse_args();print(plan(a.root,a.limit))
