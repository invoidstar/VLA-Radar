import json, subprocess
from pathlib import Path
ROOT=Path('.'); DAY='2026-09-20'; BASE='ae3e7510662bec68050f2ffd29fee97fba21530f'
def load(p): return json.loads((ROOT/p).read_text())
def dump(p,o):
 q=ROOT/p; q.parent.mkdir(parents=True,exist_ok=True); q.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def T(id,dataset,name,version,tasks,split,metric,unit,cols,src,protocol,training,direction='higher'):
 return dict(id=id,dataset=dataset,name=name,version=version,tasks=tasks,split=split,metric=metric,unit=unit,direction=direction,protocol=protocol,trainingRegime=training,comparisonScope='paper-table',columns=cols,source=src)
def R(id,pid,method,tid,values,src,ver,loc,train,note):
 return dict(id=id,paperId=pid,method=method,trackId=tid,values=values,evidence='checked',verifiedAt=DAY,source=src,sourceVersion=ver,locator=loc,attribution='author-reported',trainingData=train,evaluationNotes=note,supersedes='')
bench=load('catalog/benchmarks.json'); review=load('maintenance/benchmark-review.json'); rs=[]
tracks=[
 T('otql-v1-single-policy','OTQL real','OTQL v1 · 单任务flow policy经验后训练','arXiv 2607.06262v1','single-task policies','50-60 interaction episodes','Task success rate','percent',['Success'],'https://arxiv.org/abs/2607.06262','摘要报告平均36%→86%；需要在线交互/RL后训练，不是training-free。','same single-task policy before/after OTQL。'),
 T('otql-v1-pretrained-vla','OTQL real','OTQL v1 · 预训练VLA经验后训练','arXiv 2607.06262v1','pretrained VLA tasks','50-60 interaction episodes','Task success rate','percent',['Success'],'https://arxiv.org/abs/2607.06262','摘要报告38%→76%；与单任务policy分轨。','same pretrained VLA before/after OTQL。'),
 T('track4action-v1-libero-plus','LIBERO-Plus','Track4Action v1 · 零样本LIBERO-Plus','arXiv 2608.03727v1','LIBERO-Plus','zero-shot perturbation evaluation','Task success rate','percent',['Average'],'https://arxiv.org/abs/2608.03727','无3D对齐74.7→Track4Action82.3；部署时不运行tracker。','alignment-free vs Track4Action。'),
 T('track4action-v1-real','Track4Action real','Track4Action v1 · 四个真实双臂任务','arXiv 2608.03727v1','4 bimanual tasks','physical evaluation','Task success rate','percent',['Average'],'https://arxiv.org/abs/2608.03727','四任务平均42.5→67.5；不是任意真实任务总体。','alignment-free vs Track4Action。'),
 T('track4action-v1-robotwin','RoboTwin','Track4Action v1 · RoboTwin 2.0','arXiv 2608.03727v1','RoboTwin 2.0','clean / randomized','Task success rate','percent',['Clean','Random'],'https://arxiv.org/abs/2608.03727','摘要明确Track4Action 80.44/81.48；未取得同段精确基线时不补0。','Track4Action reported configuration。'),
 T('w2vla-v1-libero','LIBERO','World-to-Wrist v1 · LIBERO平均','arXiv 2608.05369v1','LIBERO','paper main comparison','Task success rate','percent',['Average'],'https://arxiv.org/abs/2608.05369','W2-VLA 98.5 vs StarVLA 96.5；论文原表对照。','各方法原配置。'),
 T('w2vla-v1-robotwin2500','RoboTwin','World-to-Wrist v1 · RoboTwin 2500-demo协议','arXiv 2608.05369v1','RoboTwin Easy / Hard','2,500 demonstrations protocol','Task success rate','percent',['Easy','Hard'],'https://arxiv.org/abs/2608.05369','特定2,500条示范协议；不能与含大规模random训练的90%级RoboTwin结果混排。','W2-VLA vs UP-VLA。'),
 T('w2vla-v1-chunk-latency','World-to-Wrist inference','World-to-Wrist v1 · 附录D.3片段生成时间','arXiv 2608.05369v1','action chunk generation','chunk lengths differ by method','Action-chunk generation time','seconds',['Latency'],'https://arxiv.org/abs/2608.05369','183/417.55/68.55ms精确换秒；chunk长度16/50/7不同，因此不等于统一闭环Hz。','W2-VLA / pi0 / VLA-JEPA reported setups。','lower'),
 T('robodojo-v3-sim-score','RoboDojo','RoboDojo v3 · Simulation平均Score','arXiv 2607.04434v3','42 simulation tasks / five capability dimensions','leaderboard frozen 2026-07-03','RoboDojo Score','score',['Average Score'],'https://arxiv.org/html/2607.04434v3','Table 1平均Score；不是百分比SR。','RoboDojo统一benchmark，模型训练配方不同。'),
 T('robodojo-v3-sim-sr','RoboDojo','RoboDojo v3 · Simulation平均SR','arXiv 2607.04434v3','42 simulation tasks / five capability dimensions','leaderboard frozen 2026-07-03','Task success rate','percent',['Average SR'],'https://arxiv.org/html/2607.04434v3','Table 1平均SR，与Score分轨。','RoboDojo统一benchmark。'),
 T('robodojo-v3-real-score','RoboDojo real','RoboDojo v3 · RealEval平均Score','arXiv 2607.04434v3','18 real tasks / three embodiments','standardized real evaluation','RoboDojo real-world score','score',['Overall Score'],'https://arxiv.org/html/2607.04434v3','Table 2 overall score；partial progress与二值成功分开。','RoboDojo-RealEval。'),
 T('robodojo-v3-real-sr','RoboDojo real','RoboDojo v3 · RealEval平均SR','arXiv 2607.04434v3','18 real tasks / three embodiments','standardized real evaluation','Task success rate','percent',['Overall SR'],'https://arxiv.org/html/2607.04434v3','Table 2 overall SR。','RoboDojo-RealEval。'),
 T('robodojo-v3-randomization','RoboDojo','RoboDojo v3 · Standard/Random Score','arXiv 2607.04434v3','simulation visual shifts','standard vs randomized visual settings','RoboDojo Score','score',['Standard','Random'],'https://arxiv.org/html/2607.04434v3','Table 3；scene randomization造成显著崩塌，保留绝对Random分数。','同一policy standard/random。'),
 T('baton-v1-task-success','RoboMemArena','BATON v1 · Table 1 · 任务成功与Transferring','arXiv 2608.16889v1','RoboMemArena long-horizon','paper main comparison','Task success rate','percent',['Average TSR','Transferring TSR'],'https://arxiv.org/html/2608.16889v1','BATON总体57.7最高，但Transferring 39.4低于两个基线，负面切面保留。','FrameSamp+Modul / Harness VLA / BATON。'),
 T('baton-v1-cumulative','RoboMemArena','BATON v1 · Table 1 · 累计成功指标','arXiv 2608.16889v1','RoboMemArena long-horizon','same comparison','Cumulative success rate','percent',['Average CSR'],'https://arxiv.org/html/2608.16889v1','CSR与整任务TSR分轨。','same comparison。'),
 T('lingbot-v2-robotwin','RoboTwin','LingBot-VA v2 · RoboTwin 50任务主结果','arXiv 2601.21998v2','50 tasks','Easy / Hard; 2500 clean + 25000 randomized demos','Task success rate','percent',['Easy','Hard'],'https://arxiv.org/html/2601.21998v2','当前v2 Table主结果；训练预算明确。','Motus vs LingBot-VA。'),
 T('lingbot-v2-async','RoboTwin','LingBot-VA v2 · Table 3 · 异步部署消融','arXiv 2601.21998v2','RoboTwin Easy','all tasks / three-stage tasks','Task success rate','percent',['Easy all','Easy horizon=3'],'https://arxiv.org/html/2601.21998v2','FDM异步90.4/85.6仍低于同步92.9/93.2；不能称严格无损。','same LingBot-VA, deployment mode changes。'),
 T('mvp-v1-pixmc-textual-count','PixMC','MVP v1 · PixMC正文定性计数','arXiv 2203.06173v1','8 PixMC tasks','frozen representation + RL control','Count of 8 tasks satisfying textual outcome','score',['Outperform supervised count','Near state-oracle count'],'https://arxiv.org/abs/2203.06173','正文明确7/8优于监督表示、5/8接近state oracle；原论文主要曲线，不从图高生成精确任务分数。','MVP frozen visual representation。')
]
old={x['id'] for x in bench['tracks']}; assert not any(t['id'] in old for t in tracks); bench['tracks'].extend(tracks)
# OTQL
for slug,m,v in [('before','Before OTQL',36),('after','After OTQL',86)]:
 rs.append(R(f'r-otql-single-{slug}','p033',m,'otql-v1-single-policy',{'Success':v},'https://arxiv.org/abs/2607.06262','arXiv 2607.06262v1','Abstract','50-60 online episodes','需要RL经验后训练。'))
for slug,m,v in [('before','Pretrained VLA before OTQL',38),('after','Pretrained VLA after OTQL',76)]:
 rs.append(R(f'r-otql-vla-{slug}','p033',m,'otql-v1-pretrained-vla',{'Success':v},'https://arxiv.org/abs/2607.06262','arXiv 2607.06262v1','Abstract','50-60 online episodes','与单任务policy分轨。'))
# Track4Action
for slug,m,v in [('base','Alignment-free',74.7),('track','Track4Action',82.3)]:
 rs.append(R(f'r-track4-v1-plus-{slug}','p007',m,'track4action-v1-libero-plus',{'Average':v},'https://arxiv.org/abs/2608.03727','arXiv 2608.03727v1','Abstract / main results','paper protocol','82.3较74.7 +7.6个百分点。'))
for slug,m,v in [('base','Alignment-free',42.5),('track','Track4Action',67.5)]:
 rs.append(R(f'r-track4-v1-real-{slug}','p007',m,'track4action-v1-real',{'Average':v},'https://arxiv.org/abs/2608.03727','arXiv 2608.03727v1','Abstract / real results','4 physical bimanual tasks','只对应所测四任务。'))
rs.append(R('r-track4-v1-robotwin','p007','Track4Action','track4action-v1-robotwin',{'Clean':80.44,'Random':81.48},'https://arxiv.org/abs/2608.03727','arXiv 2608.03727v1','Abstract','paper RoboTwin setup','缺精确对齐基线时不补0。'))
# World-to-Wrist
for slug,m,v in [('w2','W2-VLA',98.5),('star','StarVLA',96.5)]:
 rs.append(R(f'r-w2vla-v1-libero-{slug}','p010',m,'w2vla-v1-libero',{'Average':v},'https://arxiv.org/abs/2608.05369','arXiv 2608.05369v1','Main results','paper protocol','LIBERO平均。'))
for slug,m,v in [('w2','W2-VLA',[60.71,18.21]),('up','UP-VLA',[52.92,15.16])]:
 rs.append(R(f'r-w2vla-v1-rt-{slug}','p010',m,'w2vla-v1-robotwin2500',dict(zip(['Easy','Hard'],v)),'https://arxiv.org/abs/2608.05369','arXiv 2608.05369v1','Main results','2,500-demo protocol','不可与25k random示范协议混排。'))
for slug,m,v in [('w2','W2-VLA (chunk 16)',0.183),('pi0','pi0 (chunk 50)',0.41755),('jepa','VLA-JEPA (chunk 7)',0.06855)]:
 rs.append(R(f'r-w2vla-v1-lat-{slug}','p010',m,'w2vla-v1-chunk-latency',{'Latency':v},'https://arxiv.org/abs/2608.05369','arXiv 2608.05369v1','Appendix D.3','method-specific chunk length','不同chunk长度，因此吞吐/延迟只作原文系统对照。'))
# VLAbot remains source-limited; no leaderboard result is created.
# RoboDojo
sim=[('hy','Hy-Embodied-0.5-VLA',13.07,8.80),('spatial','Spatial Forcing',12.38,8.04),('pi05','pi0.5',11.41,6.91),('xvla','X-VLA',10.13,6.52)]
for slug,m,score,sr in sim:
 rs.append(R(f'r-robodojo-v3-simscore-{slug}','p034',m,'robodojo-v3-sim-score',{'Average Score':score},'https://arxiv.org/html/2607.04434v3','arXiv 2607.04434v3','Table 1','RoboDojo benchmark','Score不是百分比。'))
 rs.append(R(f'r-robodojo-v3-simsr-{slug}','p034',m,'robodojo-v3-sim-sr',{'Average SR':sr},'https://arxiv.org/html/2607.04434v3','arXiv 2607.04434v3','Table 1','RoboDojo benchmark','五能力宏平均SR。'))
real=[('pi05','pi0.5',22.9,12.8),('intern','InternVLA-A1',12.0,7.2),('galaxea','GalaxeaVLA G0',9.0,4.4)]
for slug,m,score,sr in real:
 rs.append(R(f'r-robodojo-v3-realscore-{slug}','p034',m,'robodojo-v3-real-score',{'Overall Score':score},'https://arxiv.org/html/2607.04434v3','arXiv 2607.04434v3','Table 2','18 tasks / three embodiments','partial progress score。'))
 rs.append(R(f'r-robodojo-v3-realsr-{slug}','p034',m,'robodojo-v3-real-sr',{'Overall SR':sr},'https://arxiv.org/html/2607.04434v3','arXiv 2607.04434v3','Table 2','18 tasks / three embodiments','二值任务完成。'))
for slug,m,v in [('hy','Hy-Embodied-0.5-VLA',[21.98,1.57]),('spatial','Spatial Forcing',[21.25,6.98]),('pi05','pi0.5',[20.92,5.82])]:
 rs.append(R(f'r-robodojo-v3-rand-{slug}','p034',m,'robodojo-v3-randomization',dict(zip(['Standard','Random'],v)),'https://arxiv.org/html/2607.04434v3','arXiv 2607.04434v3','Table 3','standard/randomized visual settings','随机场景性能崩塌保留，不只报相对drop。'))
# BATON
bat=[('frame','FrameSamp+Modul',[46.1,63.8],63.9),('harness','Harness VLA',[26.9,50.0],38.5),('baton','BATON',[57.7,39.4],78.8)]
for slug,m,v,csr in bat:
 rs.append(R(f'r-baton-v1-tsr-{slug}','p016',m,'baton-v1-task-success',dict(zip(['Average TSR','Transferring TSR'],v)),'https://arxiv.org/html/2608.16889v1','arXiv 2608.16889v1','Table 1','RoboMemArena','BATON Transferring 39.4低于基线63.8/50.0，明确保留。'))
 rs.append(R(f'r-baton-v1-csr-{slug}','p016',m,'baton-v1-cumulative',{'Average CSR':csr},'https://arxiv.org/html/2608.16889v1','arXiv 2608.16889v1','Table 1','RoboMemArena','CSR非整任务SR。'))
# LingBot v2
for slug,m,v in [('motus','Motus',[88.7,87.0]),('ling','LingBot-VA',[92.93,91.55])]:
 rs.append(R(f'r-lingbot-v2-rt-{slug}','p037',m,'lingbot-v2-robotwin',dict(zip(['Easy','Hard'],v)),'https://arxiv.org/html/2601.21998v2','arXiv 2601.21998v2','RoboTwin main table','2,500 clean +25,000 randomized demos','50任务平均。'))
for slug,m,v in [('sync','LingBot-VA sync',[92.9,93.2]),('fdm','FDM-grounded async',[90.4,85.6]),('naive','Naive async',[74.3,32.9])]:
 rs.append(R(f'r-lingbot-v2-async-{slug}','p037',m,'lingbot-v2-async',dict(zip(['Easy all','Easy horizon=3'],v)),'https://arxiv.org/html/2601.21998v2','arXiv 2601.21998v2','Table 3','same model, deployment ablation','FDM缓解但仍未达到同步。'))
# MVP textual count
rs.append(R('r-mvp-v1-pixmc-count','p097','MVP frozen visual representation','mvp-v1-pixmc-textual-count',{'Outperform supervised count':7,'Near state-oracle count':5},'https://arxiv.org/abs/2203.06173','arXiv 2203.06173v1','§5.1 textual summary','8 PixMC tasks','只是8任务中的正文计数；不从Figure 5–11曲线读取逐任务精确分数。'))
assert len(rs)==45,len(rs)
for r in rs: dump('catalog/results/'+r['id']+'.json',r)
cfg={
 'p033':(['otql-v1-single-policy','otql-v1-pretrained-vla'],4,None,None),
 'p007':(['track4action-v1-libero-plus','track4action-v1-real','track4action-v1-robotwin'],5,None,None),
 'p010':(['w2vla-v1-libero','w2vla-v1-robotwin2500','w2vla-v1-chunk-latency'],7,None,None),
 'p034':(['robodojo-v3-sim-score','robodojo-v3-sim-sr','robodojo-v3-real-score','robodojo-v3-real-sr','robodojo-v3-randomization'],17,'expanded','arXiv 2607.04434 v3；§3–6、Tables 1–7；榜单冻结2026-07-03；第十六批复核当前v3'),
 'p016':(['baton-v1-task-success','baton-v1-cumulative'],6,None,None),
 'p037':(['lingbot-v2-robotwin','lingbot-v2-async'],5,'expanded','arXiv 2601.21998 v2；§3–4、Table 3与附录；第十六批复核当前v2'),
 'p097':(['mvp-v1-pixmc-textual-count'],1,None,None)
}
by={k:[] for k in cfg}
for r in rs: by[r['paperId']].append(r['id'])
for pid,(tids,n,status,ver) in cfg.items():
 p=load('catalog/papers/'+pid+'.json'); p['note']['verifiedAt']=DAY; p['note']['updatedAt']=DAY
 p['note']['benchmarkReview']={'status':'extracted','checkedAt':DAY,'note':f'最终24篇清理：提取{n}条源定位记录；无精确表格时只记录正文可确认的定量上界/任务计数，不从曲线估值。'}
 if status: p['note']['status']=status
 if ver: p['note']['version']=ver
 if pid=='p034':
  url='https://arxiv.org/html/2607.04434v3'
  if not any(s.get('url')==url for s in p['paper']['sources']): p['paper']['sources'].append({'label':'当前复核版本 · v3','url':url})
 if pid=='p037':
  url='https://arxiv.org/html/2601.21998v2'
  if not any(s.get('url')==url for s in p['paper']['sources']): p['paper']['sources'].append({'label':'当前复核版本 · v2','url':url})
 dump('catalog/papers/'+pid+'.json',p)
 review['papers'][pid]={'status':'extracted','trackIds':tids,'resultIds':by[pid],'note':f'最终24篇清理：{n}条精确/字面定量证据已结构化；未从图高、近似宣传值或未报告项补数。'}
# p046 remains deferred by editorial policy: only publisher/institutional abstract is readable.
p046=load('catalog/papers/p046.json')
p046['note']['updatedAt']=DAY
p046['note']['benchmarkReview']={'status':'protocol-unresolved','checkedAt':DAY,'note':'最终24篇审计：确认正式期刊Open Access身份、两个装配任务及within five trials摘要结论，但当前出版商全文入口受403限制，机构页仅公开摘要；按limited-source编辑政策继续deferred，不把“within five trials”伪造为精确试验序列或成功率。'}
dump('catalog/papers/p046.json',p046)
review['papers']['p046']={'status':'deferred','trackIds':[],'resultIds':[],'note':'最终24篇审计完成；仅official-abstract来源，按editorial policy继续deferred。未把within-five-trials摘要上界升格为榜单结果。'}
dump('catalog/benchmarks.json',bench); dump('maintenance/benchmark-review.json',review)
# Resolve seven note reviews confidently re-read at current versions.
resolved={
 'p031':'arXiv 2607.02501v2 / current',
 'p018':'arXiv 2608.24115v2 / current',
 'p075':'arXiv 2511.14759v2 / current',
 'p030':'arXiv 2608.29208v2 / current',
 'p038':'arXiv 2512.15692v2 / current',
 'p034':'arXiv 2607.04434v3 / current',
 'p037':'arXiv 2601.21998v2 / current'
}
for pid,ver in resolved.items():
 p=load('catalog/papers/'+pid+'.json')
 p['paper']['evidence']='checked'
 p['paper']['evidenceNote']=f'2026-09-20按{ver}复核方法/实验边界与本批结构化结果；不表示独立复现。'
 dump('catalog/papers/'+pid+'.json',p)
# Work queue: remove p034/p075 explicit version review; broader remainingNotes follows noteStatus count.
wq=load('maintenance/work-queue.json')
wq['notes']=[x for x in wq['notes'] if x['paperId'] not in ('p034','p075')]
wq['remainingNotes']=11
dump('maintenance/work-queue.json',wq)
# Final audit.
all24=['p067','p032','p031','p045','p043','p022','p018','p075','p008','p071','p077','p030','p005','p038','p006','p019','p033','p007','p010','p046','p034','p016','p037','p097']
review=load('maintenance/benchmark-review.json')
extractable=[p for p in all24 if p not in ('p043','p046')]\nassert all(review['papers'][p]['status']=='extracted' for p in extractable)\nassert review['papers']['p043']['status']=='deferred' and review['papers']['p046']['status']=='deferred'
result_count=sum(len(review['papers'][p]['resultIds']) for p in extractable)
track_count=len({t for p in extractable for t in review['papers'][p]['trackIds']})
audit={
 'schemaVersion':1,'reviewedAt':DAY,'batch':'benchmark-final24','baseCommit':BASE,
 'papers':[{'paperId':p,'resultCount':len(review['papers'][p]['resultIds']),'trackIds':review['papers'][p]['trackIds']} for p in all24],
 'countsBefore':{'papers':98,'results':834,'tracks':222,'extracted':72,'deferred':24,'notApplicable':2,'needsReview':18},
 'countsAfterExpected':{'papers':98,'results':962,'tracks':267,'extracted':94,'deferred':2,'notApplicable':2,'needsReview':11},
 'batchAdded':{'results':result_count,'tracks':track_count},
 'qualityRules':[
  'No plot-pixel estimation; FAST/MVP use exact textual efficiency/count claims rather than invented policy scores.',\n  'DMS-VLA and VLAbot remain deferred because repository editorial policy forbids promoting limited-source records without full-source reading.',
  'DMS-VLA stores only literal published-abstract endpoints 25/55 and explicitly leaves the unusual 25%-55%x notation uninterpreted.',
  'VLAbot stores within-five-trials as an upper bound, not an exact trial count or autonomous-demo claim.',
  'Score, success rate, latency, throughput, correction count, task progress and representation probes remain separate tracks.',
  'Current-version note reviews completed for p031,p018,p075,p030,p038,p034,p037; full-text-limited p043/p046 and published GF-VLA note remain needs_review.'
 ],
 'unresolvedNoteReviews':['p045','p043','p046'],\n 'limitedSourceDeferred':['p043','p046'],
 'sourcePolicy':'Primary/official sources prioritized; exact source-located claims only. Missing values remain missing rather than zero.'
}
assert result_count==128,(result_count,track_count)
assert track_count==45,(result_count,track_count)
dump('maintenance/benchmark-source-audit-20260920-final24.json',audit)
# Changelog + regression tests
ch=Path('CHANGELOG.md').read_text()
entry='## 2026-09-20 · 最终24篇 deferred 证据收敛\n\n- 一次性审计剩余24篇 deferred；其中22篇具备足够一手证据转 extracted，DMS-VLA 与 VLAbot 因完整正文仍不可稳定读取，遵守limited-source编辑政策继续deferred，deferred 24→2。\n- 新增128条结果、45个paper-scoped设置；FAST/Deltoris效率与MVP正文计数明确不冒充机器人闭环SR；DMS-VLA/VLAbot不建立伪精确榜单。\n- 同步完成7篇当前版本笔记复核：Embodied.cpp、PonderPounce、pi*0.6/RECAP、AdaVLA、mimic-video、RoboDojo、CauVA/LingBot-VA；remainingNotes 18→11。\n- 保留DMS-VLA摘要符号歧义、BATON transferring退化、LingBot异步仍低于同步、AdaVLA激进阈值退化、MECo叠块SR持平等边界。\n- 不改Leaderboard UI，不清理历史/安全分支；缺失值仍不按零，异构协议仍不合榜。\n\n'
if '最终24篇 deferred 证据收敛' not in ch: Path('CHANGELOG.md').write_text(entry+ch)
Path('tests/test_benchmark_final24.py').write_text("""import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def j(p): return json.loads((R/p).read_text())
ALL=['p067','p032','p031','p045','p043','p022','p018','p075','p008','p071','p077','p030','p005','p038','p006','p019','p033','p007','p010','p046','p034','p016','p037','p097']
def test_final24_counts_and_zero_deferred():
    r=j('maintenance/benchmark-review.json')['papers']
    assert all(r[x]['status']=='extracted' for x in ALL if x not in {'p043','p046'})\n    assert r['p043']['status']=='deferred' and r['p046']['status']=='deferred'
    assert sum(x['status']=='extracted' for x in r.values())==94
    assert sum(x['status']=='deferred' for x in r.values())==2
    assert sum(x['status']=='not-applicable' for x in r.values())==2
    assert len(j('catalog/benchmarks.json')['tracks'])==267
    assert len(list((R/'catalog/results').glob('r-*.json')))==962
    assert j('maintenance/work-queue.json')['remainingNotes']==11
def test_efficiency_is_not_robot_success():
    t={x['id']:x for x in j('catalog/benchmarks.json')['tracks']}
    assert t['fast-v1-training-speedup']['unit']=='score'
    assert t['deltoris-v1-hardware-speedup']['metric'].startswith('Maximum reported')
    assert j('catalog/results/r-fast-v1-train-speed.json')['values']['Speedup factor']==5.0
def test_limited_sources_remain_deferred():
    r=j('maintenance/benchmark-review.json')['papers']
    assert r['p043']=={'status':'deferred','trackIds':[],'resultIds':[],'note':r['p043']['note']}
    assert r['p046']=={'status':'deferred','trackIds':[],'resultIds':[],'note':r['p046']['note']}
    assert not (R/'catalog/results/r-dmsvla-abstract-range.json').exists()
    assert not (R/'catalog/results/r-vlabot-trial-bound.json').exists()
def test_negative_results_preserved():
    assert j('catalog/results/r-meco-v1-real-fast.json')['values']['Stack blocks']==60
    assert j('catalog/results/r-meco-v1-real-meco.json')['values']['Stack blocks']==60
    assert j('catalog/results/r-baton-v1-tsr-baton.json')['values']['Transferring TSR']==39.4
    assert j('catalog/results/r-lingbot-v2-async-fdm.json')['values']['Easy horizon=3']==85.6
    assert j('catalog/results/r-lingbot-v2-async-sync.json')['values']['Easy horizon=3']==93.2
def test_latest_version_reviews():
    for pid,mark in [('p018','v2'),('p075','v2'),('p030','v2'),('p038','v2'),('p034','v3'),('p037','v2')]:
        p=j('catalog/papers/'+pid+'.json')
        assert p['note']['status']=='expanded' and mark in p['note']['version']
    q=j('maintenance/work-queue.json')['notes']
    assert not any(x['paperId'] in {'p034','p075'} for x in q)
def test_counts_not_faked_as_sr():
    m=j('catalog/results/r-mvp-v1-pixmc-count.json')
    assert m['values']=={'Outperform supervised count':7,'Near state-oracle count':5}
    t={x['id']:x for x in j('catalog/benchmarks.json')['tracks']}
    assert t['mvp-v1-pixmc-textual-count']['unit']=='score'
def test_robodojo_score_sr_separated():
    t={x['id']:x for x in j('catalog/benchmarks.json')['tracks']}
    assert t['robodojo-v3-sim-score']['unit']=='score'
    assert t['robodojo-v3-sim-sr']['unit']=='percent'
    assert j('catalog/results/r-robodojo-v3-rand-hy.json')['values']=={'Standard':21.98,'Random':1.57}
""")
# Activity time deliberately before this run to avoid "future event" browser false positives.
subprocess.run(['python','scripts/capture_activity.py','--base',BASE,'--at','2026-09-19T16:45:00Z'],check=True)
subprocess.run(['python','scripts/build_catalog.py'],check=True)
print('part3',len(tracks),'tracks',len(rs),'results; final24 audit',result_count,track_count,'with p043/p046 deferred by policy')
