"""Original-source metric and identity invariants; not independent scientific certification."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
class BatchSevenTests(unittest.TestCase):
 def setUp(self):self.t={t['id']:t for t in read('catalog/benchmarks.json')['tracks']}
 def test_real_google_is_not_simpler(self):
  for k in ['google-real-rt1-v2-table2','google-real-rt2-v1-generalization']:
   self.assertEqual(self.t[k]['dataset'],'Google Robot (real)')
   self.assertEqual(self.t[k]['comparisonScope'],'paper-table')
 def test_rt1_scope_conflict_and_same_source_dedup(self):
  t=self.t['google-real-rt1-v2-table2'];self.assertIn('21',t['protocol']);self.assertIn('53',t['protocol'])
  audit=read('maintenance/benchmark-source-audit-20260919-batch7.json')
  self.assertEqual(len([i for i in audit['newResults'] if i.startswith('r-google-real-rt1')]),9)
 def test_rt2_original_table_average_not_larger_value(self):
  r=read('catalog/results/r-google-real-rt2-v1-generalization-palix.json')
  self.assertEqual(r['values']['UnseenAverage'],62)
  self.assertIn('63',r['evaluationNotes']);self.assertEqual(r['paperId'],'p058')
 def test_palme_vla_variant_not_original_palme_paper(self):
  r=read('catalog/results/r-google-real-rt2-v1-generalization-palme.json')
  self.assertEqual(r['paperId'],'p058');self.assertNotEqual(r['paperId'],'p054')
 def test_palme_table2_accuracy_is_not_rollout_success(self):
  a=self.t['language-table-palme-icml23-task1-accuracy'];b=self.t['language-table-palme-icml23-task23-success']
  self.assertEqual(a['metric'],'Validation accuracy');self.assertEqual(b['metric'],'Task success rate')
  self.assertIn('80',b['protocol']);self.assertNotEqual(a['columns'],b['columns'])
 def test_palme_modified_reward_does_not_replace_main_table(self):
  r=read('catalog/results/r-language-table-palme-icml23-task23-success-finetuned.json')
  self.assertEqual(r['values']['Task3D80'],56.3);self.assertIn('77.0',r['evaluationNotes'])
 def test_f1_is_score_and_missing_is_null(self):
  t=self.t['google-real-palme-icml23-perception-f1'];self.assertEqual(t['unit'],'score')
  r=read('catalog/results/r-google-real-palme-icml23-perception-f1-clip-ft.json')
  self.assertIsNone(r['values']['Affordance']);self.assertEqual(r['values']['FailureDetection'],.65)
 def test_real_zero_not_missing(self):
  r=read('catalog/results/r-google-real-rt1-v2-kuka-transfer-kuka.json')
  self.assertEqual(r['values'],{'Classroom':0,'BinPicking':0})
 def test_original_dates_and_formal_authors_separate(self):
  for p,first in [('p052','2022-12-13'),('p054','2023-03-06'),('p058','2023-07-28')]:
   r=read('catalog/papers/'+p+'.json');self.assertEqual(r['paper']['firstPublished'],first)
   self.assertEqual(r['publication']['publishedAt'],'2023');self.assertIsNone(r['publication']['acceptedAt'])
  bib=read('catalog/bibliography.json')['entries'];self.assertEqual(bib['p058']['item']['author'][0]['family'],'Zitkovich')
