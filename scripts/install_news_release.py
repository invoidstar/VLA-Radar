"""Apply inspectable integration edits only on the news release branch, then remove this installer."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
BASE='87539bdedaaa507f64d900f674fee1f1f687c365'
ALLOWED={'README.md','MAINTENANCE.md','CHANGELOG.md','AGENTS.md','experience-loader.js','index.html','experience.js','app.js','scripts/validate_all.py','scripts/build_catalog.py','catalog/activity.json','scripts/browser_news.py','scripts/test_news.cjs','tests/test_news.py'}
def sha(b):return hashlib.sha256(b).hexdigest()
def require(ok,msg):
    if not ok:raise ValueError(msg)
def main():
    config=json.loads((ROOT/'maintenance/news-integration.json').read_text(encoding='utf-8'))
    require(config['base']==BASE,'Unexpected baseline')
    require({x['path'] for x in config['files']}==ALLOWED,'Unexpected integration paths')
    staged={}
    for x in config['files']:
        p=ROOT/x['path'];raw=p.read_bytes();old=raw.decode('utf-8')
        if sha(raw)==x['after']:staged[x['path']]=raw;continue
        require(sha(raw)==x['before'],f"Preimage mismatch {x['path']}: {sha(raw)}")
        last=len(old)+1;new=old
        for start,end,replacement in reversed(x['edits']):
            require(0<=start<=end<=len(old) and end<=last,'Overlapping edit')
            new=new[:start]+replacement+new[end:];last=start
        encoded=new.encode('utf-8')
        require(sha(encoded)==x['after'],f"Postimage mismatch {x['path']}: {sha(encoded)}")
        staged[x['path']]=encoded
    expected=json.loads((ROOT/'maintenance/news-source-hashes.json').read_text(encoding='utf-8'))
    require(len(expected)==28,'Unexpected source manifest')
    for path,wanted in expected.items():
        require(not Path(path).is_absolute() and '..' not in Path(path).parts,'Invalid source path')
        data=staged.get(path,(ROOT/path).read_bytes())
        require(sha(data)==wanted,f'Source mismatch {path}: {sha(data)}')
    protected=['catalog/papers','catalog/results','catalog/benchmarks.json','catalog/first-public.json','catalog/manifest.json','maintenance/state.json']
    files=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--',*protected],cwd=ROOT,text=True).splitlines()
    for path in files:
        original=subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT)
        require((ROOT/path).read_bytes()==original,'Scientific source changed: '+path)
    for path,data in staged.items():(ROOT/path).write_bytes(data)
    (ROOT/'maintenance/news-release-validation.json').write_text(json.dumps({'schemaVersion':1,'base':BASE,'sourceHashChecks':len(expected),'preservedScientificAndStateFiles':len(files),'scope':'Pre/postimage and scientific source invariance. Full CI and real browser checks are separate workflow steps.','newsCount':6,'newsSearchStatus':'partial'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS: 28 source hashes, guarded integration and',len(files),'unchanged scientific/state files')
if __name__=='__main__':main()
