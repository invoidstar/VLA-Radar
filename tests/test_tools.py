import copy,json,sys,tempfile,unittest
from pathlib import Path
from scripts.build.tools_build import outputs,bibliography
from scripts.build.catalog_core import read_catalog
from scripts.build.experience_build import outputs as experience
ROOT=Path(__file__).resolve().parents[1]
class ToolBuildTests(unittest.TestCase):
 def setUp(self):
  self.m,self.rs,self.ts,self.rr=read_catalog(ROOT)
 def test_deterministic(self):
  ex,ix=experience(ROOT,self.rs,self.ts,self.rr)
  a,ai=outputs(ROOT,self.rs,self.ts,self.rr,ex,ix);b,bi=outputs(ROOT,self.rs,self.ts,self.rr,ex,ix)
  self.assertEqual((a,ai),(b,bi));self.assertNotIn('seenAt',json.dumps(a));self.assertLess(len(a[ai].encode()),120000)
 def test_snapshot_exclusion(self):
  ex,ix=experience(ROOT,self.rs,self.ts,self.rr);a,ai=outputs(ROOT,self.rs,self.ts,self.rr,ex,ix)
  for part in json.loads(a[ai])['events']:
   for e in json.loads(a[part['url']])['items']:
    self.assertNotEqual(e['mode'],'snapshot');self.assertTrue(e['observedAt'])
 def test_authors_require_verified_source(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);(r/'catalog').mkdir();p=self.rs[0]['paper']
   obj={'schemaVersion':1,'entries':{p['id']:{'item':{'type':'article','title':p['title'],'author':[{'literal':'Example Team'}]},'sources':[],'verifiedAt':'2026-09-18'}}}
   (r/'catalog/bibliography.json').write_text(json.dumps(obj))
   with self.assertRaises(AssertionError):bibliography(r,{p['id']:self.rs[0]})
 def test_wrong_title_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);(r/'catalog').mkdir();p=self.rs[0]['paper'];obj={'schemaVersion':1,'entries':{p['id']:{'item':{'type':'article','title':'Wrong'},'sources':[{'url':'https://arxiv.org/abs/2608.27550','label':'primary'}],'verifiedAt':'2026-09-18'}}}
   (r/'catalog/bibliography.json').write_text(json.dumps(obj))
   with self.assertRaises(AssertionError):bibliography(r,{p['id']:self.rs[0]})
