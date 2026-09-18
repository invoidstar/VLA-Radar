"""Deterministic public follow/palette indexes; never ingest browser preferences."""
from __future__ import annotations
import hashlib,json,re
from datetime import date
from pathlib import Path
from news_core import CATEGORIES,url

def text(v):return json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n'
def bibliography(root,papers):
 path=root/'catalog/bibliography.json';obj=json.loads(path.read_text()) if path.exists() else {'schemaVersion':1,'entries':{}}
 assert obj.get('schemaVersion')==1 and isinstance(obj.get('entries'),dict),'Bibliography schema'
 allowed={'type','title','author','issued','container-title','volume','issue','page','publisher','DOI','URL'}
 for pid,e in obj['entries'].items():
  assert pid in papers and set(e)=={'item','sources','verifiedAt'},'Unknown bibliography identity/field'
  assert date.fromisoformat(e['verifiedAt'])<=date.today() and e['sources'],'Bibliography verification required'
  for s in e['sources']:assert set(s)=={'url','label'} and s['label'];url(s['url'])
  b=e['item'];assert set(b)<=allowed and b.get('type') in {'article','article-journal','paper-conference','report'},'Bibliography fields/type'
  assert b.get('title')==papers[pid]['paper']['title'],'Citation title must match tracked identity'
  for a in b.get('author',[]):
   assert isinstance(a,dict) and set(a)<={'family','given','literal'} and (a.get('literal') or a.get('family')),'Structured author required'
   assert all(isinstance(v,str) and '\n' not in v for v in a.values()),'Invalid author'
   assert not (a.get('literal') and (a.get('family') or a.get('given'))),'Literal vs personal author'
  if b['type'] in {'article-journal','paper-conference'}:assert 'issued' in b,'Final citation needs its own source-verified issue/online date'
  if 'issued' in b:
   parts=b['issued'].get('date-parts');assert isinstance(parts,list) and len(parts)==1 and 1<=len(parts[0])<=3
   d=parts[0];assert all(type(v) is int for v in d) and date(*(d+[1]*(3-len(d))))<=date.today(),'Invalid citation date'
  for k,v in b.items():
   if k not in {'author','issued'}:assert isinstance(v,str) and len(v)<=2000,'Citation text required'
  if b.get('URL'):url(b['URL'])
  if b.get('DOI'):assert re.fullmatch(r'10\.\d{4,9}/\S+',b['DOI'])
 return obj

def outputs(root,records,tracks,results,experience,indexurl):
 root=Path(root);out={};papers={r['paper']['id']:r for r in records}
 def shard(name,v):
  s=text(v);path='data/tools/'+name+'.'+hashlib.sha256(s.encode()).hexdigest()[:16]+'.json';out[path]=s;return path
 def split(name,items):return [{'url':shard(name+'-'+str(i//100),{'items':items[i:i+100]}),'count':len(items[i:i+100])} for i in range(0,len(items),100)]
 bib=bibliography(root,papers);biburl=shard('bibliography',bib)
 tid={t['id']:t for t in tracks};datasets=sorted({t['dataset'] for t in tracks});pds={pid:set() for pid in papers}
 replaced={r['supersedes'] for r in results if r['evidence']=='checked' and r['supersedes']}
 for r in results:
  if r['evidence']=='checked' and r['id'] not in replaced:pds[r['paperId']].add(tid[r['trackId']]['dataset'])
 ix=json.loads(experience[indexurl]);streams=json.loads(experience[ix['updatesUrl']])['streams']['all'];events=[]
 for part in streams:
  for e in json.loads(experience[part['url']])['events']:
   if e.get('mode')=='snapshot' or not e.get('observedAt') or not e.get('paperId'):continue
   pid=e['paperId'];ds=pds[pid]
   if e['kind']=='result':
    track_changes=[c.get('after') for c in e.get('changes',[]) if c.get('field')=='trackId'];known=[tid[t]['dataset'] for t in track_changes if t in tid]
    if known:ds=set(known)
   events.append({'id':e['id'],'kind':e['kind'],'paperId':pid,'title':e['title'],'date':e.get('date'),'observedAt':e['observedAt'],'mode':e['mode'],'summary':e['summary'],'topics':papers[pid]['paper']['topics'],'datasets':sorted(ds),'categories':[]})
 news=[json.loads(p.read_text()) for p in sorted((root/'catalog/news').glob('news-*.json'))];headlines=[]
 for n in news:
  headlines.append({'id':n['id'],'title':n['title'],'date':n['eventDate'] or n['publishedAt'],'category':n['primaryCategory'],'tags':n['tags'],'status':n['status']})
  events.append({'id':'watch-'+n['id']+'-'+n['updatedAt'],'kind':'news','newsId':n['id'],'paperId':None,'title':n['title'],'date':n['eventDate'] or n['publishedAt'],'observedAt':n['updatedAt'],'mode':'record','summary':n['whatHappened'],'topics':[],'datasets':[],'categories':[n['primaryCategory']]})
 events.sort(key=lambda e:(e['observedAt'],e['id']),reverse=True);headlines.sort(key=lambda e:(e['date'],e['id']),reverse=True)
 manifest={'schemaVersion':1,'datasets':datasets,'categories':[{'id':k,'name':v} for k,v in CATEGORIES.items()],'paperDatasets':{pid:sorted(ds) for pid,ds in pds.items() if ds},'bibliographyUrl':biburl,'events':split('events',events),'headlines':split('headlines',headlines),'scope':'Public observed records only; no snapshots treated as new. Dataset matches use checked evidence. News is independently reported, not paper results.'}
 return out,shard('index',manifest)
