"""Capture actual public-content deltas before committing, never invent historical dates.
Usage: python scripts/maintenance/capture_activity.py --base <verified-main-sha> [--at UTC-ISO]
Only the activity log is written; metadata, note verification and discovery remain untouched.
"""
from __future__ import annotations
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import argparse,hashlib,json,subprocess,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REPO='https://github.com/invoidstar/VLA-Radar'
def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:20]
def read_prior(root,base,path):
 r=subprocess.run(['git','show',base+':'+path],cwd=root,text=True,capture_output=True)
 if r.returncode:
  known=subprocess.run(['git','cat-file','-e',base],cwd=root,capture_output=True)
  if known.returncode:raise ValueError('Unknown base commit')
  return None
 return json.loads(r.stdout)
def display(v):
 s=v if isinstance(v,str) else json.dumps(v,ensure_ascii=False,sort_keys=True)
 return s if len(s)<=900 else s[:900]+'… [摘录；完整记录见来源]'
def changes(old,new):
 return [{'field':k,'before':display(old.get(k)),'after':display(new.get(k))} for k in sorted(set(old)|set(new)) if old.get(k)!=new.get(k)]
def note_fields(note):
 # Keep changed chapters separate so later edits are not hidden behind a long common prefix.
 result={k:note.get(k) for k in ['version','verifiedAt','coverage','tables','figures']}
 for section in note.get('sections',[]):result['section:'+section['id']]={'title':section['title'],'body':section['body'],'sources':section['sources']}
 return result

def paper_events(old,new,at,base):
 p=new['paper'];pid=p['id'];output=[]
 def emit(kind,before,after,label):
  delta=changes(before,after)
  if not delta:return
  output.append({'id':'change-'+digest([kind,pid,before,after]),'kind':kind,'paperId':pid,'title':p['name']+' · '+label,'date':at[:10],'observedAt':at,'mode':'change','summary':'本站内容变更；不是论文首次公开时间。','source':REPO+'/blob/main/catalog/papers/'+pid+'.json','baseCommit':base,'changes':delta})
 if old is None:emit('collected',{}, {'title':p['title'],'firstPublished':p['firstPublished'],'readingVersion':new['note']['version']},'新收录');return output
 emit('note',note_fields(old['note']),note_fields(new['note']),'笔记变更')
 for kind,keys,label in [('revision',['latestArxivVersion','latestArxivAt'],'版本元数据变更'),('publication',['status','venue','doi','acceptedAt','publishedAt'],'发表元数据变更')]:
  emit(kind,{k:old['publication'].get(k) for k in keys},{k:new['publication'].get(k) for k in keys},label)
 return output

def capture(root,base,at):
 root=Path(root)
 if not re.fullmatch(r'[0-9a-f]{40}',base):raise ValueError('Use an exact 40-character base commit')
 when=datetime.fromisoformat(at.replace('Z','+00:00'))
 if when.tzinfo is None:raise ValueError('Activity timestamp must include timezone')
 subprocess.run(['git','cat-file','-e',base+'^{commit}'],cwd=root,check=True,capture_output=True)
 logpath=root/'catalog/activity.json';log=json.loads(logpath.read_text()) if logpath.exists() else {'schemaVersion':1,'events':[]}
 known={e['id'] for e in log['events']};events=[]
 for f in sorted((root/'catalog/papers').glob('p*.json')):
  path=f.relative_to(root).as_posix();old=read_prior(root,base,path);new=json.loads(f.read_text());events.extend(paper_events(old,new,at,base))
 for f in sorted((root/'catalog/results').glob('r-*.json')):
  path=f.relative_to(root).as_posix();old=read_prior(root,base,path);new=json.loads(f.read_text())
  if old==new:continue
  events.append({'id':'result-change-'+digest([old,new]),'kind':'result','paperId':new['paperId'],'title':new['method']+' · 评测记录变更','date':at[:10],'observedAt':at,'mode':'change','summary':new['trackId']+' · '+new['sourceVersion'],'source':new['source'],'baseCommit':base,'changes':changes(old or {},new)})
 added=[e for e in events if e['id'] not in known]
 log['events'].extend(added);log['events'].sort(key=lambda e:(e['observedAt'],e['id']))
 if added:logpath.write_text(json.dumps(log,ensure_ascii=False,indent=2)+'\n')
 print(f'Activity: {len(added)} new real changes; no snapshots converted to historical updates.')
 return added
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--base',required=True);ap.add_argument('--at',default=datetime.now(timezone.utc).isoformat(timespec='seconds'));a=ap.parse_args();capture(ROOT,a.base,a.at)
