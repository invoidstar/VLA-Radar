import json, subprocess
from pathlib import Path
BASE='f102ab13eba5a28b4bf98aff01c7e94d49e5c04d'
assert subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()==BASE, 'main moved'
root=Path('.'); day='2026-09-19'
def load(p): return json.loads((root/p).read_text())
def dump(p,obj):
    q=root/p; q.parent.mkdir(parents=True,exist_ok=True)
    q.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def T(id,dataset,name,version,tasks,split,metric,columns,source,protocol,training,direction='higher'):
    return dict(id=id,dataset=dataset,name=name,version=version,tasks=tasks,split=split,metric=metric,unit='percent',direction=direction,protocol=protocol,trainingRegime=training,comparisonScope='paper-table',columns=columns,source=source)
tracks=[
  T('ocvlapp-v1-maniskill2-ablation','ManiSkill2','OC-VLA++ v1 · Table 3 · 同架构视角监督消融','arXiv 2608.01066v1','5 task categories','multi-view simulation','Average task success rate',['Average'],'https://arxiv.org/pdf/2608.01066v1','ManiSkill2五类任务论文内部消融；同Dita架构。只比较OC-VLA及监督变体。','同文Dita设置；paired-view/等变监督按行变化。'),
  T('ocvlapp-v1-real-dita-view','OC-VLA++ real robot','OC-VLA++ v1 · Dita · 固定/最大相机位移','arXiv 2608.01066v1','real Franka tasks','fixed camera vs largest tested displacement','Task success rate',['Fixed view','Largest displacement'],'https://arxiv.org/pdf/2608.01066v1','真实Franka；每任务10条示范，每任务每相机设置20次rollout；最大位移约30.48cm/23.40deg。','Dita架构内部OC-VLA与OC-VLA++对照。'),
  T('ocvlapp-v1-real-qwen-view','OC-VLA++ real robot','OC-VLA++ v1 · Qwen3-VL flow · 固定/最大相机位移','arXiv 2608.01066v1','real Franka tasks','fixed camera vs largest tested displacement','Task success rate',['Fixed view','Largest displacement'],'https://arxiv.org/pdf/2608.01066v1','真实Franka；每任务10条示范，每任务每相机设置20次rollout。与Dita架构分轨。','Qwen3-VL-2B + flow action expert；同架构内部比较。'),
  T('temporalflow-v1-libero-main','LIBERO','TemporalFlow-VLA v1 · 三种子主结果','arXiv 2608.26821v1','40 tasks / four suites','3 seeds; 500 rollouts per suite per seed','Task success rate',['Long','Average'],'https://arxiv.org/abs/2608.26821','四套件联合训练30k步；这里只存摘要/正文明确的Long与总体平均，不补其余套件精确值。','同文TemporalFlow-VLA主模型；3 seeds (0,2,5)。'),
  T('temporalflow-v1-robotwin12-ablation','RoboTwin','TemporalFlow-VLA v1 · 12任务时序接口消融','arXiv 2608.26821v1','12 tasks','clean / randomized','Task success rate',['Clean','Random'],'https://arxiv.org/abs/2608.26821','12任务子集；每任务50 clean+500 random示范，clean/random各100次评测；不是完整50任务榜。','同文π0.5基础与历史接口消融。'),
  T('vtwam-v1-real-main','VT-WAM real robot','VT-WAM v1 · 六任务综合报告','arXiv 2607.02503v1','6 contact-rich tasks','20 trials per method-task','Paper mixed completion score',['Average'],'https://vt-wam.github.io/','表面三任务允许0/0.5/1部分完成，插入三任务二值；论文称success rate，但本站标为混合完成分数。','每任务100人工示范、逐任务训练；模型预训练不同。'),
  T('vtwam-v1-ablation','VT-WAM real robot','VT-WAM v1 · Table III · 触觉时序与AVTAG消融','arXiv 2607.02503v1','Wipe Vase / Insert Tube','same demonstrations','Task score / success rate',['Wipe Vase score','Insert Tube SR'],'https://arxiv.org/abs/2607.02503','Wipe Vase允许部分完成得分；Insert Tube为二值SR。两列口径不同，仅作为论文内部消融并列显示。','所有变体从Fast-WAM加不同触觉建模/注意力设计。'),
  T('vlaflow-v2-libero','LIBERO','VLAFlow v2 · 内部训练范式 · LIBERO','arXiv 2607.01586v2','40 tasks / four suites','paper-reported average','Task success rate',['Average'],'https://github.com/MindVLA-Team/VLAFlow','官方表格；内部变体共享框架但预训练监督不同。','下游统一配方；Robot PT/辅助监督按行变化。'),
  T('vlaflow-v2-libero-plus','LIBERO-Plus','VLAFlow v2 · 内部训练范式 · LIBERO-Plus','arXiv 2607.01586v2','LIBERO-Plus perturbation benchmark','paper-reported total','Task success rate',['Total'],'https://github.com/MindVLA-Team/VLAFlow','官方表格；LIBERO-Plus与标准LIBERO分轨。','内部变体；Robot PT/辅助监督按行变化。'),
  T('vlaflow-v2-simpler-widowx','SimplerEnv','VLAFlow v2 · SimplerEnv WidowX','arXiv 2607.01586v2','WidowX tasks','Bridge-only downstream fine-tuning','Task success rate',['WidowX Average'],'https://github.com/MindVLA-Team/VLAFlow','官方README明确WidowX使用Bridge-only FT。','同文内部变体；不同预训练监督。'),
  T('vlaflow-v2-simpler-rt1','SimplerEnv','VLAFlow v2 · SimplerEnv RT-1','arXiv 2607.01586v2','RT-1 Google robot tasks','RT-1-only downstream fine-tuning','Task success rate',['RT-1 VM','RT-1 VA'],'https://github.com/MindVLA-Team/VLAFlow','官方README明确RT-1-only FT；VM与VA同轨不同列。','同文内部变体；不同预训练监督。'),
  T('onevomemory-v1-libero-long','LIBERO','OnEvoMemory v1 · LIBERO Long 10任务','arXiv 2608.08749v1','10 long-horizon tasks','base / offline memory / one online round','Task success rate',['Average'],'https://arxiv.org/abs/2608.08749','冻结基础VLA；离线记忆后再用在线rollout更新记忆模块。在线阶段有额外交互，不当作同训练预算静态榜。','基于QwenOFT；base policy frozen，更新memory/value相关模块。'),
  T('onevomemory-v1-rmbench','RMBench','OnEvoMemory v1 · RMBench两任务','arXiv 2608.08749v1','SwapBlocks / SwapT','base / offline memory / one online round','Task success rate',['SwapBlocks','SwapT'],'https://arxiv.org/abs/2608.08749','只覆盖两个RMBench任务；在线阶段每任务有额外rollout，不代表完整RMBench平均。','基于QwenOFT；记忆模块离线初始化并在线演化。')
]
bench=load('catalog/benchmarks.json'); existing={x['id'] for x in bench['tracks']}
assert not any(x['id'] in existing for x in tracks)
bench['tracks'].extend(tracks); dump('catalog/benchmarks.json',bench)
def R(id,pid,method,tid,values,source,version,locator,train,note):
    return dict(id=id,paperId=pid,method=method,trackId=tid,values=values,evidence='checked',verifiedAt=day,source=source,sourceVersion=version,locator=locator,attribution='author-reported',trainingData=train,evaluationNotes=note,supersedes='')
rs=[]
s012='https://arxiv.org/pdf/2608.01066v1'
for slug,m,v in [('base','OC-VLA (Dita)',52.4),('synth','OC-VLA + synthesized-view supervision',53.4),('equiv','OC-VLA + equivariance supervision',54.2),('full','OC-VLA++',56.8)]:
    rs.append(R(f'r-ocvlapp-v1-maniskill-{slug}','p012',m,'ocvlapp-v1-maniskill2-ablation',{'Average':v},s012,'arXiv 2608.01066v1','Table 3','同Dita架构；paired-view/等变监督按变体变化。','五类ManiSkill2平均；论文内部消融。'))
for slug,m,v in [('ocvla','OC-VLA',[68.3,40.8]),('plus','OC-VLA++',[68.3,48.3])]:
    rs.append(R(f'r-ocvlapp-v1-dita-{slug}','p012',m,'ocvlapp-v1-real-dita-view',dict(zip(['Fixed view','Largest displacement'],v)),s012,'arXiv 2608.01066v1','Real-robot viewpoint evaluation','每任务10示范；每任务每相机设置20 rollout。','固定视角无提升；最大位移下提升，不能概括为所有视角都更好。'))
for slug,m,v in [('ocvla','OC-VLA',[60.0,37.5]),('plus','OC-VLA++',[59.2,43.3])]:
    rs.append(R(f'r-ocvlapp-v1-qwen-{slug}','p012',m,'ocvlapp-v1-real-qwen-view',dict(zip(['Fixed view','Largest displacement'],v)),s012,'arXiv 2608.01066v1','Real-robot viewpoint evaluation','Qwen3-VL-2B + flow action expert。','固定视角60.0→59.2的轻微下降保留；最大位移37.5→43.3。'))
s014='https://arxiv.org/abs/2608.26821'
rs.append(R('r-temporalflow-v1-libero-main','p014','TemporalFlow-VLA','temporalflow-v1-libero-main',{'Long':96.60,'Average':97.63},s014,'arXiv 2608.26821v1','Abstract; main LIBERO results','四套件联合训练30k步；3 seeds。','原文还报告±0.87/±0.26；本站当前结果schema不单列误差。其余套件未在当前精确文本中补猜。'))
for slug,m,v in [('base','π0.5',[79.0,72.3]),('multiframe','Direct multi-frame',[79.8,81.5]),('queries','Two queries, no flow supervision',[83.2,83.6]),('full','TemporalFlow-VLA',[85.5,84.2])]:
    rs.append(R(f'r-temporalflow-v1-rt12-{slug}','p014',m,'temporalflow-v1-robotwin12-ablation',dict(zip(['Clean','Random'],v)),s014,'arXiv 2608.26821v1','Table III','12任务；50 clean+500 random示范/任务；60k步。','12任务子集，不能并入完整50任务RoboTwin协议。'))
s025='https://arxiv.org/pdf/2607.02503v1'
for slug,m,v in [('omnivtla','OmniVTLA',35.83),('fastwam','Fast-WAM',45.00),('vtwam','VT-WAM',71.67)]:
    rs.append(R(f'r-vtwam-v1-main-{slug}','p025',m,'vtwam-v1-real-main',{'Average':v},s025,'arXiv 2607.02503v1','Table I; §IV-B','每任务100人工示范；逐任务训练；20次测试。','综合均值混合了0/0.5/1表面任务得分与二值插入成功，不能称六任务严格二值SR。'))
for slug,m,v in [('m0','M0 Fast-WAM',[55,25]),('m1','M1 + Sym. tactile sequence',[65,40]),('m2','M2 + Asym. first tactile frame',[40,30]),('m3','M3 + Asym. tactile sequence',[70,50]),('m4','M4 VT-WAM + AVTAG',[85,55])]:
    rs.append(R(f'r-vtwam-v1-ablation-{slug}','p025',m,'vtwam-v1-ablation',dict(zip(['Wipe Vase score','Insert Tube SR'],v)),s025,'arXiv 2607.02503v1','Table III','相同任务示范；触觉设计按变体变化。','M2擦瓶40低于视觉Fast-WAM 55，说明只加初始触觉可退化；保留负面结果。'))
source2='https://github.com/MindVLA-Team/VLAFlow'
vrows=[('pi-nopt','MindPI w/o PT',[97.0,59.9,59.6,75.7,60.4]),('wpi-nopt','MindWPI w/o PT',[97.4,66.1,71.9,75.2,51.6]),('pi-frozen','MindPI (Frozen VLM)',[97.2,74.9,54.4,72.7,66.0]),('pi-full','MindPI (Full PT)',[97.5,68.8,65.9,68.2,55.5]),('lpi','MindLPI',[97.2,72.3,65.6,74.6,59.2]),('wpi','MindWPI',[98.5,72.6,74.5,86.7,71.1]),('lwpi','MindLWPI',[99.1,74.8,75.5,84.4,69.8])]
for slug,m,v in vrows:
    common='官方项目表格；内部训练范式对照。'
    rs.append(R(f'r-vlaflow-v2-libero-{slug}','p002',m,'vlaflow-v2-libero',{'Average':v[0]},source2,'VLAFlow official README / arXiv 2607.01586v2','Internal paradigm table',common,'同文内部比较；不与其他论文不同训练预算直接公平排名。'))
    rs.append(R(f'r-vlaflow-v2-lplus-{slug}','p002',m,'vlaflow-v2-libero-plus',{'Total':v[1]},source2,'VLAFlow official README / arXiv 2607.01586v2','Internal paradigm table',common,'LIBERO-Plus与标准LIBERO分开。'))
    rs.append(R(f'r-vlaflow-v2-widowx-{slug}','p002',m,'vlaflow-v2-simpler-widowx',{'WidowX Average':v[2]},source2,'VLAFlow official README / arXiv 2607.01586v2','Internal paradigm table','WidowX使用Bridge-only FT。','Action-only Full PT并非所有迁移都更好。'))
    rs.append(R(f'r-vlaflow-v2-rt1-{slug}','p002',m,'vlaflow-v2-simpler-rt1',{'RT-1 VM':v[3],'RT-1 VA':v[4]},source2,'VLAFlow official README / arXiv 2607.01586v2','Internal paradigm table','RT-1使用RT-1-only FT。','MindPI Full PT在RT-1为68.2/55.5，低于w/o PT的75.7/60.4；负迁移保留。'))
s015='https://arxiv.org/pdf/2608.08749v1'
for slug,m,v in [('base','Base QwenOFT',86.2),('offline','Offline-initialized memory',88.6),('online','Online evolution round 1',90.2)]:
    rs.append(R(f'r-onevomemory-v1-long-{slug}','p015',m,'onevomemory-v1-libero-long',{'Average':v},s015,'arXiv 2608.08749v1','Table 1','基础policy冻结；memory/value模块按阶段训练。','在线阶段使用额外rollout，因此不是完全同训练数据预算的静态消融。'))
for slug,m,v in [('base','Base QwenOFT',[0,0]),('offline','Offline-initialized memory',[10,8]),('online','Online evolution round 1',[14,10])]:
    rs.append(R(f'r-onevomemory-v1-rmbench-{slug}','p015',m,'onevomemory-v1-rmbench',dict(zip(['SwapBlocks','SwapT'],v)),s015,'arXiv 2608.08749v1','Table 1','基础policy冻结；memory/value模块按阶段训练。','只覆盖两个RMBench任务；0是真实作者报告值，不是缺失值。'))
assert len(rs)==55
for x in rs: dump('catalog/results/'+x['id']+'.json',x)
cfg={
  'p012':(8,['ocvlapp-v1-maniskill2-ablation','ocvlapp-v1-real-dita-view','ocvlapp-v1-real-qwen-view']),
  'p014':(5,['temporalflow-v1-libero-main','temporalflow-v1-robotwin12-ablation']),
  'p025':(8,['vtwam-v1-real-main','vtwam-v1-ablation']),
  'p002':(28,['vlaflow-v2-libero','vlaflow-v2-libero-plus','vlaflow-v2-simpler-widowx','vlaflow-v2-simpler-rt1']),
  'p015':(6,['onevomemory-v1-libero-long','onevomemory-v1-rmbench'])
}
by={k:[] for k in cfg}
for x in rs: by[x['paperId']].append(x['id'])
review=load('maintenance/benchmark-review.json')
for pid,(n,tids) in cfg.items():
    p=load('catalog/papers/'+pid+'.json')
    p['note']['verifiedAt']=day; p['note']['updatedAt']=day
    p['note']['benchmarkReview']={'status':'extracted','checkedAt':day,'note':f'第十四批完成{n}条源定位结果；仅录原表/官方页面明确值。不同指标、任务子集、训练阶段和混合计分口径分开；不从图高或相对增益反推。'}
    dump('catalog/papers/'+pid+'.json',p)
    review['papers'][pid]={'status':'extracted','trackIds':tids,'resultIds':by[pid],'note':f'第十四批：新增{n}条源定位结果；主结果与消融按协议分轨，负面结果和真实0值保留；不表示全文数值穷尽或本站复现。'}
dump('maintenance/benchmark-review.json',review)
audit={
  'schemaVersion':1,'reviewedAt':day,'batch':'benchmark-batch14','baseCommit':BASE,
  'papers':[{'paperId':p,'results':cfg[p][0],'trackIds':cfg[p][1]} for p in cfg],
  'countsBefore':{'papers':98,'results':720,'tracks':194,'extracted':62,'deferred':34,'notApplicable':2,'needsReview':19},
  'countsAfterExpected':{'papers':98,'results':775,'tracks':207,'extracted':67,'deferred':29,'notApplicable':2,'needsReview':19},
  'boundaries':[
    'OC-VLA++保留Qwen固定视角60.0→59.2的退化，最大位移与固定视角同列不同条件',
    'TemporalFlow RoboTwin仅12任务子集，LIBERO只存当前可精确核验Long与Average',
    'VT-WAM六任务综合值包含部分完成得分，不冒充全二值成功率；M2擦瓶40低于Fast-WAM55',
    'VLAFlow按LIBERO/LIBERO-Plus/SimplerEnv分轨；Full PT在RT-1负迁移保留',
    'OnEvoMemory在线阶段使用额外rollout；RMBench的0为真实报告而非缺失'
  ],
  'sourcePolicy':'Primary/official source values only; no plot-pixel estimation or reverse-engineered baselines.'
}
dump('maintenance/benchmark-source-audit-20260919-batch14.json',audit)
ch=Path('CHANGELOG.md').read_text()
entry='## 2026-09-19 · 第十四批：五篇原始证据回补\n\n- 深读/复核 OC-VLA++、TemporalFlow-VLA、VT-WAM、VLAFlow、OnEvoMemory；五篇 deferred→extracted。\n- 新增55条源定位结果、13个具体设置；视角、任务子集、混合计分、训练阶段和benchmark family严格分轨。\n- 保留固定视角退化、初始触觉退化、action-only预训练负迁移与在线额外交互等负面/成本边界。\n- 不改Leaderboard UI，不清理历史/安全分支，不从Deltoris/FAST图形或不兼容硬件指标强行提取。\n\n'
if '第十四批：五篇原始证据回补' not in ch: Path('CHANGELOG.md').write_text(entry+ch)
Path('tests/test_benchmark_batch14.py').write_text("""import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def j(p): return json.loads((R/p).read_text())
def test_batch14_counts():
    r=j('maintenance/benchmark-review.json')['papers']
    assert all(r[x]['status']=='extracted' for x in ['p012','p014','p025','p002','p015'])
    assert sum(x['status']=='extracted' for x in r.values())==67
    assert sum(x['status']=='deferred' for x in r.values())==29
    assert len(j('catalog/benchmarks.json')['tracks'])==207
    assert len(list((R/'catalog/results').glob('r-*.json')))==775
def test_ocvla_fixed_negative_preserved():
    a=j('catalog/results/r-ocvlapp-v1-qwen-ocvla.json')['values']
    b=j('catalog/results/r-ocvlapp-v1-qwen-plus.json')['values']
    assert a['Fixed view']==60.0 and b['Fixed view']==59.2
    assert b['Largest displacement']==43.3
def test_temporalflow_subset_boundary():
    x=j('catalog/results/r-temporalflow-v1-rt12-full.json')
    assert x['values']=={'Clean':85.5,'Random':84.2}
    t={z['id']:z for z in j('catalog/benchmarks.json')['tracks']}
    assert t['temporalflow-v1-robotwin12-ablation']['tasks']=='12 tasks'
def test_vtwam_negative_ablation_and_mixed_metric():
    assert j('catalog/results/r-vtwam-v1-ablation-m2.json')['values']['Wipe Vase score']==40
    assert j('catalog/results/r-vtwam-v1-ablation-m0.json')['values']['Wipe Vase score']==55
    t={z['id']:z for z in j('catalog/benchmarks.json')['tracks']}
    assert 'mixed' in t['vtwam-v1-real-main']['metric'].lower()
def test_vlaflow_negative_transfer():
    a=j('catalog/results/r-vlaflow-v2-rt1-pi-nopt.json')['values']
    b=j('catalog/results/r-vlaflow-v2-rt1-pi-full.json')['values']
    assert a['RT-1 VM']==75.7 and b['RT-1 VM']==68.2
def test_onevomemory_real_zero_not_missing():
    x=j('catalog/results/r-onevomemory-v1-rmbench-base.json')
    assert x['values']=={'SwapBlocks':0,'SwapT':0}
""")
subprocess.run(['python','scripts/capture_activity.py','--base',BASE,'--at','2026-09-19T16:30:00Z'],check=True)
subprocess.run(['python','scripts/build_catalog.py'],check=True)
