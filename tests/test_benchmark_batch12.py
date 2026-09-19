"""Protect source/version/metric boundaries; not independent scientific replication."""
import json
import unittest
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text())
class BatchTwelveTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.a=read('maintenance/benchmark-source-audit-20260919-batch12.json')
  cls.t={t['id']:t for t in read('catalog/benchmarks.json')['tracks']}
  cls.r={i:read('catalog/results/'+i+'.json') for i in cls.a['newResults']}
  cls.p={p:read('catalog/papers/'+p+'.json') for p in cls.a['papers']}
 def row(self,i):return self.r['r-'+i]
 def text(self,p):return '\n'.join(s['body'] for s in self.p[p]['note']['sections'])
 def test_batch_is_five_existing_papers(self):
  self.assertEqual(set(self.p),{'p041','p042','p027','p028','p029'})
  self.assertEqual(self.a['newPapers'],[])
  self.assertEqual(len(self.r),161);self.assertEqual(len(self.a['newTracks']),40)
  self.assertEqual(Counter(r['paperId'] for r in self.r.values()),{'p041':20,'p042':14,'p027':38,'p028':66,'p029':23})
 def test_deep_notes_and_citations(self):
  for p in self.p:
   n=self.p[p]['note'];self.assertEqual(len(n['sections']),9)
   self.assertGreater(len(self.text(p)),2400)
   self.assertTrue(all(s['sources'] for s in n['sections']))
   self.assertGreaterEqual(len(n['figures']),2);self.assertTrue(n['tables'])
   self.assertEqual(n['benchmarkReview']['status'],'extracted')
 def test_no_fairness_or_replication_inflation(self):
  for r in self.r.values():
   self.assertEqual(self.t[r['trackId']]['comparisonScope'],'paper-table')
   self.assertIn(r['attribution'],['author-reported','reported-baseline'])
   self.assertEqual(r['evidence'],'checked');self.assertTrue(r['locator'])
   self.assertEqual(set(r['values']),set(self.t[r['trackId']]['columns']))
 def test_source_versions_are_explicit(self):
  ver={'p041':'2602.12978v2','p042':'2604.05323v1','p027':'2607.27205v2','p028':'2607.06370v2','p029':'2608.27384v1'}
  for r in self.r.values():self.assertIn(ver[r['paperId']],r['source'])
  self.assertIn('v2',self.p['p028']['note']['version'])
  self.assertIn('v2',self.p['p041']['note']['version'])
 def test_review_cross_references(self):
  d=read('maintenance/benchmark-review.json')['papers']
  for p in self.p:
   self.assertEqual(d[p]['status'],'extracted')
   self.assertEqual(set(d[p]['resultIds']),{i for i,r in self.r.items() if r['paperId']==p})
   self.assertEqual(set(d[p]['trackIds']),{r['trackId'] for r in self.r.values() if r['paperId']==p})
 def test_legato_score_is_not_sr(self):
  self.assertEqual(self.t['legato-v2-main-score']['unit'],'score')
  self.assertEqual(self.row('legato-v2-main-score-legato')['values']['Pour'],9.72)
  self.assertEqual(self.row('legato-v2-main-time-legato')['values']['Pour'],75.73)
  self.assertEqual(self.t['legato-v2-main-time']['unit'],'seconds')
 def test_legato_smoothness_units_and_errors(self):
  for s in ['nldlj','nsparc','rmse']:
   self.assertEqual(self.t['legato-v2-main-'+s]['unit'],'score')
   self.assertEqual(self.t['legato-v2-main-'+s]['direction'],'lower')
  self.assertEqual(self.row('legato-v2-main-rmse-legato')['values']['PickPlace'],5.98)
  self.assertIn('standard error',self.row('legato-v2-main-nldlj-legato')['evaluationNotes'])
  self.assertIn('排除',self.t['legato-v2-main-nldlj']['protocol']+self.row('legato-v2-main-nldlj-legato')['evaluationNotes'])
 def test_legato_missing_columns_and_repeated_rows(self):
  for typ in ['training-rtc','one-shot']:
   r=self.row('legato-v2-main-time-'+typ)
   self.assertIsNone(r['values']['Bowls']);self.assertIsNone(r['values']['Drawer'])
  self.assertEqual(len([r for r in self.r.values() if r['trackId']=='legato-v2-main-time']),4)
 def test_legato_later_cohort_and_unstable_not_zero(self):
  self.assertIsNone(self.row('legato-v2-later-n-sensitivity-with-cond')['values']['N1'])
  self.assertEqual(self.row('legato-v2-later-n-sensitivity-no-cond')['values']['N1'],1.98)
  self.assertIn('后续',self.t['legato-v2-later-n-sensitivity']['split'])
 def test_infoentropy_undefined_latency_never_seconds(self):
  ts=[self.t[r['trackId']] for r in self.r.values() if r['paperId']=='p042']
  self.assertTrue(all(t['unit']=='percent' for t in ts))
  tx=self.text('p042');self.assertIn('1.214',tx);self.assertIn('1.205',tx);self.assertIn('3.100',tx)
 def test_infoentropy_negative_long_and_ablations(self):
  self.assertEqual(self.row('libero-infoentropy-v1-100-openvla')['values']['Long'],53.2)
  self.assertEqual(self.row('libero-infoentropy-v1-100-ours')['values']['Long'],52.2)
  self.assertEqual(self.row('libero-infoentropy-v1-100-visual')['values']['Average'],69.8)
  self.assertEqual(self.row('libero-infoentropy-v1-100-static')['values']['Average'],75.8)
 def test_infoentropy_budget_and_dedup(self):
  self.assertEqual(len([r for r in self.r.values() if r['trackId']=='libero-infoentropy-v1-100']),10)
  self.assertEqual(self.row('libero-infoentropy-v1-budget120-ours')['values'],{'Average':75.4})
  self.assertEqual(self.row('libero-infoentropy-v1-budget140-ours')['values'],{'Average':76.8})
  self.assertIn('并集',self.text('p042'));self.assertIn('取整',self.text('p042'))
 def test_infoentropy_missing_appendix_and_correct_figure(self):
  self.assertIn('没有该附录',self.text('p042'))
  self.assertTrue(self.p['p042']['note']['figures'][1]['url'].endswith('#page=4'))
 def test_turbo_text_encoder_not_vision_replacement(self):
  self.assertEqual(self.row('libero-turbovla-v2-siglip')['method'],'SigLIP-Base instruction encoder')
  self.assertEqual(self.row('libero-turbovla-v2-t5')['method'],'T5-Base instruction encoder')
  self.assertIn('不是把DINOv3',self.text('p027'))
 def test_turbo_clean_multitask_per_task_separate(self):
  ids=['robotwin2-turbovla-v2-clean-per-task','robotwin2-turbovla-v2-clean-multi-task']
  self.assertEqual([len([r for r in self.r.values() if r['trackId']==i]) for i in ids],[7,4])
  self.assertEqual(self.row(ids[1]+'-ours')['values']['Average'],60.2)
  self.assertIn('clean',self.t[ids[1]]['trainingRegime'])
 def test_turbo_ablations_full_row_deduplicated(self):
  self.assertEqual(len([r for r in self.r.values() if r['trackId']=='libero-turbovla-v2']),27)
  self.assertEqual(self.row('libero-turbovla-v2-no-language')['values']['Goal'],11.6)
  self.assertEqual(self.row('libero-turbovla-v2-depth8')['values']['Average'],96.6)
  self.assertEqual(self.row('libero-turbovla-v2-ours')['values']['Average'],97.7)
 def test_actioncache_latest_v2_and_head_units(self):
  self.assertEqual(self.row('vlabench-actioncache-v2-pi05-cache-zero')['values']['Average'],40.9)
  self.assertEqual(self.row('vlabench-actioncache-v2-gr00t-head-cache-zero')['values']['Average'],0.0006)
  self.assertEqual(self.row('vlabench-actioncache-v2-pi05-head-base-full')['values']['Average'],0.0188)
  self.assertEqual(self.t['vlabench-actioncache-v2-pi05-head']['unit'],'seconds')
 def test_actioncache_zero_step_not_lossless(self):
  self.assertEqual(self.row('libero-actioncache-v2-pi05-cache-zero')['values']['Long'],83.4)
  self.assertEqual(self.row('libero-actioncache-v2-pi05-base-one')['values']['Average'],96.9)
  self.assertLess(self.row('libero-actioncache-v2-pi05-head-base-one')['values']['Average'],self.row('libero-actioncache-v2-pi05-head-cache-zero')['values']['Average'])
 def test_actioncache_realtime_training_budget(self):
  self.assertIn('100成功+50恢复',self.t['actioncache-v2-real-sausage']['trainingRegime'])
  self.assertIn('C=1000',self.t['actioncache-v2-real-sausage']['protocol'])
  self.assertIn('C=300',self.t['actioncache-v2-real-button']['protocol'])
 def test_actioncache_real_success_and_latency_distinct(self):
  self.assertEqual(self.row('actioncache-v2-real-sausage-base')['values']['Success'],90)
  self.assertEqual(self.row('actioncache-v2-real-sausage-cache')['values']['Success'],88)
  self.assertEqual(self.row('actioncache-v2-real-button-latency-cache')['values'],{'ActionHead':0.00953,'Overall':0.05646})
 def test_actioncache_combination_not_additive(self):
  self.assertEqual(self.row('vlabench-actioncache-v2-combination-actioncache')['values']['Average'],41.2)
  self.assertEqual(self.row('vlabench-actioncache-v2-combination-both')['values']['Average'],39.1)
  self.assertEqual(self.row('vlabench-actioncache-v2-combination-latency-both')['values']['Overall'],0.057)
  self.assertIn('三任务',self.t['vlabench-actioncache-v2-combination']['protocol'])
 def test_flash_distinct_async_delays(self):
  self.assertEqual(self.row('libero-flashvla-v1-pi05-d0-flash')['values']['Average'],97.9)
  self.assertEqual(self.row('libero-flashvla-v1-pi05-d1-flash')['values']['Average'],97.8)
  self.assertEqual(self.row('libero-flashvla-v1-pi05-d4-vlash')['values']['Average'],93.1)
 def test_flash_robotwin_training_mixture_is_not_turbo(self):
  self.assertIn('clean与random示范并集',self.t['robotwin2-flashvla-v1-pi05-all']['trainingRegime'])
  self.assertEqual(self.row('robotwin2-flashvla-v1-pi05-all-flash')['values'],{'Clean':90.8,'Random':90.2,'Average':90.5})
 def test_flash_short_task_and_smol_negative_results(self):
  self.assertEqual(self.row('robotwin2-flashvla-v1-pi05-short-flash')['values']['Average'],93.2)
  self.assertEqual(self.row('robotwin2-flashvla-v1-pi05-short-base')['values']['Average'],93.9)
  self.assertEqual(self.row('libero-flashvla-v1-smol-d1-flash')['values']['Average'],79.5)
  self.assertIn('None',self.row('libero-flashvla-v1-smol-d1-flash')['evaluationNotes'])
 def test_flash_latency_different_hardware_not_averaged(self):
  r=self.row('flashvla-v1-inference-latency-flash')
  self.assertEqual(r['values'],{'RTX4090_2views':0.0267,'RTX4090_3views':0.0368,'RTX5090_2views':0.0203,'RTX5090_3views':0.0271})
  self.assertNotIn('Average',r['values']);self.assertEqual(self.t[r['trackId']]['unit'],'seconds')
 def test_public_audit_original_evidence_preserved(self):
  a=self.a['preservationAudit'];self.assertEqual(a['originalResults'],507)
  self.assertEqual(a['originalTracks'],138);self.assertEqual(a['unchangedNonTargetPapers'],93)
  self.assertTrue(a['keyResultAndPublicationObjectsUnchanged'])
  self.assertGreater(a['unchangedCanonicalAndCodeFiles'],600)
  self.assertEqual(self.a['baseCommit'],'ccb22c7b78de0326660cbb5ba91301ac6ab8c228')
if __name__=='__main__':unittest.main()
