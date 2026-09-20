"""Guard original evidence boundaries, not independent scientific replication."""
import json
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(path): return json.loads((R/path).read_text())
class BatchElevenTests(unittest.TestCase):
 def setUp(self):
  self.audit=read('maintenance/audits/benchmark/benchmark-source-audit-20260919-batch11.json')
  self.tracks={t['id']:t for t in read('catalog/benchmarks.json')['tracks']}
  self.rows=[read('catalog/results/'+id+'.json') for id in self.audit['newResults']]
  self.rec={id:read('catalog/papers/'+id+'.json') for id in ['p053','p044']}
 def row(self,suffix): return next(r for r in self.rows if r['id'].endswith(suffix))
 def test_two_existing_deep_notes(self):
  self.assertEqual(self.audit['newPapers'],[])
  for r in self.rec.values():
   n=r['note'];self.assertEqual(len(n['sections']),9)
   self.assertGreater(sum(len(s['body']) for s in n['sections']),3000)
   self.assertTrue(all(s['sources'] for s in n['sections']))
   self.assertEqual(n['benchmarkReview']['status'],'extracted')
 def test_evidence_counts_and_no_invented_replication(self):
  self.assertEqual(len(self.rows),24);self.assertEqual(len(self.audit['newTracks']),5)
  self.assertEqual(sum(r['paperId']=='p053' for r in self.rows),13)
  self.assertEqual(sum(r['paperId']=='p044' for r in self.rows),11)
  self.assertTrue(all(self.tracks[r['trackId']]['comparisonScope']=='paper-table' for r in self.rows))
 def test_unipi_table2_complete_model_not_duplicated(self):
  rows=[r for r in self.rows if r['trackId']=='unipi-neurips23-compositional']
  self.assertEqual(len(rows),8)
  self.assertEqual(sum(r['values']['SeenPlace']==59.1 and r['values']['SeenRelation']==53.2 for r in rows),1)
  for suffix in ['no-components','frame-only','frame-consistency']:
   r=self.row('compositional-'+suffix)
   self.assertIsNone(r['values']['NovelPlace']);self.assertIsNone(r['values']['NovelRelation'])
 def test_original_means_and_uncertain_error_definition(self):
  self.assertEqual(self.row('compositional-unipi')['values'],{'SeenPlace':59.1,'SeenRelation':53.2,'NovelPlace':60.1,'NovelRelation':46.1})
  self.assertEqual(self.row('transfer-unipi')['values'],{'PlaceBowl':51.6,'PackObject':75.5,'PackPair':45.7})
  self.assertTrue(all('±' in r['evaluationNotes'] for r in self.rows if r['paperId']=='p053'))
 def test_unipi_control_and_budget_domains(self):
  t=self.tracks['unipi-neurips23-compositional'];self.assertIn('开环',t['protocol']);self.assertIn('20k',t['trainingRegime'])
  t=self.tracks['ravens-unipi-neurips23-transfer'];self.assertIn('11',t['protocol']);self.assertIn('200k',t['trainingRegime'])
  self.assertNotIn('Average',t['columns']);self.assertEqual(t['dataset'],'Ravens (CLIPort)')
 def test_video_proxy_is_not_a_robot_result(self):
  rows=[r for r in self.rows if r['paperId']=='p053']
  self.assertFalse(any(77.1 in r['values'].values() for r in rows))
  self.assertFalse(any('real' in self.tracks[r['trackId']]['dataset'].lower() for r in rows))
  text=' '.join(s['body'] for s in self.rec['p053']['note']['sections'])
  self.assertIn('末帧',text);self.assertIn('higher FID/FVD',text)
 def test_touch_prerequisite_vla_training_is_explicit(self):
  text=' '.join(s['body'] for s in self.rec['p044']['note']['sections'])
  for term in ['10万步','2万步','前48步','64步','8Hz','Octopi','Octo']:
   self.assertIn(term,text)
  self.assertIn('无触觉任务微调',self.rec['p044']['paper']['contribution'])
 def test_touch_completion_counts_and_counterexample(self):
  self.assertEqual(self.row('manipulation-rdt')['values'],{'CupPlace':35,'WipeComplete':25,'PeelComplete':30})
  self.assertEqual(self.row('manipulation-interpolant')['values'],{'CupPlace':50,'WipeComplete':60,'PeelComplete':50})
  self.assertEqual(self.row('manipulation-residual')['values']['CupPlace'],30)
  self.assertTrue(all('Partial' not in c and 'Pick' not in c for c in self.tracks['vlatouch-v2-real-manipulation']['columns']))
 def test_touch_interleaved_does_not_take_best_from_other_table(self):
  self.assertEqual(self.row('interleaved-full')['values'],{'Cup':45,'Wipe':60,'Peel':35})
  self.assertNotEqual(self.row('interleaved-full')['values']['Peel'],self.row('manipulation-interpolant')['values']['PeelComplete'])
 def test_property_metric_and_raw_tactile_tie(self):
  tr=self.tracks['vlatouch-v2-property-decisions'];self.assertIn('accuracy',tr['metric'])
  self.assertEqual(self.row('decisions-raw-tactile')['values']['Roughness'],100)
  self.assertEqual(self.row('decisions-structured')['values'],{'Force':90,'Roughness':100,'Hardness':75})
 def test_first_dates_and_journal_boundary_preserved(self):
  self.assertEqual(self.rec['p053']['paper']['firstPublished'],'2023-01-31')
  self.assertEqual(self.rec['p053']['publication']['publishedAt'],'2023')
  self.assertEqual(self.rec['p044']['publication']['lastCheckedAt'],'2026-09-18')
  self.assertEqual(self.rec['p044']['publication']['firstArxivAt'],'2025-07-23')
  b=read('catalog/bibliography.json')['entries']
  self.assertEqual(len(b['p053']['item']['author']),8);self.assertEqual(len(b['p044']['item']['author']),5)
  self.assertEqual(b['p044']['item']['type'],'article');self.assertNotIn('DOI',b['p044']['item'])
 def test_corrections_have_exact_before_after_sources(self):
  k=self.audit['keyResultCorrections'][0]
  self.assertEqual(k['paperId'],'p053');self.assertEqual(k['after'],self.rec['p053']['paper']['findings'])
  s=self.audit['summaryCorrections'][0];self.assertEqual(s['after'],self.rec['p044']['paper']['contribution'])
  self.assertIn('7/20→10/20',self.rec['p044']['paper']['findings'])
if __name__=='__main__':unittest.main()
