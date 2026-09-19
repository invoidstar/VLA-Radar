"""Guard source-scoped extraction and keep timing/protocol facts distinct."""
import json
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
def read(p): return json.loads((R/p).read_text())
class BatchTenTests(unittest.TestCase):
 def setUp(self):
  self.audit=read('maintenance/benchmark-source-audit-20260919-batch10.json')
  self.tracks={x['id']:x for x in read('catalog/benchmarks.json')['tracks']}
  self.rows=[read('catalog/results/'+i+'.json') for i in self.audit['newResults']]
  self.records={p:read('catalog/papers/'+p+'.json') for p in ['p047','p049']}
 def byid(self,suffix): return next(r for r in self.rows if r['id'].endswith(suffix))
 def test_existing_papers_deep_scope(self):
  self.assertEqual(self.audit['newPapers'],[])
  for rec in self.records.values():
   self.assertEqual(len(rec['note']['sections']),9)
   self.assertGreater(sum(len(s['body']) for s in rec['note']['sections']),3000)
   self.assertTrue(all(s['sources'] for s in rec['note']['sections']))
   self.assertEqual(rec['note']['benchmarkReview']['status'],'extracted')
 def test_exact_scopes_and_no_false_replication(self):
  self.assertEqual(len(self.rows),36);self.assertEqual(len(self.audit['newTracks']),9)
  self.assertEqual(sum(r['paperId']=='p047' for r in self.rows),24)
  self.assertTrue(all(self.tracks[r['trackId']]['comparisonScope']=='paper-table' for r in self.rows))
  self.assertFalse(any(r['attribution']=='independent-reproduction' for r in self.rows))
 def test_cliport_partial_score_and_four_budgets(self):
  for budget in [1,10,100,1000]:
   t=self.tracks[f'ravens-cliport-corl21-test-{budget}d']
   self.assertEqual(t['unit'],'score');self.assertEqual(len(t['columns']),18)
   self.assertNotIn('Average',t['columns']);self.assertIn('部分',t['protocol'])
   self.assertIn('200k',t['trainingRegime']);self.assertIn('600k',t['trainingRegime'])
 def test_cliport_null_not_zero(self):
  r=self.byid('test-1000d-multi-attr')
  self.assertIsNone(r['values']['PyramidSeen']);self.assertEqual(r['values']['PyramidUnseen'],79.8)
  self.assertEqual(r['values']['PilesUnseen'],59.8)
 def test_cliport_uses_test_not_validation(self):
  r=self.byid('test-1000d-single')
  self.assertEqual(r['values']['BlocksBowlUnseen'],25)
  self.assertEqual(r['values']['PilesUnseen'],75.2)
  self.assertNotEqual(r['values']['BlocksBowlUnseen'],48.3)
  self.assertEqual(self.byid('test-1000d-multi')['values']['PyramidUnseen'],22.2)
 def test_bcz_conditional_overall_and_zero(self):
  self.assertEqual(self.byid('heldout-1-language')['values']['Overall'],38)
  self.assertEqual(self.byid('heldout-4to5-language')['values']['Overall'],32)
  self.assertEqual(self.byid('heldout-4to5-video')['values']['Overall'],4)
  self.assertEqual(self.byid('heldout-4to5-language')['values']['WipeTraySponge'],0)
  self.assertEqual(self.byid('heldout-4to5-video')['values']['WipeTraySponge'],28)
 def test_bcz_declared_rows_not_invented_29th_task(self):
  rows=[r for r in self.rows if 'bcz-heldout' in r['id']]
  self.assertEqual(len(rows),3)
  self.assertTrue(all(len(r['values'])==29 for r in rows)) # 28 named tasks + Overall
  self.assertTrue(all('28' in r['evaluationNotes'] and '29' in r['evaluationNotes'] for r in rows))
  self.assertIn('24',self.records['p049']['paper']['findings']);self.assertIn('32%',self.records['p049']['paper']['findings'])
 def test_bcz_training_and_heldout_summary_not_duplicated(self):
  rr=[r for r in self.rows if 'bcz-train21' in r['id']]
  self.assertEqual([r['values']['Overall'] for r in rr],[42,40,24])
  self.assertEqual(len(rr),3);self.assertTrue(all('训练任务' in r['evaluationNotes'] for r in rr))
 def test_episode_control_and_adaptive_actions(self):
  self.assertEqual(self.byid('bcz-intervention-expert')['values'],{'OneTask':27,'EightTask':23})
  self.assertEqual(self.byid('bcz-intervention-mixture')['values'],{'OneTask':53,'EightTask':47})
  self.assertEqual(self.byid('bcz-bottle-ablation-no-adaptive')['values']['BottleInBowl'],3)
  text=' '.join(s['body'] for s in self.records['p049']['note']['sections'])
  self.assertIn('第一个动作',text);self.assertIn('10段',text);self.assertIn('一两次',text)
 def test_documented_first_public_correction_preserves_arxiv(self):
  r=self.records['p049'];self.assertEqual(r['paper']['firstPublished'],'2022-01-11')
  self.assertEqual(r['publication']['firstArxivAt'],'2022-02-04')
  self.assertEqual(read('catalog/first-public.json')['p049'],'2022-01-11')
  self.assertEqual(self.audit['firstPublicCorrections'][0]['before'],'2022-02-04')
  self.assertTrue(any(e['kind']=='first_public_correction' for e in r['publication']['history']))
  self.assertEqual(self.records['p047']['paper']['firstPublished'],'2021-09-24')
 def test_formal_complete_authors_and_resolved_candidate(self):
  b=read('catalog/bibliography.json')['entries']
  self.assertEqual(len(b['p049']['item']['author']),8);self.assertEqual(len(b['p047']['item']['author']),3)
  self.assertTrue(all(b[p]['item']['issued']['date-parts']==[[2022,1,11]] for p in self.records))
  self.assertFalse(any(c.get('paperId')=='p049' for c in read('maintenance/publication-candidates.json')['candidates']))
 def test_limits_stay_visible(self):
  self.assertEqual(len(self.audit['deferred']),2)
  self.assertEqual({c['paperId'] for c in self.audit['keyResultCorrections']},{'p049'})
  self.assertEqual(self.records['p049']['paper']['findings'],self.audit['keyResultCorrections'][0]['after'])
  for pid in self.records:self.assertTrue(self.records[pid]['paper']['hasCautionaryResult'])
if __name__=='__main__':unittest.main()
