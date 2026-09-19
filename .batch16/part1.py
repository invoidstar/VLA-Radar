import json, subprocess
from pathlib import Path
ROOT=Path('.'); DAY='2026-09-20'; BASE='ae3e7510662bec68050f2ffd29fee97fba21530f'
assert subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()==BASE, 'main moved'
def load(p): return json.loads((ROOT/p).read_text())
def dump(p,o):
 q=ROOT/p; q.parent.mkdir(parents=True,exist_ok=True); q.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def T(id,dataset,name,version,tasks,split,metric,unit,cols,src,protocol,training,direction='higher'):
 return dict(id=id,dataset=dataset,name=name,version=version,tasks=tasks,split=split,metric=metric,unit=unit,direction=direction,protocol=protocol,trainingRegime=training,comparisonScope='paper-table',columns=cols,source=src)
def R(id,pid,method,tid,values,src,ver,loc,train,note):
 return dict(id=id,paperId=pid,method=method,trackId=tid,values=values,evidence='checked',verifiedAt=DAY,source=src,sourceVersion=ver,locator=loc,attribution='author-reported',trainingData=train,evaluationNotes=note,supersedes='')
bench=load('catalog/benchmarks.json'); review=load('maintenance/benchmark-review.json'); rs=[]
tracks=[
 T('fast-v1-training-speedup','FAST training','FAST v1 · 大规模训练加速上限','arXiv 2501.09747v1','pi0 VLA on ~10k robot hours','FAST vs diffusion VLA training','Maximum reported training speedup','score',['Speedup factor'],'https://arxiv.org/abs/2501.09747','摘要明确“match diffusion VLA performance while reducing training time by up to 5x”；这是训练效率而非闭环频率。','FAST tokenization + pi0；约10k小时机器人数据。'),
 T('deltoris-v1-hardware-speedup','Deltoris hardware','Deltoris v1 · 摘要硬件加速上限','arXiv 2608.04428v1','diffusion VLA inference','dedicated accelerator evaluation','Maximum reported inference speedup','score',['vs mobile GPU','vs prior accelerator'],'https://arxiv.org/abs/2608.04428','摘要精确报告34.2x与6.1x；专用加速器、RTL/周期模拟条件，不解释为普通GPU软件加速。','算法-硬件协同；非统一闭环任务榜。'),
 T('embcpp-v2-vla-success','Embodied.cpp','Embodied.cpp v2 · VLA闭环部署成功率','arXiv 2607.02501v2','two deployed VLA models','runtime deployment evaluation','Task success rate','percent',['Success'],'https://arxiv.org/abs/2607.02501','摘要分别报告HY-VLA 100.0%、pi0.5 91.0%；模型/任务路径不同，仅paper-table展示。','Embodied.cpp C++ runtime；模型原配置。'),
 T('embcpp-v2-wam-block-latency','Embodied.cpp','Embodied.cpp v2 · LingBot-VA单Transformer块延迟','arXiv 2607.02501v2','single LingBot-VA Transformer block','Python BF16 vs C++ Q4_K','Single-block latency','seconds',['Latency'],'https://arxiv.org/html/2607.02501v2','3.236ms与3.171ms精确换算秒；同时改变运行时与精度，不归因于C++单因素，也不是完整WAM端到端时延。','Python BF16 vs Embodied.cpp Q4_K。','lower'),
 T('gfvla-2026-basic-ops','GF-VLA real','GF-VLA · 基础操作成功率','Information Fusion 131 (2026) 104193','dual-arm block assembly','490 real-world trials reported across experiments','Operation success rate','percent',['Grasp','Placement'],'https://doi.org/10.1016/j.inffus.2026.104193','正式摘要明确94%抓取、89%放置；与图准确率/分割准确率分开。','GF-VLA dual-arm execution。'),
 T('gfvla-2026-overall-tsr','GF-VLA real','GF-VLA · 结构化双臂任务总体成功率','Information Fusion 131 (2026) 104193','four structured dual-arm assembly tasks','reported overall across scenarios','Overall task success rate','percent',['Overall'],'https://doi.org/10.1016/j.inffus.2026.104193','正式摘要明确90% overall task success；不与95%图准确率或93%分割准确率求平均。','GF-VLA dual-arm execution。'),
 T('stwam-v1-libero-plus-ablation','LIBERO-Plus','ST-WAM v1 · Table 5 · 表征与历史消融','arXiv 2607.28993v1','LIBERO-Plus','internal ablation','Task success rate','percent',['SR'],'https://arxiv.org/html/2607.28993v1','同论文Table 5；语义未来、双空间和历史检索受控比较。','FastWAM/ST-WAM内部变体。'),
 T('ponder-v2-robomme-base','RoboMME','PonderPounce v2 · RoboMME基础数据','arXiv 2608.24115v2','RoboMME','base-scale training data','Average task success rate','percent',['Average'],'https://arxiv.org/abs/2608.24115','v2摘要明确基础数据结果；相同Pounce接口时比较Ponder模型规模及历史基线。','base-scale data；模型/历史机制按行变化。'),
 T('ponder-v2-robomme-9x','RoboMME','PonderPounce v2 · RoboMME 9x数据','arXiv 2608.24115v2','RoboMME','9x training data','Average task success rate','percent',['Average'],'https://arxiv.org/abs/2608.24115','v2摘要明确PonderPounce 75.54 vs FrameSamp+Modul 57.88；与base-scale分轨。','9x data。'),
 T('ponder-v2-cognition-ablation','RoboMME','PonderPounce v2 · 连续认知通道消融','arXiv 2608.24115v2','RoboMME','base-scale controlled ablation','Average task success rate','percent',['Average'],'https://arxiv.org/html/2608.24115v2','Table III；文本子目标采用不同训练路径，数值不单独证明连续接口显著更优。','base-scale controlled ablation。'),
 T('recap-v2-throughput-factor','RECAP real','pi*0.6 / RECAP v2 · 困难任务吞吐提升','arXiv 2511.14759v2','laundry / long-horizon box assembly','real deployment iterations','Reported throughput factor relative to pre-RECAP reference','score',['Laundry factor','Box-assembly factor'],'https://arxiv.org/html/2511.14759v2','正文精确描述laundry +50%与box assembly 2x；分别记为1.5x与2.0x，属于不同任务，不求平均。','RECAP含on-policy数据与专家纠正。'),
 T('recap-v2-targeted-failure-success','RECAP real','pi*0.6 / RECAP v2 · 定向失败消除成功率','arXiv 2511.14759v2','targeted failure-removal task','two iterations; 600 trajectories each iteration','Task success rate','percent',['Success'],'https://arxiv.org/html/2511.14759v2','正文明确两轮后97%成功率；每轮收集600条轨迹。不是全任务统一成功率。','RECAP targeted failure-removal experiment。')
]
old={x['id'] for x in bench['tracks']}; assert not any(t['id'] in old for t in tracks); bench['tracks'].extend(tracks)
# FAST / Deltoris
rs += [
 R('r-fast-v1-train-speed','p067','FAST + pi0','fast-v1-training-speedup',{'Speedup factor':5.0},'https://arxiv.org/abs/2501.09747','arXiv 2501.09747v1','Abstract','~10k hours robot data','“up to 5x”训练时间缩短；不是推理或控制频率。'),
 R('r-deltoris-v1-speed','p032','Deltoris','deltoris-v1-hardware-speedup',{'vs mobile GPU':34.2,'vs prior accelerator':6.1},'https://arxiv.org/abs/2608.04428','arXiv 2608.04428v1','Abstract','dedicated accelerator','摘要headline；正文另有更高局部数字冲突，本站不替换摘要口径。')
]
# Embodied.cpp
for slug,m,v in [('hy','HY-VLA',100.0),('pi05','pi0.5',91.0)]:
 rs.append(R(f'r-embcpp-v2-success-{slug}','p031',m,'embcpp-v2-vla-success',{'Success':v},'https://arxiv.org/abs/2607.02501','arXiv 2607.02501v2','Abstract','Embodied.cpp runtime','闭环成功率作者报告；两种VLA不是同任务/同模型配置的严格单因素消融。'))
for slug,m,v in [('py','Python BF16',0.003236),('cpp','Embodied.cpp Q4_K',0.003171)]:
 rs.append(R(f'r-embcpp-v2-blocklat-{slug}','p031',m,'embcpp-v2-wam-block-latency',{'Latency':v},'https://arxiv.org/html/2607.02501v2','arXiv 2607.02501v2','WAM block benchmark','single LingBot-VA Transformer block','原文ms精确×0.001；量化和runtime同时变化。'))
# GF-VLA / DMS
rs += [
 R('r-gfvla-ops','p045','GF-VLA','gfvla-2026-basic-ops',{'Grasp':94.0,'Placement':89.0},'https://doi.org/10.1016/j.inffus.2026.104193','Information Fusion 131 (2026) 104193','Published abstract','490 real-world trials across study','抓取/放置为不同基础操作。'),
 R('r-gfvla-overall','p045','GF-VLA','gfvla-2026-overall-tsr',{'Overall':90.0},'https://doi.org/10.1016/j.inffus.2026.104193','Information Fusion 131 (2026) 104193','Published abstract','four structured dual-arm tasks','正式摘要的overall task success。'),
]
# ST-WAM
for slug,m,v in [('fast','FastWAM: VAE future',51.5),('dino','DINO future only',39.7),('dual','Dual-space, no CAIR',66.4),('history','Unanchored history retrieval',56.5),('full','ST-WAM',72.8)]:
 rs.append(R(f'r-stwam-v1-ablate-{slug}','p022',m,'stwam-v1-libero-plus-ablation',{'SR':v},'https://arxiv.org/html/2607.28993v1','arXiv 2607.28993v1','Table 5','internal ablation','仅DINO 39.7低于FastWAM 51.5、未锚定历史56.5低于双空间66.4，负面结果保留。'))
# PonderPounce
for slug,m,v in [('p9','PonderPounce 9B',60.83),('p08','PonderPounce 0.8B',50.04),('frame','FrameSamp+Modul',44.51),('pi05','Current-observation pi0.5',17.93)]:
 rs.append(R(f'r-ponder-v2-base-{slug}','p018',m,'ponder-v2-robomme-base',{'Average':v},'https://arxiv.org/abs/2608.24115','arXiv 2608.24115v2','Abstract','base-scale data','v2摘要精确值。'))
for slug,m,v in [('p9','PonderPounce 9B',75.54),('frame','FrameSamp+Modul',57.88)]:
 rs.append(R(f'r-ponder-v2-9x-{slug}','p018',m,'ponder-v2-robomme-9x',{'Average':v},'https://arxiv.org/abs/2608.24115','arXiv 2608.24115v2','Abstract','9x data','与基础数据分轨。'))
for slug,m,v in [('full','Full continuous cognition',60.83),('nodemo','w/o demonstration reasoning',48.21),('noground','w/o LM-head grounding',27.96),('text','Subgoal-text reference',59.96)]:
 rs.append(R(f'r-ponder-v2-ablate-{slug}','p018',m,'ponder-v2-cognition-ablation',{'Average':v},'https://arxiv.org/html/2608.24115v2','arXiv 2608.24115v2','Table III','base-scale data','文本参考训练方式不同；60.83 vs59.96的0.87点差不宣称显著。'))
# RECAP
rs += [
 R('r-recap-v2-throughput','p075','Full RECAP','recap-v2-throughput-factor',{'Laundry factor':1.5,'Box-assembly factor':2.0},'https://arxiv.org/html/2511.14759v2','arXiv 2511.14759v2','Results: deployment iterations','on-robot RECAP','+50%精确转为1.5x；2x保持原表述。两个任务不同，不求平均。'),
 R('r-recap-v2-targeted97','p075','RECAP after two iterations','recap-v2-targeted-failure-success',{'Success':97.0},'https://arxiv.org/html/2511.14759v2','arXiv 2511.14759v2','Targeted failure removal','600 trajectories per iteration','97%只对应定向失败消除实验。')
]
assert len(rs)==26, len(rs)
for r in rs: dump('catalog/results/'+r['id']+'.json',r)
# paper/review state
cfg={
 'p067':(['fast-v1-training-speedup'],1,None,None),
 'p032':(['deltoris-v1-hardware-speedup'],1,None,None),
 'p031':(['embcpp-v2-vla-success','embcpp-v2-wam-block-latency'],4,'expanded','arXiv 2607.02501 v2；§2–4、Tables 3–6；第十六批复核当前v2'),
 'p045':(['gfvla-2026-basic-ops','gfvla-2026-overall-tsr'],2,None,None),
 'p022':(['stwam-v1-libero-plus-ablation'],5,None,None),
 'p018':(['ponder-v2-robomme-base','ponder-v2-robomme-9x','ponder-v2-cognition-ablation'],10,'expanded','arXiv 2608.24115 v2；摘要、§3–5、Tables III/V/VI/IX；第十六批复核当前v2'),
 'p075':(['recap-v2-throughput-factor','recap-v2-targeted-failure-success'],2,'expanded','arXiv 2511.14759 v2；§IV–V、部署迭代与失败消除；第十六批复核当前v2')
}
by={k:[] for k in cfg}
for r in rs: by[r['paperId']].append(r['id'])
for pid,(tids,n,status,ver) in cfg.items():
 p=load('catalog/papers/'+pid+'.json'); p['note']['verifiedAt']=DAY; p['note']['updatedAt']=DAY
 p['note']['benchmarkReview']={'status':'extracted','checkedAt':DAY,'note':f'最终24篇清理：提取{n}条精确源定位记录；效率/摘要边界/诊断指标不伪装成闭环成功率。'}
 if status: p['note']['status']=status
 if ver: p['note']['version']=ver
 if pid in ('p018','p075'):
  url='https://arxiv.org/html/2608.24115v2' if pid=='p018' else 'https://arxiv.org/html/2511.14759v2'
  if not any(s.get('url')==url for s in p['paper']['sources']): p['paper']['sources'].append({'label':'当前复核版本 · v2','url':url})
 dump('catalog/papers/'+pid+'.json',p)
 review['papers'][pid]={'status':'extracted','trackIds':tids,'resultIds':by[pid],'note':f'最终24篇清理：{n}条源定位结果；指标边界、版本与负面结果保留，不从图高或缺失值推导。'}
# p043 remains deferred by editorial policy: only partial author/abstract materials are readable.
p043=load('catalog/papers/p043.json')
p043['note']['updatedAt']=DAY
p043['note']['benchmarkReview']={'status':'protocol-unresolved','checkedAt':DAY,'note':'最终24篇审计：已复核正式出版摘要与现有作者材料，但完整方法/实验正文仍不可稳定读取；按limited-source编辑政策继续deferred，不把摘要速度字符串或二手数值升格为榜单结果。'}
dump('catalog/papers/p043.json',p043)
review['papers']['p043']={'status':'deferred','trackIds':[],'resultIds':[],'note':'最终24篇审计完成；仅partial sources，按editorial policy继续deferred。未从含混的25%-55%×摘要字符串推导标准化加速成绩。'}
dump('catalog/benchmarks.json',bench); dump('maintenance/benchmark-review.json',review)
print('part1',len(tracks),'tracks',len(rs),'results')
