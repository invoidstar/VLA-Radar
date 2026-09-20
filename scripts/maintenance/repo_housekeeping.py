"""Public repository housekeeping. Dry-run by default; only exact merged heads qualify.
Deletion is a compare-and-delete push with an exact SHA lease, never a forced history
update. A successful main Pages deployment is required before any deletion.
"""
from __future__ import annotations
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import argparse, json, os, subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError
REPO='invoidstar/VLA-Radar'
ROOT=Path(__file__).resolve().parents[2]

def api(path,method='GET',body=None):
    if not path.startswith(f'repos/{REPO}/') and path!=f'repos/{REPO}':raise ValueError('Repository scope violation')
    headers={'Accept':'application/vnd.github+json','User-Agent':'VLA-Radar-maintenance'}
    token=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:headers['Authorization']='Bearer '+token
    if body is not None:headers['Content-Type']='application/json'
    req=Request('https://api.github.com/'+path,headers=headers,method=method,data=json.dumps(body).encode() if body is not None else None)
    with urlopen(req,timeout=25) as r:return json.load(r) if r.status!=204 else None

def pages(path):
    rows=[]
    for n in range(1,101):
        batch=api(path+('&' if '?' in path else '?')+f'per_page=100&page={n}')
        if not isinstance(batch,list):raise ValueError('Unexpected paginated response')
        rows.extend(batch)
        if len(batch)<100:return rows
    raise ValueError('Pagination cap exceeded; refuse incomplete branch inventory')

def instant(value):return datetime.fromisoformat(value.replace('Z','+00:00'))

def decide(branch,prs,policy,now):
    name=branch['name'];sha=branch['commit']['sha']
    out={'branch':name,'sha':sha,'action':'keep','reason':''}
    if name in policy['keepNames'] or any(name.startswith(p) for p in policy['keepPrefixes']):out['reason']='reserved';return out
    if branch.get('protected'):out['reason']='protected';return out
    if not any(name.startswith(p) for p in policy['managedPrefixes']):out['reason']='unmanaged';return out
    if any(p['state']=='open' and ((p.get('head',{}).get('repo') or {}).get('full_name')==REPO and p['head']['ref']==name or p.get('base',{}).get('ref')==name) for p in prs):out['reason']='open-pr-reference';return out
    merged=[p for p in prs if p.get('merged_at') and p.get('merge_commit_sha')
            and p.get('base',{}).get('ref')==policy['defaultBranch']
            and (p.get('head',{}).get('repo') or {}).get('full_name')==REPO
            and p['head']['ref']==name and p['head']['sha']==sha]
    if not merged:out['reason']='no-merged-pr-for-exact-head';return out
    p=max(merged,key=lambda p:p['merged_at'])
    hours=(now-instant(p['merged_at'])).total_seconds()/3600
    if hours<policy['minMergedHours']:out['reason']='recovery-grace-period';return out
    out.update(action='candidate',reason='exact-head-merged',pr=p['number'],mergedAt=p['merged_at'],mergeCommit=p['merge_commit_sha'])
    return out

def published(sha):
    runs=api(f'repos/{REPO}/actions/runs?head_sha={sha}&branch=main&per_page=100')['workflow_runs']
    for run in runs:
        if run.get('path')!='.github/workflows/site.yml' or run['status']!='completed' or run['conclusion']!='success':continue
        jobs=api(f'repos/{REPO}/actions/runs/{run["id"]}/jobs?per_page=100')['jobs']
        if any(j['name']=='deploy' and j['conclusion']=='success' for j in jobs):return run['html_url']
    return None

def clean(apply=False,root=ROOT,report=None):
    root=Path(root);policy=json.loads((root/'maintenance/policies/branch-policy.json').read_text())
    if report is None:report={}
    report.update({'repository':REPO,'checkedAt':datetime.now(timezone.utc).isoformat(),'mode':'apply' if apply else 'dry-run','decisions':[],'deleted':[],'status':'success'})
    branches=pages(f'repos/{REPO}/branches');prs=pages(f'repos/{REPO}/pulls?state=all')
    main=api(f'repos/{REPO}/branches/main');deployment=published(main['commit']['sha'])
    report['mainSha']=main['commit']['sha'];report['deployment']=deployment;report['mainProtected']=main.get('protected')
    now=datetime.now(timezone.utc)
    report['decisions']=[decide(b,prs,policy,now) for b in branches]
    if apply:
        remote=subprocess.run(['git','remote','get-url','origin'],cwd=root,capture_output=True,text=True,check=True).stdout.strip()
        if remote not in {f'https://github.com/{REPO}',f'https://github.com/{REPO}.git',f'git@github.com:{REPO}.git'}:raise ValueError('Unexpected git remote')
        if not deployment:report['status']='blocked-no-confirmed-main-deployment';return report
        for entry in [e for e in report['decisions'] if e['action']=='candidate'][:policy['maxDeletes']]:
            name=entry['branch'];ref='refs/heads/'+name
            # Inventory may be old. Recheck references and PR state just before deletion.
            branch=api(f'repos/{REPO}/branches/'+quote(name,safe=''))
            fresh=decide(branch,pages(f'repos/{REPO}/pulls?state=all'),policy,datetime.now(timezone.utc))
            if fresh['action']!='candidate' or fresh['sha']!=entry['sha']:entry.update(action='keep',reason='changed-during-audit');continue
            comparison=api(f'repos/{REPO}/compare/{entry["mergeCommit"]}...{main["commit"]["sha"]}')
            if comparison.get('status') not in {'ahead','identical'}:entry.update(action='keep',reason='merge-not-in-published-main');continue
            # SHA lease atomically refuses deletion if new commits arrive after the check.
            result=subprocess.run(['git','push',f'--force-with-lease={ref}:{entry["sha"]}','origin',':'+ref],cwd=root,capture_output=True,text=True,timeout=40)
            if result.returncode:entry.update(action='keep',reason='lease-or-protection-refused');report['status']='partial'
            else:entry['action']='deleted';report['deleted'].append({'branch':name,'sha':entry['sha'],'pr':entry['pr']})
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');p.add_argument('--output',default='/tmp/radar-branch-audit.json');a=p.parse_args()
    report={}
    try:clean(a.apply,report=report)
    except Exception as e:report.update(repository=REPO,status='blocked',error=str(e))
    Path(a.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
