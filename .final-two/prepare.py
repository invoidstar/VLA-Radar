import json, subprocess
from pathlib import Path

ROOT=Path('.')
BASE='18f9491aeb6ecd8172099054601ee1204b7f6e39'
DAY='2026-09-20'
DMS='https://ieeexplore.ieee.org/document/11479850'
VLABOT='https://www.sciencedirect.com/science/article/pii/S0736584526000475'
assert subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()==BASE, 'main moved'

def load(p): return json.loads((ROOT/p).read_text())
def dump(p,o):
    q=ROOT/p; q.parent.mkdir(parents=True,exist_ok=True)
    q.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def add_event(pub,kind,date,source,venue,note):
    e={'kind':kind,'date':date,'observedAt':DAY,'venue':venue,'source':source,'note':note}
    sig=lambda x:(x['kind'],x['date'],x['venue'],x['source'],x['note'])
    if sig(e) not in {sig(x) for x in pub['history']}: pub['history'].append(e)
def ensure_source(p,label,url):
    if not any(s.get('url')==url for s in p['paper']['sources']):
        p['paper']['sources'].append({'label':label,'url':url})
def T(id,dataset,name,version,tasks,split,metric,unit,columns,source,protocol,training,direction='higher'):
    return dict(id=id,dataset=dataset,name=name,version=version,tasks=tasks,split=split,metric=metric,unit=unit,direction=direction,
                protocol=protocol,trainingRegime=training,comparisonScope='paper-table',columns=columns,source=source)
def R(id,pid,method,track,values,source,version,locator,training,note,attribution='author-reported'):
    return dict(id=id,paperId=pid,method=method,trackId=track,values=values,evidence='checked',verifiedAt=DAY,source=source,
                sourceVersion=version,locator=locator,attribution=attribution,trainingData=training,evaluationNotes=note,supersedes='')

# ---------------- DMS-VLA full-text note ----------------
p=load('catalog/papers/p043.json')
p['paper']['team']='Chong Yu、Zhongxue Gan｜Fudan University, College of Intelligent Robotics and Advanced Manufacturing'
p['paper']['publicationStatus']='IEEE Robotics and Automation Letters 11(7):8252–8259；online 2026-04-13；DOI:10.1109/LRA.2026.3683324'
p['paper']['dateNote']='Received 2025-08-09；accepted 2026-03-11；online 2026-04-13；current version 2026-05-27'
p['paper']['contribution']='用跨层共享的Maclaurin-series weight templates与层相关系数替代每层独立Transformer权重，并依据输入复杂度动态选择参与计算的模板项数，以联合降低VLA存储和推理成本。'
p['paper']['findings']='LIBERO与SIMPLER中DMS变体总体与对应原模型接近，部分任务略升、部分略降；OpenVLA-DMS在LIBERO平均仍为76.5%，π0-DMS为94.3%。Fig.6的BF16 DMS加速约1.21×–1.56×；Table IV中叠加INT4的OpenVLA-DMS达到Jetson 2.96×、H100 2.64×。'
p['paper']['limitations']='DMS并非逐项无损：例如Octo-DMS的LIBERO Spatial 78.7低于78.9、OpenVLA-DMS的Object/Goal/Long均略低；模板越少速度和内存越好但成功率下降。摘要/结论中的“25%-55%×”字符串存在排版/语义歧义，本站只采用表格和带数值标签的图。'
p['paper']['insight']='共享模板解决参数冗余，动态项数解决输入无关的固定计算预算；两者需要和量化、缓存等额外优化分开归因。真正有价值的是成功率—速度—运行内存三轴权衡，而不是单一最大加速倍率。'
p['paper']['readingFocus']='先看Figs.1–4理解共享模板和target-action-diff，再读Tables I–IV区分模型质量与额外量化收益，最后用Fig.6和Tables V–VII检查动态策略、复杂度度量与模板数量的性能—效率折中。'
p['paper']['evidence']='checked'
p['paper']['evidenceNote']='2026-09-20根据用户提供的IEEE Xplore完整8页正式PDF逐页核读，并以IEEE Xplore公开条目作为可追溯来源；非独立实验复现。'
p['paper']['hasCautionaryResult']=True
ensure_source(p,'IEEE Xplore · 正式全文入口',DMS)
p['publication']['status']='published'
p['publication']['acceptedAt']='2026-03-11'
p['publication']['publishedAt']='2026-04-13'
p['publication']['lastCheckedAt']=DAY
p['publication']['alerts']=[
    '正式PDF摘要/结论写“up to 25%-55%× speedups”，但Fig.6带标签的BF16 DMS比值为约1.21×–1.56×，Table IV的INT4+DMS为Jetson 2.96× / H100 2.64×；本站不将该字符串自行标准化成25×–55×。'
]
add_event(p['publication'],'accepted','2026-03-11',DMS,'IEEE Robotics and Automation Letters','正式PDF首页Received/accepted信息。')
add_event(p['publication'],'published','2026-04-13',DMS,'IEEE Robotics and Automation Letters','正式PDF首页Date of publication 13 April 2026。')
p['note']={
 'status':'expanded','updatedAt':DAY,'verifiedAt':DAY,
 'version':'IEEE Robotics and Automation Letters 11(7), July 2026, pp.8252–8259；完整正式PDF；Tables I–VII、Figs.1–6',
 'coverage':{'level':'deep','scope':'primary-methods-experiments','source':DMS},
 'sections':[
  {'id':'problem','title':'问题：VLA的层间参数冗余与固定计算预算同时限制部署',
   'body':'论文把VLA部署瓶颈拆成两类：Transformer每层独立Q/K/V、输出投影与FFN权重带来高常驻内存，而所有输入都走固定深度/固定计算又浪费简单场景的算力。DMS-VLA不是只做token缓存或单独量化，而是直接重参数化Transformer权重，并让每次输入动态决定使用多少共享模板。理解结果时必须分别记录模型质量、平均每帧延迟加速和运行内存，不能从其中一个指标替代另外两个。',
   'sources':[{'label':'§I–II；正式全文', 'url':DMS}]},
  {'id':'templates','title':'共享Maclaurin模板：跨层共享大矩阵，层差异保留在系数',
   'body':'§III-A把每层FFN、输出投影及Q/K/V权重表示为少量共享Maclaurin-series weight templates的线性组合，每层仍有独立可学习系数；Q/K/V因形状一致可共享同一模板组，FFN和输出投影使用各自模板组。作者的内存论证来自K个Transformer块远多于模板数M/N/L，而系数只是标量。这个结构与INT4量化不同：前者减少需要存储的独立大矩阵，后者改变数值精度。',
   'sources':[{'label':'§III-A，Eqs.1–3，Figs.1–2', 'url':DMS}]},
  {'id':'dynamic','title':'动态展开：full-frame-diff与target-action-diff按输入复杂度选择项数',
   'body':'§III-B提出两类复杂度信号。full-frame-diff直接比较相邻帧；target-action-diff先利用语言提示抽取目标对象和相关动作，过滤背景与无关视觉token，再计算相邻帧差异。差异越小使用越少的低阶模板，变化越复杂则加入更多高阶模板。论文还比较MSE、Mahalanobis及带IoU权重的版本；因此“动态”并不是提前知道未来专家动作，而是根据当前语言和观察得到的任务相关变化分配计算。',
   'sources':[{'label':'§III-B，Figs.3–4', 'url':DMS}]},
  {'id':'training','title':'训练与部署条件：DMS变体沿用原模型损失和超参数',
   'body':'实验使用PyTorch 2.2.0，训练/微调在H100集群上完成；部署使用TensorRT 8.6（H100、RTX4090）与JetPack 6.0（Jetson AGX Orin）。脚注明确每个DMS变体采用与对应原模型相同的loss和训练超参数，早期尝试过原权重与Maclaurin近似之间的辅助L2，后来发现只用原始loss也能收敛。Table IV另有INT4的OpenVLA-DMS，必须与BF16 DMS单独归因。',
   'sources':[{'label':'§IV开头与脚注2', 'url':DMS}]},
  {'id':'protocol','title':'评测协议：LIBERO、SIMPLER与真实机器人三类成功口径不同',
   'body':'LIBERO每个suite按6个随机种子×10任务×50 episodes报告，论文写为3000 trials；SIMPLER采用Visual Matching并遵循各任务默认试验数。真实ALOHA和Emergen各评估put balls into box、clean table、stack bowls三任务，但其“success rate”按任务步骤计分：每完成一个步骤获得分数，最终SR为earned points/total points，因此更接近分步完成率而不是整段二值episode成功。本站将三者分成独立protocol。',
   'sources':[{'label':'§IV-A；Tables I–III', 'url':DMS}]},
  {'id':'results','title':'主结果：DMS总体接近原模型，但不是每个单元格都更高',
   'body':'Table I中π0从94.2%到π0-DMS 94.3%、UniVLA从95.5%到95.6%、OpenVLA-OFT从97.1%到97.2%，但Octo平均仍75.1%、OpenVLA平均仍76.5%，且部分suite略降。Table II的SIMPLER平均提升也很小，例如π0 58.8→59.0、RoboVLM 60.8→60.9。Table III真实平台同样是小幅变化。这支持“压缩后大体保持质量”，不支持“DMS对所有模型和任务都提升”。',
   'sources':[{'label':'Tables I–III', 'url':DMS}]},
  {'id':'deployment','title':'部署收益：BF16 DMS本身与INT4+DMS的倍率必须分开',
   'body':'Fig.6直接给出DMS相对对应naive VLA的每帧平均延迟加速：LIBERO上Jetson/RTX4090/H100分别约1.45–1.56×、1.37–1.50×、1.27–1.41×，SIMPLER约1.40–1.53×、1.33–1.46×、1.21–1.38×。Table IV在统一OpenVLA比较中，BF16 OpenVLA-DMS为Jetson 1.56×、H100 1.41×；INT4 OpenVLA-DMS为2.96×/2.64×，这是DMS叠加量化后的系统，不应归因成DMS单独收益。',
   'sources':[{'label':'Fig.6；Table IV', 'url':DMS}]},
  {'id':'ablation','title':'消融：任务相关差异、IoU加权和12个模板构成推荐折中',
   'body':'Table V显示target-action-diff在两套DMS模型上总体优于full-frame-diff；Table VI中MSE-IoU与Mahalanobis-IoU优于未加IoU的对应度量。Table VII最清楚展示质量—效率交换：12模板时LIBERO/SIMPLER平均76.5/33.0，Jetson/H100为1.56×/1.41×且运行内存为基线41%/53%；降到2模板时加速1.85×/1.78×、内存11%/17%，但成功率跌到72.9/30.3。作者因此推荐12模板而非追求最大压缩。',
   'sources':[{'label':'Tables V–VII', 'url':DMS}]},
  {'id':'limits','title':'证据边界：数学动机、摘要加速字符串与统计显著性都要谨慎',
   'body':'论文将Maclaurin级数作为共享权重的建模动机，但工程有效性主要由实验支持，而不是一个对任意Transformer权重族的严格有限项逼近定理。主表大量差异只有0.1–0.4个百分点，论文没有为这些单元格提供置信区间，因此不应宣称稳定显著提升。正式PDF摘要和结论中的“25%-55%×”存在明显排版/单位歧义；本站只使用Table IV、Table VII和Fig.6中明确标注的比值与内存百分比。',
   'sources':[{'label':'Abstract、§III、§IV、§V', 'url':DMS}]}
 ],
 'figures':[
   {'title':'Fig.2 · shared Maclaurin-series weight templates','url':DMS,'caption':'跨Transformer块共享模板、每层保留可学习系数。'},
   {'title':'Fig.4 · target-action-diff','url':DMS,'caption':'利用语言提取任务相关对象/动作后过滤视觉token，再计算相邻帧差异。'},
   {'title':'Fig.6 · deployment speedup','url':DMS,'caption':'带数值标签的BF16 DMS相对naive模型加速；本站以图中标签而非摘要歧义字符串为准。'}
 ],
 'tables':[
   {'title':'DMS主结果摘要','columns':['设置','原模型','DMS','说明'],
    'rows':[['LIBERO π0 Avg','94.2%','94.3%','小幅提升'],['LIBERO OpenVLA Avg','76.5%','76.5%','总体持平，若干suite略降'],['SIMPLER RoboVLM Avg','60.8%','60.9%','小幅提升'],['ALOHA OpenVLA Avg','82.6%','82.8%','分步计分SR']],
    'locator':'Tables I–III','caption':'不同benchmark/平台分轨，不合并平均。'},
   {'title':'OpenVLA效率比较','columns':['配置','LIBERO Avg','Jetson','H100'],
    'rows':[['OpenVLA BF16','76.5%','1.00×','1.00×'],['OpenVLA-DMS BF16','76.5%','1.56×','1.41×'],['OpenVLA-DMS INT4','75.7%','2.96×','2.64×']],
    'locator':'Table IV','caption':'INT4+DMS包含额外量化，不能视为DMS单因素。'},
   {'title':'模板数量折中','columns':['模板数','LIBERO','SIMPLER','Jetson speedup','Jetson memory'],
    'rows':[['32 baseline','76.5%','32.7%','1.00×','100%'],['12 DMS','76.5%','33.0%','1.56×','41%'],['2 DMS','72.9%','30.3%','1.85×','11%']],
    'locator':'Table VII','caption':'减少模板继续提速/省内存，但会牺牲任务表现。'}
 ],
 'benchmarkReview':{'status':'extracted','checkedAt':DAY,'note':'用户提供IEEE Xplore完整正式PDF后完成全文复核；Tables I–VII与Fig.6精确落库。成功率、分步真实任务得分、speedup与runtime memory分轨；摘要“25%-55%×”不作为标准化榜单值。'}
}
dump('catalog/papers/p043.json',p)

# ---------------- VLAbot full-text note ----------------
p=load('catalog/papers/p046.json')
p['paper']['publicationStatus']='Robotics and Computer-Integrated Manufacturing 100 (2026) 103268；online 2026-02-16；DOI:10.1016/j.rcim.2026.103268'
p['paper']['dateNote']='Received 2025-08-13；revised 2026-01-14；accepted 2026-02-12；online 2026-02-16'
p['paper']['contribution']='提出面向长程工业装配的人—VLA交互框架：AR界面、分布式多模态数据层、高层LLM规划器与由四个模块组成的VLA agent协同，使机器人能主动向人请求文本、视觉和动作指导并逐轮减少依赖。'
p['paper']['findings']='五轮真机试验中，齿轮装配从2/3成功对象提升到第3轮起3/3，beam/peg装配从第1轮1/3到第2轮起3/3；Table 3/4报告Avg. Time分别1360.11→500.86 s和1177.24→498.06 s。主动调节版本在Table 5能完成更多子任务，但绝对执行时间并非普遍优于人工或RAMP。'
p['paper']['limitations']='系统显式依赖人类文本、视觉和示范交互，以及远程高算力模型；active interactions在beam任务中前3轮并非单调下降。正文§6.4给出1264→450 s、1177→450 s的叙述，与Tables 3–4的1360.11→500.86、1177.24→498.06不一致，本站采用原表并保留冲突。'
p['paper']['insight']='VLAbot的核心不是“5-shot自主学习”，而是把求助、计划、视觉定位、数值动作和完成监控组织成可持续的人机闭环。评估应同时计量任务完成、人工交互次数、更新次数和执行时间，而不是只看最终能否装配。'
p['paper']['readingFocus']='先读Fig.1/2理解系统与分布式数据流，再读Fig.4的四模块VLA agent和§5三类交互，最后用Tables 3–6核对五轮学习、人工成本和active regulation消融；特别注意正文时间叙述与原表冲突。'
p['paper']['evidence']='checked'
p['paper']['evidenceNote']='2026-09-20根据用户提供的ScienceDirect完整13页正式PDF逐页核读，并以ScienceDirect公开文章页作为可追溯来源；非独立实验复现。'
p['paper']['hasCautionaryResult']=True
ensure_source(p,'ScienceDirect · 正式全文入口',VLABOT)
p['publication']['status']='published'
p['publication']['acceptedAt']='2026-02-12'
p['publication']['publishedAt']='2026-02-16'
p['publication']['lastCheckedAt']=DAY
p['publication']['alerts']=[
    '§6.4叙述称gear/beam每对象时间约1264→450 s、1177→450 s，但Tables 3–4的Avg. Time为1360.11→500.86 s、1177.24→498.06 s；本站结构化结果采用原表。'
]
add_event(p['publication'],'accepted','2026-02-12',VLABOT,'Robotics and Computer-Integrated Manufacturing','正式PDF首页Accepted 12 February 2026。')
add_event(p['publication'],'published','2026-02-16',VLABOT,'Robotics and Computer-Integrated Manufacturing','正式PDF首页Available online 16 February 2026。')
p['note']={
 'status':'expanded','updatedAt':DAY,'verifiedAt':DAY,
 'version':'Robotics and Computer-Integrated Manufacturing 100 (2026) 103268；完整正式PDF；§1–7、Tables 1–6、Figs.1–9',
 'coverage':{'level':'deep','scope':'primary-methods-experiments','source':VLABOT},
 'sections':[
  {'id':'problem','title':'问题：长程装配要求动态组合原子技能并持续向人获取缺失信息',
   'body':'论文将long-horizon定义为动态组合多个Atomic Actions，而不只是持续时间长。现有VLA适合较短动作序列，单次LLM计划又难以适应零件位置和环境随执行变化。VLAbot因此把人类角色从单纯演示轨迹提升为持续指导AI agent：机器人可以主动询问装配顺序、对象位置和动作细节，并在执行过程中根据反馈修改计划。',
   'sources':[{'label':'§1；Fig.1', 'url':VLABOT}]},
  {'id':'system','title':'五层HRC系统：物理、数据、连接、应用和专家层分工',
   'body':'Fig.2把系统拆成Physical、Data、Connection、Application、Expert五层。机器人、RGB-D、夹爪和板载电脑在物理层；数据层保存文本、视觉、动作、计划和标注；连接层用ROS/TCP连接AR头显、板载电脑和远程server；应用层提供AR面板；专家层运行高层规划与VLA agent。§3.4强调分布式设计的目标是把实时硬件控制留在本地，同时将多模态大模型请求放到远程计算资源。',
   'sources':[{'label':'§3；Figs.2–3', 'url':VLABOT}]},
  {'id':'agent','title':'VLA agent不是单一端到端网络，而是四个专门模块的执行框架',
   'body':'Fig.4中的VLA agent由Intent-to-Action Planner、Visual Information Detector、Numeric Action Planner和Multimodal Action Monitor组成。高层planner先把长程目标拆成步骤；视觉模块融合原图与人类annotation并用轻量Mask Decoder输出位置与IoU；数值动作规划器把命令翻译成坐标动作并允许人类验证；动作监控器融合interaction prompt、robot status和image feature决定是否进入下一计划。论文这里把VLA作为功能框架术语，而不是特指OpenVLA。',
   'sources':[{'label':'§4；Fig.4–5', 'url':VLABOT}]},
  {'id':'interaction','title':'三类人类输入：文本、示范和视觉标注直接改变系统可用信息',
   'body':'§5提供文本、Demonstration和Visual三类interaction。语音经Whisper转文字；示范交互记录AR控制器给出的末端pose/trajectory；视觉交互可给文本类别、keypoint或bounding box，帮助Mask Decoder定位目标。机器人不是被动等待，而是在不确定时主动提问。所有这些人工信息都会进入后续规划或动作，因此“五次试验内学会”包含显著的人类监督成本，不能写成5条无人干预数据。',
   'sources':[{'label':'§5；Figs.6–7；Tables 1–2', 'url':VLABOT}]},
  {'id':'protocol','title':'真机协议：两个三对象长程任务、每项五轮，并随机加入无关物体',
   'body':'§6在真实机器人上测试gear assembly和beam assembly。齿轮任务依次安装small/medium/large三件；beam任务先插入两个peg再放置beam，因此两项都可用0–3成功对象数表征进度。每项进行5个trials，工作区随机放置无关物体。VLA框架使用两个temperature 0.5的预训练GPT-4o（intent-to-action与action monitor），以及两个fine-tuned GPT-3.5（high-level task planner与numeric action planner）。',
   'sources':[{'label':'§6.1–6.3；Fig.8', 'url':VLABOT}]},
  {'id':'results','title':'五轮学习结果：成功对象数快速饱和，但交互负担并非逐轮单调下降',
   'body':'Tables 3–4显示gear任务成功对象数为2、2、3、3、3，beam任务为1、3、3、3、3，因此摘要“within five trials”可以被更精确地理解为gear第3轮达到3/3、beam第2轮达到3/3。Table 3的Avg. Time从1360.11降至500.86 s，Table 4从1177.24降至498.06 s。gear active interactions总体42降到31，但beam为37.3、56、55、35、35.3，前3轮明显非单调。',
   'sources':[{'label':'Tables 3–4', 'url':VLABOT}]},
  {'id':'ablation','title':'主动manipulation regulation提高可完成性，但绝对时间并非全面快于人类/RAMP',
   'body':'Table 5把Manual、Our w/o interaction updates、Our active regulation和RAMP分开。主动调节后Gear1/2/3都能完成，而无更新版本在Gear3、Peg2、Beam为不可完成；但“能完成”不代表用时更短，例如Gear1人工185.2 s而VLAbot active为596.3 s，Peg1 active 213.4 s接近RAMP 175.3 s，Beam active 469.2 s仍高于人工378.9 s。该表说明交互主要提升鲁棒完成，而不是全面超越人工速度。',
   'sources':[{'label':'§6.4；Table 5', 'url':VLABOT}]},
  {'id':'human-cost','title':'人工成本：求助主要集中在数值动作规划，视觉模块较稳定',
   'body':'Table 6按模块统计五轮主动interaction。Intent-to-action planner从15次降到7次，Numeric Action Planner从16降到14，Multimodal Action Monitor恒为5；Visual Information Detector约5–6次。正文说明数值位置和角度的不确定性是主动提问的主要来源。用户熟练度主要影响完成时间和交互频率，作者称总体成功率没有显著受影响，但没有给出相应统计检验或分组表。',
   'sources':[{'label':'§6.4；Table 6', 'url':VLABOT}]},
  {'id':'limits','title':'边界：两项案例、远程大模型和正文/表格时间冲突限制外推',
   'body':'论文只验证gear与beam/peg两项装配，作者也在§7承认复杂任务中VLA可能遗漏上下文并生成错误waypoints。系统需要AR设备、远程高算力server和持续人类反馈，不能与纯本地自主policy按同一人工成本口径比较。另外§6.4文字写gear约1264→450 s、beam 1177→450 s，与Tables 3–4的1360.11→500.86、1177.24→498.06不一致；本站始终采用原表数值并把冲突公开。',
   'sources':[{'label':'§6.4–7；Tables 3–4', 'url':VLABOT}]}
 ],
 'figures':[
   {'title':'Fig.1 · intelligent human-robot collaboration workflow','url':VLABOT,'caption':'AR用户、高层planner、低层VLA agent与物理执行之间的闭环。'},
   {'title':'Fig.4 · VLA agent modules','url':VLABOT,'caption':'Intent-to-Action、Visual Detector、Numeric Action Planner和Multimodal Action Monitor四模块。'},
   {'title':'Fig.6–7 · AR interaction client and modalities','url':VLABOT,'caption':'文本面板、视觉标注与示范交互直接为agent补充信息。'}
 ],
 'tables':[
   {'title':'五轮学习轨迹','columns':['Trial','Gear success objects','Beam success objects','Gear Avg.Time (s)','Beam Avg.Time (s)'],
    'rows':[['1','2/3','1/3','1360.11','1177.24'],['2','2/3','3/3','1079.76','1147.24'],['3','3/3','3/3','828.20','941.19'],['4','3/3','3/3','606.89','608.54'],['5','3/3','3/3','500.86','498.06']],
    'locator':'Tables 3–4','caption':'Success是成功装配对象数，不是百分比；Avg.Time采用原表。'},
   {'title':'主动调节消融的执行时间','columns':['Task','Manual','VLAbot w/o updates','VLAbot active','RAMP'],
    'rows':[['Gear1','185.2','1054.8','596.3','—'],['Gear2','520.5','1255.4','438.1','—'],['Gear3','275.8','—','468.1','—'],['Peg1','216.7','987.2','213.4','175.3'],['Peg2','181.7','—','282.2','215.8'],['Beam','378.9','—','469.2','—']],
    'locator':'Table 5','caption':'单位秒；—表示该设置无法装配，不按0处理。'},
   {'title':'模块主动交互次数','columns':['Trial','Intent planner','Visual detector','Numeric planner','Action monitor'],
    'rows':[['1','15','6','16','5'],['2','13','6','15','5'],['3','7','5','15','5'],['4','6','6','15','5'],['5','7','6','14','5']],
    'locator':'Table 6','caption':'展示人工/agent交互负担的变化，而非任务成功率。'}
 ],
 'benchmarkReview':{'status':'extracted','checkedAt':DAY,'note':'用户提供ScienceDirect完整正式PDF后完成全文复核；Tables 3–6精确落库。成功对象数、Avg.Time、active interactions、interaction updates和执行时间分轨；ADE(mm)因当前榜单单位schema不支持而保留在笔记、不强塞为score。'}
}
dump('catalog/papers/p046.json',p)

# ---------------- Tracks ----------------
bench=load('catalog/benchmarks.json')
tracks=[
 T('dmsvla-ieee-libero-main','LIBERO','DMS-VLA IEEE · Table I · base vs DMS','IEEE RA-L 11(7), 2026','four LIBERO suites / 40 tasks','6 seeds × 10 tasks × 50 episodes per suite','Task success rate','percent',['Spatial','Object','Goal','Long','Average'],DMS,'Paper reimplementation of base VLA and corresponding DMS variant; 3000 rollouts per suite as described.','DMS variant uses same loss/training hyperparameters as corresponding base.'),
 T('dmsvla-ieee-simpler-main','SimplerEnv','DMS-VLA IEEE · Table II · Visual Matching','IEEE RA-L 11(7), 2026','Pick Coke Can / Move Near / Open-Close Drawer','SIMPLER Visual Matching; default task trial counts','Task success rate','percent',['Pick Coke Can','Move Near','Open / Close Drawer','Average'],DMS,'Visual Matching evaluation; task-specific default trial counts.','Corresponding base vs DMS variant.'),
 T('dmsvla-ieee-real-aloha','DMS-VLA real','DMS-VLA IEEE · Table III · ALOHA','IEEE RA-L 11(7), 2026','three step-scored tasks','ALOHA ViperX-300; third-person RealSense D435','Step-scored task completion rate','percent',['Put Balls Into Box','Clean Table','Stack Bowls','Average'],DMS,'SR is earned task points / total task points, not binary episode success.','pi0/OpenVLA base and DMS variants.'),
 T('dmsvla-ieee-real-emergen','DMS-VLA real','DMS-VLA IEEE · Table III · Emergen','IEEE RA-L 11(7), 2026','three step-scored tasks','Emergen C3; third-person RealSense D435','Step-scored task completion rate','percent',['Put Balls Into Box','Clean Table','Stack Bowls','Average'],DMS,'SR is earned task points / total task points, not binary episode success.','pi0/OpenVLA base and DMS variants.'),
 T('dmsvla-ieee-efficient-success','LIBERO','DMS-VLA IEEE · Table IV · efficient VLA quality','IEEE RA-L 11(7), 2026','LIBERO four-suite aggregate','OpenVLA-centered efficiency comparison','LIBERO average success rate','percent',['Average'],DMS,'Precision differs by method and is part of the method label; this is a paper-table comparison, not a common-training-budget leaderboard.','OpenVLA baseline; efficient methods from paper comparison.'),
 T('dmsvla-ieee-efficient-speedup','DMS-VLA deployment','DMS-VLA IEEE · Table IV · efficient VLA speedup','IEEE RA-L 11(7), 2026','OpenVLA-centered deployment comparison','Jetson AGX Orin and H100','Inference speedup vs OpenVLA BF16','score',['Jetson Orin','H100'],DMS,'Table IV speedup ratios; INT4+DMS includes quantization in addition to DMS.','Hardware/precision stated in method label.'),
 T('dmsvla-ieee-deploy-libero','DMS-VLA deployment','DMS-VLA IEEE · Fig.6 · LIBERO DMS-only speedup','IEEE RA-L 11(7), 2026','Octo / pi0 / OpenVLA','LIBERO; average latency per frame','Inference speedup vs corresponding naive VLA','score',['Jetson Orin','RTX4090','H100'],DMS,'Exact numeric labels printed on Fig.6 bars; DMS variant divided by corresponding naive model latency.','BF16/default repo dtype; no INT4 combination.'),
 T('dmsvla-ieee-deploy-simpler','DMS-VLA deployment','DMS-VLA IEEE · Fig.6 · SIMPLER DMS-only speedup','IEEE RA-L 11(7), 2026','Octo / pi0 / OpenVLA','SIMPLER; average latency per frame','Inference speedup vs corresponding naive VLA','score',['Jetson Orin','RTX4090','H100'],DMS,'Exact numeric labels printed on Fig.6 bars.','BF16/default repo dtype; no INT4 combination.'),
 T('dmsvla-ieee-strategy-ablation','SimplerEnv','DMS-VLA IEEE · Table V · complexity strategy','IEEE RA-L 11(7), 2026','SIMPLER three tasks','same number of Maclaurin templates','Task success rate','percent',['Pick Coke Can','Move Near','Open / Close Drawer','Average'],DMS,'Full-frame-diff vs target-action-diff within pi0-DMS and RoboVLM-DMS.','Controlled paper ablation.'),
 T('dmsvla-ieee-metric-ablation','SimplerEnv','DMS-VLA IEEE · Table VI · complexity metric','IEEE RA-L 11(7), 2026','SIMPLER three tasks','DMS-RoboVLM','Task success rate','percent',['Pick Coke Can','Move Near','Open / Close Drawer','Average'],DMS,'MSE, Mahalanobis and IoU-weighted variants.','Controlled metric ablation.'),
 T('dmsvla-ieee-template-quality','DMS-VLA deployment','DMS-VLA IEEE · Table VII · template count quality','IEEE RA-L 11(7), 2026','OpenVLA / OpenVLA-DMS','2–32 distinctive templates','Benchmark average success rate','percent',['LIBERO Average','SIMPLER Average'],DMS,'Template-count tradeoff; OpenVLA 32 is non-DMS baseline.','Same OpenVLA family; template count varies.'),
 T('dmsvla-ieee-template-speedup','DMS-VLA deployment','DMS-VLA IEEE · Table VII · template count speedup','IEEE RA-L 11(7), 2026','OpenVLA / OpenVLA-DMS','2–32 distinctive templates','Inference speedup vs OpenVLA','score',['Jetson Orin','H100'],DMS,'Same rows as Table VII quality track; speedup direction higher.','Same OpenVLA family; template count varies.'),
 T('dmsvla-ieee-template-memory','DMS-VLA deployment','DMS-VLA IEEE · Table VII · runtime memory','IEEE RA-L 11(7), 2026','OpenVLA / OpenVLA-DMS','2–32 distinctive templates','Runtime memory relative to baseline','percent',['Jetson Orin','H100'],DMS,'OpenVLA baseline=100%; lower means less runtime memory.','Same OpenVLA family; template count varies.','lower'),
 T('vlabot-rcim-learning-success','VLAbot real','VLAbot RCIM · Tables 3–4 · successful objects across trials','RCIM 100 (2026) 103268','gear assembly and beam assembly','five trials per task','Successfully assembled object count (out of 3)','score',['Gear assembly','Beam assembly'],VLABOT,'Each task contains three target objects/stages; value is count, not percent.','Human-in-the-loop VLAbot; interaction history accumulates across trials.'),
 T('vlabot-rcim-learning-time','VLAbot real','VLAbot RCIM · Tables 3–4 · reported Avg. Time','RCIM 100 (2026) 103268','gear assembly and beam assembly','five trials per task','Reported average operating time','seconds',['Gear assembly','Beam assembly'],VLABOT,'Uses Table 3/4 Avg. Time values; paper prose gives conflicting rounded endpoints, so structured rows follow tables.','Human-in-the-loop VLAbot across trials.','lower'),
 T('vlabot-rcim-active-interactions','VLAbot real','VLAbot RCIM · Tables 3–4 · active interactions','RCIM 100 (2026) 103268','gear assembly and beam assembly','five trials per task','Active robot interaction count','score',['Gear assembly','Beam assembly'],VLABOT,'# Int. values from Tables 3–4; beam interactions are non-monotonic in early trials.','Human-in-the-loop interaction burden.','lower'),
 T('vlabot-rcim-interaction-updates','VLAbot real','VLAbot RCIM · Tables 3–4 · interaction updates','RCIM 100 (2026) 103268','gear assembly and beam assembly','five trials per task','Interaction update count','score',['Gear assembly','Beam assembly'],VLABOT,'# Upd. from Tables 3–4; not a success metric.','Human-in-the-loop update burden.','lower'),
 T('vlabot-rcim-execution-time','VLAbot real','VLAbot RCIM · Table 5 · execution-time ablation','RCIM 100 (2026) 103268','Gear1/Gear2/Gear3/Peg1/Peg2/Beam','interaction time excluded for ablation','Robot planning and execution time','seconds',['Gear1','Gear2','Gear3','Peg1','Peg2','Beam'],VLABOT,'Null means the method could not assemble / was not reported, never zero. Manual and RAMP already know assembly process.','Manual vs no-update VLAbot vs active regulation vs RAMP.','lower'),
 T('vlabot-rcim-module-interactions','VLAbot real','VLAbot RCIM · Table 6 · module interaction burden','RCIM 100 (2026) 103268','four VLA-agent modules','five trials','Module active interaction count','score',['Intent-action planner','Visual detector','Numeric action planner','Action monitor'],VLABOT,'Counts active interactions per module; lower indicates less human/agent questioning burden, not higher task quality.','Same VLAbot system across trials.','lower')
]
existing={x['id'] for x in bench['tracks']}
assert not any(x['id'] in existing for x in tracks)
bench['tracks'].extend(tracks)
dump('catalog/benchmarks.json',bench)

# ---------------- Results ----------------
rs=[]
dver='IEEE Robotics and Automation Letters 11(7), 2026, pp.8252–8259'
def add_dms(id,method,track,values,loc,note,training='Corresponding base model/public repo configuration; DMS variant uses same loss and training hyperparameters as base.'):
    rs.append(R(id,'p043',method,track,values,DMS,dver,loc,training,note))
# Table I
for slug,m,v in [
 ('octo','Octo',[78.9,85.7,84.6,51.1,75.1]),('octo-dms','Octo-DMS',[78.7,85.9,84.9,50.9,75.1]),
 ('pi0','pi0',[96.8,98.8,95.8,85.2,94.2]),('pi0-dms','pi0-DMS',[96.9,98.7,96.0,85.4,94.3]),
 ('univla','UniVLA',[95.4,98.8,93.6,94.0,95.5]),('univla-dms','UniVLA-DMS',[95.6,98.8,93.9,94.1,95.6]),
 ('openvla','OpenVLA',[84.7,88.4,79.2,53.7,76.5]),('openvla-dms','OpenVLA-DMS',[85.6,88.1,78.9,53.4,76.5]),
 ('oft','OpenVLA-OFT',[97.6,98.4,97.9,94.5,97.1]),('oft-dms','OpenVLA-OFT-DMS',[97.2,98.6,97.4,95.6,97.2])
]:
    add_dms(f'r-dms-ieee-libero-{slug}',m,'dmsvla-ieee-libero-main',dict(zip(['Spatial','Object','Goal','Long','Average'],v)),'Table I','DMS is not uniformly higher; negative cells are retained.')
# Table II
for slug,m,v in [
 ('octo','Octo',[29.3,35.0,33.3,32.5]),('octo-dms','Octo-DMS',[30.1,34.9,33.5,32.8]),
 ('pi0','pi0',[72.7,65.3,38.3,58.8]),('pi0-dms','pi0-DMS',[73.2,65.2,38.6,59.0]),
 ('robovlm','RoboVLM',[77.3,61.7,43.5,60.8]),('robovlm-dms','RoboVLM-DMS',[77.5,61.8,43.4,60.9]),
 ('openvla','OpenVLA',[16.3,46.2,35.6,32.7]),('openvla-dms','OpenVLA-DMS',[16.6,46.4,35.9,33.0])
]:
    add_dms(f'r-dms-ieee-simpler-{slug}',m,'dmsvla-ieee-simpler-main',dict(zip(['Pick Coke Can','Move Near','Open / Close Drawer','Average'],v)),'Table II','SIMPLER Visual Matching; small negative cells retained.')
# Table III ALOHA / Emergen
for platform,track,rows in [
 ('aloha','dmsvla-ieee-real-aloha',[('pi0','pi0',[82.5,76.0,70.5,76.3]),('pi0-dms','pi0-DMS',[82.8,76.3,71.0,76.7]),('openvla','OpenVLA',[92.5,81.7,73.7,82.6]),('openvla-dms','OpenVLA-DMS',[93.0,81.5,74.0,82.8])]),
 ('emergen','dmsvla-ieee-real-emergen',[('pi0','pi0',[85.0,77.5,73.7,78.7]),('pi0-dms','pi0-DMS',[84.8,77.8,74.0,78.9]),('openvla','OpenVLA',[95.5,83.5,75.3,84.8]),('openvla-dms','OpenVLA-DMS',[95.7,83.7,75.5,85.0])])
]:
    for slug,m,v in rows:
        add_dms(f'r-dms-ieee-real-{platform}-{slug}',m,track,dict(zip(['Put Balls Into Box','Clean Table','Stack Bowls','Average'],v)),'Table III','Paper defines SR as earned step points / total points; not binary episode success.','Real robot task setup from Table III; step-scored evaluation.')
# Table IV
eff=[
 ('openvla','OpenVLA (BF16)',76.5,[1.0,1.0]),('deer','DeeR-VLA (BF16)',73.6,[1.47,1.36]),
 ('qail','QAIL (INT4)',73.7,[2.47,1.89]),('spvla','SP-VLA (BF16)',74.6,[1.37,1.25]),
 ('cache','VLA-Cache (BF16)',74.7,[1.39,1.32]),('dms-int4','OpenVLA-DMS (INT4)',75.7,[2.96,2.64]),
 ('dms-bf16','OpenVLA-DMS (BF16)',76.5,[1.56,1.41])
]
for slug,m,avg,sp in eff:
    add_dms(f'r-dms-ieee-eff-quality-{slug}',m,'dmsvla-ieee-efficient-success',{'Average':avg},'Table IV','Precision and auxiliary optimization differ by method; paper-table only.',m)
    add_dms(f'r-dms-ieee-eff-speed-{slug}',m,'dmsvla-ieee-efficient-speedup',dict(zip(['Jetson Orin','H100'],sp)),'Table IV','INT4+DMS includes quantization; speedup is not attributable to DMS alone.',m)
# Fig.6
for benchname,track,vals in [
 ('libero','dmsvla-ieee-deploy-libero',[('octo','Octo-DMS',[1.45,1.37,1.27]),('pi0','pi0-DMS',[1.48,1.40,1.29]),('openvla','OpenVLA-DMS',[1.56,1.50,1.41])]),
 ('simpler','dmsvla-ieee-deploy-simpler',[('octo','Octo-DMS',[1.40,1.33,1.23]),('pi0','pi0-DMS',[1.43,1.35,1.24]),('openvla','OpenVLA-DMS',[1.53,1.46,1.38])])
]:
    for slug,m,v in vals:
        add_dms(f'r-dms-ieee-fig6-{benchname}-{slug}',m,track,dict(zip(['Jetson Orin','RTX4090','H100'],v)),'Fig. 6','Exact printed labels above bars; no pixel-height estimation.','DMS vs corresponding naive model; average latency per frame.')
# Table V
for slug,m,v in [
 ('pi0-full','pi0-DMS · full-frame-diff',[72.5,65.2,38.1,58.6]),('pi0-target','pi0-DMS · target-action-diff',[73.2,65.2,38.6,59.0]),
 ('robovlm-full','RoboVLM-DMS · full-frame-diff',[76.5,61.3,43.0,60.3]),('robovlm-target','RoboVLM-DMS · target-action-diff',[77.5,61.8,43.4,60.9])
]:
    add_dms(f'r-dms-ieee-strategy-{slug}',m,'dmsvla-ieee-strategy-ablation',dict(zip(['Pick Coke Can','Move Near','Open / Close Drawer','Average'],v)),'Table V','Same number of Maclaurin templates; target-action strategy generally improves average.','Controlled strategy ablation.')
# Table VI
for slug,m,v in [
 ('mse','MSE',[75.2,60.6,41.9,59.2]),('maha','Mahalanobis',[75.4,60.5,42.1,59.3]),
 ('mse-iou','MSE-IoU',[77.4,61.9,43.1,60.8]),('maha-iou','Mahalanobis-IoU',[77.5,61.8,43.4,60.9])
]:
    add_dms(f'r-dms-ieee-metric-{slug}',m,'dmsvla-ieee-metric-ablation',dict(zip(['Pick Coke Can','Move Near','Open / Close Drawer','Average'],v)),'Table VI','IoU-weighted metrics improve average; MSE-IoU vs Mahalanobis-IoU differs by task.','DMS-RoboVLM metric ablation.')
# Table VII
templ=[
 ('base','OpenVLA · 32 blocks',[76.5,32.7],[1.0,1.0],[100,100]),
 ('16','OpenVLA-DMS · 16 templates',[76.6,33.4],[1.40,1.27],[58,65]),
 ('12','OpenVLA-DMS · 12 templates',[76.5,33.0],[1.56,1.41],[41,53]),
 ('8','OpenVLA-DMS · 8 templates',[75.9,32.2],[1.67,1.55],[29,39]),
 ('4','OpenVLA-DMS · 4 templates',[74.6,31.5],[1.75,1.66],[18,27]),
 ('2','OpenVLA-DMS · 2 templates',[72.9,30.3],[1.85,1.78],[11,17])
]
for slug,m,q,sp,mem in templ:
    add_dms(f'r-dms-ieee-template-quality-{slug}',m,'dmsvla-ieee-template-quality',dict(zip(['LIBERO Average','SIMPLER Average'],q)),'Table VII','Fewer templates improve efficiency but eventually reduce task quality.','OpenVLA family; template count ablation.')
    add_dms(f'r-dms-ieee-template-speed-{slug}',m,'dmsvla-ieee-template-speedup',dict(zip(['Jetson Orin','H100'],sp)),'Table VII','Speedup increases as templates decrease.','OpenVLA family; template count ablation.')
    add_dms(f'r-dms-ieee-template-memory-{slug}',m,'dmsvla-ieee-template-memory',dict(zip(['Jetson Orin','H100'],mem)),'Table VII','Runtime memory is percentage of baseline; lower is better.','OpenVLA family; template count ablation.')

# VLAbot results
vver='Robotics and Computer-Integrated Manufacturing 100 (2026) 103268'
success=[(1,2,1),(2,2,3),(3,3,3),(4,3,3),(5,3,3)]
times=[(1,1360.11,1177.24),(2,1079.76,1147.24),(3,828.20,941.19),(4,606.89,608.54),(5,500.86,498.06)]
ints=[(1,42,37.3),(2,39.5,56),(3,32.3,55),(4,32.6,35),(5,31,35.3)]
upds=[(1,8,6),(2,6,8),(3,3,10),(4,3,3),(5,2,3)]
for trial,g,b in success:
    rs.append(R(f'r-vlabot-trial-success-{trial}','p046',f'VLAbot trial {trial}','vlabot-rcim-learning-success',{'Gear assembly':g,'Beam assembly':b},VLABOT,vver,'Tables 3–4','Five sequential trials per task with human-VLA interaction history.','Count of successfully assembled objects out of three; not percentage.'))
for trial,g,b in times:
    rs.append(R(f'r-vlabot-trial-time-{trial}','p046',f'VLAbot trial {trial}','vlabot-rcim-learning-time',{'Gear assembly':g,'Beam assembly':b},VLABOT,vver,'Tables 3–4','Same five-trial real-robot protocol.','Uses table Avg. Time values; prose endpoints conflict and are not substituted.'))
for trial,g,b in ints:
    rs.append(R(f'r-vlabot-trial-int-{trial}','p046',f'VLAbot trial {trial}','vlabot-rcim-active-interactions',{'Gear assembly':g,'Beam assembly':b},VLABOT,vver,'Tables 3–4','Same five-trial protocol.','Beam interactions rise in trials 2–3; non-monotonic evidence retained.'))
for trial,g,b in upds:
    rs.append(R(f'r-vlabot-trial-upd-{trial}','p046',f'VLAbot trial {trial}','vlabot-rcim-interaction-updates',{'Gear assembly':g,'Beam assembly':b},VLABOT,vver,'Tables 3–4','Same five-trial protocol.','Interaction updates are a human/agent intervention burden metric.'))
exec_rows=[
 ('manual','Manual user',[185.2,520.5,275.8,216.7,181.7,378.9]),
 ('no-updates','VLAbot w/o interaction updates',[1054.8,1255.4,None,987.2,None,None]),
 ('active','VLAbot active regulation',[596.3,438.1,468.1,213.4,282.2,469.2]),
 ('ramp','RAMP',[None,None,None,175.3,215.8,None])
]
for slug,m,v in exec_rows:
    rs.append(R(f'r-vlabot-exec-{slug}','p046',m,'vlabot-rcim-execution-time',dict(zip(['Gear1','Gear2','Gear3','Peg1','Peg2','Beam'],v)),VLABOT,vver,'Table 5','Ablation excludes interaction time; manual/RAMP already know assembly process.','Null means cannot assemble or not reported, not zero.'))
mods=[(1,[15,6,16,5]),(2,[13,6,15,5]),(3,[7,5,15,5]),(4,[6,6,15,5]),(5,[7,6,14,5])]
for trial,v in mods:
    rs.append(R(f'r-vlabot-module-int-{trial}','p046',f'VLAbot trial {trial}','vlabot-rcim-module-interactions',dict(zip(['Intent-action planner','Visual detector','Numeric action planner','Action monitor'],v)),VLABOT,vver,'Table 6','Five-trial system interaction analysis.','Numeric action planner remains the dominant source of active questions.'))

assert len(rs)==101, len(rs)
for x in rs: dump('catalog/results/'+x['id']+'.json',x)

# Review ledger.
review=load('maintenance/benchmark-review.json')
dms_ids=[x['id'] for x in rs if x['paperId']=='p043']; v_ids=[x['id'] for x in rs if x['paperId']=='p046']
dms_tracks=sorted({x['trackId'] for x in rs if x['paperId']=='p043'})
v_tracks=sorted({x['trackId'] for x in rs if x['paperId']=='p046'})
assert len(dms_ids)==72 and len(dms_tracks)==13
assert len(v_ids)==29 and len(v_tracks)==6
review['papers']['p043']={'status':'extracted','trackIds':dms_tracks,'resultIds':dms_ids,'note':'用户提供IEEE正式全文后完成最终复核：72条、13个paper-scoped设置；Tables I–VII与Fig.6精确值，保留负面单元格、INT4额外变量及摘要速度字符串歧义。'}
review['papers']['p046']={'status':'extracted','trackIds':v_tracks,'resultIds':v_ids,'note':'用户提供ScienceDirect正式全文后完成最终复核：29条、6个paper-scoped设置；Tables 3–6精确值，成功对象数/时间/人工交互分轨，缺失项保持null。'}
dump('maintenance/benchmark-review.json',review)

# Remove limited-source exception now that primary full text was actually read.
policy=load('maintenance/editorial-policy.json')
policy['limitedLegacyIds'].pop('p043',None)
policy['limitedLegacyIds'].pop('p046',None)
dump('maintenance/editorial-policy.json',policy)

# Work queue fully clear.
wq=load('maintenance/work-queue.json')
wq['notes']=[]
wq['remainingNotes']=0
dump('maintenance/work-queue.json',wq)

audit={
 'schemaVersion':1,'reviewedAt':DAY,'batch':'final-two-fulltext','baseCommit':BASE,
 'papers':[
   {'paperId':'p043','source':'user-supplied official IEEE Xplore PDF','publicSource':DMS,'results':72,'tracks':13},
   {'paperId':'p046','source':'user-supplied official ScienceDirect PDF','publicSource':VLABOT,'results':29,'tracks':6}
 ],
 'countsBefore':{'papers':98,'results':962,'tracks':267,'extracted':94,'deferred':2,'notApplicable':2,'remainingNotes':2},
 'countsAfterExpected':{'papers':98,'results':1063,'tracks':286,'extracted':96,'deferred':0,'notApplicable':2,'remainingNotes':0},
 'boundaries':[
   'DMS-VLA Fig.6 uses exact printed bar labels; no plot-height estimation.',
   'DMS-VLA abstract/conclusion speed string 25%-55%x is not standardized; tables/figure labels are authoritative for structured rows.',
   'DMS-VLA real-robot SR is step-scored earned-points/total-points, not binary episode success.',
   'VLAbot trial Success is number of assembled objects out of three, not percentage.',
   'VLAbot Tables 3-4 time values are used instead of conflicting prose endpoints.',
   'VLAbot Table 5 em dash is stored as null, never zero; ADE in mm remains in notes because leaderboard unit schema does not support length.'
 ]
}
dump('maintenance/final-two-source-audit-20260920.json',audit)

ch=Path('CHANGELOG.md').read_text()
entry='## 2026-09-20 · 最后两篇全文补齐：DMS-VLA 与 VLAbot\n\n- 用户提供IEEE Xplore与ScienceDirect下载的完整正式PDF，解除p043/p046 limited-source证据限制；两篇均从needs_review/deferred升级为expanded/extracted。\n- DMS-VLA新增72条结果、13个设置：LIBERO、SIMPLER、ALOHA、Emergen、效率对照、Fig.6部署以及Tables V–VII消融全部按原表/带标签图精确落库。\n- VLAbot新增29条结果、6个设置：五轮成功对象数、Avg.Time、active interactions、updates、Table 5执行时间和Table 6模块交互分轨；缺失保持null。\n- 保留DMS摘要“25%-55%×”歧义、部分DMS任务略降、VLAbot beam交互非单调和§6.4时间叙述与Tables 3–4不一致等负面/冲突证据。\n- 最终状态：96 extracted、0 deferred、2 not-applicable；1063 results、286 tracks；remainingNotes=0。\n\n'
if '最后两篇全文补齐：DMS-VLA 与 VLAbot' not in ch:
    Path('CHANGELOG.md').write_text(entry+ch)

Path('tests/test_final_two_fulltext.py').write_text("""import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def j(p): return json.loads((R/p).read_text())
def test_final_counts_zero_deferred_and_notes():
    review=j('maintenance/benchmark-review.json')['papers']
    assert sum(x['status']=='extracted' for x in review.values())==96
    assert sum(x['status']=='deferred' for x in review.values())==0
    assert sum(x['status']=='not-applicable' for x in review.values())==2
    assert len(j('catalog/benchmarks.json')['tracks'])==286
    assert len(list((R/'catalog/results').glob('r-*.json')))==1063
    assert j('maintenance/work-queue.json')['remainingNotes']==0
    assert j('maintenance/work-queue.json')['notes']==[]
    cat=[j('catalog/papers/p043.json'),j('catalog/papers/p046.json')]
    assert all(x['note']['status']=='expanded' and x['note']['coverage']['level']=='deep' for x in cat)
def test_limited_policy_cleared():
    limited=j('maintenance/editorial-policy.json')['limitedLegacyIds']
    assert 'p043' not in limited and 'p046' not in limited
def test_dms_negative_cells_and_speedup_distinction():
    base=j('catalog/results/r-dms-ieee-libero-openvla.json')['values']
    dms=j('catalog/results/r-dms-ieee-libero-openvla-dms.json')['values']
    assert base['Object']==88.4 and dms['Object']==88.1
    assert base['Goal']==79.2 and dms['Goal']==78.9
    assert j('catalog/results/r-dms-ieee-eff-speed-dms-int4.json')['values']=={'Jetson Orin':2.96,'H100':2.64}
    assert j('catalog/results/r-dms-ieee-fig6-libero-openvla.json')['values']=={'Jetson Orin':1.56,'RTX4090':1.5,'H100':1.41}
def test_dms_template_tradeoff():
    q12=j('catalog/results/r-dms-ieee-template-quality-12.json')['values']
    q2=j('catalog/results/r-dms-ieee-template-quality-2.json')['values']
    s12=j('catalog/results/r-dms-ieee-template-speed-12.json')['values']
    s2=j('catalog/results/r-dms-ieee-template-speed-2.json')['values']
    assert q12=={'LIBERO Average':76.5,'SIMPLER Average':33.0}
    assert q2=={'LIBERO Average':72.9,'SIMPLER Average':30.3}
    assert s12['Jetson Orin']==1.56 and s2['Jetson Orin']==1.85
def test_vlabot_learning_and_nonmonotonic_interaction():
    assert j('catalog/results/r-vlabot-trial-success-1.json')['values']=={'Gear assembly':2,'Beam assembly':1}
    assert j('catalog/results/r-vlabot-trial-success-3.json')['values']=={'Gear assembly':3,'Beam assembly':3}
    assert j('catalog/results/r-vlabot-trial-int-1.json')['values']['Beam assembly']==37.3
    assert j('catalog/results/r-vlabot-trial-int-2.json')['values']['Beam assembly']==56
def test_vlabot_missing_is_null_not_zero():
    no=j('catalog/results/r-vlabot-exec-no-updates.json')['values']
    ramp=j('catalog/results/r-vlabot-exec-ramp.json')['values']
    assert no['Gear3'] is None and no['Peg2'] is None and no['Beam'] is None
    assert ramp['Gear1'] is None and ramp['Beam'] is None
def test_vlabot_table_times_authoritative():
    assert j('catalog/results/r-vlabot-trial-time-1.json')['values']=={'Gear assembly':1360.11,'Beam assembly':1177.24}
    assert j('catalog/results/r-vlabot-trial-time-5.json')['values']=={'Gear assembly':500.86,'Beam assembly':498.06}
    p=j('catalog/papers/p046.json')
    assert any('1360.11' in x and '500.86' in x for x in p['publication']['alerts'])
""")

subprocess.run(['python','scripts/capture_activity.py','--base',BASE,'--at','2026-09-20T02:20:00Z'],check=True)
subprocess.run(['python','scripts/build_catalog.py'],check=True)
print('final two full-text payload materialized:',len(rs),'results',len(tracks),'tracks')
