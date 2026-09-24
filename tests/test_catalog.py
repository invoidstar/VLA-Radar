import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
from scripts.build.catalog_core import *
from scripts.build.build_catalog import outputs,build
from scripts.maintenance.sync_publications import parse_feed,apply_arxiv,apply_crossref,publisher_date,sync
from scripts.discovery.extract_results import extract,number
from scripts.discovery.discover_results import discover
from scripts.maintenance.maintenance_queue import plan
from scripts.migrations.apply_content_batch import prepare_resources,prepare_reproducibility

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.rec=load(ROOT/'catalog/papers/p069.json')
        self.rec['publication'].update(firstArxivAt='2025-02-27',latestArxivVersion='v2',latestArxivAt='2025-04-28',status='published',acceptedAt=None)
        self.rec['note']['version']='arXiv v1'
    def test_entire_catalog(self):
        m,r,t,v=read_catalog(ROOT);self.assertGreaterEqual(len(r),78);self.assertTrue(t);self.assertTrue(v)
    def test_official_resources_registry(self):
        m,r,_,_=read_catalog(ROOT);resources=load_resources(ROOT,{x['paper']['id'] for x in r})
        self.assertGreaterEqual(len(resources),80);self.assertTrue(all(set(v)<={'project','code'} and v for v in resources.values()))
        self.assertEqual(set(resources['p064']),{'project','code'});self.assertNotIn('p006',resources)
        out=outputs(ROOT);lib=json.loads(out['data/library.json']);byid={p['id']:p for p in lib['papers']}
        for pid,value in resources.items():self.assertEqual(byid[pid]['resources'],value)
        self.assertTrue(all('resources' in p for p in lib['papers']))

    def test_batch_resource_updates_merge_and_remove(self):
        _,records,_,_=read_catalog(ROOT);ids={x['paper']['id'] for x in records}
        merged=prepare_resources(ROOT,ids,{'p064':{'project':'https://example.com/openvla-project'},'p001':{'project':None}})
        self.assertEqual(merged['papers']['p064']['project'],'https://example.com/openvla-project')
        self.assertEqual(merged['papers']['p064']['code'],'https://github.com/openvla/openvla')
        self.assertNotIn('p001',merged['papers'])
        with self.assertRaises(ValueError):prepare_resources(ROOT,ids,{'p999':{'project':'https://example.com'}})
        with self.assertRaises(ValueError):prepare_resources(ROOT,ids,{'p064':{'demo':'https://example.com'}})

    def test_batch_reproducibility_updates_merge_and_remove(self):
        _,records,_,_=read_catalog(ROOT);ids={x['paper']['id'] for x in records}
        audit={'verifiedAt':'2026-09-25','items':{'weights':{'status':'unavailable','note':'Officially not released.','url':None,'source':'https://example.com/release-note'}}}
        merged=prepare_reproducibility(ROOT,ids,{'p001':audit,'p064':None})
        self.assertEqual(merged['papers']['p001'],audit)
        self.assertNotIn('p064',merged['papers'])
        with self.assertRaises(ValueError):prepare_reproducibility(ROOT,ids,{'p999':audit})
        bad=copy.deepcopy(audit);bad['items']['weights']['status']='unknown'
        with self.assertRaises(ValueError):prepare_reproducibility(ROOT,ids,{'p001':bad})

    def test_public_keys(self):
        self.rec['privateNotes']='not allowed'
        with self.assertRaises(ValueError):validate_record(self.rec)
    def test_source_ssrf_boundaries(self):
        for s in ['file:///etc/passwd','http://127.0.0.1','http://169.254.169.254/','http://[::1]','https://x:y@arxiv.org','http://localhost','http://a.internal','http://arxiv.org:8123']:
            with self.subTest(s=s),self.assertRaises(ValueError):public_url(s)
    def test_expanded_requires_sources(self):
        self.rec['note']['status']='expanded';self.rec['note']['sections'][0]['sources']=[]
        with self.assertRaises(ValueError):validate_record(self.rec)
    def test_unknown_date_stays_unknown(self):
        p=copy.deepcopy(self.rec['paper']);p['firstPublished']=None;p['dateNote']='not known';r=migrate_paper(p,'2026-09-17');self.assertIsNone(r['publication']['firstArxivAt']);self.assertIsNone(r['publication']['acceptedAt'])
    def test_migration_not_certification(self):
        r=migrate_paper(self.rec['paper'],'2026-09-17');self.assertEqual(r['publication']['status'],'legacy');self.assertIsNone(r['note']['verifiedAt']);self.assertEqual(r['paper'],self.rec['paper'])
    def test_deterministic_outputs(self):self.assertEqual(outputs(ROOT),outputs(ROOT));build(ROOT,True)
    def test_generated_separation(self):
        out=outputs(ROOT);short=json.loads(out['data/catalog.json']);full=json.loads(out['data/details/p069.json'])
        self.assertNotIn('note',short['papers'][0]);self.assertIn('sections',full['note']);self.assertEqual(json.loads(out['data/papers.json'])['schemaVersion'],1)
    def test_immutable_first_public(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ROOT/'catalog',Path(tmp)/'catalog');r=load(Path(tmp)/'catalog/papers/p069.json');r['paper']['firstPublished']='2026-01-01';write(Path(tmp)/'catalog/papers/p069.json',r)
            with self.assertRaises(ValueError):read_catalog(tmp)
    def test_id_mismatch(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ROOT/'catalog',Path(tmp)/'catalog');r=load(Path(tmp)/'catalog/papers/p069.json');r['paper']['id']='p064';write(Path(tmp)/'catalog/papers/p069.json',r)
            with self.assertRaises(ValueError):read_catalog(tmp)
    def test_network_failure_does_not_advance_search(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ROOT/'catalog',Path(tmp)/'catalog');Path(tmp,'maintenance').mkdir();write(Path(tmp)/'maintenance/state/state.json',{'lastSuccessfulSearchAt':None});before=load(Path(tmp)/'maintenance/state/state.json')
            with patch('scripts.maintenance.sync_publications.fetch',side_effect=OSError('offline')):report=sync(tmp,1,True,pause=0,due_days=0)
            self.assertEqual(report['status'],'partial');self.assertFalse(report['metadataChecked']);self.assertEqual(load(Path(tmp)/'maintenance/state/state.json'),before)
    def meta(self,**kw):return dict(arxiv='2502.19645',version='v3',firstArxivAt='2025-02-27',latestArxivAt='2026-09-01',title=self.rec['paper']['title'],doi='',journalRef='',comment='',**kw)
    def test_arxiv_version_preserves_first_public(self):
        prior=self.rec['paper']['firstPublished'];self.rec['note']['status']='expanded';apply_arxiv(self.rec,self.meta(),'2026-09-17');self.assertEqual(self.rec['paper']['firstPublished'],prior);self.assertEqual(self.rec['publication']['status'],'published');self.assertEqual(self.rec['note']['status'],'needs_review')
    def test_adjacent_arxiv_version_is_understood(self):
        self.rec['note']['version']='arXiv:2502.19645v2；method sections'
        self.rec['note']['status']='expanded';meta=self.meta();meta['version']='v2'
        apply_arxiv(self.rec,meta,'2026-09-18');self.assertEqual(self.rec['note']['status'],'expanded')
    def test_quoted_key_result_version_is_not_read_version(self):
        self.rec['note']['version']='arXiv v1；KEY RESULT retained from v3'
        self.rec['note']['status']='expanded';meta=self.meta();meta['version']='v2'
        apply_arxiv(self.rec,meta,'2026-09-18');self.assertEqual(self.rec['note']['status'],'needs_review')
    def test_arxiv_date_conflict_queued(self):
        meta=self.meta();meta['firstArxivAt']='2025-02-28';out=apply_arxiv(self.rec,meta,'2026-09-17');self.assertEqual(self.rec['publication']['firstArxivAt'],'2025-02-27');self.assertEqual(out[0]['kind'],'first-arxiv-conflict')
    def test_arxiv_identity(self):
        meta=self.meta();meta['arxiv']='0000.00000'
        with self.assertRaises(ValueError):apply_arxiv(self.rec,meta,'2026-09-17')
    def test_arxiv_acceptance_is_only_candidate(self):
        r=migrate_paper(self.rec['paper'],'2026-09-17');r['paper']['publicationType']='preprint';meta=self.meta();meta['comment']='Accepted to RSS';out=apply_arxiv(r,meta,'2026-09-17');self.assertEqual(r['publication']['status'],'preprint');self.assertEqual(out[0]['kind'],'venue-mention');self.assertIsNone(r['publication']['acceptedAt'])
    def test_no_duplicate_event(self):
        apply_arxiv(self.rec,self.meta(),'2026-09-17');n=len(self.rec['publication']['history']);apply_arxiv(self.rec,self.meta(),'2026-09-18');self.assertEqual(len(self.rec['publication']['history']),n)
    def message(self):return {'DOI':'10.1111/example','title':[self.rec['paper']['title']],'type':'proceedings-article','container-title':['Example proceedings'],'published':{'date-parts':[[2025,6]]}}
    def test_publication_precision_and_no_acceptance_guess(self):
        ok,_=apply_crossref(self.rec,self.message(),'10.1111/example','2026-09-17');self.assertTrue(ok);self.assertEqual(self.rec['publication']['publishedAt'],'2025-06');self.assertIsNone(self.rec['publication']['acceptedAt']);self.assertEqual(self.rec['paper']['firstPublished'],'2025-02-27')
    def test_arxiv_doi_not_acceptance(self):
        msg=self.message();msg['DOI']='10.48550/arxiv.2502.19645';self.assertFalse(apply_crossref(self.rec,msg,msg['DOI'],'2026-09-17')[0])
    def test_mismatched_title_not_accepted(self):
        msg=self.message();msg['title']=['A different scientific work'];self.assertFalse(apply_crossref(self.rec,msg,msg['DOI'],'2026-09-17')[0])
    def test_future_date_not_published(self):
        msg=self.message();msg['published']['date-parts']=[[2027,1,1]];self.assertFalse(apply_crossref(self.rec,msg,msg['DOI'],'2026-09-17')[0])
    def test_atom(self):
        xml='<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2502.19645v2</id><published>2025-02-27T00:30:29Z</published><updated>2025-04-28T07:49:39Z</updated><title> Example </title></entry></feed>';r=parse_feed(xml)['2502.19645'];self.assertEqual(r['version'],'v2');self.assertEqual(r['firstArxivAt'],'2025-02-27')
    def test_extract_candidates_only(self):
        html='<table id="t1"><tr><th>Method</th><th>Average</th></tr><tr><td>A</td><td>98.5</td></tr><tr><td>B</td><td>—</td></tr></table>';r=extract(html,'p076','https://arxiv.org/html/2601.16163v1','v1',0,'libero-cosmos-3seeds',{'Average':1});self.assertEqual(r['candidates'][0]['evidence'],'candidate');self.assertIsNone(r['candidates'][0]['verifiedAt']);self.assertTrue(r['reviewRequired'])
    def test_discover_never_invents_protocol(self):
        html='<h2>RoboTwin evaluation</h2><table><tr><th>Method</th><th>Clean</th><th>Average</th></tr><tr><td>A</td><td>92.0</td><td>91.0</td></tr></table>';r=discover(html,'p021','https://arxiv.org/html/2608.00725v1','v1');self.assertEqual(r['tables'][0]['protocolStatus'],'unresolved');self.assertEqual(r['tables'][0]['possibleDatasets'],['RoboTwin'])
    def test_missing_score_not_zero(self):
        self.assertIsNone(number('—'))
        with self.assertRaises(ValueError):number('94.0 / 96.0')
    def test_invalid_result(self):
        m,recs,tracks,results=read_catalog(ROOT);r=copy.deepcopy(results[0]);r['values'][next(iter(r['values']))]=float('nan')
        with self.assertRaises(ValueError):validate_result(r,set(m['paperOrder']),{t['id']:t for t in tracks})
    def test_review_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            import shutil
            root=Path(tmp);shutil.copytree(ROOT/'catalog',root/'catalog')
            pending={'p001','p002','p003'}
            for pid in pending:
                path=root/'catalog'/'papers'/f'{pid}.json';rec=json.loads(path.read_text());rec['note']['status']='needs_review';path.write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n')
            p=plan(root,3)
            self.assertEqual({x['paperId'] for x in p['notes']},pending)
            self.assertEqual(p['remainingNotes'],3)
if __name__=='__main__':unittest.main()
