import json, os, subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT=Path('.')
REPO='invoidstar/VLA-Radar'
BASE='f477ab6eaa29c3e1bf7310bfbc84910bd21f1699'
DAY='2026-09-20'
TOKEN=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
if not TOKEN:
    raise SystemExit('Missing GH_TOKEN/GITHUB_TOKEN')

def load(p): return json.loads((ROOT/p).read_text())
def dump(p,o):
    q=ROOT/p; q.parent.mkdir(parents=True,exist_ok=True)
    q.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def api(path,method='GET'):
    if not path.startswith(f'repos/{REPO}/') and path!=f'repos/{REPO}':
        raise ValueError('repository scope violation')
    req=Request('https://api.github.com/'+path,method=method,headers={
        'Accept':'application/vnd.github+json','Authorization':'Bearer '+TOKEN,'User-Agent':'VLA-Radar-final-audit'})
    try:
        with urlopen(req,timeout=30) as r:
            return json.load(r) if r.status!=204 else None
    except HTTPError as e:
        return {'_httpStatus':e.code,'_error':e.read().decode('utf-8','replace')}
def pages(path):
    out=[]
    for n in range(1,20):
        sep='&' if '?' in path else '?'
        batch=api(path+sep+f'per_page=100&page={n}')
        if not isinstance(batch,list): raise ValueError(f'pagination failed: {path}: {batch}')
        out.extend(batch)
        if len(batch)<100:return out
    raise ValueError('pagination cap')
def sh(*args,check=True):
    r=subprocess.run(list(args),cwd=ROOT,text=True,capture_output=True)
    if check and r.returncode:
        raise RuntimeError(f'command failed {args}: {r.stdout}\n{r.stderr}')
    return r
def branch_sha(name):
    row=api(f'repos/{REPO}/branches/'+quote(name,safe=''))
    if not isinstance(row,dict) or 'commit' not in row: raise ValueError(f'missing branch {name}: {row}')
    return row['commit']['sha'],bool(row.get('protected'))
def published_main(sha):
    runs=api(f'repos/{REPO}/actions/runs?head_sha={sha}&branch=main&per_page=100')
    for run in runs.get('workflow_runs',[]):
        if run.get('path')!='.github/workflows/site.yml' or run.get('event')!='push':
            continue
        if run.get('status')!='completed' or run.get('conclusion')!='success':
            continue
        jobs=api(f'repos/{REPO}/actions/runs/{run["id"]}/jobs?per_page=100')
        if any(j.get('name')=='deploy' and j.get('conclusion')=='success' for j in jobs.get('jobs',[])):
            return {'runId':run['id'],'url':run['html_url']}
    return None

# Exact-current-main precondition and published deployment.
main=api(f'repos/{REPO}/branches/main')
assert main['commit']['sha']==BASE,(main['commit']['sha'],BASE)
deployment=published_main(BASE)
assert deployment, 'current main has no confirmed successful Pages deploy'

# Full fetch so merge-base/diff checks are local and deterministic.
sh('git','fetch','origin','--prune','+refs/heads/*:refs/remotes/origin/*')
assert sh('git','rev-parse','origin/main').stdout.strip()==BASE
open_prs=pages(f'repos/{REPO}/pulls?state=open')
assert not open_prs, 'unexpected open PR before final cleanup'

# Explicit final-cleanup allowlist. Safety branch deletion is a maintainer-authorized
# one-time override after proving it has zero unique commits. General branch policy stays unchanged.
candidates=[
    {
      'name':'pre-update-safety-2026-09-17',
      'sha':'5af47965977194b0c57734ce9fd542f6176dde9c',
      'proof':'ancestor-of-main',
      'reason':'final safety snapshot is fully contained in published main; explicit maintainer final-cleanup request'
    },
    {
      'name':'feature/vla-radar-v2-2026-09-17',
      'sha':'2a1da46650ac0a905baca2f52372204e59af9ad5',
      'proof':'only-obsolete-temp-files',
      'uniqueCommits':1,
      'allowedFiles':['.github/workflows/materialize-v2.yml'],
      'reason':'only unique content is obsolete branch-scoped one-time migration workflow'
    },
    {
      'name':'weekly-update-2026-09-18-benchmark-batch4',
      'sha':'03148dcab86dbcf1f976941ce26055671d2cb727',
      'proof':'only-obsolete-temp-files',
      'uniqueCommits':3,
      'allowedFiles':['.github/workflows/batch4-prepare.yml','maintenance/.batch4-part0','maintenance/.batch4-part1'],
      'reason':'only unique content is obsolete one-shot prepare workflow and two marker files'
    }
]

cleanup={'schemaVersion':1,'repository':REPO,'checkedAt':datetime.now(timezone.utc).isoformat(),
         'baseMainSha':BASE,'deployment':deployment,'explicitMaintainerRequest':True,
         'deleted':[],'preserved':[],'checks':[]}

open_refs=set()
for p in open_prs:
    if p.get('head',{}).get('repo',{}).get('full_name')==REPO: open_refs.add(p['head']['ref'])
    open_refs.add(p.get('base',{}).get('ref'))

for item in candidates:
    name=item['name']; expected=item['sha']
    sha,protected=branch_sha(name)
    assert sha==expected,(name,sha,expected)
    assert not protected,(name,'protected')
    assert name not in open_refs,(name,'open-pr-reference')
    remote=f'origin/{name}'
    if item['proof']=='ancestor-of-main':
        r=sh('git','merge-base','--is-ancestor',expected,'origin/main',check=False)
        assert r.returncode==0,(name,'not ancestor of main')
        unique=int(sh('git','rev-list','--count',f'origin/main..{expected}').stdout.strip())
        assert unique==0,(name,'unexpected unique commits',unique)
        proof={'branch':name,'sha':sha,'proof':'ancestor-of-main','uniqueCommits':0}
    else:
        unique=int(sh('git','rev-list','--count',f'origin/main..{expected}').stdout.strip())
        assert unique==item['uniqueCommits'],(name,'unique commit count',unique)
        mb=sh('git','merge-base','origin/main',expected).stdout.strip()
        files=[x for x in sh('git','diff','--name-only',mb,expected).stdout.splitlines() if x]
        assert sorted(files)==sorted(item['allowedFiles']),(name,files,item['allowedFiles'])
        proof={'branch':name,'sha':sha,'proof':'only-obsolete-temp-files','uniqueCommits':unique,'uniqueFiles':files}
    cleanup['checks'].append(proof)
    ref='refs/heads/'+name
    deletion=sh('git','push',f'--force-with-lease={ref}:{expected}','origin',':'+ref,check=False)
    if deletion.returncode:
        raise RuntimeError(f'deletion refused for {name}: {deletion.stdout}\n{deletion.stderr}')
    # API confirmation that the ref is gone.
    gone=api(f'repos/{REPO}/branches/'+quote(name,safe=''))
    assert isinstance(gone,dict) and gone.get('_httpStatus')==404,(name,'still exists',gone)
    cleanup['deleted'].append({'branch':name,'sha':expected,'reason':item['reason']})

# Re-inventory after deletions.
branches=pages(f'repos/{REPO}/branches')
branch_names={b['name'] for b in branches}
assert not ({x['name'] for x in candidates} & branch_names)

# Preserve branches that are not proven safe for immediate deletion.
prs=pages(f'repos/{REPO}/pulls?state=all')
by_head={}
for pr in prs:
    by_head.setdefault(pr.get('head',{}).get('ref'),[]).append(pr)

# release/deep-notes: genuine unmerged unique content; retain.
deep='release/deep-notes-2026-09-17'
if deep in branch_names:
    sha,_=branch_sha(deep)
    unique=int(sh('git','rev-list','--count',f'origin/main..{sha}').stdout.strip())
    assert unique==19,(deep,unique)
    cleanup['preserved'].append({'branch':deep,'sha':sha,'reason':'19 unique historical content commits; no exact merged PR; unmerged history is preserved rather than deleted'})

# Recent merged heads: respect six-hour recovery window.
for name in ['release/batch-2026-09-20-weekly-notes','weekly-update-2026-09-20-note-final8','weekly-update-2026-09-20-final-two-fulltext']:
    if name not in branch_names: continue
    sha,_=branch_sha(name)
    matches=[p for p in by_head.get(name,[]) if p.get('merged_at') and p.get('base',{}).get('ref')=='main' and p.get('head',{}).get('sha')==sha]
    assert matches,(name,'missing exact merged PR')
    pr=max(matches,key=lambda p:p['merged_at'])
    cleanup['preserved'].append({'branch':name,'sha':sha,'reason':'merged exact head, but still inside repository 6-hour recovery grace period','pr':pr['number'],'mergedAt':pr['merged_at']})

dump('maintenance/final-branch-cleanup-20260920.json',cleanup)

# ---------- Full repository consistency audit ----------
manifest=load('catalog/manifest.json')
paper_ids=manifest['paperOrder']
paper_files=sorted((ROOT/'catalog/papers').glob('p*.json'))
papers=[load(x) for x in paper_files]
bench=load('catalog/benchmarks.json')
tracks=bench['tracks']
track_ids={x['id'] for x in tracks}
result_files=sorted((ROOT/'catalog/results').glob('r-*.json'))
results=[load(x) for x in result_files]
result_ids={x['id'] for x in results}
review=load('maintenance/benchmark-review.json')
work=load('maintenance/work-queue.json')
policy=load('maintenance/editorial-policy.json')
pub=load('maintenance/publication-check.json')
health=load('maintenance/source-health.json')
state=load('maintenance/state.json')
first=load('catalog/first-public.json')

assert len(paper_ids)==98
assert {p['paper']['id'] for p in papers}==set(paper_ids)
assert len(results)==1063 and len(result_ids)==1063
assert len(tracks)==286 and len(track_ids)==286
assert set(review['papers'])==set(paper_ids)
statuses={}
for x in review['papers'].values(): statuses[x['status']]=statuses.get(x['status'],0)+1
assert statuses=={'extracted':96,'not-applicable':2},statuses
assert work['remainingNotes']==0 and work['notes']==[]
assert not policy['limitedLegacyIds']
assert not [p['paper']['id'] for p in papers if p['note']['status']=='needs_review']
assert pub['status']=='success' and pub['dueCount']==0 and pub['dueRemaining']==0 and not pub['errors']
assert len(first)==78, len(first)

# Result/track/review referential closure.
review_results=[]
review_tracks=[]
for pid,row in review['papers'].items():
    if row['status']=='extracted':
        assert row['resultIds'] and row['trackIds'],pid
        review_results.extend(row['resultIds']); review_tracks.extend(row['trackIds'])
    else:
        assert row['resultIds']==[] and row['trackIds']==[],pid
assert len(review_results)==len(set(review_results)),'result referenced by multiple paper dispositions'
assert set(review_results)==result_ids,(len(set(review_results)),len(result_ids))
assert set(review_tracks)<=track_ids
assert all(r['paperId'] in set(paper_ids) and r['trackId'] in track_ids for r in results)
used_tracks={r['trackId'] for r in results}
orphan_tracks=sorted(track_ids-used_tracks)
assert not orphan_tracks,orphan_tracks

# Generated exports are exact before audit-only maintenance files are committed.
sh('python','scripts/build_catalog.py','--check')

# No old one-shot preparation payload is retained on published main.
main_tree=set(sh('git','ls-tree','-r','--name-only','origin/main').stdout.splitlines())
forbidden=[x for x in main_tree if (
    x.startswith(('.batch','.note-final','.final-two','.final-audit/')) or
    (x.startswith('.github/workflows/prepare-') and x.endswith('.yml')) or
    x in {'.github/workflows/materialize-v2.yml','.github/workflows/batch4-prepare.yml'}
)]
assert not forbidden,forbidden

# Governance state: observe, never pretend admin enforcement exists.
main_row=api(f'repos/{REPO}/branches/main')
rulesets=api(f'repos/{REPO}/rulesets?per_page=100')
protection=api(f'repos/{REPO}/branches/main/protection')
governance={
    'branchApiProtectedFlag':bool(main_row.get('protected')),
    'rulesetCount':len(rulesets) if isinstance(rulesets,list) else None,
    'branchProtectionReadHttpStatus':protection.get('_httpStatus') if isinstance(protection,dict) else 200,
    'branchProtectionReadAccessible':not (isinstance(protection,dict) and '_httpStatus' in protection),
    'finding':'GitHub App lacks Administration(write/read for protection endpoint); server-side main protection is not confirmed/enforced by this audit. PR exact-head CI discipline remains procedural, not a substitute for branch protection.'
}

audit={
 'schemaVersion':1,'auditedAt':datetime.now(timezone.utc).isoformat(),'baseMainSha':BASE,
 'scope':'repository-wide consistency audit after benchmark/note backlog closure; structural consistency is not independent scientific replication',
 'canonical':{
   'papers':len(papers),'manifestIds':len(paper_ids),'results':len(results),'tracks':len(tracks),
   'benchmarkDisposition':statuses,'remainingNotes':work['remainingNotes'],'limitedLegacyIds':len(policy['limitedLegacyIds']),
   'orphanResults':0,'orphanTracks':0,'duplicateResultReferences':0,'firstPublicLocks':len(first)
 },
 'generated':{'buildCatalogCheck':'pass','temporaryOneShotFilesOnPublishedMain':forbidden},
 'publication':{
   'status':pub['status'],'dueCount':pub['dueCount'],'dueRemaining':pub['dueRemaining'],
   'manualSourceReview':pub['manualSourceReview']
 },
 'discovery':{
   'lastStatus':state['lastStatus'],'lastSuccessfulSearchAt':state['lastSuccessfulSearchAt'],
   'note':'Literature discovery checkpoint remains partial by design because candidate discovery was not exhaustively completed; this is not a canonical consistency failure.'
 },
 'sourceHealth':{
   'checkedThisRun':health['checkedThisRun'],'totalSources':health['totalSources'],'dueRemaining':health['dueRemaining'],
   'note':'Reachability is a rotating warning-only maintenance queue, not a content correctness gate.'
 },
 'delivery':{
   'publishedMainSha':BASE,'pagesDeployment':deployment,'openPullRequestsBeforeAudit':0
 },
 'branches':{
   'deletedNow':[x['branch'] for x in cleanup['deleted']],
   'preservedNow':cleanup['preserved'],
   'remainingBranchNames':sorted(branch_names)
 },
 'governance':governance,
 'findings':[
   'Canonical paper/result/track/review/work-queue references are closed and internally consistent.',
   'All benchmark deferred and note review queues are zero; two papers remain intentionally not-applicable.',
   'Generated catalog is current and published main contains no obsolete one-shot preparation payloads.',
   'Three provably obsolete historical/safety branches were deleted with exact-SHA lease checks.',
   'One unmerged deep-notes history branch is intentionally preserved because it contains unique commits.',
   'Three recent merged heads are intentionally preserved until the six-hour recovery grace period expires.',
   'Source-health rotation still has due URLs; literature discovery state remains partial, both explicitly documented maintenance state rather than hidden completion claims.',
   'Main branch server-side protection is not confirmed because the installed GitHub App lacks Administration permission; this remains the only repository-governance warning.'
 ]
}
dump('maintenance/final-consistency-audit-20260920.json',audit)

# Regression coverage for the permanent audit records.
Path('tests/test_final_repository_audit.py').write_text("""import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def j(p): return json.loads((R/p).read_text())
def test_content_queues_are_closed():
    r=j('maintenance/benchmark-review.json')['papers']
    counts={}
    for x in r.values(): counts[x['status']]=counts.get(x['status'],0)+1
    assert counts=={'extracted':96,'not-applicable':2}
    w=j('maintenance/work-queue.json')
    assert w['remainingNotes']==0 and w['notes']==[]
def test_final_counts_and_referential_closure():
    a=j('maintenance/final-consistency-audit-20260920.json')
    assert a['canonical']['papers']==98
    assert a['canonical']['results']==1063
    assert a['canonical']['tracks']==286
    assert a['canonical']['orphanResults']==0
    assert a['canonical']['orphanTracks']==0
def test_cleanup_audit_is_exact_and_conservative():
    a=j('maintenance/final-branch-cleanup-20260920.json')
    assert {x['branch'] for x in a['deleted']}=={
      'pre-update-safety-2026-09-17',
      'feature/vla-radar-v2-2026-09-17',
      'weekly-update-2026-09-18-benchmark-batch4'}
    preserved={x['branch']:x['reason'] for x in a['preserved']}
    assert 'release/deep-notes-2026-09-17' in preserved
    assert 'unique historical content commits' in preserved['release/deep-notes-2026-09-17']
def test_governance_warning_is_not_hidden():
    g=j('maintenance/final-consistency-audit-20260920.json')['governance']
    assert g['branchProtectionReadHttpStatus']==403
    assert g['branchProtectionReadAccessible'] is False
""")

ch=Path('CHANGELOG.md').read_text()
entry='## 2026-09-20 · 最终仓库一致性审计与安全分支清理\n\n- 删除3个经精确SHA与内容差异证明可安全清理的历史/安全分支；保留含19个独有内容提交的release/deep-notes历史分支，以及仍处6小时恢复窗口的3个近期已合并分支。\n- 全仓一致性审计确认98 papers、1063 results、286 tracks；96 extracted、0 deferred、2 not-applicable、remainingNotes=0，result/track/review无孤儿或重复归属。\n- build_catalog --check与完整离线/浏览器CI继续作为发布门槛；published main无遗留一次性prepare payload。\n- 明确保留两个非阻塞维护状态：source-health轮检仍有due URL，文献发现checkpoint仍为partial；二者不冒充全量完成。\n- GitHub App访问branch protection端点仍为403，main API protected flag为false且无ruleset；记录为最终治理warning，不声称服务端保护已启用。\n\n'
if '最终仓库一致性审计与安全分支清理' not in ch:
    Path('CHANGELOG.md').write_text(entry+ch)

print(json.dumps({'deleted':cleanup['deleted'],'preserved':cleanup['preserved'],'audit':audit},ensure_ascii=False,indent=2))
