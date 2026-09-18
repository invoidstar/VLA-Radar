"""Source-specific protocol invariants; these tests do not certify scientific truth."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def read(path): return json.loads((ROOT/path).read_text())
class BatchTwoTests(unittest.TestCase):
 def setUp(self):
  self.tracks={t['id']:t for t in read('catalog/benchmarks.json')['tracks']}
 def test_distinct_three_dimensional_diffusion_identities(self):
  self.assertEqual(read('catalog/papers/p088.json')['paper']['arxiv'],'2402.10885')
  self.assertNotEqual(read('catalog/papers/p085.json')['paper']['arxiv'],'2402.10885')
 def test_corl_year_not_publication_year_or_arxiv_first(self):
  r=read('catalog/papers/p088.json')
  self.assertEqual(r['paper']['firstPublished'],'2024-02-16')
  self.assertEqual(r['publication']['publishedAt'],'2025-01-12')
  self.assertEqual(r['paper']['venue'],'CoRL 2024')
 def test_calvin_horizons_remain_nonranking_score(self):
  t=self.tracks['calvin-3dda-v3-abc-d-paper']
  self.assertEqual(t['unit'],'score');self.assertEqual(t['comparisonScope'],'paper-table')
  self.assertIn('60',t['protocol']);self.assertIn('360',t['protocol'])
 def test_rvt2_text_conflict_stays_visible(self):
  p=read('catalog/papers/p087.json')
  self.assertIn('77.6',p['paper']['findings']);self.assertIn('81.4',p['paper']['findings'])
 def test_colosseum_no_invented_overall_average(self):
  a=self.tracks['colosseum-original-v2-no-variations'];b=self.tracks['colosseum-original-v2-all-variations']
  self.assertEqual(len(a['columns']),20);self.assertEqual(a['columns'],b['columns'])
  self.assertNotIn('Average',a['columns']);self.assertNotEqual(a['split'],b['split'])
 def test_colosseum_counterexample_and_raw_precision_preserved(self):
  a=read('catalog/results/r-colosseum-original-v2-no-variations-rvt.json')
  b=read('catalog/results/r-colosseum-original-v2-all-variations-rvt.json')
  self.assertEqual(a['values']['meat_on_grill'],12);self.assertEqual(b['values']['meat_on_grill'],40)
  c=read('catalog/results/r-colosseum-original-v2-no-variations-peract.json')
  self.assertEqual(c['values']['close_box'],65);self.assertIn('步长',c['evaluationNotes'])
 def test_selected_average_does_not_turn_unrecorded_tasks_into_zero(self):
  r=read('catalog/results/r-rlbench-rvt2-v1-table1-act3d.json')
  self.assertEqual(r['values']['Average'],65.0)
  self.assertTrue(all(v is None for k,v in r['values'].items() if k!='Average'))
