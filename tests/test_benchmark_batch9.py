"""Regression for source-specific batch-nine boundaries, not scientific certification."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())
class BatchNineTests(unittest.TestCase):
 def setUp(self):
  self.a=load('maintenance/benchmark-source-audit-20260919-batch9.json')
  self.tracks={t['id']:t for t in load('catalog/benchmarks.json')['tracks']}
  self.rows=[load('catalog/results/'+r+'.json') for r in self.a['newResults']]
  self.records={p:load('catalog/papers/'+p+'.json') for p in ['p048','p050','p062']}
 def row(self,key): return next(r for r in self.rows if r['id']==key)
 def test_existing_id_and_first_dates(self):
  for p,dt in [('p048','2021-12-06'),('p050','2022-04-04'),('p062','2024-03-19')]:
   self.assertEqual(self.records[p]['paper']['firstPublished'],dt)
  self.assertEqual(self.a['newPapers'],[])
 def test_deep_source_scoped_notes(self):
  for r in self.records.values():
   n=r['note'];self.assertEqual(n['status'],'expanded');self.assertEqual(len(n['sections']),9)
   self.assertGreater(sum(len(s['body']) for s in n['sections']),2800)
   self.assertTrue(all(s['sources'] for s in n['sections']))
   self.assertEqual(n['benchmarkReview']['status'],'extracted')
 def test_calvin_single_vs_chain_and_splits(self):
  ts=[self.tracks[t] for t in self.a['newTracks'] if t.startswith('calvin-')]
  self.assertEqual(len(ts),6)
  for t in ts:
   self.assertEqual(t['dataset'],'CALVIN');self.assertEqual(t['unit'],'percent');self.assertNotIn('Average',t['columns'])
   self.assertEqual(len(t['columns']),1 if t['id'].endswith('mtlc') else 5)
 def test_calvin_reported_precision_not_counts(self):
  r=self.row('r-calvin-original-v4-d-d-chain-static');self.assertEqual(r['values']['Chain5'],.08)
  self.assertEqual(self.row('r-calvin-original-v4-abcd-d-chain-rgb-wrist')['values']['Chain3'],.17)
  self.assertEqual(self.row('r-calvin-original-v4-d-d-mtlc-rgb-tactile')['values']['MTLC'],54.2)
 def test_droid_budget_exception_is_not_release_size(self):
  for r in self.rows:
   if r['paperId']=='p062':
    self.assertIn('40k',r['trainingData']);self.assertIn('50k',r['trainingData']);self.assertIn('共享',r['trainingData'])
    self.assertIn('文字标签',r['evaluationNotes']);self.assertEqual(self.tracks[r['trackId']]['dataset'],'DROID (real)')
 def test_droid_ood_novel_negative_and_zero(self):
  d=self.row('r-droid-v2-real-figure8-ood-droid')['values'];o=self.row('r-droid-v2-real-figure8-ood-oxe')['values']
  self.assertEqual(d['ChipsNovel'],30);self.assertEqual(o['ChipsNovel'],60);self.assertEqual(o['LentilsDistractorsCamera'],0)
  self.assertEqual(len(d),8);self.assertEqual(d['Average'],53)
 def test_droid_diversity_no_duplicate_full_data(self):
  rs=[r for r in self.rows if 'figure10' in r['id']];self.assertEqual(len(rs),2)
  self.assertEqual([r['values']['Average'] for r in rs],[40,60]);self.assertTrue(all('7362' in r['trainingData'] for r in rs))
 def test_saycan_plan_execution_physical_and_no_duplicate(self):
  ts=[self.tracks[t] for t in self.a['newTracks'] if 'saycan' in t];self.assertEqual(len(ts),4)
  self.assertTrue(all(t['dataset']=='Google Robot (real)' and 'Mock不是仿真' in t['protocol'] for t in ts))
  self.assertEqual(self.row('r-google-real-saycan-v2-mock-plan-palm')['values']['Total'],84)
  self.assertEqual(self.row('r-google-real-saycan-v2-office-execute-palm')['values']['Total'],60)
  self.assertFalse(any('execute-no-vf' in r['id'] for r in self.rows))
 def test_saycan_single_family_counterexample_and_real_zero(self):
  palm=self.row('r-google-real-saycan-v2-mock-execute-palm')['values'];flan=self.row('r-google-real-saycan-v2-mock-execute-flan')['values']
  self.assertGreater(flan['Nouns'],palm['Nouns']);self.assertEqual(self.row('r-google-real-saycan-v2-mock-execute-bc-nl')['values']['Total'],0)
 def test_source_supported_key_result_corrections(self):
  self.assertEqual({c['paperId'] for c in self.a['keyResultCorrections']},{'p048','p050'})
  for c in self.a['keyResultCorrections']:
   self.assertNotEqual(c['before'],c['after']);self.assertTrue(c['source'].startswith('https://'));self.assertEqual(self.records[c['paperId']]['paper']['findings'],c['after'])
 def test_formal_authors_and_date_precision(self):
  b=load('catalog/bibliography.json')['entries']
  self.assertEqual(len(b['p062']['item']['author']),98);self.assertEqual(len(b['p050']['item']['author']),45)
  self.assertEqual(b['p050']['item']['author'][0]['family'],'ichter')
  self.assertEqual(self.records['p048']['publication']['acceptedAt'],'2022-05-22')
  self.assertEqual(self.records['p062']['publication']['publishedAt'],'2024-07')
 def test_result_scopes_and_claims(self):
  self.assertEqual(len(self.rows),42);self.assertEqual(len(self.a['newTracks']),13)
  self.assertTrue(all(self.tracks[r['trackId']]['comparisonScope']=='paper-table' for r in self.rows))
  self.assertEqual({r['paperId'] for r in self.rows},{'p048','p050','p062'})
  self.assertEqual(len([r for r in self.rows if r['paperId']=='p048']),24)
