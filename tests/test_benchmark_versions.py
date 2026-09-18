"""Stable dataset identity and observed protocol boundaries, not research certification."""
import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class BenchmarkVersionTests(unittest.TestCase):
 def setUp(self):
  self.tracks={t['id']:t for t in json.loads((ROOT/'catalog/benchmarks.json').read_text())['tracks']}
 def test_robocasa365_is_separate_family(self):
  for tid,t in self.tracks.items():
   if tid.startswith('robocasa365-'):self.assertEqual(t['dataset'],'RoboCasa365',tid)
   elif tid.startswith(('robocasa24-','robocasa-original-')):self.assertEqual(t['dataset'],'RoboCasa',tid)
 def test_official_horizon_versions_are_separate(self):
  for tid,version in [('robocasa365-official-100','1.0.0'),('robocasa365-official-101','1.0.1')]:
   self.assertIn(version,self.tracks[tid]['version']);self.assertEqual(self.tracks[tid]['comparisonScope'],'paper-table')
 def test_original_xiaomi_track_id_preserved(self):
  self.assertIn('robocasa365-xiaomi-50tasks',self.tracks)
 def test_official_aggregate_declares_weighting(self):
  for p in (ROOT/'catalog/results').glob('r-robocasa365-official-*.json'):
   r=json.loads(p.read_text());v=r['values'];expected=round((18*v['Atomic']+16*v['Seen composite']+16*v['Unseen composite'])/50,1)
   self.assertAlmostEqual(v['Average'],expected,places=1);self.assertIn('18/16/16',r['evaluationNotes'])
 def test_robotwin_checkpoint_settings_not_combined(self):
  a=self.tracks['robotwin2-official-2500clean-cotrain'];b=self.tracks['robotwin2-official-2500clean-sft']
  self.assertNotEqual(a['split'],b['split']);self.assertEqual(a['dataset'],b['dataset'])
 def test_robodojo_score_not_percent(self):
  for tid,t in self.tracks.items():
   if tid.startswith(('robodojo-official-sim-','robodojo-real-xpolicylab-v3-')):
    self.assertEqual(t['unit'],'score' if tid.endswith('-score') else 'percent')
