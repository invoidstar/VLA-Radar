"""Audit main protection; --apply installs a baseline ONLY on an unprotected branch.
Requires Administration(write). Existing protection is never overwritten or weakened.
"""
import argparse,json
from pathlib import Path
from urllib.error import HTTPError
from repo_housekeeping import api,REPO,ROOT

def configure(apply=False):
    branch=api(f'repos/{REPO}/branches/main')
    try:
        current=api(f'repos/{REPO}/branches/main/protection')
        return {'status':'existing-protection-preserved','protected':True,'requiredChecks':current.get('required_status_checks')}
    except HTTPError as e:
        if e.code!=404 or branch.get('protected'):
            return {'status':'blocked-administration-permission' if e.code==403 else 'blocked','protected':branch.get('protected'),'httpStatus':e.code}
    payload=json.loads((ROOT/'maintenance/main-protection.json').read_text())
    if not apply:return {'status':'not-enabled','protected':False,'proposed':payload}
    try:
        api(f'repos/{REPO}/branches/main/protection','PUT',payload)
        actual=api(f'repos/{REPO}/branches/main/protection')
        return {'status':'enabled','protected':True,'requiredChecks':actual.get('required_status_checks')}
    except HTTPError as e:return {'status':'blocked-administration-permission','httpStatus':e.code,'protected':False}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');p.add_argument('--output',default='/tmp/radar-protection-audit.json');a=p.parse_args()
    try:r=configure(a.apply)
    except Exception as e:r={'status':'blocked','error':str(e)}
    Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False,indent=2))
