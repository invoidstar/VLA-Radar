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
