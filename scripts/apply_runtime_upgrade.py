"""One-time auditable text patch application; validates every preimage and output.
No code is evaluated from patch strings. Canonical scientific records are not patched.
"""
import hashlib,json,os,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ALLOWED={'AGENTS.md','CHANGELOG.md','MAINTENANCE.md','app.js','index.html','research.css','research.js','runtime.js','search-core.js','search-client.js','search-worker.js','maintenance/operations.md','maintenance/branch-policy.json','maintenance/main-protection.json','scripts/arxiv_metadata.py','scripts/browser_smoke.py','scripts/build_catalog.py','scripts/check_performance.py','scripts/check_sources.py','scripts/configure_main_protection.py','scripts/http_public.py','scripts/repo_housekeeping.py','scripts/sync_publications.py','scripts/test_performance.cjs','scripts/test_research.cjs','scripts/validate_all.py','tests/test_maintenance.py'}
def sha(b):return hashlib.sha256(b).hexdigest()
def invariants():
    papers={}
    for p in sorted((ROOT/'catalog/papers').glob('p*.json')):
        r=json.loads(p.read_text());a=r['paper'];n=r['note']
        papers[a['id']]={'stable':{k:a[k] for k in ('id','arxiv','firstPublished','name','title','findings')},'notes':{k:n.get(k) for k in ('sections','figures','tables','verifiedAt','version')}}
    return {'papers':papers,'results':{p.name:sha(p.read_bytes()) for p in (ROOT/'catalog/results').glob('*.json')},'firstPublic':sha((ROOT/'catalog/first-public.json').read_bytes()),'discovery':sha((ROOT/'maintenance/state.json').read_bytes())}
if __name__=='__main__':
    assert os.environ.get('GITHUB_REPOSITORY')=='invoidstar/VLA-Radar'
    assert os.environ.get('GITHUB_REF_NAME')=='release/batch-2026-09-18-maintenance-performance'
    inputs=sorted((ROOT/'maintenance/runtime-staging').glob('patch-*.json'));assert len(inputs)==7
    before=invariants();Path('/tmp/radar-invariants-before.json').write_text(json.dumps(before,ensure_ascii=False))
    writes={};report=[]
    for item in inputs:
        for change in json.loads(item.read_text())['files']:
            path=change['path'];assert path in ALLOWED and path not in writes,path
            f=ROOT/path;old=f.read_bytes() if f.exists() else b''
            assert (sha(old) if f.exists() else None)==change['before'],'Changed preimage: '+path
            lines=old.decode('utf-8').splitlines(keepends=True);out=[];cursor=0
            for edit in change['edits']:
                start,end=edit['start'],edit['end'];assert cursor<=start<=end<=len(lines),path
                out.extend(lines[cursor:start]);out.extend(edit['lines']);cursor=end
            out.extend(lines[cursor:]);new=''.join(out).encode('utf-8')
            assert sha(new)==change['after'],'Changed output: '+path
            writes[path]=new;report.append({'path':path,'before':change['before'],'after':change['after']})
    assert set(writes)==ALLOWED
    for path,value in writes.items():
        f=ROOT/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(value)
    assert invariants()==before,'Scientific records unexpectedly changed by code patch'
    (ROOT/'maintenance/runtime-upgrade.json').write_text(json.dumps({'schemaVersion':1,'base':'a788c0ac2839e41b6f40fe0ecd48b9161541f224','patchMethod':'preimage-and-output-SHA256 checked text edits','files':report,'scientificRecordsUnchanged':True},ensure_ascii=False,indent=2)+'\n')
    shutil.rmtree(ROOT/'maintenance/runtime-staging')
    Path(__file__).unlink()
    print('PASS: 27 source/code changes verified, all canonical paper facts/notes/results preserved. Staging removed.')
