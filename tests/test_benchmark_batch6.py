"""Regression guards for reviewed historical evidence, not scientific certification."""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))
class BatchSixTests(unittest.TestCase):
    def setUp(self):
        self.tracks = {x['id']:x for x in read('catalog/benchmarks.json')['tracks']}
    def test_distinct_original_mvp_identity(self):
        p = read('catalog/papers/p097.json')
        self.assertEqual(p['paper']['arxiv'], '2203.06173')
        self.assertEqual(p['paper']['title'], 'Masked Visual Pre-training for Motor Control')
        self.assertIn('ViT-S', ''.join(s['body'] for s in p['note']['sections']))
    def test_mvp_cited_variant_keeps_reporting_paper(self):
        r = read('catalog/results/r-kitchen-r3m-snapshot-aggregate-mvp-vitb-egosoup.json')
        self.assertEqual(r['paperId'], 'p096')
        self.assertIn('ViT-B', r['method'])
        self.assertIn('Ego-Soup', r['method'])
        self.assertEqual(r['values']['Average'], 27.0)
    def test_r3m_duplicate_table_value_not_double_counted(self):
        rows = [read(p.relative_to(ROOT)) for p in (ROOT/'catalog/results').glob('r-kitchen-r3m-snapshot-aggregate-*.json')]
        self.assertEqual(sum(r['method']=='R3M' for r in rows), 1)
        r = next(r for r in rows if r['method']=='R3M')
        self.assertEqual(r['values']['Average'], 53.1)
    def test_r3m_multi_configuration_aggregate_is_not_fair_rank(self):
        t = self.tracks['metaworld-r3m-snapshot-aggregate']
        self.assertEqual(t['comparisonScope'], 'paper-table')
        self.assertIn('5/10/25', t['protocol'])
        self.assertIn('单视角输入', t['protocol'])
    def test_metaworld_train_test_stay_separate(self):
        a=self.tracks['metaworld-v2-original-ml45-meta-train']
        b=self.tracks['metaworld-v2-original-ml45-meta-test']
        self.assertEqual(a['tasks'], '45');self.assertEqual(b['tasks'], '5')
        self.assertNotEqual(a['split'], b['split'])
        self.assertEqual(a['comparisonScope'], 'paper-table')
    def test_metaworld_original_table_conflict_is_visible(self):
        p=read('catalog/papers/p098.json')
        text=''.join(s['body'] for s in p['note']['sections'])
        self.assertIn('38.5', text);self.assertIn('35.4', text);self.assertIn('冲突', text)
        r=read('catalog/results/r-metaworld-v2-original-mt50-sac.json')
        self.assertEqual(r['values']['Average'],38.5)
        self.assertIn('average maximum success rate', r['evaluationNotes'])
    def test_earliest_dates_not_replaced_by_publication_year(self):
        p=read('catalog/papers/p098.json')
        self.assertEqual(p['paper']['firstPublished'],'2019-10-24')
        self.assertEqual(p['publication']['publishedAt'],'2020')
        r=read('catalog/papers/p096.json')
        self.assertEqual(r['paper']['firstPublished'],'2022-03-23')
        self.assertEqual(r['publication']['publishedAt'],'2023')
    def test_reading_scope_and_unsupported_curves_remain_documented(self):
        audit=read('maintenance/benchmark-source-audit-20260919-batch6.json')
        m=next(x for x in audit['deferred'] if x.get('paperId')=='p097')
        self.assertEqual(m['status'],'exact-numeric-results-pending')
        self.assertEqual(audit['counts']['newResultCount'],30)
        self.assertTrue(any('未明示' in x['scope'] for x in audit['readSources'] if x['paperId']=='p096'))
if __name__=='__main__':unittest.main()
