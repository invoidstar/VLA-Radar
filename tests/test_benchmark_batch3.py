"""Historical source/protocol regression, not independent scientific verification."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
class BatchThreeTests(unittest.TestCase):
 def setUp(self):self.tracks={t['id']:t for t in read('catalog/benchmarks.json')['tracks']}
 def test_original_method_identities(self):
  self.assertEqual(read('catalog/papers/p090.json')['paper']['arxiv'],'2306.17817')
  self.assertEqual(read('catalog/papers/p091.json')['paper']['arxiv'],'2308.16891')
  self.assertIn('ChainedDiffuser',read('catalog/papers/p092.json')['paper']['title'])
 def test_unknown_first_date_not_replaced_by_publication(self):
  p=read('catalog/papers/p092.json')
  self.assertIsNone(p['paper']['firstPublished']);self.assertEqual(p['paper']['arxiv'],'')
  self.assertEqual(p['publication']['publishedAt'],'2023-12-02')
  self.assertTrue(p['paper']['dateNote'])
 def test_act3d_scopes_and_original_precision(self):
  a=self.tracks['rlbench-act3d-corl2023-74single'];b=self.tracks['rlbench-act3d-corl2023-18multi']
  self.assertEqual(a['tasks'],'74');self.assertEqual(b['tasks'],'18')
  self.assertEqual(read('catalog/results/r-rlbench-act3d-corl2023-18multi-act3d-100.json')['values']['Average'],65)
  self.assertIn('65.1',read('catalog/papers/p090.json')['paper']['findings'])
 def test_gnf_training_privilege_and_checkpoint_selection(self):
  a=self.tracks['rlbench-gnfactor-v3-final20'];b=self.tracks['rlbench-gnfactor-v3-best20']
  self.assertIn('19',a['trainingRegime']);self.assertNotEqual(a['split'],b['split'])
  self.assertEqual(a['comparisonScope'],'paper-table')
  self.assertEqual(read('catalog/results/r-rlbench-gnfactor-v3-final20-gnfactor.json')['values']['Average'],31.7)
  self.assertEqual(read('catalog/results/r-rlbench-gnfactor-v3-best20-gnfactor.json')['values']['Average'],40)
 def test_gnf_negative_and_reported_rounding(self):
  r=read('catalog/results/r-rlbench-gnfactor-v3-final20-gnfactor.json')
  self.assertEqual(r['values']['put_in_drawer'],0)
  g=read('catalog/results/r-rlbench-gnfactor-v3-generalization20-peract.json')
  self.assertEqual(g['values']['drag_D'],6.6)
 def test_chained_protocol_feedback_and_counterexample(self):
  a=self.tracks['rlbench-chained-corl2023-standard10'];b=self.tracks['rlbench-chained-corl2023-contact10']
  self.assertEqual(a['tasks'],'10');self.assertEqual(b['tasks'],'10');self.assertNotEqual(a['columns'],b['columns'])
  self.assertIn('open-loop',a['protocol']);self.assertEqual(a['unit'],'percent')
  x=read('catalog/results/r-rlbench-chained-corl2023-contact10-chained.json')['values']
  y=read('catalog/results/r-rlbench-chained-corl2023-contact10-trajectory-regression.json')['values']
  self.assertEqual(x['wipe_desk'],65);self.assertEqual(y['wipe_desk'],70)
 def test_chained_original_vs_later_reporting_paper(self):
  old=read('catalog/results/r-calvin-3dda-v3-abc-d-paper-chaineddiffuser.json')
  self.assertEqual(old['paperId'],'p088')
  new=read('catalog/results/r-rlbench-chained-corl2023-standard10-chained.json')
  self.assertEqual(new['paperId'],'p092');self.assertEqual(new['values']['Average'],95.8)
