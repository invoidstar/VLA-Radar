import json
from pathlib import Path
ROOT=Path('.'); DAY='2026-09-20'
def load(p): return json.loads((ROOT/p).read_text())
def dump(p,o):
 q=ROOT/p; q.parent.mkdir(parents=True,exist_ok=True); q.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def T(id,dataset,name,version,tasks,split,metric,unit,cols,src,protocol,training,direction='higher'):
 return dict(id=id,dataset=dataset,name=name,version=version,tasks=tasks,split=split,metric=metric,unit=unit,direction=direction,protocol=protocol,trainingRegime=training,comparisonScope='paper-table',columns=cols,source=src)
def R(id,pid,method,tid,values,src,ver,loc,train,note):
 return dict(id=id,paperId=pid,method=method,trackId=tid,values=values,evidence='checked',verifiedAt=DAY,source=src,sourceVersion=ver,locator=loc,attribution='author-reported',trainingData=train,evaluationNotes=note,supersedes='')
bench=load('catalog/benchmarks.json'); review=load('maintenance/benchmark-review.json'); rs=[]
tracks=[
 T('meco-v1-robotwin','RoboTwin','MECo-WAM v1 · RoboTwin clean/random','arXiv 2607.05468v1','RoboTwin 2.0','clean / randomized','Task success rate','percent',['Clean','Random'],'https://arxiv.org/abs/2607.05468','Fast-WAM与MECo-WAM同文比较；辅助4D专家部署时移除。','同文WAM设置。'),
 T('meco-v1-real-success','MECo-WAM real','MECo-WAM v1 · 真实任务成功率','arXiv 2607.05468v1','stack blocks / sort by size','paper real-robot trials','Task success rate','percent',['Stack blocks','Sort by size'],'https://arxiv.org/html/2607.05468v1','真实两任务；缺失组合不按零处理。','Fast-WAM vs MECo-WAM。'),
 T('meco-v1-real-corrections','MECo-WAM real','MECo-WAM v1 · 叠方块纠正次数','arXiv 2607.05468v1','stack blocks','same real-robot setting','Average correction count','score',['Corrections'],'https://arxiv.org/html/2607.05468v1','纠正次数越低越好，与成功率分轨。','Fast-WAM vs MECo-WAM。','lower'),
 T('gemini-er-v1-aloha2-sim','ALOHA2 sim','Gemini Robotics-ER v1 · Table 5 · 代码控制','arXiv 2503.20020v1','7 simulation tasks','50 random initializations per task','Task success rate','percent',['Zero-shot code','In-context demos'],'https://arxiv.org/html/2503.20020v1','这是Gemini Robotics-ER的ALOHA2仿真代码控制，不是主VLA真实机器人动作模型榜。','Gemini 2.0 Flash vs Gemini Robotics-ER。'),
 T('dreamzero-v1-progress','DreamZero real','DreamZero v1 · Table 3 · 收桌面Task Progress','arXiv 2602.15922v1','table-clearing task','4-step vs 1-step / Flash','Task progress','percent',['Task Progress'],'https://arxiv.org/html/2602.15922v1','Task Progress不是最终二值SR；±标准误保留在说明，不塞进主值。','原模型/Flash不同采样配置。'),
 T('dreamzero-v1-latency','DreamZero real','DreamZero v1 · Table 3 · 单次模型延迟','arXiv 2602.15922v1','table-clearing task','same Table 3','Model latency','seconds',['Latency'],'https://arxiv.org/html/2602.15922v1','350/150ms精确换算秒；不是完整机器人回路端到端延迟。','原模型/Flash不同采样配置。','lower'),
 T('adavla-v2-libero-sr','LIBERO','AdaVLA v2 · Table III · pi0.5组件/阈值成功率','arXiv 2608.29208v2','LIBERO','Jetson AGX Orin; pi0.5 ablation','Task success rate','percent',['Average'],'https://arxiv.org/html/2608.29208v2','Table III全行保存；不同ODE步数/剪枝/阈值分行。','training-free inference variants。'),
 T('adavla-v2-libero-latency','LIBERO','AdaVLA v2 · Table III · pi0.5组件/阈值片段延迟','arXiv 2608.29208v2','LIBERO','Jetson AGX Orin; pi0.5 ablation','Action-chunk latency','seconds',['Latency'],'https://arxiv.org/html/2608.29208v2','Table III ms精确×0.001；指定Orin硬件与pi0.5配置。','training-free inference variants。','lower'),
 T('dyna2-2026-scaling','Dyna-2 real','Dyna-2 · 14任务人类视频预训练规模律','Dyna official technical report Aug 2026','14 real robot tasks','matched post-training at four human-video scales','Mean normalized on-robot performance','percent',['Normalized performance'],'https://www.dyna.co/dyna-2','1k/10k/100k/1M小时为嵌套人类视频集合；每级相同机器人后训练配方。','每任务最多10小时机器人后训练；14任务宏观归一化表现。'),
 T('dyna2-2026-customer-pass','Dyna-2 real','Dyna-2 · 客户现场零样本production pass','Dyna official technical report Aug 2026','production deployment tasks','matched post-training; unseen customer sites','Production pass-criteria rate','percent',['On-site pass'],'https://www.dyna.co/dyna-2','官方报告Dyna-1 46%、Dyna-2 87%；相同后训练预算，现场数据未参与训练。','Dyna-1 vs early Dyna-2 matched comparison。'),
 T('mimic-v2-simpler','SimplerEnv','mimic-video v2 · SIMPLER四任务平均','arXiv 2512.15692v2 / RSS 2026','4 SIMPLER tasks','default vs per-task tau_v','Task success rate','percent',['Average'],'https://arxiv.org/html/2512.15692v2','默认配置与逐任务tau_v调节分开保留；后者不是统一超参结果。','内部pi0.5-style参考与mimic-video。'),
 T('mimic-v2-libero3','LIBERO','mimic-video v2 · LIBERO三套件平均','arXiv 2512.15692v2 / RSS 2026','3 suites excluding Long','paper-reported average','Task success rate','percent',['Average'],'https://arxiv.org/html/2512.15692v2','该表不含Long；未报告项不按零。','内部参考、mimic-video、外部OpenVLA-OFT。'),
 T('vlatalker-v1-libero','LIBERO','VLA-Talker v1 · Tables 1–2 · Gen-CoT对照','arXiv 2608.05738v1','LIBERO four suites','paper main protocol','Task success rate','percent',['Average','Long'],'https://arxiv.org/html/2608.05738v1','只录可核验LIBERO平均与Long；RoboCasa汇总口径不在此补造。','Gen-CoT vs VLA-Talker。'),
 T('sparkvla-v1-task-sr','RoboCerebra','SparkVLA v1 · Table 3 · 层级选择任务成功率','arXiv 2608.16172v1','RoboCerebra long-horizon','internal decision ablation','Task success rate','percent',['SR'],'https://arxiv.org/html/2608.16172v1','固定长度/AQC/配对排名/统一排名受控比较。','同文层级VLA决策接口。'),
 T('sparkvla-v1-stop-acc','RoboCerebra','SparkVLA v1 · Table 3 · Stop准确率','arXiv 2608.16172v1','RoboCerebra long-horizon','same ablation','Stop decision accuracy','percent',['Accuracy'],'https://arxiv.org/html/2608.16172v1','Stop准确率与整任务SR是不同指标，分轨。','同文层级VLA决策接口。')
]
old={x['id'] for x in bench['tracks']}; assert not any(t['id'] in old for t in tracks); bench['tracks'].extend(tracks)
# MECo
for slug,m,v in [('fast','Fast-WAM',[91.88,91.78]),('meco','MECo-WAM',[93.26,91.98])]:
 rs.append(R(f'r-meco-v1-rt-{slug}','p008',m,'meco-v1-robotwin',dict(zip(['Clean','Random'],v)),'https://arxiv.org/abs/2607.05468','arXiv 2607.05468v1','Tables 2–3','same paper setting','RoboTwin条件分开。'))
for slug,m,v in [('fast','Fast-WAM',[60,60]),('meco','MECo-WAM',[60,70])]:
 rs.append(R(f'r-meco-v1-real-{slug}','p008',m,'meco-v1-real-success',dict(zip(['Stack blocks','Sort by size'],v)),'https://arxiv.org/html/2607.05468v1','arXiv 2607.05468v1','Table 3','real robot','叠块成功率持平60%，排序提升；非全面提升。'))
for slug,m,v in [('fast','Fast-WAM',1.67),('meco','MECo-WAM',0.83)]:
 rs.append(R(f'r-meco-v1-corr-{slug}','p008',m,'meco-v1-real-corrections',{'Corrections':v},'https://arxiv.org/html/2607.05468v1','arXiv 2607.05468v1','Table 3','real stack task','越低越好。'))
# Gemini ER
for slug,m,v in [('flash','Gemini 2.0 Flash',[27,51]),('er','Gemini Robotics-ER',[53,65])]:
 rs.append(R(f'r-gemini-er-v1-{slug}','p071',m,'gemini-er-v1-aloha2-sim',dict(zip(['Zero-shot code','In-context demos'],v)),'https://arxiv.org/html/2503.20020v1','arXiv 2503.20020v1','Table 5','ALOHA2 simulation code-control','七任务×50随机初始条件；两列控制方式不同。'))
# DreamZero
dream=[('4step','Original model, 4 steps',83,0.350),('1step','Original model, 1 step',52,0.150),('flash','DreamZero-Flash, 1 step',74,0.150)]
for slug,m,prog,lat in dream:
 rs.append(R(f'r-dreamzero-v1-progress-{slug}','p077',m,'dreamzero-v1-progress',{'Task Progress':prog},'https://arxiv.org/html/2602.15922v1','arXiv 2602.15922v1','Table 3','table-clearing evaluation','点估计；标准误不改变主值。'))
 rs.append(R(f'r-dreamzero-v1-lat-{slug}','p077',m,'dreamzero-v1-latency',{'Latency':lat},'https://arxiv.org/html/2602.15922v1','arXiv 2602.15922v1','Table 3','same evaluation','原始ms换秒。'))
# AdaVLA full Table III
ada=[
 ('b10','Baseline, 10 steps',98.65,0.95854),
 ('pr-adp15','PR + Adaptive, threshold 0.15',99.45,0.51335),
 ('svd-adp','SVD + Adaptive',99.65,0.89478),
 ('fixed-adp','Fixed pruning + Adaptive',99.35,0.49200),
 ('noprun-adp','No pruning + Adaptive',98.65,0.53232),
 ('pr-noadp','PR only, no Adaptive',99.25,0.92571),
 ('pr-adp20','PR + Adaptive, threshold 0.20',99.20,0.42824),
 ('pr-adp25','PR + Adaptive, threshold 0.25',98.40,0.41326),
 ('b1','Baseline, 1 step',97.05,0.44745),
 ('b5','Baseline, 5 steps',98.00,0.67756),
 ('brand','Baseline, random steps',98.65,0.69413)
]
for slug,m,sr,lat in ada:
 rs.append(R(f'r-adavla-v2-sr-{slug}','p030',m,'adavla-v2-libero-sr',{'Average':sr},'https://arxiv.org/html/2608.29208v2','arXiv 2608.29208v2','Table III','pi0.5 on Jetson AGX Orin','成功率与延迟分轨；阈值更激进时98.40低于10步基线98.65，保留退化。'))
 rs.append(R(f'r-adavla-v2-lat-{slug}','p030',m,'adavla-v2-libero-latency',{'Latency':lat},'https://arxiv.org/html/2608.29208v2','arXiv 2608.29208v2','Table III','pi0.5 on Jetson AGX Orin','原始ms精确换秒。'))
# Dyna-2
for slug,m,v in [('1k','1k human-video hours',20),('10k','10k hours',28),('100k','100k hours',45),('1m','1M hours',53)]:
 rs.append(R(f'r-dyna2-scale-{slug}','p005',m,'dyna2-2026-scaling',{'Normalized performance':v},'https://www.dyna.co/dyna-2','Dyna official technical report Aug 2026','§3.3 / Figure scaling discussion','matched robot post-training','14任务均值；normalized to attainable maximum，不称二值SR。'))
for slug,m,v in [('d1','Dyna-1',46),('d2','Dyna-2',87)]:
 rs.append(R(f'r-dyna2-site-{slug}','p005',m,'dyna2-2026-customer-pass',{'On-site pass':v},'https://www.dyna.co/dyna-2','Dyna official technical report Aug 2026','§4.2 / Figure 14','matched pre/post-training; unseen customer sites','官方现场验收pass rate；in-house接近100为近似值未入榜。'))
# mimic-video
for slug,m,v in [('pi','pi0.5-style internal reference',35.4),('default','mimic-video default',46.9),('tuned','mimic-video per-task tau_v',56.3)]:
 rs.append(R(f'r-mimic-v2-simpler-{slug}','p038',m,'mimic-v2-simpler',{'Average':v},'https://arxiv.org/html/2512.15692v2','arXiv 2512.15692v2 / RSS 2026','Table I','paper protocol','逐任务调参单独标注。'))
for slug,m,v in [('pi','pi0.5-style internal reference',85.9),('mimic','mimic-video',93.9),('oft','OpenVLA-OFT external',96.9)]:
 rs.append(R(f'r-mimic-v2-libero-{slug}','p038',m,'mimic-v2-libero3',{'Average':v},'https://arxiv.org/html/2512.15692v2','arXiv 2512.15692v2 / RSS 2026','Table II','3 suites excluding Long','外部参考预算不同，仅paper-table。'))
# VLA-Talker
for slug,m,v in [('gen','Gen-CoT',[96.2,91.6]),('talker','VLA-Talker',[97.4,93.6])]:
 rs.append(R(f'r-vlatalker-v1-libero-{slug}','p006',m,'vlatalker-v1-libero',dict(zip(['Average','Long'],v)),'https://arxiv.org/html/2608.05738v1','arXiv 2608.05738v1','Tables 1–2','paper protocol','自由形式推理并非所有任务都带来收益；这里只保存明确汇总。'))
# Spark
spark=[('fixed','Fixed length + independent Stop',34.26,79.52),('aqc','Adaptive length AQC',40.92,80.43),('paired','Paired ranking',42.53,80.37),('unified','Unified ranking',47.12,96.65)]
for slug,m,sr,acc in spark:
 rs.append(R(f'r-spark-v1-sr-{slug}','p019',m,'sparkvla-v1-task-sr',{'SR':sr},'https://arxiv.org/html/2608.16172v1','arXiv 2608.16172v1','Table 3','same hierarchy','任务SR。'))
 rs.append(R(f'r-spark-v1-stop-{slug}','p019',m,'sparkvla-v1-stop-acc',{'Accuracy':acc},'https://arxiv.org/html/2608.16172v1','arXiv 2608.16172v1','Table 3','same hierarchy','Stop准确率不等于任务SR。'))
assert len(rs)==58,len(rs)
for r in rs: dump('catalog/results/'+r['id']+'.json',r)
cfg={
 'p008':(['meco-v1-robotwin','meco-v1-real-success','meco-v1-real-corrections'],6,None,None),
 'p071':(['gemini-er-v1-aloha2-sim'],2,None,None),
 'p077':(['dreamzero-v1-progress','dreamzero-v1-latency'],6,None,None),
 'p030':(['adavla-v2-libero-sr','adavla-v2-libero-latency'],22,'expanded','arXiv 2608.29208 v2；Tables II–IV；IROS 2026录用信息与当前v2复核'),
 'p005':(['dyna2-2026-scaling','dyna2-2026-customer-pass'],6,None,None),
 'p038':(['mimic-v2-simpler','mimic-v2-libero3'],6,'expanded','arXiv 2512.15692 v2；Tables I–III；RSS 2026；v2修订不改变本批主表口径'),
 'p006':(['vlatalker-v1-libero'],2,None,None),
 'p019':(['sparkvla-v1-task-sr','sparkvla-v1-stop-acc'],8,None,None)
}
by={k:[] for k in cfg}
for r in rs: by[r['paperId']].append(r['id'])
for pid,(tids,n,status,ver) in cfg.items():
 p=load('catalog/papers/'+pid+'.json'); p['note']['verifiedAt']=DAY; p['note']['updatedAt']=DAY
 p['note']['benchmarkReview']={'status':'extracted','checkedAt':DAY,'note':f'最终24篇清理：提取{n}条精确记录；成功率、Task Progress、延迟、归一化分数与诊断指标严格分轨。'}
 if status: p['note']['status']=status
 if ver: p['note']['version']=ver
 if pid=='p030':
  url='https://arxiv.org/html/2608.29208v2'
  if not any(s.get('url')==url for s in p['paper']['sources']): p['paper']['sources'].append({'label':'当前复核版本 · v2','url':url})
 if pid=='p038':
  url='https://arxiv.org/html/2512.15692v2'
  if not any(s.get('url')==url for s in p['paper']['sources']): p['paper']['sources'].append({'label':'当前复核版本 · v2','url':url})
 dump('catalog/papers/'+pid+'.json',p)
 review['papers'][pid]={'status':'extracted','trackIds':tids,'resultIds':by[pid],'note':f'最终24篇清理：{n}条源定位结果；不同指标/协议/训练条件不合并，负面结果保留。'}
dump('catalog/benchmarks.json',bench); dump('maintenance/benchmark-review.json',review)
print('part2',len(tracks),'tracks',len(rs),'results')
