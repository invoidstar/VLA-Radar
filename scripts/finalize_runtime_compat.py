"""One-time exact pre/postimage repair for live-metadata-independent test fixtures."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
BEFORE={'tests/test_catalog.py':'06de8f22004793394c7d754e32ea1219207c198ba8729aceb463037ae14b656e','tests/test_maintenance.py':'b33219b6328c700c7def0f2c02219a6433c7d34f0b91d39627c3639c63dc9b17','scripts/sync_publications.py':'7a38e61f264478a76bfa82549389357a2febb8f2d7014a126fce624f321ee169'}
AFTER={'tests/test_catalog.py':'72a4a598d1e4e51d3f4d26afc262dc3f82ae78e1f4e5e9658d49cefabc3a1a0a','tests/test_maintenance.py':'8f2d27c596d6965cd5b9788b18abdd6d4a9d22f814c6513b615059f3adf46159','scripts/sync_publications.py':'b8ef179efdbc5ca09852eb9e526e5a2c931487b05ea60aa7557ea14f68943248'}
texts={}
for name,wanted in BEFORE.items():
    raw=(ROOT/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==wanted,name
    texts[name]=raw.decode()
s=texts['tests/test_catalog.py'];assert 'sync(tmp,1,True,pause=0)' in s
s=s.replace('sync(tmp,1,True,pause=0)','sync(tmp,1,True,pause=0,due_days=0)')
test='''    def test_adjacent_arxiv_version_is_understood(self):
        self.rec['note']['version']='arXiv:2502.19645v2；method sections'
        self.rec['note']['status']='expanded';meta=self.meta();meta['version']='v2'
        apply_arxiv(self.rec,meta,'2026-09-18');self.assertEqual(self.rec['note']['status'],'expanded')
    def test_quoted_key_result_version_is_not_read_version(self):
        self.rec['note']['version']='arXiv v1；KEY RESULT retained from v3'
        self.rec['note']['status']='expanded';meta=self.meta();meta['version']='v2'
        apply_arxiv(self.rec,meta,'2026-09-18');self.assertEqual(self.rec['note']['status'],'needs_review')
'''
s=s.replace('    def test_arxiv_date_conflict_queued(self):',test+'    def test_arxiv_date_conflict_queued(self):');texts['tests/test_catalog.py']=s
s=texts['tests/test_maintenance.py'];a="        rec=load(root/'catalog/papers/p001.json');ident=rec['paper']['arxiv']\n"
b="""        # Deterministic fixture: one chosen due record, independent of live metadata.
        from catalog_core import today
        for file in (root/'catalog/papers').glob('*.json'):
            item=load(file);item['publication']['lastCheckedAt']=today();write(file,item)
        rec=load(root/'catalog/papers/p001.json');ident=rec['paper']['arxiv']
        rec['publication']['lastCheckedAt']=None
        rec['publication']['doi']='';rec['paper']['doi']=''
        write(root/'catalog/papers/p001.json',rec)
"""
assert a in s;s=s.replace(a,b).replace('due_days=0)','due_days=7)');texts['tests/test_maintenance.py']=s
s=texts['scripts/sync_publications.py'];a="read_versions=re.findall(r'\\bv(\\d+)\\b',rec['note']['version'])";b="read_versions=re.findall(r'(?<![A-Za-z])v(\\d+)\\b',re.split(r'[;；]',rec['note']['version'],maxsplit=1)[0])"
assert a in s;s=s.replace(a,b);texts['scripts/sync_publications.py']=s
for name,s in texts.items():assert hashlib.sha256(s.encode()).hexdigest()==AFTER[name],name
for name,s in texts.items():(ROOT/name).write_text(s)
p=ROOT/'maintenance/runtime-upgrade.json';record=json.loads(p.read_text());record['followupRepairs']=[{'path':k,'before':BEFORE[k],'after':AFTER[k]} for k in texts];p.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
Path(__file__).unlink()
print('PASS: network-failure/406 tests are independent of live due dates; explicit read-version parser has two new regressions. No assertions removed.')
