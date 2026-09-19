## 2026-09-19 · 第十四批：五篇原始证据回补

- 深读/复核 OC-VLA++、TemporalFlow-VLA、VT-WAM、VLAFlow、OnEvoMemory；五篇 deferred→extracted。
- 新增55条源定位结果、13个具体设置；视角、任务子集、混合计分、训练阶段和benchmark family严格分轨。
- 保留固定视角退化、初始触觉退化、action-only预训练负迁移与在线额外交互等负面/成本边界。
- 不改Leaderboard UI，不清理历史/安全分支，不从Deltoris/FAST图形或不兼容硬件指标强行提取。

## 2026-09-19 · 第十三批：五篇原始证据回补

- 深读/复核 τ0-VLA、Co-training Study、HALO、DSWAM、VERITAS；五篇 deferred→extracted。
- 新增52条源定位结果、16个明确设置；成功率、时间、错误数与训练阶段分开；不从图高或相对增益反推精确值。
- 保留HALO非逐项最优、CoT/离散token无显著收益、DSWAM单任务非全优、VERITAS小样本差异等边界。
- 不改UI/导航，不清理历史/安全分支，不推进完整周检索检查点。

## 2026-09-19 · 原始证据回补第十一批

## 2026-09-19 · 第十二批：五篇原始证据回补

- 深读/复核 Legato v2、VLA-InfoEntropy v1、TurboVLA v2、ActionCache v2、FlashVLA v1；两篇旧版笔记完成版本核验。
- 新增161条源定位结果、40个明确设置；98篇保持，结果507→668、设置138→178，extracted52→57、deferred44→39，needs_review21→19。
- 分离评分/成功率/时间、延迟组件与训练/部署条件；重复主行不重计；保留单位缺失、FLOPs冲突、低步数退化和负面消融。
- 内容回补不是完整论文/新闻周检索，不推进相关成功检查点。历史分支清理按维护者要求暂缓；既有UI和科学证据保留。


深化既有UniPi和VLA-Touch各9节；补24条分协议原始结果，Table2/1同源完整模型不重复，生成视频代理与机器人执行/属性决策不混排。核对UniPi正式发表与书目，保留首发；VLA-Touch明确v2先进行RDT适配、触觉融合不等于整体免训练。保留来源分组导航与全部旧记录；完整周更检查点不前移。

## 2026-09-19 · 榜单来源分组导航

按数据集→来源论文/官方榜单→具体设置组织原榜单，提供全部设置模式和完整协议折叠。保留所有track、原始分数、旧深链接、排序、CSV与散点的精确协议边界；不把导航归组当成绩混排，不额外读取全库结果。

## 2026-09-19 · 原始证据回补第十批

深化CLIPort、BC-Z各9节来源限定正文；补36条原报告结果、9个协议。CLIPort保留部分完成score、四示范预算与验证/测试差异；BC-Z区分干扰物、已见/未见、干预与动作标签消融，澄清44%子集不是总体。核对正式作者与出版日期；BC-Z最早已核实公开节点据论文集更正，arXiv v1时间不变。旧结果和前端不改，未纳入实验保留审计。

## 2026-09-19 · 原始证据回补第九批

深化既有CALVIN、DROID、SayCan各9节正文，新增42条可追溯结果与13个协议；CALVIN短任务/链式、DROID实际40k训练/ID与OOD、SayCan规划/执行分开。DROID新增真实评测归档，不当新统一公共benchmark。三篇正式发表与完整书目同步，最早日期保持；按Figure8更正CALVIN“最高53.9”并按Table2澄清SayCan两厨房KEY RESULT，before/after与来源留审计；仅处理本批来源，完整周检索检查点不前移。

## 2026-09-19 · 跨本体原始证据回补第八批

深化Open X-Embodiment/RT-X与Octo各9节，补29条来源定位真机结果与8个独立协议；新增BridgeData真机和Octo作者真机归档以免误入SimplerEnv。保留OXE容量/历史混杂和反例、Octo重复原表去重/平均及回合冲突、零样本与微调区别。确认两篇及RoboFlamingo正式发表，后者仅元数据、全文复核仍待完成；首发、KEY RESULT和旧结果保持。前端排序与散点图不改，非完整周检索。

## 2026-09-19 · 榜单列排序与时间—成绩散点图

按明确使用需求改进现有Leaderboard：所有成绩列可点选排序及升降序切换，论文对照表也可排列但不赋公平名次；名次方向与显示顺序分开，缺失与零分不混淆。新增协议内时间—成绩SVG散点图、来源首发/本站核验两种日期口径、重合记录展开、CSV和共享URL。保持按需加载、有限绘图数量和移动端局部滚动；没有改写论文、笔记、首发日期、评测记录或检索检查点。详细语义见maintenance/leaderboard-analysis.md，增加对应纯函数和真实HTTP浏览器回归。

## 2026-09-19 · 原始证据回补第七批

深化RT-1、RT-2、PaLM-E各9节正文，补充37条原表结果和8个协议，核对三篇正式论文集书目与发表状态，最早日期和KEY RESULT保持。新真机归档与Language Table用于避免错误归入SimplerEnv，不新增前端功能。明确RT-1任务范围差异/同源重复，RT-2原表62与63冲突，PaLM-E同表准确率/执行成功分离、Table9奖励变化及F1边界。全程作者报告非本站复现，未提取部分留审计，完整周更检查点不前移。

## 2026-09-19 · 原表覆盖第六批

新增R3M、MVP早期技术报告与Meta-World三篇来源限定的深入笔记，各9节。补R3M低示范跨视角/预算聚合10条、Meta-World v2原表20条，合计30条结果与8个协议；MVP曲线缺精确值，保持deferred，不创建空PixMC榜。不将后续MVP变体回绑原报告，不混Meta-World旧会议稿与v2，不伪造新论文/新闻完整检索。正式作者、出版年、首发锁与图表导读同步。旧记录和前端保持，collection起始年随新收录2019工作更正为2019。

## 2026-09-19 · 覆盖扩充第五批：既有论文原始证据

深化p057 LIBERO和p064 OpenVLA各9节笔记，新增27条结果、4个协议，不新增论文。LIBERO原始FWT/NBT/AUC分别存score，NBT越低越好；Table1/2重复证据只记一次；OpenVLA v3单视角清洗示范成功率独立于终身协议与OFT。补2篇来源核验书目及LIBERO正式NeurIPS2023/DOI，首发锁、KEY RESULT与原282条结果保持。原架构图定位更正为Figure1；附录或全文访问限制明确留待办。完整周更检索检查点不前移。

# 2026-09-18 · 覆盖扩充第四批

新增RoboMimic原研究、DexMimicGen、SIMPLER三篇9节深读；补充47条原报告结果、10个既有数据集协议，新增3篇来源核验书目。低维/图像、PH/MH、硬件、示范预算、检查点和VM/VA均分别记录；只提取完整任务成功率，不把部分抓取、生成成功或MMRV混排。原92篇论文、235条结果和6条新闻保持，RoboCasa与RoboCasa365分组不变。实际阅读范围与未完成项见batch4审计，未推进完整周更检索检查点。此记录为内容变更说明，不替代远端发布状态。

## 2026-09-18 — 覆盖扩充第三批：原方法与执行条件

新增Act3D、GNFactor、ChainedDiffuser共3篇九节深入阅读，补充26条原报告RLBench结果及8个协议。89→92篇、209→235条、65→73协议，数据集系列保持15；三篇新书目来源独立核验。保留Act3D不同任务规模和预算、GNFactor训练额外视角及final/best检查点、ChainedDiffuser宏闭环/微开环和两个10任务设置；未知首发不猜填。引用基线不改原报告paperId，不扩大功能、不推进完整周更检索时间，原内容与RoboCasa分组不变。

## 2026-09-18 — 官网论文覆盖第二批

新增RVT、RVT-2、3D Diffuser Actor、THE COLOSSEUM四篇全文级九节笔记与核验书目；在RLBench、CALVIN、COLOSSEUM补充27条原表结果及7个非空来源/协议分组，不新增数据集系列或网站功能。保留关键帧与轨迹执行、观测/训练预算、CALVIN时限、COLOSSEUM逐任务No/All与原文冲突；既有RoboCasa/RoboCasa365分组和原有论文、182条结果不变。仅本批内容回补，不推进完整周更检索检查点。

## 2026-09-18 — 官网反向检索与RoboCasa版本分离

内容维护批次：新增RoboCasa、RoboCasa365、RLDX-1、PRTS、GigaWorld-Policy、XPolicyLab和DP3共7篇深读，补充77条来源定位结果与29个协议赛道；为7篇补充有一手来源的书目信息。RoboCasa365成为独立数据集入口，旧Xiaomi365赛道ID和值不变；官网1.0.0/1.0.1、预训练/目标厨房、示范预算分别归档。RoboTwin单任务/联合与2,500clean/27,500mixed、RoboDojo过程得分/完整成功率、LIBERO/Plus/PRO分别记录。保留作者原表的冲突与负结果，不取最大值、不将官方成绩冒充本站复现。官网审计和未完成论文线索留可追溯队列；本批不等于穷尽收录，也不推进完整文献检索日期。既有正文、KEY RESULT、首发和105条旧结果值保持；发布前续审将一条误关联MECo-WAM的4D-WAM官网成绩退回身份/全文待核验队列。

## 2026-09-18 — 高频工具收口与稳定维护

加入本地 My Radar（论文、方向、基准、新闻分类关注）、Ctrl/Cmd+K 全局快捷搜索，以及 BibTeX/RIS/CSL-JSON/Markdown 单篇和批量导出。索引与工具按需加载，保留来源缺失提示、阅读状态和所有既有科学数据；不加入 RSS。此次功能收口后默认仅提高内容质量、覆盖率和稳定性，除非出现明确痛点或实际需求。

## 2026-09-18 — 可拖拽导航宽度

左侧导航加入鼠标/指针拖拽、双击或Enter复位、方向键微调和本地宽度记忆。桌面默认260px，可调244–380px并为正文保留至少400px；手机仍使用独立抽屉。导航标题与徽标不换行，修复小屏“具身智能周报”拥挤。加入真实HTTP拖拽、取消、边界、刷新恢复、存储禁用及窄屏回归；不修改论文、新闻或评测数据。

## 2026-09-18 — 具身智能周报

新增独立新闻页、每周精选、ISO周归档、类别/来源/关键词筛选、证据边界和原始来源、与论文双向关联、收录分布及12周未知覆盖标记。首批6条有限来源核验新闻，分布于W37/W38，检索状态partial。新闻不生成新论文或榜单结果；源码和每20条周报分片按需加载。周更保留所有既有职责并加入新闻独立检查点；完整测试后经PR正常发布。

## 2026-09-18 — 阅读工作台与证据可视化

增加独立阅读页、2–4篇来源摘录对比、真实变化中心、方向×数据集覆盖图、单协议图表、BibTeX/Markdown/CSV导出与阅读优先视觉层次。保持按需加载、现有论文/笔记/结果/首发锁不变；本机偏好不进入公开库。周更增加真实变更捕获，历史快照不伪造入库日期。

## 2026-09-18 — 运行维护与页面性能

新增每周/发布后的保守分支清理：精确已合并head、6小时窗口、备份和未合并保护、SHA条件删除与审计。新增main保护配置和只增不弱化安装器，权限不足必须明确报告。发表同步加入端点Accept、官方摘要页版本历史回退、限流/熔断、到期轮转与身份检查；来源健康加入时长预算和去片段去重。

首页改为轻量目录，搜索索引首次检索加载并进入Worker；详情与赛道内容哈希分片、单篇结果按需加载、有界缓存与请求超时。保留旧公开导出、首发日期、阅读记录与全部来源结果；增加数据预算、模拟万篇检索和分支安全回归。

## 2026-09-18 — 全库深入笔记与自检发布规则

合入其余28篇正文／报告笔记；两篇资料受限论文扩展为8节导读并明确限制（DMS作者供稿、VLAbot官方摘要），不认证为完整期刊正文。全库78条均有分节笔记，76条为正文／理论／报告范围。保留全部最早公开日期、KEY RESULT、发表状态与原66条结果；恢复39条原表结果，共14系列、29赛道、105条。新增全库笔记和逐篇榜单处理检查，周更改为来源自检、CI通过后正常合并并核实Pages，不绕过保护。

## 2026-09-18 — 深入笔记恢复批次

从固定保留提交恢复42篇分节原文笔记，保留当前main六篇更详细的动作/空间笔记及全部既有榜单结果。增加来源范围、解释性表格与原图定位展示；不把恢复操作计为全网检索或新版本核验。

## 2026-09-18 — 2026-09-18-action-models

第二批：深入重写 Diffusion Policy、ACT/ALOHA、FAST 三篇阅读笔记，补充算法步骤、训练部署差异、真实消融、量化结果与原图定位。新增 RoboMimic、Push-T、Franka Kitchen、ALOHA-Sim 四个数据集系列，7个协议、21条核验结果；明确区分checkpoint、示范来源、图像/状态、覆盖率/成功率。Diffusion Policy原文22初始化更正脚注与Kitchen示范数冲突均保留。

## 2026-09-18 — 2026-09-18-spatial-memory

第一批可验证增量：重写 PerAct、SpatialVLA、GR-1 深入笔记；新增 RLBench、SimplerEnv、CALVIN 三个数据集系列及六个独立协议，共18条来源定位结果。新增安全笔记表格、动态数据集导航，修复非百分比指标的详情显示。保留全部论文 ID、最早公开日期、KEY RESULT；不声明全库已深化或已完成本周检索。


## 2026-09-17 · V2 lifecycle, notes and evidence-scoped leaderboards

- Migrated all 78 existing paper IDs to individually editable `catalog/papers/`; preserved original first-public dates and every existing KEY RESULT. Added deterministic legacy export, compact search catalog and lazy per-paper details.
- Added arXiv revision / first-arXiv / formal-publication lifecycle records, direct DOI metadata synchronization, candidate review queues and separate note-verification versions. Recorded OpenVLA in CoRL 2024 proceedings and OpenVLA-OFT in RSS 2025; no acceptance dates guessed.
- Expanded six public reading notes (p001, p004, p021, p064, p069, p076). Older notes retain explicit legacy status; p069's v1 note is marked for v2 review.
- Added RoboTwin / RoboCasa / LIBERO Leaderboards: 8 protocol tracks, 27 source-located rows. Candidate detection and extraction are separate from ranked checked evidence. Heterogeneous comparison tables are unranked; no cross-protocol SOTA total.
- Added monthly-age source health rotation, quarterly review / old-note queues, strict source/build/result tests, bounded pagination and lazy timeline. KEY RESULT and the local reading storage key remain unchanged.
- New changes are proposed via a feature PR; no automatic main merge. See `maintenance/v2-validation.md` for completed checks and remaining verification boundaries.

# Changelog

## 2026-09-17 — 关键文献补充与 ISO 周检索

- 增补 32 篇关键文献（p047–p078），合计 78 篇；原有 46 条记录和稳定 ID 未修改。
- 覆盖语言条件控制前驱、通用策略、VLA、动作生成、空间表征、数据/基准与世界动作模型；关键文献为编辑精选，不是影响力或引用量排行榜。
- 新增首发年份与 ISO 周次筛选、可切换的周/月时间线、周范围详情与 CSV 字段；收录批次保持独立口径。
- 只精确到月份或日期未知的记录不推算周数，单独显示；使用 UTC 计算以避免浏览器时区改变周归属。
- 新增日期模块和日期回归测试；发布制品加入 dates.js。
- 本次为历史关键文献定向补充，不是 9 月全量检索；不推进 maintenance/state.json 的周更检查点。
- 文献清单和证据边界见 maintenance/landmarks-2026-09.md；周检索维护说明见 maintenance/week-search.md。
- 周日定时维护调整为人工审核流程：自动任务只创建 `weekly-update-YYYY-MM-DD` 分支和 PR，不直接修改 `main`，不自动合并；维护者审核后手动合并。交互式明确要求的即时更新仍可在完整验证后直接 fast-forward 到 `main`。

## 2026-09-17 — 独立仓库迁移

- 将既有 VLA Radar 站点迁入独立仓库，保留原界面、检索、筛选和本地阅读逻辑。
- 已从固定公开快照导入首批 46 篇记录；原始文件哈希、数据字节一致性、公开结构、去重和 JavaScript 语法校验通过。具体记录见 maintenance/migration.json。迁移不代表重新核验论文。
- 修正仓库和数据编辑入口；新增 AGENTS.md、MAINTENANCE.md、检索检查点、去重校验和 Pages 发布流程。
- 原主页仓库当前文件树已恢复到迁移前的主页状态；与添加文献站之前相比，文件差异为零，正常提交历史保留。
- 已设置每周日早晨约 08:00（Asia/Singapore，UTC+8）的文献维护任务，首次为 2026-09-20。首轮回补 2026-09-01 起的公开成果；截至本次迁移尚未执行该轮检索。后续运行依赖可用的检索工具与 GitHub 授权，任务结果必须区分新增、修订和未完成项。
- 本次迁移时新仓库尚未启用 Pages。请在 Settings → Pages → Source 选择 GitHub Actions，然后手动运行 Validate and deploy VLA Radar。代码迁移及校验通过不等于网站已经发布。

后续周更应在本文件新增日期分节，记录新增/修订 ID、数量及公开核验范围。不要重写已有历史，也不要写入私人研究内容。
