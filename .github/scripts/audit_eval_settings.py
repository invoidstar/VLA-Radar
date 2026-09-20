from pathlib import Path
import re,sys,json,unicodedata
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/build'))
from catalog_core import read_catalog
_,_,tracks,results=read_catalog(ROOT)

def norm(s):
    return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',str(s or '')).strip().lower())
def metric_class(s):
    n=norm(s)
    if 'success' in n:return 'success'
    if 'latency' in n or 'time' in n:return 'latency'
    if 'score' in n:return 'score'
    if 'fwt' in n:return 'fwt'
    if 'nbt' in n:return 'nbt'
    if 'auc' in n:return 'auc'
    return n
def canon_cols(cols):
    out=[]
    for c in cols:
        x=norm(c).replace('avg.','average').replace('avg','average').replace('success rate','success')
        out.append(x)
    return tuple(out)
def task_count(t):
    n=norm(t['tasks'])
    m=re.search(r'(?<!\d)(\d{1,3})(?!\d)',n)
    return int(m.group(1)) if m else None
def eval_flags(t):
    text=' '.join(map(norm,[t['name'],t['tasks'],t['split'],t['protocol']]))
    flags=[]
    rules=[
      ('single-view',r'single[- ]?view|单视角'),('multi-view',r'multi[- ]?view|多视角|wrist'),
      ('async',r'async|异步'),('d0',r'\bd\s*=\s*0\b'),('d1',r'\bd\s*=\s*1\b'),('d4',r'\bd\s*=\s*4\b'),
      ('single-task',r'\bsingle\b|单任务'),('multi-task',r'\bmulti\b|多任务'),
      ('clean-only',r'clean[- ]?only|只评clean'),('clean-random',r'clean\s*[+/]\s*random|clean.*random'),
      ('easy-hard',r'easy.*hard|hard.*easy'),('subset',r'subset|子集|short|medium|long-duration|12任务|12 tasks'),
      ('real',r'\breal\b|真实'),('sim',r'\bsim\b|仿真'),
    ]
    for label,pat in rules:
        if re.search(pat,text,re.I):flags.append(label)
    return tuple(flags)

def explicit(t):
    if t.get('settingEvalId'): return 'explicit:'+t['settingEvalId']
    if t.get('familyId') and t.get('familyMode')=='aligned': return 'family:'+t['familyId']
    return None

def sig(t,level):
    e=explicit(t)
    if e:return (t['dataset'],e,metric_class(t['metric']),t['unit'],t['direction'])
    base=(t['dataset'],metric_class(t['metric']),t['unit'],t['direction'],canon_cols(t['columns']))
    if level=='loose': return base
    if level=='medium': return base+(task_count(t),eval_flags(t))
    return base+(norm(t['tasks']),norm(t['split']),eval_flags(t))

out={}
for level in ['strict','medium','loose']:
    g=defaultdict(list)
    for t in tracks:g[sig(t,level)].append(t)
    groups=list(g.values())
    out[level]={
      'settings':len(groups),
      'crossTrackGroups':sum(len(x)>1 for x in groups),
      'maxGroup':max(map(len,groups)),
      'datasets':{}
    }
    for ds in sorted({t['dataset'] for t in tracks}):
        dsg=[x for x in groups if x[0]['dataset']==ds]
        out[level]['datasets'][ds]={
          'tracks':sum(map(len,dsg)),'settings':len(dsg),
          'groups':[{
            'ids':[t['id'] for t in x],
            'names':[t['name'] for t in x],
            'tasks':[t['tasks'] for t in x],
            'splits':[t['split'] for t in x],
            'columns':x[0]['columns'],
            'metric':x[0]['metric']
          } for x in dsg if len(x)>1]
        }
print(json.dumps(out,ensure_ascii=False,indent=2))
