import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/build'))
from catalog_core import read_catalog
from benchmark_taxonomy import load_taxonomy

class BenchmarkTaxonomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.tracks,_=read_catalog(ROOT)
        cls.tax=load_taxonomy(ROOT,cls.tracks)

    def test_exact_dataset_coverage(self):
        self.assertEqual(set(self.tax['benchmarks']),{t['dataset'] for t in self.tracks})
        self.assertGreaterEqual(len(self.tax['benchmarks']),61)

    def test_all_focuses_are_used(self):
        used={x['focus'] for x in self.tax['benchmarks'].values()}
        self.assertEqual(used,{x['id'] for x in self.tax['focuses']})

    def test_all_environments_are_used(self):
        used={x['environment'] for x in self.tax['benchmarks'].values()}
        self.assertEqual(used,{x['id'] for x in self.tax['environments']})

    def test_key_examples(self):
        b=self.tax['benchmarks']
        self.assertEqual(b['RoboTwin']['focus'],'general-manipulation')
        self.assertEqual(b['CALVIN']['focus'],'long-horizon-memory')
        self.assertEqual(b['SimplerEnv']['focus'],'generalization-robustness')
        self.assertEqual(b['VLA-Touch (real)']['focus'],'dexterous-contact')
        self.assertEqual(b['Google Robot (real)']['focus'],'language-planning-compositionality')
        self.assertEqual(b['ActionCache (real)']['focus'],'efficiency-deployment')
        self.assertEqual(b['RoboFollow']['focus'],'language-planning-compositionality')
        self.assertEqual(b['RoboTwin-Phys']['focus'],'generalization-robustness')
        self.assertEqual(b['LIBERO-PRO']['focus'],'generalization-robustness')
        self.assertEqual(b['RMBench']['focus'],'long-horizon-memory')
        self.assertEqual(b['RoboTwin']['environment'],'simulation')
        self.assertEqual(b['RoboDojo real']['environment'],'real')
        self.assertEqual(b['SimplerEnv']['environment'],'mixed')

    def test_tags_are_benchmark_level_and_nonduplicated(self):
        for name,item in self.tax['benchmarks'].items():
            self.assertEqual(len(item['tags']),len(set(item['tags'])),name)

if __name__=='__main__':
    unittest.main()
