"""Warning-only link health audit, with a rotating due queue and bounded requests."""
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import argparse, time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError
from catalog_core import load, read_catalog, today, write
from http_public import fetch
from urllib.parse import urldefrag

def audit(root,limit=100,due_days=30,max_seconds=180):
    root=Path(root);_,records,tracks,results=read_catalog(root); urls=set()
    for r in records:
        urls.update(s['url'] for s in r['paper']['sources'])
        for sec in r['note']['sections']:urls.update(s['url'] for s in sec['sources'])
    urls.update(r['source'] for r in results);urls.update(t['source'] for t in tracks)
    for r in records:
        urls.update(x['url'] for x in r['note'].get('figures',[]))
        urls.update(x['source'] for x in r['publication']['history'])
    # Keep the current operational health snapshot aligned with all public source
    # families, not just papers. Archives carry historical health evidence.
    for f in sorted((root/'catalog/news').glob('news-*.json')):
        urls.update(s['url'] for s in load(f).get('sources',[]))
    resources=load(root/'catalog/resources.json').get('papers',{})
    for item in resources.values():
        urls.update(value for value in item.values() if value)
    reproduction=load(root/'catalog/reproducibility.json').get('papers',{})
    for record in reproduction.values():
        for item in record.get('items',{}).values():
            urls.update(item[k] for k in ('url','source') if item.get(k))
    urls={urldefrag(u)[0] for u in urls}
    started=time.monotonic();attempted=0
    path=root/'maintenance/state/source-health.json';old=load(path) if path.exists() else {'sources':{}}
    # Expired/unreferenced URLs remain in immutable old GitHub audits, rather
    # than inflating current statusCounts above current totalSources.
    cache={u:entry for u,entry in old['sources'].items() if u in urls}
    when=today()
    due=[u for u in sorted(urls,key=lambda u:(cache.get(u,{}).get('checkedAt',''),u)) if u not in cache or (date.fromisoformat(when)-date.fromisoformat(cache[u]['checkedAt'])).days>=due_days]
    for url in due[:limit]:
        if time.monotonic()-started>=max_seconds:break
        attempted+=1
        status='unknown';code=None;final=url;error=''
        try:
            try:_,code,final=fetch(url,method='HEAD',attempts=1,timeout=10)
            except HTTPError as e:
                if e.code!=405:raise
                _,code,final=fetch(url,method='GET',attempts=1,timeout=10,max_bytes=1000000)
            status='reachable'
        except HTTPError as e:code=e.code;status='not-found' if code in {404,410} else 'blocked-or-transient';error=str(e)
        except Exception as e:error=str(e)
        cache[url]={'checkedAt':when,'status':status,'httpStatus':code,'finalUrl':final,'error':error[:300]};time.sleep(.12)
    report={'schemaVersion':1,'lastAttemptAt':when,'scope':'current paper, experiment, news, project and reproducibility link reachability only; not content or publication verification','checkedThisRun':attempted,'totalSources':len(urls),'dueRemaining':max(0,len(due)-attempted),'sources':cache}
    write(path,report);print(f'WARN-ONLY: checked {attempted} URLs; {report["dueRemaining"]} remain due. No record removed.')
    return report
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);ap.add_argument('--limit',type=int,default=100);ap.add_argument('--due-days',type=int,default=30);ap.add_argument('--max-seconds',type=int,default=180);a=ap.parse_args();audit(a.root,max(1,a.limit),a.due_days,max_seconds=a.max_seconds)
