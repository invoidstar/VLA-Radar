"""Synthetic changes only: these tests cannot verify scientific/news claims."""
import copy,json,sys,unittest
from pathlib import Path
from datetime import date,timedelta
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from news_core import validate,outputs,week_key,week_start
class NewsTests(unittest.TestCase):
 def setUp(self):
  self.records=[json.loads(p.read_text()) for p in sorted((ROOT/'catalog/news').glob('*.json'))]
  self.paperids={p.stem for p in (ROOT/'catalog/papers').glob('*.json')}
  self.state=json.loads((ROOT/'maintenance/news-state.json').read_text());self.today=date.fromisoformat(self.state['asOf'])
 def runcheck(self):return validate(self.records,self.paperids,self.state,self.today)
 def fails(self):
  with self.assertRaises(ValueError):self.runcheck()
 def test_actual_records_pass(self):self.assertTrue(self.runcheck())
 def test_duplicate_event(self):self.records.append(copy.deepcopy(self.records[0]));self.fails()
 def test_duplicate_canonical(self):self.records[1]['sources'][0]['url']=self.records[0]['sources'][0]['url']+'#another';self.fails()
 def test_private_source(self):self.records[0]['sources'][0]['url']='https://127.0.0.1/admin';self.fails()
 def test_script_url(self):self.records[0]['sources'][0]['url']='javascript:alert(1)';self.fails()
 def test_unverified_candidate(self):self.records[0]['status']='candidate';self.fails()
 def test_future_event(self):self.records[0]['eventDate']=(self.today+timedelta(days=15)).isoformat();self.fails()
 def test_invalid_day(self):self.records[0]['eventDate']='2026-02-31';self.fails()
 def test_no_date(self):self.records[0]['eventDate']=self.records[0]['publishedAt']=None;self.fails()
 def test_unknown_paper(self):self.records[0]['paperLinks']=[{'paperId':'p999999','relation':'direct','note':'Not in catalog: reject this.'}];self.fails()
 def test_official_requires_primary(self):self.records[0]['evidence']='official';[s.update(kind='media') for s in self.records[0]['sources']];self.fails()
 def test_paper_backed_requires_full_read(self):self.records[0]['evidence']='paper-backed';self.fails()
 def test_correction_must_retain_history(self):self.records[0]['status']='corrected';self.fails()
 def test_partial_does_not_claim_success(self):self.state['lastSuccessfulSearchAt']=self.state['asOf'];self.fails()
 def test_future_checkpoint(self):self.state['asOf']=(self.today+timedelta(days=15)).isoformat();self.fails()
 def test_no_hype_without_limits(self):self.records[0]['limits']='';self.fails()
 def test_unknown_category(self):self.records[0]['primaryCategory']='misc';self.fails()
 def test_observed_after_source(self):self.records[0]['observedAt']='2025-01-01';self.fails()
 def test_iso_week(self):self.assertEqual(week_key('2021-01-01'),'2020-W53')
 def test_invalid_week(self):
  with self.assertRaises(ValueError):week_start('2026-W54')
 def test_unknown_week_not_zero(self):
  papers=[json.loads(p.read_text()) for p in (ROOT/'catalog/papers').glob('*.json')];out,index=outputs(ROOT,papers);m=json.loads(out[index]);self.assertTrue(all(x['status']!='not_run' or x['count'] is None for x in m['trend']))
 def test_deterministic_shards(self):
  papers=[json.loads(p.read_text()) for p in (ROOT/'catalog/papers').glob('*.json')];self.assertEqual(outputs(ROOT,papers),outputs(ROOT,papers))
if __name__=='__main__':unittest.main()
