# 官网反向检索与基准版本维护

本项目保持稳定维护，不新增大型功能。2026-09-18起，定期将各已覆盖基准的官网、官方榜单提交和作者论文集作为文献发现入口，而不只搜索新arXiv关键词。当前批次范围见benchmark-source-audit-20260918.json；未完成全文/协议的项目是候选，不声称穷尽榜单。

## Evaluation Setting 结构化与防膨胀

Evaluation Setting 只表示“是否在回答同一个评测问题”，不表示训练条件、模型架构或来源完全公平。构建器统一通过 `scripts/build/benchmark_settings.py` 的结构化 protocol profile 归一化现有 track，并生成稳定 evaluation identity；已有 Setting ID 与公开链接保持兼容。

硬身份维度包括：Benchmark、task/suite/subset scope、真正改变评测问题的 split / deployment / perturbation 条件、metric、unit 与 direction。只有这些维度发生实质变化时才应产生新的 Setting。任务列覆盖不完整但仍回答同一问题时保留在同一 Setting，并标记为 partial coverage，而不是机械复制 Setting。

以下属于 Result Report / 原始 track 的报告或训练差异，**不得单独制造 Setting**：训练数据与 demonstration budget、base model、optimization recipe、checkpoint 选择、来源论文、作者实现、回合数/seed 数等重复统计细节。它们必须继续保留在 Training Data、Recipe / Evidence、原始 track 与 source locator 中；必要时提示 compatible / partial，而不是伪装成完全公平比较。

新增或复核 track 时，先检查现有 Setting 的结构化 identity，再决定是否创建新 evaluation scope。禁止仅因论文命名、作者 wording、训练预算或 protocol prose 不同就增加 Setting。CI 中的 protocol profile / fingerprint / compatibility 回归用于防止未来增长重新退化为“每篇论文一个 Setting”。

## RoboCasa身份不可混合

- `dataset=RoboCasa`仅对应原版RoboCasa；原版24原子任务、5复合迁移及其他子协议仍分开。
- `dataset=RoboCasa365`对应升级的365任务框架。网站主榜实际评价50任务（18原子、16已见复合、16未见复合），不能称365任务总平均。
- 预训练厨房Human300多任务评价与目标厨房微调不能混排；目标每任务50/150/500示范分赛道。
- RoboCasa365官方1.0.0与1.0.1必须分赛道。官网说明1.0.1任务时长上限扩大1.5倍；未来新版本也核对episode horizon、reset、success条件与任务子集，不能只改version字符串。
- 保留已有稳定track ID。原Xiaomi365赛道从RoboCasa改归RoboCasa365，其结果值/来源不改。新官网记录注明是否与论文原表同源，不将相同值重复当独立评测。

## 榜单不是同名方法的最大值集合

官网声明、论文原表、后续重测各有日期/版本/提交者/训练设置。记录原始source和locator；官方投稿JSON的代码commit只作公开来源定位，不读取私人checkpoint或日志。基础模型论文链接到后续变体时明确其家族背景关系，不假装原论文报告了新版结果。缺完整论文/变体身份先候选；不能把ABot-M0、M0.5、M0.6或Xiaomi0/1自动视为同篇。

RoboTwin50×50clean的co-train与每任务独立checkpoint分开；2,500clean与27,500含随机示范分开。RoboDojo过程score和二元成功率分别建赛道，仿真和真机分开。LIBERO原版、Plus和PRO分开。官方原表预算未统一时使用paper-table，不赋公平排名。缺值为null，真实0保留；冲突记录两方来源，不取最大值。分组已舍入后计算的加权平均说明权重和精度，不包装成独立原始测量。

## 每周与轮转

在既有周更中检查官网新增条目，按3–8篇完成组交付，允许轮转已覆盖基准。候选保存明确原因，记录成功/失败和实际覆盖范围；本类局部审计不前移完整文献检索lastSuccessfulSearchAt。新增论文满足8节/2000字以上的深读标准，逐节指向实际版本，配表/读图说明保留原文定位。新增结果更新逐篇benchmark-review；没有重新阅读全文不提升旧笔记verifiedAt。正式发表状态另查会议/出版商，首版日期永久保留。

完成canonical修改后，以修改前真实main SHA运行capture_activity.py，再build_catalog.py、validate_all.py和既有浏览器测试。完整CI通过后正常自检PR合并，并核实对应提交的Pages部署。仍保持不大改功能、不过度堆测试门槛的维护原则。

## 同名或近名方法的身份核验

官网方法名不能靠关键词或相似标题直接绑定paperId。须核对原始论文链接、arXiv/DOI、作者和明确的版本/变体关系；例如4D-WAM与MECo-WAM不能因为都含4D几何就归为同篇。缺少对应全文或身份映射的结果先保存在候选审计，不进入正式榜单，也不能据此把旧论文的benchmarkReview提升为extracted。

## 第二批已完成范围

`maintenance/audits/benchmark/benchmark-source-audit-20260918-batch2.json` 记录RVT、RVT-2、3D Diffuser Actor和THE COLOSSEUM的正文级回补与来源链。先按现有arXiv/DOI去重再处理历史候选；旧审计是当时快照，不能将已收录条目再作为新论文重复添加。RVT/RVT-2的重复规划执行不是独立训练种子；3D Diffuser Actor不是DP3；CALVIN轨迹时限不等于单动作时限；COLOSSEUM原始20任务与后续子协议分开。所有引用基线归属实际报告论文，不因新增原表行而宣称增加了同等数量的方法论文。

## 第三批原方法回补记录

`benchmark-source-audit-20260918-batch3.json`记录Act3D、GNFactor、ChainedDiffuser三篇原报告的完成范围。历史审计保留发现过程，后续候选去重应同时对照最新paperOrder、arXiv/DOI/规范标题与各批resolved字段，而非仅因旧deferred数组仍有名称就再次新增。GNFactor的20示范最终/最佳检查点、额外训练视角，以及Act3D和ChainedDiffuser的不同任务规模与执行接口必须保留。未知最早公开日可以留null；正式出版日期有证据也不能自动代填为首次公开日。


## 第四批原始数据与评测论文

`benchmark-source-audit-20260918-batch4.json`记录RoboMimic、DexMimicGen、SIMPLER三篇实际深读范围。PH/MH、低维/图像、最佳/末期检查点、源/生成示范、机器人硬件及VM/VA均保留独立语义。SIMPLER的Grasp是部分进度，MMRV是整个策略集合的排序质量，不得当作策略完成成功率。数据生成成功率也不能混入策略榜。章节和不同载体图表编号按实际版本标注；已入库的原始研究不再从旧发现队列重复新增。

## 原始真机报告与同表异质指标（第七批）

RT-1/RT-2原作者Google机器人真机实验不能因硬件相似就归入SimplerEnv；新归档组`Google Robot (real)`明确是作者报告集合，不是一个统一公开复现基准，逐轨保持论文、场景、训练及评测差异。PaLM-E的Language Table Table2即使同为百分数，Task1也是验证准确率、Task2/3才是模拟rollout成功；Appendix E.2/Table9修改奖励的结果另对待。失败检测/可供性F1必须独立于操作成功率。重复主表/附表同源只入一次，未报告值为null，未确定种子/检查点不猜。

## Benchmark Method 展示精简（2026-10-10）

- **Benchmark Method 是独立方法/基线，不是消融实验变量。** 论文的模块开关、阈值搜索、骨干冻结、模板数、采样步数等内部对照，原则上不应占据对外主方法列表。
- 显式维护 `catalog/benchmark-method-curation.json`：整组内部消融用 `excludedTracks`，混合主表中的消融行用 `excludedResults`，已核验代表性配置可用 `methodLabels` 显示方法名。原文的具体配置应保留在结果证据说明。
- **不删除原始核验结果。** `catalog/results`、论文逐条结果和阅读笔记仍保留完整消融与复现实验数据；仅派生 Benchmark 比较目录、Method 下拉和对外榜单时应用精简。不得把不同实验协议或训练预算错误合并为公平排名。
- 新增主结果时同步复核 Method 命名与配置，避免把同一方法的多行消融误标成独立方法。

## 单方法、孤立 Benchmark 类别精简（2026-10-11）

- Benchmark 目录应突出可复用、可横向比较的评测集合。若某个单独的 `dataset` 只由一篇论文提供结果，且所列方法只是该论文自身的版本、训练规模、模块开关、部署条件或仅有一条方法记录，就不应以独立 Benchmark 分类占用网站导航。
- `catalog/benchmark-method-curation.json` 的 `excludedDatasets` 显式管理这些暂不展示的孤立类别；排除作用于对外 Benchmark、Evaluation Setting、方法筛选、Evidence Coverage 和 My Radar 的数据集菜单。保留 `catalog/benchmark-taxonomy.json` 的完整规范登记及原始 `catalog/benchmarks.json` 协议。
- 如果该类别随后出现其他论文真实核验且协议可对齐的结果，构建会提示重新审核，不允许长期隐藏已经具有跨论文比较价值的 Benchmark。
- **不可仅以某个 Track 或 Setting 当前只有一行而排除标准公共 Benchmark。** LIBERO、CALVIN、RoboTwin 等公共数据集里的单篇论文结果仍然可供其他来源对齐；相反，OC-VLA++ real robot、GF-VLA real 等论文特有自测不应独立成类。
- 完整实验和消融一律保留在 `catalog/results`、按论文分片的 `data/paper-results` 与论文阅读详情。此处的「不展示」不等于删除核验数字或修改论文。
