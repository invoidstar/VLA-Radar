"""One-time, reproducible v1 -> per-paper v2 migration. Never rewrites IDs/KEY RESULT."""
from pathlib import Path
from catalog_core import load, write, migrate_paper, add_event

ROOT=Path(__file__).resolve().parents[1]
WHEN='2026-09-17'
SOURCES={
'p001':('https://arxiv.org/html/2608.27550v1','arXiv v1'),
'p004':('https://arxiv.org/html/2607.15330v2','arXiv v2'),
'p021':('https://arxiv.org/html/2608.00725v1','arXiv v1'),
'p064':('https://openvla.github.io/','作者项目页；2026-09-17 核验'),
'p069':('https://arxiv.org/html/2502.19645v1','arXiv v1'),
'p076':('https://arxiv.org/html/2601.16163v1','arXiv v1')}
# Independently authored reading summaries, not copied abstracts or paper text.
NOTES={
'p001':[
('problem','研究问题：迁移表征，而非固定策略','论文把持续预训练的目标从拟合一个动作头，转为得到可迁移的视觉语言骨干。判断收益时，需要固定下游动作头、初始化方式、数据与训练预算，再比较骨干；只看预训练动作损失不能回答迁移是否改善。'),
('contributions','主要贡献与创新','三个设计相互配合：保留 VLM 先验、多种连续动作头共同监督、跨本体部分统一的动作布局。区别不只是增加数据，而是减少骨干对某一种机器人接口和动作头的过度专门化。'),
('mechanism','方法机制与训练路径','持续预训练冻结视觉编码器和 LLM 的较低层，图像描述联合训练为可训练层提供语义约束；机器人数据提供动作监督。下游再放开模型适配，并允许重新连接任务动作头，不能将“冻结预训练”误读为“下游始终冻结”。'),
('evidence','关键结果应怎样阅读','§4 的 LIBERO-Plus 是扰动鲁棒性测试，不是标准 LIBERO 总分；Table 1 中 VLAct 为 82.6%，内部 Qwen3VL-OFT 对照为 75.0%。这组控制比较比不同数据规模模型之间的横向比较更能解释配方的贡献。'),
('transfer','跨本体迁移的含义','RoboCasa-GR1 的结果关注预训练未见的人形本体：使用 20% 下游轨迹达到 49.5%，全数据 GR00T-N1.6 对照为 47.6%。这是低数据适配，仍需要后训练，不能写成零样本操控。'),
('limits','证据边界与阅读重点','优先核对冻结、动作头和动作布局消融，以及下游固定配置的范围。RoboTwin 的少量 clean 训练与增加 randomized 专家示范属于不同赛道；训练算力和检查点选择也不一定跨论文一致。本文结论来自作者报告，不代表本站独立复现。')],
'p004':[
('problem','研究问题与整体定位','论文研究大规模真实操控数据如何转化为可迁移的机器人基础模型。主线同时涉及 UMI 轨迹规模、视觉语言标注、模型训练和跨本体适配，不能把整体结果直接归因于某一个新增模块。'),
('contributions','主要贡献与创新','核心组合是规模化 UMI 数据采集、基于状态变化的自动描述，以及与机器人策略联合训练的视觉语言／动作专家体系。它试图连接数据覆盖、语义理解与连续动作生成，而不是只替换动作解码器。'),
('mechanism','模型与两阶段训练','骨干采用 Qwen3-VL 与 DiT 动作专家的组合。预训练使用状态转移描述获得语义与动作联系；后训练再对齐面向执行的指令和混合本体数据。注意文本描述监督与实际部署指令不是同一种输入分布。'),
('protocol','实验设置与可比性','§3.4 的 RoboCasa 使用 24 项任务、每任务 300 条合成示范，并在五种场景中评测每任务 100 个回合。RoboCasa365 另用 50 项评测任务：18 项原子、16 项已见组合和16项未见组合；不能称为“365 项任务的平均”。'),
('results','主要结果与原文不一致','RoboCasa365 Table 3 的平均成功率为 57.4%，三个子集为 80.2%、57.1%、32.1%。引言中另出现 57.6%；本站保留冲突提示并采用具体表格值，不取较高数字。该结果单独建赛道，不与旧版 RoboCasa 24 任务混排。'),
('limits','局限与优先阅读内容','先分别阅读数据构建、训练输入、跨本体控制空间和未见组合任务，再评价泛化。更大数据、不同初始化与不同评测预算同时变化时，领先结果不等于架构改动的纯增益。既有 KEY RESULT 保持不变，本笔记补充 v2 的设置与证据定位。')],
'p021':[
('problem','研究问题：未来是否真正受动作控制','仅预测当前场景后续视频，可能学到观察相关性，而不是给定动作造成的后果。SelfWAM 在统一世界动作模型中加入明确动作条件，并用机器人自身的运动区域强化这种关联。'),
('contributions','主要贡献与差异','一是给未来视觉分支提供干净的示范动作；二是预测未来机器人 self-mask，强调可控制的自身运动。定向信息流使视觉预测可读动作，但动作策略不能读取干净动作标签或未来观测，防止训练信息泄漏。'),
('mechanism','训练目标与部署流程','训练联合动作和视觉 flow matching，视觉任务在 RGB 与 self-mask 之间切换。部署默认只去噪动作块，不生成未来视频；世界模型的诊断／反事实预测是可选路径，不能把两条路径的时延混写。'),
('protocol','数据与评测口径','RoboTwin 2.0 使用 2,500 条 clean 与 25,000 条场景随机化专家示范，分别评测 clean/random，每任务 100 次。Table 1 的比较属于这一配方，不可与只使用 50 条 clean 示范的结果合并排名。'),
('ablation','消融比最高分更重要','Table 4：FastWAM 平均 91.84%；仅加动作条件未来 RGB 为 90.80%；再加 self-mask 为 92.62%。因此不能总结成“动作条件本身就提升策略”，增益需要结合 self-mask 和具体实验解释。'),
('limits','有效性边界与阅读重点','动作扰动实验检验预测是否随干预方向变化，比仅看视频逼真度更直接。真机只有四项任务、每任务十次，95% 是这组作者实验的平均，不能视为广泛泛化保证。部署时延、遮罩来源及动作信息隔离应单独核对。')],
'p064':[
('problem','问题与方法定位','OpenVLA 关注可开放获取、可适配的通用视觉语言动作模型。它将视觉语言预训练模型连接到跨机器人动作数据，使机器人策略的预训练、微调和部署能够沿同一开放实现进行。'),
('contributions','主要贡献','贡献包括开放的 7B 级策略与训练实现、跨机器人示范上的动作学习，以及实际新任务适配分析。开放权重和数据处理链路本身是复现价值的一部分，但不应与某个单独模块的精度增益等同。'),
('mechanism','视觉表征与动作输出','视觉侧结合 DINOv2 与 SigLIP 特征，再与语言骨干共同处理图像和指令；动作通过离散 token 表达。理解这一路径，有助于区分原始 OpenVLA 与后续连续动作、并行输出配方。'),
('adaptation','微调与计算效率','作者研究低秩适配与量化，以降低新机器人／任务的微调和部署门槛。评估“高效”时要同时看显存、训练设置、推理速度和任务成功率，不能仅凭参数可训练比例判断部署成本。'),
('limits','能力与限制','公开项目页也讨论窄任务分布下专用策略可能更强的情况。跨本体预训练和开放实现不意味着任意机器人零样本可用；动作规范、观测输入和下游示范仍影响适配结果。'),
('publication','发表状态与阅读路线','先读视觉与动作接口，再读新任务适配和失败案例。该工作已收入 CoRL 2024 的 PMLR 270 论文集；会议年份与论文集的 2025 年出版信息分开记录，最早 arXiv 日期仍为 2024-06-13。')],
'p069':[
('problem','研究问题与实验思路','工作并不主要扩展模型规模，而是系统考察 VLA 微调设计如何同时影响成功率与推理吞吐。它将串行动作 token 预测、动作块长度和训练目标拆开比较，强调可执行的微调配方。'),
('contributions','核心贡献与创新','OFT 组合并行解码、动作分块与连续 L1 回归。关键是解除动作 token 逐个生成的开销，并在同一观察下输出一段控制序列。后续 OFT+ 的语言条件增强需要与基础 OFT 配方分开描述。'),
('mechanism','方法运行方式','多步动作在一次模型前向中并行预测；连续输出不再完全沿用原始离散 token 的逐步生成方式。与扩散头比较时，应同时检查采样次数和输入模态，不能只用动作头名称解释分数差异。'),
('results','证据与输入设置','v1 Table I 的多视角 OpenVLA-OFT 平均为 97.1%；单第三人称视角下，增加并行分块和连续 L1 后为 95.3%。这两个数字对应不同输入组；本站将单视角控制比较和多视角结果分开保存。'),
('efficiency','速度指标怎么读','Table II 的吞吐分析固定单张 224 像素图像、7 维动作及 A100 条件。论文的动作输出吞吐倍数不能直接写成整个机器人闭环同倍数加速；执行分块还会改变反应频率。'),
('limits','局限、版本与发表','动作块长度带来吞吐和反馈及时性的权衡，连续回归也需关注多模态动作分布。本文 v1 的实验笔记不是 v2 全文复核；已确认 RSS 2025 正式论文页，最早 arXiv 为 2025-02-27，不随会议发表改变。')],
'p076':[
('problem','研究问题与贡献定位','Cosmos Policy 研究如何把视频生成基础模型转化为直接控制策略，同时获得世界模型与价值预测能力。核心不是把视频预测作为外接展示，而是将动作、未来状态与价值纳入同一建模体系。'),
('mechanism','联合预测机制','方法从 Cosmos 视频模型初始化，将连续动作与状态／价值目标接入生成过程。可分别用于条件动作生成、给定动作的后果预测和价值估计；这些功能共享训练框架，但部署时的输入条件不同。'),
('planning','直接策略与规划不可混淆','仿真主表报告直接策略。更强的基于模型规划还使用额外策略 rollout 数据对世界模型和价值函数后训练，再评估候选动作。不能把规划收益全部归到最初的示范学习检查点。'),
('protocol','评测预算与任务定义','LIBERO 为四套共 40 项任务，每任务 50 回合、三个随机种子；RoboCasa 为旧版 24 项厨房任务，每任务 50 回合、三个种子。RoboCasa 仅使用每任务 50 条人工示范，需单列训练预算。'),
('ablation','主要证据与消融','直接策略平均成功率在 LIBERO 为 98.5%，RoboCasa 为 67.1%。移除辅助监督下降 1.5 个百分点、随机初始化下降 3.9 个百分点；这支持联合目标和视频先验的作用，但不是所有组件相互独立的证明。'),
('limits','局限与阅读重点','世界模型可能难以预测遮挡下的抓取失败，额外 rollout 后训练与规划开销也属于成本。主表中引用的其他工作未必使用同样示范数量和种子，所以提供论文对照表与独立协议赛道，不宣称跨论文公平总榜。')]
}

def main():
    if (ROOT/'catalog/manifest.json').exists():
        print('Catalog v2 already present; migration skipped.');return
    data=load(ROOT/'data/papers.json'); order=[p['id'] for p in data['papers']]
    write(ROOT/'catalog/manifest.json',{'schemaVersion':2,**{k:v for k,v in data.items() if k not in {'schemaVersion','papers'}},'paperOrder':order})
    write(ROOT/'catalog/first-public.json',{p['id']:p['firstPublished'] for p in data['papers']})
    records={p['id']:migrate_paper(p,WHEN) for p in data['papers']}
    for pid,sections in NOTES.items():
        url,version=SOURCES[pid]
        records[pid]['note']={'status':'expanded','updatedAt':WHEN,'verifiedAt':WHEN,'version':version,
            'sections':[{'id':sid,'title':title,'body':body,'sources':[{'label':version+' · 方法／实验与附录','url':url}]} for sid,title,body in sections]}
    records['p064']['note']['sections'][-1]['sources']=[{'label':'CoRL 2024 · PMLR 270','url':'https://proceedings.mlr.press/v270/kim25c.html'},{'label':'arXiv 版本历史','url':'https://arxiv.org/abs/2406.09246'}]
    records['p069']['note']['sections'][-1]['sources'].append({'label':'RSS 2025 正式页面','url':'https://www.roboticsproceedings.org/rss21/p017.html'})
    records['p004']['publication']['alerts'].append('arXiv v2 的 RoboCasa365 引言为 57.6%，Table 3 为 57.4%；榜单采用 Table 3，冲突尚待作者澄清。')
    # The following dates/versions were explicitly checked on arXiv history, not inferred from IDs.
    for pid,first,version,updated in [('p064','2024-06-13','v3','2024-09-05'),('p069','2025-02-27','v2','2025-04-28')]:
        p=records[pid]['paper'];pub=records[pid]['publication'];src=f'https://arxiv.org/abs/{p["arxiv"]}'
        pub.update(firstArxivAt=first,firstArxivSource=src+'v1',latestArxivVersion=version,latestArxivAt=updated,lastCheckedAt=WHEN)
        add_event(pub,'arxiv_first',first,src+'v1',note='arXiv submission history v1',observed=WHEN)
        add_event(pub,'arxiv_version',updated,src+version,note=version,observed=WHEN)
    for pid,venue,dt,url,doi in [('p064','CoRL 2024','2025-01-12','https://proceedings.mlr.press/v270/kim25c.html',''),('p069','RSS 2025','2025-06','https://www.roboticsproceedings.org/rss21/p017.html','10.15607/RSS.2025.XXI.017')]:
        r=records[pid];r['publication'].update(status='published',venue=venue,doi=doi,publishedAt=dt)
        add_event(r['publication'],'published',dt,url,venue,'正式论文集；出版日期与会议年份分开，未推断录用日期。',WHEN)
        r['paper'].update(venue=venue,publicationType='conference',publicationStatus=venue+' · 正式论文集',doi=doi)
        r['paper']['sources'].append({'label':venue+' 正式论文页','url':url})
    # Newer metadata does not imply that the notes were reread at that newer version.
    records['p069']['note']['status']='needs_review'
    for pid,r in records.items():write(ROOT/f'catalog/papers/{pid}.json',r)
    tracks=[];results=[]
    def track(id,dataset,name,version,tasks,split,protocol,training,columns,source,scope='protocol'):
        t=dict(id=id,dataset=dataset,name=name,version=version,tasks=tasks,split=split,metric='Task success rate',unit='percent',direction='higher',protocol=protocol,trainingRegime=training,comparisonScope=scope,columns=columns,source=source);tracks.append(t);return t
    def row(t,pid,method,vals,source,version,locator,training,evalnote,own=False):
        import re
        rid='r-'+t['id']+'-'+re.sub('[^a-z0-9]+','-',method.lower()).strip('-')
        results.append(dict(id=rid,paperId=pid,method=method,trackId=t['id'],values=dict(zip(t['columns'],vals)),evidence='checked',verifiedAt=WHEN,source=source,sourceVersion=version,locator=locator,attribution='author-reported' if own else 'reported-baseline',trainingData=training,evaluationNotes=evalnote,supersedes=''))
    u=SOURCES['p021'][0]
    t=track('robotwin2-selfwam-27500','RoboTwin','RoboTwin 2.0 · 27,500 示范 · SelfWAM 协议','2.0','50','clean + randomized','每任务、每设置 100 回合；两种设置分别平均。作者同文比较，不是本站复现。','2,500 clean + 25,000 randomized 专家示范；不同方法预训练基础不同',['Clean','Random','Average'],u)
    for method,vals in [('pi0',[65.92,58.40,62.16]),('pi0.5',[82.74,76.76,79.75]),('Motus',[88.66,87.02,87.84]),('GigaWorld-Policy',[86.36,85.04,85.70]),('FastWAM',[91.82,91.86,91.84]),('SelfWAM',[92.16,93.08,92.62])]:row(t,'p021',method,vals,u,'arXiv v1','Table 1; §4 Benchmarks',t['trainingRegime'],t['protocol'],method=='SelfWAM')
    u=SOURCES['p069'][0]
    t=track('libero-oft-single-view','LIBERO','LIBERO · 单视角 · OFT 控制比较','standard four suites','40','Spatial / Object / Goal / Long','OpenVLA 变体：每套 500 回合；仅第三人称图像与语言。种子数未据此推断。','同文微调配方；不同动作目标／解码方式',['Spatial','Object','Goal','Long','Average'],u)
    for method,vals in [('OpenVLA',[84.7,88.4,79.2,53.7,76.5]),('OpenVLA-PD-AC',[91.3,92.7,90.5,86.5,90.2]),('OpenVLA-PD-AC-L1',[96.2,98.3,96.2,90.7,95.3]),('OpenVLA-PD-AC-Diffusion',[96.9,98.1,95.5,91.1,95.4])]:row(t,'p069',method,vals,u,'arXiv v1','Table I · single-view block',t['trainingRegime'],t['protocol'],True)
    t=track('libero-oft-multi-view','LIBERO','LIBERO · 多视角 · OpenVLA-OFT','standard four suites','40','Spatial / Object / Goal / Long','第三人称 + 腕部图像和状态；每套 500 回合；不与单视角合榜。','每任务 50 示范；采用论文描述的过滤',['Spatial','Object','Goal','Long','Average'],u)
    row(t,'p069','OpenVLA-OFT',[97.6,98.4,97.9,94.5,97.1],u,'arXiv v1','Table I · multi-view block',t['trainingRegime'],t['protocol'],True)
    u=SOURCES['p076'][0]
    t=track('libero-cosmos-3seeds','LIBERO','LIBERO · Cosmos Policy · 三种子','standard four suites','40','Spatial / Object / Goal / Long','10任务×50回合×4套×3种子=6000回合；直接策略，非额外规划模型。','每任务50条示范；策略训练过滤失败轨迹',['Spatial','Object','Goal','Long','Average'],u)
    row(t,'p076','Cosmos Policy',[98.1,100,98.2,97.6,98.5],u,'arXiv v1','Table 1; §5.1',t['trainingRegime'],t['protocol'],True)
    t=track('robocasa24-cosmos-50demos','RoboCasa','RoboCasa 24 · 50 条人工示范','24-task Panda benchmark','24','five scenes; unseen object instances','每任务50回合×3种子=3600回合；五场景，其中两种未见风格；直接策略。','每任务50条人工示范',['Average'],u)
    row(t,'p076','Cosmos Policy',[67.1],u,'arXiv v1','Table 2; §5.1',t['trainingRegime'],t['protocol'],True)
    t=track('robocasa24-cosmos-table','RoboCasa','RoboCasa 24 · 论文对照表（不同训练预算）','24-task Panda benchmark','24','paper-reported comparison','原文 Table 2 汇总。基线评测种子和训练预算并非统一；只列来源表，不生成公平名次。','50 / 300 / 1000 / 3000 示范等，逐行标注',['Average'],u,'paper-table')
    for method,val,dem in [('GR00T-N1',49.6,'300'),('UVA',50.0,'50'),('DP-VLA',57.3,'3000'),('GR00T-N1-DreamGen',57.6,'300 + 10000 synthetic'),('GR00T-N1-DUST',58.5,'300'),('UWM',60.8,'1000'),('pi0',62.5,'300'),('GR00T-N1.5',64.1,'300'),('Video Policy',66.0,'300'),('FLARE',66.4,'300'),('GR00T-N1.5-HAMLET',66.4,'300'),('Cosmos Policy',67.1,'50')]:row(t,'p076',method,[val],u,'arXiv v1','Table 2',dem+' demos/task',t['protocol'],method=='Cosmos Policy')
    u=SOURCES['p004'][0]
    t=track('robocasa24-xiaomi-300demos','RoboCasa','RoboCasa 24 · 300 条合成示范','24-task benchmark','24','five scenes','每任务100回合；五评测场景；不得与50示范/三种子赛道直接合并。','每任务300条合成示范',['Average'],u)
    row(t,'p004','Xiaomi-Robotics-1',[74.5],u,'arXiv v2','Table 2; §3.4',t['trainingRegime'],t['protocol'],True)
    t=track('robocasa365-xiaomi-50tasks','RoboCasa','RoboCasa365 · 50 项评测任务','365-task collection; evaluated subset of 50','50 = 18 atomic + 16 seen-composite + 16 unseen-composite','atomic / seen composite / unseen composite','依 Table 3 的50任务子集；并非365任务总平均。完整种子设置仍以原文为准。','每任务100条示范',['Atomic','Seen composite','Unseen composite','Average'],u)
    row(t,'p004','Xiaomi-Robotics-1',[80.2,57.1,32.1,57.4],u,'arXiv v2','Table 3; §3.4',t['trainingRegime'],t['protocol']+' 引言57.6与表格57.4不一致，此处使用表格。',True)
    write(ROOT/'catalog/benchmarks.json',{'schemaVersion':1,'tracks':tracks})
    for r in results:write(ROOT/f'catalog/results/{r["id"]}.json',r)
    write(ROOT/'maintenance/v2-migration.json',{'schemaVersion':1,'migratedAt':WHEN,'papers':len(order),'expandedNotes':list(NOTES),'results':len(results),'tracks':len(tracks),'fullLibraryReverified':False,'firstPublicDatesChanged':0,'keyResultsChanged':0,'notes':'旧笔记未冒充重新读全文；新版本元数据与笔记核验分开。'})
    print(f'Migrated {len(order)} papers; {len(NOTES)} enriched notes; {len(results)} results; {len(tracks)} tracks.')
if __name__=='__main__':main()
