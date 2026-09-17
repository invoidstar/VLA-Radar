"""Warning-only link health audit, with a rotating due queue and bounded requests."""
import argparse, time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError
from catalog_core import load, read_catalog, today, write
from http_public import fetch

def audit(root,limit=100,due_days=30):
    root=Path(root);_,records,tracks,results=read_catalog(root); urls=set()
    for r in records:
        urls.update(s['url'] for s in r['paper']['sources'])
        for sec in r['note']['sections']:urls.update(s['url'] for s in sec['sources'])
    urls.update(r['source'] for r in results);urls.update(t['source'] for t in tracks)
    path=root/'maintenance/source-health.json';old=load(path) if path.exists() else {'sources':{}};cache=old['sources'];when=today()
    due=[u for u in sorted(urls,key=lambda u:(cache.get(u,{}).get('checkedAt',''),u)) if u not in cache or (date.fromisoformat(when)-date.fromisoformat(cache[u]['checkedAt'])).days>=due_days]
    for url in due[:limit]:
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
    report={'schemaVersion':1,'lastAttemptAt':when,'scope':'link reachability only, not correctness or publication verification','dueRemaining':max(0,len(due)-limit),'sources':cache}
    write(path,report);print(f'WARN-ONLY: checked {min(limit,len(due))} URLs; {report["dueRemaining"]} remain due. No record removed.')
    return report
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--limit',type=int,default=100);ap.add_argument('--due-days',type=int,default=30);a=ap.parse_args();audit(a.root,max(1,a.limit),a.due_days)
