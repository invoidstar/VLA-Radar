"""Original-source invariants for the limited batch5 backfill, not truth certification."""
import json
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_text())
class OriginalLiberoTests(unittest.TestCase):
 def setUp(self):self.tracks={x['id']:x for x in load('catalog/benchmarks.json')['tracks']}
 def test_no_duplicate_paper_identity_or_changed_first_public(self):
  self.assertEqual(load('catalog/papers/p057.json')['paper']['arxiv'],'2306.03310')
  self.assertEqual(load('catalog/papers/p057.json')['paper']['firstPublished'],'2023-06-05')
  self.assertEqual(load('catalog/papers/p064.json')['paper']['firstPublished'],'2024-06-13')
 def test_lifelong_units_and_directions(self):
  for m in ['fwt','nbt','auc']:
   t=self.tracks['libero-original-neurips23-'+m]
   self.assertEqual(t['unit'],'score')
   self.assertEqual(t['direction'],'lower' if m=='nbt' else 'higher')
   self.assertNotIn('Average',t['columns']);self.assertEqual(t['comparisonScope'],'paper-table')
 def test_original_table_overlap_is_not_an_extra_replication(self):
  for m in ['fwt','nbt','auc']:
   rows=list((R/'catalog/results').glob('r-libero-original-neurips23-'+m+'-*.json'))
   methods=[json.loads(x.read_text())['method'] for x in rows]
   self.assertEqual(len(methods),8);self.assertEqual(len(methods),len(set(methods)))
   self.assertFalse(any('MTL' in x for x in methods))
 def test_openvla_data_regeneration_and_budgets_stay_explicit(self):
  t=self.tracks['libero-openvla-v3-singleview-cleaned']
  for n in ['432','454','428','379']:self.assertIn(n,t['trainingRegime'])
  self.assertIn('r32',t['trainingRegime']);self.assertIn('1500',t['protocol'])
  self.assertIn('无手腕',t['protocol']);self.assertEqual(t['unit'],'percent')
 def test_methods_do_not_win_every_suite(self):
  stem='catalog/results/r-libero-openvla-v3-singleview-cleaned-'
  dp,octo,vla=[load(stem+x+'.json') for x in ['dp','octo','openvla']]
  self.assertGreater(dp['values']['Object'],vla['values']['Object'])
  self.assertGreater(octo['values']['Goal'],vla['values']['Goal'])
  self.assertEqual(vla['values']['Average'],76.5)
  self.assertTrue(all(x['paperId']=='p064' for x in [dp,octo,vla]))
 def test_seql_vs_packnet_tradeoff_is_preserved(self):
  def val(metric,method):return load('catalog/results/r-libero-original-neurips23-'+metric+'-'+method+'-resnet-t.json')['values']['Long']
  self.assertGreater(val('fwt','seql'),val('fwt','packnet'))
  self.assertGreater(val('nbt','seql'),val('nbt','packnet'))
  self.assertLess(val('auc','seql'),val('auc','packnet'))
 def test_full_scope_deep_notes_and_separate_bibliography(self):
  for pid in ['p057','p064']:
   r=load('catalog/papers/'+pid+'.json');n=r['note']
   self.assertGreaterEqual(len(n['sections']),9)
   self.assertGreaterEqual(sum(len(s['body']) for s in n['sections']),2500)
   self.assertEqual(n['benchmarkReview']['status'],'extracted')
   self.assertIn(pid,load('catalog/bibliography.json')['entries'])
  n=load('catalog/papers/p064.json')['note']
  self.assertIn('Figure 1',n['figures'][0]['title'])
  self.assertIn('仅SigLIP',''.join(s['body'] for s in n['sections']))
 def test_unread_libero_supplement_is_not_full_appendix_certification(self):
  r=load('catalog/papers/p057.json')
  self.assertIn('未展开',r['note']['version'])
  self.assertEqual(r['publication']['publishedAt'],'2023')
  self.assertIsNone(r['publication']['acceptedAt'])
  self.assertEqual(r['paper']['doi'],'10.52202/075280-1939')
