import copy,sys,unittest
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from arxiv_metadata import parse_abstract
from repo_housekeeping import decide,REPO
from catalog_core import load
ROOT=Path(__file__).resolve().parents[1]
HTML='''<meta name="citation_arxiv_id" content="2502.19645"><meta name="citation_title" content="Example paper">
<div>Comments: Accepted at test conference. Subjects: Robotics</div><div class="submission-history">Submission history
<strong>[v2]</strong> Tue, 10 Jun 2025 12:34:00 UTC <br>[v1] Thu, 27 Feb 2025 10:30:00 UTC</div>'''
class MaintenanceTests(unittest.TestCase):
    def test_first_date_not_latest(self):
        m=parse_abstract(HTML,'2502.19645');self.assertEqual(m['firstArxivAt'],'2025-02-27');self.assertEqual(m['version'],'v2');self.assertEqual(m['latestArxivAt'],'2025-06-10')
    def test_identity_rejected(self):
        with self.assertRaises(ValueError):parse_abstract(HTML,'2406.09246')
    def test_no_history_no_guess(self):
        with self.assertRaises(ValueError):parse_abstract(HTML.split('Submission history')[0],'2502.19645')
    def test_missing_v1_rejected(self):
        with self.assertRaises(ValueError):parse_abstract(HTML.replace('[v1]','[v3]'),'2502.19645')
    def test_doi_is_not_arxiv_doi(self):
        m=parse_abstract(HTML+'<a href="https://doi.org/10.48550/arXiv.2502.19645">doi</a>','2502.19645');self.assertEqual(m['doi'],'')
    def setUp(self):
        self.policy=load(ROOT/'maintenance/branch-policy.json');self.now=datetime(2026,9,18,12,tzinfo=timezone.utc)
        self.b={'name':'weekly-update-2026-09-01','commit':{'sha':'a'*40},'protected':False}
        self.pr={'number':1,'state':'closed','merged_at':'2026-09-17T00:00:00Z','merge_commit_sha':'b'*40,'base':{'ref':'main'},'head':{'ref':self.b['name'],'sha':'a'*40,'repo':{'full_name':REPO}}}
    def result(self,prs=None):return decide(self.b,[self.pr] if prs is None else prs,self.policy,self.now)
    def test_merged_exact_head_eligible(self):self.assertEqual(self.result()['action'],'candidate')
    def test_postmerge_commit_protected(self):self.b['commit']['sha']='c'*40;self.assertEqual(self.result()['action'],'keep')
    def test_open_pr_protected(self):self.pr['state']='open';self.assertEqual(self.result()['reason'],'open-pr-reference')
    def test_open_base_protected(self):
        p=copy.deepcopy(self.pr);p['state']='open';p['base']['ref']=self.b['name'];p['head']['ref']='other';self.assertEqual(self.result([self.pr,p])['action'],'keep')
    def test_main_protected(self):self.b['name']='main';self.assertEqual(self.result()['reason'],'reserved')
    def test_backup_protected(self):self.b['name']='pre-update-safety-2026';self.assertEqual(self.result()['reason'],'reserved')
    def test_server_protected(self):self.b['protected']=True;self.assertEqual(self.result()['reason'],'protected')
    def test_unmerged_never_deleted(self):self.pr['merged_at']=None;self.assertEqual(self.result()['action'],'keep')
    def test_recent_merge_preserved(self):self.pr['merged_at']='2026-09-18T11:00:00Z';self.assertEqual(self.result()['reason'],'recovery-grace-period')
    def test_fork_not_deleted(self):self.pr['head']['repo']['full_name']='other/repo';self.assertEqual(self.result()['action'],'keep')
    def test_merge_into_other_base_preserved(self):self.pr['base']['ref']='develop';self.assertEqual(self.result()['action'],'keep')
if __name__=='__main__':unittest.main()

class SyncFallbackTests(unittest.TestCase):
    def run_sync(self,fail_code):
        import tempfile,shutil
        from unittest.mock import patch
        from urllib.error import HTTPError
        from sync_publications import sync
        from catalog_core import write
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);root=Path(self.tmp.name)
        shutil.copytree(ROOT/'catalog',root/'catalog');(root/'maintenance').mkdir();write(root/'maintenance/state.json',{'lastSuccessfulSearchAt':None})
        # Deterministic fixture: one chosen due record, independent of live metadata.
        from catalog_core import today
        for file in (root/'catalog/papers').glob('*.json'):
            item=load(file);item['publication']['lastCheckedAt']=today();write(file,item)
        rec=load(root/'catalog/papers/p001.json');ident=rec['paper']['arxiv']
        rec['publication']['lastCheckedAt']=None
        rec['publication']['doi']='';rec['paper']['doi']=''
        write(root/'catalog/papers/p001.json',rec)
        html=HTML.replace('2502.19645',ident).replace('Example paper',rec['paper']['title'])
        def mock(url,**kwargs):
            if '/api/query' in url:raise HTTPError(url,fail_code,'test failure',{},None)
            return html,200,url
        with patch('sync_publications.fetch',side_effect=mock) as f:
            r=sync(root,1,True,pause=0,due_days=7)
        return r,f.call_count,load(root/'maintenance/state.json')
    def test_406_uses_official_html(self):
        report,calls,state=self.run_sync(406);self.assertEqual(calls,2);self.assertEqual(report['metadataChecked'],['p001']);self.assertEqual(report['providers']['2608.27550'],'arxiv-abstract');self.assertIsNone(state['lastSuccessfulSearchAt'])
    def test_429_does_not_bypass(self):
        report,calls,_=self.run_sync(429);self.assertEqual(calls,1);self.assertEqual(report['metadataChecked'],[])
    def test_403_does_not_bypass(self):
        report,calls,_=self.run_sync(403);self.assertEqual(calls,1);self.assertEqual(report['metadataChecked'],[])
