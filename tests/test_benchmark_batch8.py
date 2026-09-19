"""Source-scoped regression checks, not independent scientific validation."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def row(t,s):return read('catalog/results/r-'+t+'-'+s+'.json')
class BatchEightTests(unittest.TestCase):
 def setUp(self):self.tracks={t['id']:t for t in read('catalog/benchmarks.json')['tracks']}
 def test_real_domains_not_simpler_or_aloha_sim(self):
  for name in ['bridge-real-rtx-v9-iris','bridge-real-octo-v2-ablation','octo-real-v2-finetune']:
   t=self.tracks[name];self.assertNotIn(t['dataset'],['SimplerEnv','ALOHA-Sim']);self.assertEqual(t['comparisonScope'],'paper-table')
 def test_two_bridge_labs_remain_distinct(self):
  a=row('bridge-real-rtx-v9-iris','rt1');b=row('bridge-real-rtx-v9-rail','rt1')
  self.assertEqual(a['values']['Success'],40);self.assertEqual(b['values']['Success'],30);self.assertNotEqual(a['trackId'],b['trackId'])
 def test_rtx_negative_transfer_and_different_tests(self):
  r=row('google-real-rtx-v9-capacity','rt1');x=row('google-real-rtx-v9-capacity','rt2x55b')
  self.assertGreater(r['values']['Success'],x['values']['Success'])
  base=row('google-real-rtx-v9-emergent-generalization','rt2')['values'];mixed=row('google-real-rtx-v9-emergent-generalization','rt2x55b')['values']
  self.assertGreater(mixed['Emergent'],base['Emergent']);self.assertLess(mixed['Generalization'],base['Generalization']);self.assertNotIn('Average',mixed)
 def test_pretraining_cotraining_history_separated(self):
  t='google-real-rtx-v9-emergent-generalization';scratch=row(t,'5b-scratch');pre=row(t,'5b-no-co')
  self.assertEqual(scratch['values'],{'Emergent':0,'Generalization':1})
  self.assertIn('NO web co-train',scratch['trainingData']);self.assertIn('web-pretrained',pre['trainingData'])
  self.assertIn('2-frame history',pre['trainingData'])
 def test_octo_rtx_mix_is_not_original_rtx_policy(self):
  r=row('bridge-real-octo-v2-ablation','rtx-mix');self.assertEqual(r['paperId'],'p063');self.assertIn('Octo',r['method']);self.assertIn('不是RT-X模型',r['trainingData'])
 def test_octo_table_overlap_not_new_replications(self):
  audit=read('maintenance/benchmark-source-audit-20260919-batch8.json')
  self.assertEqual(len([x for x in audit['newResults'] if x.startswith('r-bridge-real-octo-v2-ablation-')]),6)
  self.assertFalse(any('-in-distribution-' in x or '-novel-object-' in x for x in audit['newResults']))
  self.assertIn('Table II',self.tracks['bridge-real-octo-v2-ablation']['protocol'])
 def test_original_rounding_and_trial_conflict_visible(self):
  t=self.tracks['octo-real-v2-finetune'];self.assertIn('20',t['protocol']);self.assertIn('10',t['protocol'])
  r=row(t['id'],'vc1');self.assertEqual(r['values']['Average'],15);self.assertIn('15.83',r['evaluationNotes'])
  self.assertEqual(row(t['id'],'octo')['values']['Average'],72)
 def test_novel_skill_zero_not_missing(self):
  r=row('bridge-real-octo-v2-novel-skill','octo-small');self.assertEqual(r['values']['BlockInSlot'],0);self.assertEqual(r['values']['Average'],5)
 def test_earliest_dates_not_formal_dates(self):
  for pid,first in [('p059','2023-10-13'),('p060','2023-11-02'),('p063','2024-05-20')]:
   r=read('catalog/papers/'+pid+'.json');self.assertEqual(r['paper']['firstPublished'],first);self.assertEqual(r['publication']['firstArxivAt'],first)
  b=read('catalog/bibliography.json')['entries'];self.assertNotIn('author',b['p059']['item']);self.assertEqual(len(b['p063']['item']['author']),18)
 def test_limited_recheck_does_not_certify_roboflamingo_notes(self):
  a=read('maintenance/benchmark-source-audit-20260919-batch8.json');self.assertEqual(a['publicationOnly'],['p060']);self.assertNotIn('p060',a['updatedPapers'])
  d=next(x for x in a['deferred'] if x.get('paperId')=='p060');self.assertEqual(d['status'],'full-text-access-pending');self.assertIn('15465717',d['reason'])
