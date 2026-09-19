"""Protect original-report protocol distinctions; not scientific certification."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text())
class BatchFourTests(unittest.TestCase):
 def setUp(self):self.tracks={t['id']:t for t in read('catalog/benchmarks.json')['tracks']}
 def test_robomimic_observations_and_demo_source_separated(self):
  for mode in ['lowdim','image']:
   for src in ['ph','mh']:
    t=self.tracks[f'robomimic-corl21-{mode}-{src}-best']
    self.assertIn('50评测回合',t['protocol']);self.assertIn('最高成功率',t['protocol'])
    self.assertEqual(len(t['columns']),5 if src=='ph' else 4)
 def test_missing_cql_scores_not_zeros(self):
  r=read('catalog/results/r-robomimic-corl21-image-mh-best-cql.json')
  self.assertEqual(r['values']['Can'],0);self.assertIsNone(r['values']['Square'])
 def test_dex_budget_and_embodiment_not_total_release_size(self):
  for group in ['panda-gripper','panda-dex','gr1-dex']:
   t=self.tracks['dexmimicgen-v2-table1-'+group]
   self.assertEqual(len(t['columns']),3);self.assertIn('1000',t['trainingRegime']);self.assertNotIn('Average',t['columns'])
 def test_dex_diffusion_is_not_always_best(self):
  prefix='catalog/results/r-dexmimicgen-v2-table1-gr1-dex-'
  r=read(prefix+'generated-rnn.json');d=read(prefix+'generated-dp.json')
  self.assertEqual(r['values']['Coffee'],84.7);self.assertEqual(d['values']['Coffee'],77.3)
 def test_simpler_grasp_and_correlation_not_completion(self):
  t=self.tracks['simpler-original-v1-widowx-vm']
  self.assertEqual(len(t['columns']),4);self.assertEqual(t['unit'],'percent')
  r=read('catalog/results/r-simpler-original-v1-widowx-vm-octo-base.json')
  self.assertEqual(r['values']['Put Spoon on Towel'],12.5)
  self.assertEqual(r['values']['Stack Green on Yellow'],0)
 def test_simpler_vm_va_original_rounding_preserved(self):
  vm=read('catalog/results/r-simpler-original-v1-google-vm-rt1-converged.json')
  va=read('catalog/results/r-simpler-original-v1-google-va-rt1-converged.json')
  self.assertEqual(vm['values']['Pick-Average'],85.7);self.assertEqual(va['values']['Pick-Average'],89.8)
  self.assertNotIn('Average',vm['values']);self.assertNotIn('MMRV',vm['values'])
 def test_first_publication_not_formal_year(self):
  a=read('catalog/papers/p093.json');b=read('catalog/papers/p095.json')
  self.assertEqual(a['paper']['firstPublished'],'2021-08-06');self.assertEqual(a['publication']['publishedAt'],'2022')
  self.assertEqual(b['paper']['firstPublished'],'2024-05-09');self.assertEqual(b['publication']['publishedAt'],'2025')
 def test_new_deep_notes_are_source_scoped(self):
  for pid in ['p093','p094','p095']:
   n=read(f'catalog/papers/{pid}.json')['note']
   self.assertGreaterEqual(len(n['sections']),8);self.assertGreaterEqual(sum(len(s['body']) for s in n['sections']),2000)
   self.assertEqual(n['benchmarkReview']['status'],'extracted');self.assertTrue(all(s['sources'] for s in n['sections']))
