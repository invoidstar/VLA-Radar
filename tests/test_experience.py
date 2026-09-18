"""Public derived views and truthful update semantics, using synthetic deltas only."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from experience_build import outputs
from capture_activity import paper_events
from catalog_core import read_catalog
class ExperienceTests(unittest.TestCase):
 def setUp(self):self.manifest,self.records,self.tracks,self.results=read_catalog(ROOT)
 def test_original_records_not_mutated(self):
  prior=copy.deepcopy([self.records,self.tracks,self.results]);outputs(ROOT,self.records,self.tracks,self.results);self.assertEqual(prior,[self.records,self.tracks,self.results])
 def test_no_first_collection_date_inferred(self):
  out,_=outputs(ROOT,self.records,self.tracks,self.results)
  for path,text in out.items():
   if '/events-' not in path:continue
   for e in json.loads(text)['events']:
    if e['mode']=='snapshot':self.assertIsNone(e['observedAt']);self.assertNotEqual(e['kind'],'collected')
 def test_metadata_check_is_not_note_update(self):
  old=copy.deepcopy(self.records[0]);new=copy.deepcopy(old);new['publication']['lastCheckedAt']='2026-09-18';new['note']['status']='needs_review'
  self.assertEqual(paper_events(old,new,'2026-09-18T06:00:00Z','a'*40),[])
 def test_actual_note_change_has_before_after(self):
  old=copy.deepcopy(self.records[0]);new=copy.deepcopy(old);new['note']['sections'][0]['body']+=' Synthetic change.'
  e=paper_events(old,new,'2026-09-18T06:00:00Z','a'*40);self.assertEqual(len(e),1);self.assertEqual(e[0]['kind'],'note');self.assertTrue(e[0]['changes']);self.assertNotEqual(e[0]['changes'][0]['before'],e[0]['changes'][0]['after'])
 def test_late_chapter_changes_remain_identifiable(self):
  old=copy.deepcopy(self.records[0]);new=copy.deepcopy(old);new['note']['sections'][-1]['body']='Synthetic replacement.'
  e=paper_events(old,new,'2026-09-18T06:00:00Z','a'*40);self.assertEqual(len(e[0]['changes']),1);self.assertIn(new['note']['sections'][-1]['id'],e[0]['changes'][0]['field'])
 def test_new_paper_explicit_collection_event(self):
  e=paper_events(None,self.records[0],'2026-09-18T06:00:00Z','a'*40);self.assertEqual(e[0]['kind'],'collected');self.assertEqual(e[0]['observedAt'],'2026-09-18T06:00:00Z')
 def test_activity_ids_are_idempotent(self):
  a=paper_events(None,self.records[0],'2026-09-18T06:00:00Z','a'*40);b=paper_events(None,self.records[0],'2026-09-19T06:00:00Z','a'*40);self.assertEqual(a[0]['id'],b[0]['id'])
 def test_publication_vs_revision(self):
  old=copy.deepcopy(self.records[0]);new=copy.deepcopy(old);new['publication']['latestArxivVersion']='v99';new['publication']['status']='published';e=paper_events(old,new,'2026-09-18T06:00:00Z','a'*40);self.assertEqual({x['kind'] for x in e},{'revision','publication'})
 def test_derived_manifest_small(self):
  out,url=outputs(ROOT,self.records,self.tracks,self.results);self.assertLess(len(out[url]),1000)
if __name__=='__main__':unittest.main()
