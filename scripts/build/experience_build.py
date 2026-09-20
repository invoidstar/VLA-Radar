"""Derived public reading tools: separate, content-addressed coverage and event streams."""
from __future__ import annotations
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import hashlib,json,re
from pathlib import Path

def text(obj):return json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n'
def digest(obj):return hashlib.sha256(text(obj).encode()).hexdigest()[:16]
def outputs(root,records,tracks,results):
 out={}
 def shard(name,obj):
  path='data/experience/'+name+'.'+digest(obj)+'.json';out[path]=text(obj);return path
 papers={r['paper']['id']:r for r in records};trackmap={t['id']:t for t in tracks}
 replaced={r['supersedes'] for r in results if r['evidence']=='checked' and r['supersedes']}
 checked=[r for r in results if r['evidence']=='checked' and r['id'] not in replaced]
 datasets=sorted({t['dataset'] for t in tracks});cells={}
 for row in checked:
  pid=row['paperId'];dataset=trackmap[row['trackId']]['dataset']
  for topic in papers[pid]['paper']['topics']:
   c=cells.setdefault((topic,dataset),{'paperIds':set(),'resultIds':[]});c['paperIds'].add(pid);c['resultIds'].append(row['id'])
 ledger=json.loads((root/'maintenance/state/benchmark-review.json').read_text())['papers']
 counts={k:sum(v['status']==k for v in ledger.values()) for k in ['extracted','deferred','not-applicable']}
 coverage={'schemaVersion':1,'datasets':datasets,'cells':[{'topic':t,'dataset':d,'paperIds':sorted(c['paperIds']),'resultCount':len(c['resultIds'])} for (t,d),c in sorted(cells.items())], 'paperCount':len(papers),'activeResultCount':len(checked),'dispositions':counts,'scope':'Only checked, non-superseded results attributed to their reporting paper topics. Topic intersections overlap. Deferred mappings are not guessed.'}
 coverageurl=shard('coverage',coverage)
 events=[]
 for pid,r in papers.items():
  p,n,pub=r['paper'],r['note'],r['publication']
  events.append({'id':'note-snapshot-'+pid+'-'+digest(n),'kind':'note','paperId':pid,'title':p['name']+' · 现存笔记快照','date':n['updatedAt'],'observedAt':None,'mode':'snapshot','summary':str(len(n['sections']))+' 节 · '+n['version'],'source':p['paperUrl'],'changes':[]})
  for e in pub['history']:
   if e['kind'] not in ['arxiv_version','accepted','published','withdrawn']:continue
   if e['kind']=='arxiv_version' and (re.search(r'\bv1\b',e.get('note','')) or e.get('source','').endswith('v1')):continue
   kind='revision' if e['kind']=='arxiv_version' else 'publication'
   events.append({'id':'life-'+pid+'-'+digest(e),'kind':kind,'paperId':pid,'title':p['name']+' · '+{'revision':'版本记录','publication':'发表状态记录'}[kind],'date':e['date'],'observedAt':e['observedAt'],'mode':'record','summary':e['note'],'source':e['source'],'changes':[]})
 bypaper={}
 for row in checked:bypaper.setdefault((row['paperId'],row['verifiedAt']),[]).append(row)
 for (pid,date),rows in bypaper.items():
  events.append({'id':'result-snapshot-'+pid+'-'+digest(rows),'kind':'result','paperId':pid,'title':papers[pid]['paper']['name']+' · 评测核验快照','date':date,'observedAt':None,'mode':'snapshot','summary':str(len(rows))+' 条当前结果；不等同于新入榜日期。','source':rows[0]['source'],'changes':[]})
 logpath=root/'catalog/activity.json'
 if logpath.exists():
  log=json.loads(logpath.read_text());assert log['schemaVersion']==1
  for e in log['events']:
   assert e['kind'] in ['collected','revision','publication','note','result','site']
   assert e.get('paperId') is None or e['paperId'] in papers
   assert e['id'] and e.get('observedAt') and e['title']
  events.extend(log['events'])
 assert len({e['id'] for e in events})==len(events),'Duplicate activity IDs'
 events.sort(key=lambda e: (e.get('observedAt') or e.get('date') or '',e['id']),reverse=True)
 streams={}
 for kind in ['all','collected','revision','publication','note','result','site']:
  subset=events if kind=='all' else [e for e in events if e['kind']==kind]
  streams[kind]=[{'url':shard('events-'+kind+'-'+str(i//50),{'schemaVersion':1,'events':subset[i:i+50]}),'count':len(subset[i:i+50])} for i in range(0,len(subset),50)]
 eventurl=shard('updates',{'schemaVersion':1,'count':len(events),'streams':streams,'note':'Snapshots do not establish historical collection or change dates; visit comparisons include dated observations only.'})
 indexurl=shard('index',{'schemaVersion':1,'coverageUrl':coverageurl,'updatesUrl':eventurl})
 return out,indexurl
