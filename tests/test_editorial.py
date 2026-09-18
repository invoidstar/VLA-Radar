"""Regression tests use synthetic edits; they do not certify paper claims."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from catalog_core import load,read_catalog
from check_editorial import check

class EditorialTests(unittest.TestCase):
    def setUp(self):
        _,records,_,self.results=read_catalog(ROOT)
        self.records=copy.deepcopy(records)
        self.policy=load(ROOT/'maintenance/editorial-policy.json')
        self.ledger=load(ROOT/'maintenance/benchmark-review.json')
        self.full=next(r for r in self.records if r['note']['coverage']['level']=='deep')
    def run_check(self):return check(self.records,self.policy,self.ledger,self.results)
    def test_entire_library_passes(self):self.assertTrue(self.run_check())
    def test_seven_sections_rejected(self):
        self.full['note']['sections']=self.full['note']['sections'][:7]
        with self.assertRaises(ValueError):self.run_check()
    def test_short_sections_rejected(self):
        self.full['note']['sections'][0]['body']='too short'
        with self.assertRaises(ValueError):self.run_check()
    def test_uncited_section_rejected(self):
        self.full['note']['sections'][0]['sources']=[]
        with self.assertRaises(ValueError):self.run_check()
    def test_shallow_eight_sections_rejected(self):
        for section in self.full['note']['sections']:section['body']='x'*91
        with self.assertRaises(ValueError):self.run_check()
    def test_missing_disposition_rejected(self):
        self.full['note'].pop('benchmarkReview')
        with self.assertRaises(ValueError):self.run_check()
    def test_nonexistent_result_rejected(self):
        pid=next(k for k,v in self.ledger['papers'].items() if v['status']=='extracted')
        self.ledger['papers'][pid]['resultIds']=['r-not-existing']
        with self.assertRaises(ValueError):self.run_check()
    def test_missing_paper_ledger_rejected(self):
        self.ledger['papers'].pop(self.full['paper']['id'])
        with self.assertRaises(ValueError):self.run_check()
    def test_partial_source_cannot_be_deep(self):
        partial=next(r for r in self.records if r['note']['coverage']['level']=='limited')
        partial['note']['coverage']['level']='deep'
        with self.assertRaises(ValueError):self.run_check()
    def test_partial_guide_must_be_visibly_incomplete(self):
        partial=next(r for r in self.records if r['note']['coverage']['level']=='limited')
        partial['note']['status']='expanded'
        with self.assertRaises(ValueError):self.run_check()
    def test_new_abstract_cannot_use_legacy_exemption(self):
        partial=next(r for r in self.records if r['note']['coverage']['level']=='limited')
        self.policy['baselinePaperIds'].remove(partial['paper']['id'])
        with self.assertRaises(ValueError):self.run_check()
    def test_new_paper_has_higher_depth_requirement(self):
        pid=self.full['paper']['id'];self.policy['baselinePaperIds'].remove(pid)
        for section in self.full['note']['sections']:section['body']='x'*190
        with self.assertRaises(ValueError):self.run_check()
    def test_valid_new_deep_record_is_supported(self):
        pid=self.full['paper']['id'];self.policy['baselinePaperIds'].remove(pid)
        # Deliberately synthetic fixture text, never written to the public catalog.
        for section in self.full['note']['sections']:section['body']='fixture '*40
        self.assertTrue(self.run_check())

if __name__=='__main__':unittest.main()
