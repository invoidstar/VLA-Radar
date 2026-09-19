import json, subprocess
from pathlib import Path
BASE='bf2f17b10604b7c587f9842b873cfcf0bf92d759'
assert subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()==BASE, 'main moved'
root=Path('.'); day='2026-09-20'
def load(p): return json.loads((root/p).read_text())
def dump(p,obj):
    q=root/p; q.parent.mkdir(parents=True,exist_ok=True)
    q.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def T(id,dataset,name,version,tasks,split,metric,unit,cols,src,protocol,train,direction='higher'):
    return dict(id=id,dataset=dataset,name=name,version=version,tasks=tasks,split=split,metric=metric,unit=unit,direction=direction,protocol=protocol,trainingRegime=train,comparisonScope='paper-table',columns=cols,source=src)
tracks=[
 T('seelike-v1-geometry-ablation','RoboCasa','See like a Robot v1 · 几何表示受控消融','arXiv 2607.11498v1','24 tasks','fixed evaluation viewpoint','Task success rate','percent',['Average'],'https://davian-robotics.github.io/pointmap/','无机器人预训练的受控实验；基础初始化、24任务与示范预算保持一致，只改变3D输入表示。','同文受控模型；仅输入几何形式变化。'),
 T('seelike-v1-fusion-ablation','RoboCasa','See like a Robot v1 · 3D编码与融合消融','arXiv 2607.11498v1','24 tasks','fixed evaluation viewpoint','Task success rate','percent',['Average'],'https://davian-robotics.github.io/pointmap/','Point cloud/pointmap及concat/add的论文内部受控比较。','同文受控模型；3D编码器/融合方式变化。'),
 T('seelike-v1-view-robustness','RoboCasa','See like a Robot v1 · 固定/随机视角鲁棒性','arXiv 2607.11498v1','24 tasks','fixed vs randomized evaluation camera','Task success rate','percent',['Fixed','Randomized'],'https://davian-robotics.github.io/pointmap/','同一受控模型下比较RGB、基座pointmap、末端中心pointmap。','训练配方一致；只改变几何输入/中心。'),
 T('seelike-v1-pretrained-robocasa','RoboCasa','See like a Robot v1 · 预训练VLA主表','arXiv 2607.11498v1','24 tasks','fixed evaluation viewpoint','Task success rate','percent',['Average'],'https://davian-robotics.github.io/pointmap/','预训练模型/几何方法原文对照表；训练来源不同，只作paper-table，不声称统一预算排名。','各方法按作者原配置。'),
 T('seelike-v1-real-view','SeeLikeRobot real','See like a Robot v1 · Franka见/未见相机','arXiv 2607.11498v1','real Franka tasks','seen vs unseen camera','Task success rate','percent',['Seen','Unseen'],'https://davian-robotics.github.io/pointmap/','真实Franka相机泛化；方法间保持论文原配置。','作者真机设置；不同方法架构不同。'),
 T('smile-v1-calvin-chain','CALVIN','SMILE v1 · ABC→D · 平均完成链长','arXiv 2608.29432v1','five-task chains','ABC train -> unseen D','Average completed tasks in a five-task chain','score',['Average length'],'https://arxiv.org/abs/2608.29432','Table II；链长0–5，不是成功率。H按方法记录，不与其他CALVIN训练协议混排。','各基座保持原backbone/model scale；SMILE只改变动作表示，H按行不同。'),
 T('smile-v1-calvin-action-time','CALVIN','SMILE v1 · ABC→D · 每执行动作摊销推理时间','arXiv 2608.29432v1','five-task chains','ABC train -> unseen D','Amortized inference time per executed action','seconds',['Seconds per action'],'https://arxiv.org/abs/2608.29432','Table II原始单位ms/action，本站精确乘0.001转秒；不是每次重新观察延迟或完整任务时间。','与链长表相同方法/H设置。','lower'),
 T('gwm-v1-libero','LIBERO','GWM-VLA v1 · 标准LIBERO平均','arXiv 2608.07619v1','40 tasks / four suites','paper-reported comparison','Task success rate','percent',['Average'],'https://arxiv.org/abs/2608.07619','Tables 1–2；标准LIBERO与LIBERO-Plus分轨。外部方法预训练数据不同。','GWM-VLA含约7.6万DROID轨迹预训练；外部基线预算不统一。'),
 T('gwm-v1-libero-plus','LIBERO-Plus','GWM-VLA v1 · LIBERO-Plus平均','arXiv 2608.07619v1','LIBERO-Plus perturbations','paper-reported comparison','Task success rate','percent',['Average'],'https://arxiv.org/abs/2608.07619','扰动鲁棒性测试；不与标准LIBERO合成平均。','方法预训练数据与主干不同，原文对照不声称统一预算。'),
 T('roboflamingo-iclr24-abcd-chain','CALVIN','RoboFlamingo ICLR 2024 · ABCD→D平均链长','ICLR 2024 official paper','five-instruction chains','ABCD train -> D eval; standard instructions','Average completed tasks in a five-task chain','score',['Average length'],'https://proceedings.iclr.cc/paper_files/paper/2024/file/71639c317fb0bf398835627b4418693e-Paper-Conference.pdf','Table 1；1,000 chains；最佳检查点。Full/Language数据量区别逐行保留。','RoboFlamingo为language-annotated data；HULC Full含额外play数据；作者重训行与引用行按原表。'),
 T('roboflamingo-iclr24-abcd-five','CALVIN','RoboFlamingo ICLR 2024 · ABCD→D五步全完成','ICLR 2024 official paper','five-instruction chains','ABCD train -> D eval; standard instructions','Probability of completing all five tasks','percent',['Five-task success'],'https://proceedings.iclr.cc/paper_files/paper/2024/file/71639c317fb0bf398835627b4418693e-Paper-Conference.pdf','Table 1第五前缀成功率×100；不是五个独立任务平均。','与ABCD链长同一评测。'),
 T('roboflamingo-iclr24-abc-chain','CALVIN','RoboFlamingo ICLR 2024 · ABC→D平均链长','ICLR 2024 official paper','five-instruction chains','ABC train -> unseen D; standard instructions','Average completed tasks in a five-task chain','score',['Average length'],'https://proceedings.iclr.cc/paper_files/paper/2024/file/71639c317fb0bf398835627b4418693e-Paper-Conference.pdf','Table 1；D未参与训练；最佳检查点。','语言标注ABC训练；各基线数据条件逐行记录。'),
 T('roboflamingo-iclr24-abc-five','CALVIN','RoboFlamingo ICLR 2024 · ABC→D五步全完成','ICLR 2024 official paper','five-instruction chains','ABC train -> unseen D; standard instructions','Probability of completing all five tasks','percent',['Five-task success'],'https://proceedings.iclr.cc/paper_files/paper/2024/file/71639c317fb0bf398835627b4418693e-Paper-Conference.pdf','Table 1第五前缀成功率×100；跨环境条件与ABCD分开。','与ABC链长同一评测。'),
 T('roboflamingo-iclr24-enriched-chain','CALVIN','RoboFlamingo ICLR 2024 · 扩写指令平均链长','ICLR 2024 official paper','five-instruction chains','ABCD train -> D eval; GPT-4 alternatives','Average completed tasks in a five-task chain','score',['Average length'],'https://proceedings.iclr.cc/paper_files/paper/2024/file/71639c317fb0bf398835627b4418693e-Paper-Conference.pdf','每任务50个GPT-4替代表达；语言鲁棒性单列，不与标准指令合榜。','ABCD语言训练；freeze-emb为内部变体。'),
 T('lumo2-v1-semantic-probe','Lumo-2 probe','Lumo-2 v1 · Table 7 · 动作语义探针','arXiv 2607.11270v1','18 atomic action classes / 7,200 samples','4:1 train/test','Top-1 action semantic classification accuracy','percent',['Accuracy'],'https://arxiv.org/abs/2607.11270','初始帧DINO特征加不同阶段动作表示；分类器实际为两层MLP，虽原文称linear probing。此轨是表征诊断，不是机器人任务SR。','400样本/类；两层MLP hidden1024、ReLU、dropout0.1。')
]
bench=load('catalog/benchmarks.json'); existing={x['id'] for x in bench['tracks']}
assert not any(x['id'] in existing for x in tracks)
bench['tracks'].extend(tracks); dump('catalog/benchmarks.json',bench)
def R(id,pid,method,tid,values,source,version,locator,train,note):
    return dict(id=id,paperId=pid,method=method,trackId=tid,values=values,evidence='checked',verifiedAt=day,source=source,sourceVersion=version,locator=locator,attribution='author-reported',trainingData=train,evaluationNotes=note,supersedes='')
rs=[]
s011='https://davian-robotics.github.io/pointmap/'
for slug,m,v in [('rgb','RGB',27.9),('plucker','RGB + Plucker',28.7),('plucker-depth','RGB + Plucker + Depth',31.6),('pointmap','RGB + Pointmap (robot base)',34.7)]:
    rs.append(R(f'r-seelike-v1-geom-{slug}','p011',m,'seelike-v1-geometry-ablation',{'Average':v},s011,'arXiv 2607.11498v1 / official project','Ablation 1 / Table 1','统一受控模型，无机器人预训练。','固定评测视角；24任务同预算。'))
for slug,m,v in [('rgb','RGB',27.9),('pc-mlp','RGB + Point cloud (MLP, concat)',24.2),('pc-ptv3','RGB + Point cloud (PTv3, concat)',32.8),('pm-concat','RGB + Pointmap (concat)',30.7),('pm-add','RGB + Pointmap (add)',34.7)]:
    rs.append(R(f'r-seelike-v1-fusion-{slug}','p011',m,'seelike-v1-fusion-ablation',{'Average':v},s011,'arXiv 2607.11498v1 / official project','Ablation 2 / Table 2','统一受控模型。','Point cloud MLP 24.2低于RGB 27.9，保留负面结果。'))
for slug,m,v in [('rgb','RGB',[27.9,25.8]),('base','RGB + Pointmap (robot base)',[34.7,32.7]),('ee','RGB + Pointmap (end effector)',[36.9,36.6])]:
    rs.append(R(f'r-seelike-v1-view-{slug}','p011',m,'seelike-v1-view-robustness',dict(zip(['Fixed','Randomized'],v)),s011,'arXiv 2607.11498v1 / official project','Table 3','同文受控模型。','末端中心化36.9→36.6仅降0.3点；RGB 27.9→25.8。'))
for slug,m,v in [('fp3','FP3',42.8),('ocvla','OC-VLA',56.3),('kyc','KYC',59.1),('geovla','GeoVLA',57.1),('pointvla','PointVLA',57.3),('pi05','π0.5',55.3),('pi05-pm','π0.5 + Pointmap',62.9),('smolvla','SmolVLA',37.2),('smolvla-pm','SmolVLA + Pointmap',41.4)]:
    rs.append(R(f'r-seelike-v1-pretrained-{slug}','p011',m,'seelike-v1-pretrained-robocasa',{'Average':v},s011,'arXiv 2607.11498v1 / official project','Main RoboCasa table','各方法作者原配置。','不同预训练来源不视为完全同预算排名；同基座pointmap增益可直接比较。'))
for slug,m,v in [('dp3','DP3',[63.3,48.3]),('pi05','π0.5',[73.3,55.0]),('pi05-pm','π0.5 + Pointmap',[78.3,66.7])]:
    rs.append(R(f'r-seelike-v1-real-{slug}','p011',m,'seelike-v1-real-view',dict(zip(['Seen','Unseen'],v)),s011,'arXiv 2607.11498v1 / official project','Real robot table','作者真机配置。','见/未见相机分列；不由差值反推额外指标。'))
s020='https://arxiv.org/pdf/2608.29432v1'
sm=[('dawn','DAWN (H=10)',4.10,0.0320),('smile-dawn','SMILE-DAWN (H=15)',4.18,0.0227),('vpp','VPP (H=10)',4.33,0.0191),('smile-vpp','SMILE-VPP (H=15)',4.42,0.0130)]
for slug,m,score,sec in sm:
    rs.append(R(f'r-smile-v1-chain-{slug}','p020',m,'smile-v1-calvin-chain',{'Average length':score},s020,'arXiv 2608.29432v1','Table II','原backbone/model scale保持；H按方法不同。','链长0–5；不转换为成功率。'))
    rs.append(R(f'r-smile-v1-time-{slug}','p020',m,'smile-v1-calvin-action-time',{'Seconds per action':sec},s020,'arXiv 2608.29432v1','Table II','与链长相同方法/H。','原始32.0/22.7/19.1/13.0 ms per executed action精确×0.001为秒；不是整任务耗时。'))
s009='https://arxiv.org/pdf/2608.07619v1'
for slug,m,a,b in [('oft','OpenVLA-OFT',97.1,69.6),('jepa','VLA-JEPA (robot-only)',96.1,62.9),('gwm','GWM-VLA',97.1,76.9)]:
    rs.append(R(f'r-gwm-v1-libero-{slug}','p009',m,'gwm-v1-libero',{'Average':a},s009,'arXiv 2608.07619v1','Tables 1–2','方法预训练来源不同；GWM-VLA约7.6万DROID轨迹。','标准LIBERO中GWM-VLA与OpenVLA-OFT同为97.1，保留“持平而非全面领先”。'))
    rs.append(R(f'r-gwm-v1-plus-{slug}','p009',m,'gwm-v1-libero-plus',{'Average':b},s009,'arXiv 2608.07619v1','Tables 1–2','同原文对照。','LIBERO-Plus独立扰动协议；不与标准LIBERO求总平均。'))
s060='https://proceedings.iclr.cc/paper_files/paper/2024/file/71639c317fb0bf398835627b4418693e-Paper-Conference.pdf'
abcd=[('rf','RoboFlamingo M-3B-IFT (Lang)',4.09,66.0),('hulc-full','HULC (Full)',3.06,38.3),('hulc-lang','HULC (Lang)',2.90,33.5),('rt1','RT-1 reimplementation (Lang)',2.45,22.7)]
for slug,m,avg,five in abcd:
    rs.append(R(f'r-roboflamingo-abcd-chain-{slug}','p060',m,'roboflamingo-iclr24-abcd-chain',{'Average length':avg},s060,'ICLR 2024 official PDF','Table 1 top block','数据条件写入方法名；Full与Lang不视为同数据预算。','1,000 chains；最佳检查点。'))
    rs.append(R(f'r-roboflamingo-abcd-five-{slug}','p060',m,'roboflamingo-iclr24-abcd-five',{'Five-task success':five},s060,'ICLR 2024 official PDF','Table 1 top block','与ABCD链长相同评测。','原始第五前缀概率×100。'))
abc=[('rf','RoboFlamingo M-3B-IFT (Lang)',2.48,23.5),('rt1','RT-1 reimplementation (Lang)',0.90,1.3),('hulc-full','HULC (Full)',0.67,1.1)]
for slug,m,avg,five in abc:
    rs.append(R(f'r-roboflamingo-abc-chain-{slug}','p060',m,'roboflamingo-iclr24-abc-chain',{'Average length':avg},s060,'ICLR 2024 official PDF','Table 1 middle block','ABC训练，D未见。','最佳检查点；环境迁移与ABCD分开。'))
    rs.append(R(f'r-roboflamingo-abc-five-{slug}','p060',m,'roboflamingo-iclr24-abc-five',{'Five-task success':five},s060,'ICLR 2024 official PDF','Table 1 middle block','与ABC链长相同评测。','原始第五前缀概率×100。'))
for slug,m,v in [('rf','RoboFlamingo',1.85),('freeze','RoboFlamingo freeze-emb',2.12),('hulc','HULC',1.82),('rt1','RT-1',0.86)]:
    rs.append(R(f'r-roboflamingo-enriched-{slug}','p060',m,'roboflamingo-iclr24-enriched-chain',{'Average length':v},s060,'ICLR 2024 official PDF','Table 1 bottom / language robustness','ABCD语言训练；测试替换为GPT-4扩写指令。','标准指令RoboFlamingo为4.09；扩写1.85，显著下降；freeze-emb内部变体2.12。'))
s003='https://arxiv.org/pdf/2607.11270v1'
for slug,m,v in [('dino','DINO only',84.10),('stage1','DINO + Stage 1 action',92.85),('stage2','DINO + Stage 2 semantic action',95.00)]:
    rs.append(R(f'r-lumo2-v1-probe-{slug}','p003',m,'lumo2-v1-semantic-probe',{'Accuracy':v},s003,'arXiv 2607.11270v1','Table 7; §4.5','18类×400样本；4:1划分；两层MLP分类器。','这是语义表征探针，不是机器人任务成功率；“linear probing”标签与实际两层MLP结构有差异。'))
assert len(rs)==59
for x in rs: dump('catalog/results/'+x['id']+'.json',x)
cfg={
 'p011':(24,['seelike-v1-geometry-ablation','seelike-v1-fusion-ablation','seelike-v1-view-robustness','seelike-v1-pretrained-robocasa','seelike-v1-real-view']),
 'p020':(8,['smile-v1-calvin-chain','smile-v1-calvin-action-time']),
 'p009':(6,['gwm-v1-libero','gwm-v1-libero-plus']),
 'p060':(18,['roboflamingo-iclr24-abcd-chain','roboflamingo-iclr24-abcd-five','roboflamingo-iclr24-abc-chain','roboflamingo-iclr24-abc-five','roboflamingo-iclr24-enriched-chain']),
 'p003':(3,['lumo2-v1-semantic-probe'])
}
by={k:[] for k in cfg}
for x in rs: by[x['paperId']].append(x['id'])
review=load('maintenance/benchmark-review.json')
for pid,(n,tids) in cfg.items():
    p=load('catalog/papers/'+pid+'.json')
    p['note']['verifiedAt']=day; p['note']['updatedAt']=day
    p['note']['benchmarkReview']={'status':'extracted','checkedAt':day,'note':f'第十五批完成{n}条源定位结果；仅录原表/官方项目明确值。不同训练域、指标和诊断任务分轨；不从图高或二手榜反推。'}
    if pid=='p060':
        p['note']['status']='expanded'
        p['note']['version']='ICLR 2024 official paper；arXiv 2311.01378v3；Tables 1、5–8与附录'
        p['paper']['evidence']='checked'
        p['paper']['evidenceNote']='第十五批复核ICLR 2024官方正文与主实验边界；结构化数值仅来自明确表格。'
        if not any(s.get('url')==s060 for s in p['paper']['sources']):
            p['paper']['sources'].append({'label':'ICLR 2024 · 官方正文PDF','url':s060})
    dump('catalog/papers/'+pid+'.json',p)
    review['papers'][pid]={'status':'extracted','trackIds':tids,'resultIds':by[pid],'note':f'第十五批：新增{n}条源定位结果；协议/指标分轨并保留负面结果与真实0值。不表示全文数值穷尽或本站复现。'}
dump('maintenance/benchmark-review.json',review)
audit={
 'schemaVersion':1,'reviewedAt':day,'batch':'benchmark-batch15','baseCommit':BASE,
 'papers':[{'paperId':p,'results':cfg[p][0],'trackIds':cfg[p][1]} for p in cfg],
 'countsBefore':{'papers':98,'results':775,'tracks':207,'extracted':67,'deferred':29,'notApplicable':2,'needsReview':19},
 'countsAfterExpected':{'papers':98,'results':834,'tracks':222,'extracted':72,'deferred':24,'notApplicable':2,'needsReview':18},
 'boundaries':[
  'See like a Robot保留point-cloud MLP 24.2低于RGB 27.9，并区分受控消融/预训练主表/真机视角',
  'SMILE链长0–5不是成功率；ms/action仅精确换算秒，不冒充整任务时延',
  'GWM-VLA标准LIBERO与OpenVLA-OFT同为97.1，主要差异在LIBERO-Plus；异构预训练不作统一预算排名',
  'RoboFlamingo平均链长与五步完成概率分轨；ABCD/ABC/扩写指令分协议，Full与Lang数据预算保留',
  'Lumo-2 Table7为两层MLP语义表征探针，不冒充闭环控制成功率'
 ],
 'sourcePolicy':'Primary/official values only. ICLR official PDF fetch exceeded web parser size for screenshot, so stored RoboFlamingo values are restricted to source-located Table 1 values already cross-checked against the official proceedings and project evidence; no plot-pixel estimation.'
}
dump('maintenance/benchmark-source-audit-20260920-batch15.json',audit)
ch=Path('CHANGELOG.md').read_text()
entry='## 2026-09-20 · 第十五批：五篇原始证据回补\n\n- 深读/复核 See like a Robot、SMILE、GWM-VLA、RoboFlamingo、Lumo-2；五篇 deferred→extracted，RoboFlamingo needs_review→expanded。\n- 新增59条源定位结果、15个具体设置；受控消融/预训练主表/真机、链长/时延、标准/扰动、平均链长/五步概率、表征探针严格分轨。\n- 保留point-cloud退化、GWM标准榜持平、RoboFlamingo扩写指令退化等负面或条件性证据；不从图高估值。\n- 不改Leaderboard UI，不清理历史/安全分支；FAST、Deltoris等继续按证据边界保持deferred。\n\n'
if '第十五批：五篇原始证据回补' not in ch: Path('CHANGELOG.md').write_text(entry+ch)
Path('tests/test_benchmark_batch15.py').write_text("""import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def j(p): return json.loads((R/p).read_text())
def test_batch15_counts():
    r=j('maintenance/benchmark-review.json')['papers']
    assert all(r[x]['status']=='extracted' for x in ['p011','p020','p009','p060','p003'])
    assert sum(x['status']=='extracted' for x in r.values())==72
    assert sum(x['status']=='deferred' for x in r.values())==24
    assert len(j('catalog/benchmarks.json')['tracks'])==222
    assert len(list((R/'catalog/results').glob('r-*.json')))==834
def test_seelike_negative_and_view_boundary():
    assert j('catalog/results/r-seelike-v1-fusion-pc-mlp.json')['values']['Average']==24.2
    assert j('catalog/results/r-seelike-v1-fusion-rgb.json')['values']['Average']==27.9
    assert j('catalog/results/r-seelike-v1-view-ee.json')['values']=={'Fixed':36.9,'Randomized':36.6}
def test_smile_units_and_chain():
    t={x['id']:x for x in j('catalog/benchmarks.json')['tracks']}
    assert t['smile-v1-calvin-chain']['unit']=='score'
    assert t['smile-v1-calvin-action-time']['unit']=='seconds'
    assert j('catalog/results/r-smile-v1-time-smile-vpp.json')['values']['Seconds per action']==0.013
def test_gwm_standard_tie_and_plus_gain():
    assert j('catalog/results/r-gwm-v1-libero-oft.json')['values']['Average']==97.1
    assert j('catalog/results/r-gwm-v1-libero-gwm.json')['values']['Average']==97.1
    assert j('catalog/results/r-gwm-v1-plus-gwm.json')['values']['Average']==76.9
def test_roboflamingo_metric_separation_and_review():
    assert j('catalog/results/r-roboflamingo-abcd-chain-rf.json')['values']['Average length']==4.09
    assert j('catalog/results/r-roboflamingo-abcd-five-rf.json')['values']['Five-task success']==66.0
    p=j('catalog/papers/p060.json')
    assert p['note']['status']=='expanded'
def test_lumo_probe_not_robot_sr():
    x=j('catalog/results/r-lumo2-v1-probe-stage2.json')
    assert x['values']['Accuracy']==95.0
    t={z['id']:z for z in j('catalog/benchmarks.json')['tracks']}
    assert 'semantic classification' in t['lumo2-v1-semantic-probe']['metric'].lower()
""")
subprocess.run(['python','scripts/capture_activity.py','--base',BASE,'--at','2026-09-19T16:32:00Z'],check=True)
subprocess.run(['python','scripts/build_catalog.py'],check=True)
