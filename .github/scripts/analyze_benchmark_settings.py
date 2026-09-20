from collections import defaultdict
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/build'))
sys.path.insert(0,str(ROOT/'scripts/discovery'))
from catalog_core import read_catalog

_,records,tracks,results=read_catalog(ROOT)
checked=[r for r in results if r['evidence']=='checked']
generic_patterns=[
    r'^same paper setting$',r'^各方法原配置[。.]?$',r'^paper .*setup$',r'^reported configuration[。.]?$',
    r'^同文.*设置[。.]?$',r'^原文.*设置[。.]?$'
]
def norm(s):
    return re.sub(r'\s+',' ',str(s or '').strip().lower())
def usable_training(s):
    n=norm(s)
    if len(n)<8:return False
    return not any(re.search(p,n,re.I) for p in generic_patterns)
def eval_sig(t):
    return (
        t['dataset'],norm(t['tasks']),norm(t['split']),norm(t['metric']),t['unit'],t['direction'],
        tuple(norm(x) for x in t['columns']),t['comparisonScope']
    )
trackmap={t['id']:t for t in tracks}
groups=defaultdict(list)
track_training=defaultdict(set)
for r in checked:
    t=trackmap[r['trackId']]
    td=norm(r['trainingData'])
    track_training[t['id']].add(td)
    if usable_training(r['trainingData']):
        groups[(eval_sig(t),td)].append(r)

cross=[]
for (sig,td),rows in groups.items():
    tids=sorted({r['trackId'] for r in rows}); pids=sorted({r['paperId'] for r in rows})
    if len(tids)>1 or len(pids)>1:
        cross.append({
            'dataset':sig[0],'tasks':sig[1],'split':sig[2],'metric':sig[3],'columns':list(sig[6]),
            'trainingData':td,'tracks':tids,'papers':pids,
            'rows':[{'method':r['method'],'paperId':r['paperId'],'trackId':r['trackId']} for r in rows]
        })
cross.sort(key=lambda x:(x['dataset'],x['trainingData'],x['tracks']))
datasets=defaultdict(lambda:{'tracks':0,'checked':0,'multiTrainingTracks':0,'candidateCrossGroups':0})
for t in tracks:datasets[t['dataset']]['tracks']+=1
for r in checked:datasets[trackmap[r['trackId']]['dataset']]['checked']+=1
for tid,vals in track_training.items():
    if len(vals)>1:datasets[trackmap[tid]['dataset']]['multiTrainingTracks']+=1
for g in cross:datasets[g['dataset']]['candidateCrossGroups']+=1
report={
  'totals':{'tracks':len(tracks),'checkedResults':len(checked),'datasets':len(datasets),'candidateCrossGroups':len(cross)},
  'datasets':dict(sorted(datasets.items(),key=lambda kv:(-kv[1]['tracks'],kv[0]))),
  'crossGroups':cross
}
print(json.dumps(report,ensure_ascii=False,indent=2))

# trigger
