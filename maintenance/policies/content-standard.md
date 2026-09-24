# 深入阅读与榜单同步标准（2026-09-18）

## 分批交付

内容按3–8篇的小批次处理。先完成可核验的条目、构建并提交，不等待全部旧笔记完成。维护者已明确授权本轮深入笔记/榜单回补由助手进行来源与代码自检、创建PR、通过CI后合并发布；这是同一助手的自检，不是第三方独立评审，不得伪造GitHub批准或绕过保护。2026-09-18起，该来源自检、CI后合并授权也适用于每周维护；仍不允许其他仓库写入或绕过保护。详细条件见publishing-policy.md。

`release/batch-*`支持明文批次JSON：`maintenance/audits/batches/*.json`。除既有 `notes / tracks / results` 外，批次可选携带 `resources` 对象，为已有论文增补或移除 `project / code`；批处理会合并到 `catalog/resources.json` 并走同一公开URL与paper ID校验。未提供 `resources` 的历史批次保持兼容。工作流只在发布分支应用未处理批次，校验后以普通push提交生成文件；主分支不由批次工作流写入。合并后须确认Pages的deploy步骤成功。`maintenance/state/applied-batches.json`记录真实完成批次及哈希，不能重写已应用批次。修正旧内容应另建新批次。

## 笔记质量

每篇新论文以及本轮深化的旧论文应有8个以上实质章节。一般目标为约2000–4000个中文正文字符或相当信息量；字符数是防止退化成短摘要的结构提醒，不是科研理解质量证明，不为凑字数重复套话。

必须让读者能顺着文字理解：研究问题和已有瓶颈；相对已有方法真正改变了什么；输入、输出、模块数据流；监督信号和训练过程；部署时实际可用的信息与执行步骤；实验协议及量化结果；消融能/不能归因什么；失败、局限与一般性启示。架构/数据集/基准论文可调整标题，但不能把不适用项伪造为做过的实验。

每节附原文版本和可定位一手来源。具体结果给出数据集版本/划分/输入、训练预算、指标单位、评测次数/种子（未公开写未知）、基线、表或图定位。区分作者结论、编辑分析与独立复现。完整训练配置只有读到才写，不从同系列其他论文补猜。

支持安全Markdown管线表（首行表头、次行分隔线）；重排数字注明原表与变换。原图优先给直达页/图链接并解释如何读图；只在明确许可允许且记录署名时镜像局部原图，不上传完整受版权保护PDF。不得由柱状图像素猜出精确榜单分数。

元数据检查不使笔记自动升级。`expanded`是限定版本的内容状态，不是整个领域的最新结论；新版本仍需复核。之前的浅笔记不会因模板上线而视作深入完成。每批记录实际处理ID，不声称未保存的本地工作已发布。

## Leaderboard同步

不再只检查LIBERO/RoboTwin/RoboCasa。每次检索与深读都检查已定义的所有数据集，并发现实质相关的新基准，包括CALVIN、RLBench、SimplerEnv、RoboMimic、Push-T、Franka Kitchen、ALOHA-Sim，以及后续有可核验数据的RoboDojo、RoboChallenge、Meta-World等。新增数据集必须有真实核验结果与协议，而不是空导航入口。

对每篇新论文或深化论文，在`maintenance/state/benchmark-review.json`记录三种结果之一：extracted（指向已核验结果ID）；deferred（说明缺少精确值、协议或可访问原文）；not-applicable（说明没有适用机器人基准）。缺项不得被简报表述为完成榜单维护。

分清：PH/MH、图像/状态、单/多视角、脚本/人类示范、clean/random、原版/Plus/PRO、最佳检查点/最后检查点/末多检查点平均，以及完整成功率/部分覆盖率/平均链长。同名方法在不同报告中的设置不能合并取最大值。相同协议有新版本用supersedes保留历史。

原文内部矛盾必须显式记录，例如表注与更正脚注的回合数不一致、示范数量冲突。训练或控制条件未统一时使用paper-table，不给公平排名。科学事实和原表定位由阅读核验，CI只能查结构、数值范围及引用/文件一致性。

## 官方资源链接

每篇新收录论文都同步检查官方项目主页与开源代码。优先论文正文/作者明确给出的 Project / Code，其次作者、实验室或机构维护页面；第三方复现、聚合站、同名仓库不收。只写入已经公开可访问的资源：若页面写着 “Code coming soon”，可记录项目主页，但不得把未公开仓库标成开源代码。

资源统一放在 `catalog/resources.json`，只允许 `project` / `code` 两类，与论文 Evidence `sources` 分离。找不到可靠官方资源时保持缺失，不写“暂无”占位，也不猜链接。旧论文在版本复核或发现新官方仓库时可通过内容批次增补；失效或误配链接可用 `null` 删除对应 kind，并保留其他已核验资源。

## 周更

沿用现有每周任务，检索新论文、追踪旧论文发表状态，同时按本标准补深读笔记、所有相关榜单和官方资源链接。新增论文在进入主库前检查 Project / Code；既有论文若出现新仓库或项目页，在当周同步更新资源 registry。

文献发现从 2026-09-25 起使用 `maintenance/policies/discovery-policy.json` 与 `scripts/discovery/discovery_coverage.py`。每次先按 last successful checkpoint 回退14天生成扫描窗口，再分别完成 primary-preprints、academic-index、curated-robotics、reverse-discovery 四个 lane，并把实际 provider、query/scope、覆盖日期、结果数和 blocked/partial 状态写入 schema-v2 discovery audit。所有候选必须有 `selected / deferred / excluded / duplicate` disposition；deferred 不因当周未深读而丢失，历史 audit 会与新 audit 聚合成持续候选队列。

单项来源被阻塞不阻塞其他已核验内容的PR，也不阻止已经充分核验的论文入库；但只要任一必需 discovery lane 未完整覆盖，本轮只能标为 partial，`lastSuccessfulSearchAt` 不得推进。完整成功日期只能由通过 coverage gate 的 audit 经 `discovery_coverage.py apply` 更新。范围、数量和状态均按仓库当前记录统计，不能把“找到了几篇论文”替代“扫描窗口已完整覆盖”的证据。

## 全库检查与受限材料

`check_editorial.py`检查全库每篇分节笔记与逐篇榜单处理引用。历史正文级笔记最低1500字符、8节；新增论文最低2000字符、8节，且需完整方法／理论／报告来源。该结构底线不替代信息质量。DMS与VLAbot为明确受限的历史例外，保持needs_review并注明实际来源；新发现仅有摘要时先放候选，不以例外身份进入主库。
