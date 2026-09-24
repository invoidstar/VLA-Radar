# VLA Radar · 长期维护手册 v2

仓库：https://github.com/invoidstar/VLA-Radar  
网站：https://invoidstar.github.io/VLA-Radar/

## 数据与构建

```
catalog/manifest.json       公共元信息、稳定论文顺序
catalog/first-public.json   最早公开日期的迁移保护值
catalog/papers/p001.json    单篇源记录（paper / publication / note）
catalog/benchmarks.json     显式评测协议与指标定义
catalog/relations.json      已核验论文前后继与系列关系
catalog/reproducibility.json 复现资源状态与核验证据
catalog/results/r-*.json    单条结果与证据
            ↓ python scripts/build/build_catalog.py
data/library.json          轻量首页目录（卡片与筛选字段）
data/search-index.HASH.json 首次检索时载入；Web Worker计算
data/catalog.json          兼容旧客户端的完整概述导出
data/details/p001.json      点击论文后按需载入
data/board-index.HASH.json  榜单目录
data/boards/*.HASH.json     当前赛道结果按需载入
data/paper-results/*.json   单篇论文评测按需载入
data/leaderboards.json      完整榜单兼容导出（不用于默认浏览）
data/papers.json            保持 v1 字段的兼容导出
```

单篇修改不再编辑整份巨大源 JSON。构建结果仍提交以支持 GitHub Pages 和静态 HTTP 预览。生成的大文件 diff 由 `.gitattributes` 标记，审核重点是单篇源记录；CI 检查生成内容与源记录完全一致。原来 78 个 ID、KEY RESULT 和浏览器阅读记录保持。分页控件数量有界；时间线首次最多80条，继续加载更早记录。无数据库或运行期 API。

本地运行：

```bash
python scripts/build/build_catalog.py
python scripts/validate/validate_all.py
python scripts/build/stage_site.py --output _site
python -m http.server 8080 -d _site
```

直接双击 HTML 受浏览器 fetch 限制，请使用本地 HTTP 服务器。网站公开导出不包含私人阅读进度；阅读备份仍使用原键，只留本地。

## 发表历程：四种日期不混用

`paper.firstPublished` 保留首次公开口径。`publication.firstArxivAt` 来自可核对的 arXiv v1；如果旧数据只有“首次公开”，不推断它一定就是 arXiv 日期。`acceptedAt` 只来自正式录用证据；`publishedAt` 保留出版方年月日精度。期刊卷期日期、online-first、会议年份、发现日期均不互相替代。

`latestArxivVersion/latestArxivAt` 表示元数据当前版本；`note.version/verifiedAt` 表示笔记实际阅读版本和核验日期。新版本会触发 `needs_review`，不把旧笔记直接认证为最新版。历史事件带原文链接、事件日期与发现日期，保留新增/修订/录用/正式发表信息。

```bash
python scripts/maintenance/sync_publications.py                 # 预览，不写源文件
python scripts/maintenance/sync_publications.py --apply-safe    # 仅在候选分支更新安全元数据
```

arXiv 按精确 ID 分批、间隔请求；Crossref 只核对直接关联的 DOI 及高相似标题。无 DOI 的论文、改题论文、仅在作者评论中出现的录用消息进入待核验队列，由维护任务查看会议、期刊或 OpenReview 的正式证据后更新。脚本不是无遗漏的录用识别器。不用 arXiv 的 DataCite DOI 证明会议发表，不根据 Crossref deposit 日期猜录用时间。部分失败不标成全量成功。

## 精简发布流水线（2026-09-25）

完整质量门禁只在 Pull Request 的 exact head 执行一次：`validate_all.py` + 全部 HTTP/browser regressions。通过助手自检后使用 expected-head 正常合并。

main push 不再重复下载 Firefox/WebKit 或重跑完整浏览器套件，只执行 `build_catalog.py --check`，随后 stage → Pages deploy → production smoke。production smoke 成功即可认定上线；housekeeping 已从每次发布链路移除，仅保留每周 schedule 与手动 dispatch。

该精简依赖“正常变更必须经过 PR exact-head 完整门禁”的既有规则；direct push main 仍不是常规发布路径。

## 文献发现覆盖门禁（2026-09-25）

文献发现不再用“本周搜过了”或单一聚合站作为成功判据。完整检索窗口由 `maintenance/policies/discovery-policy.json` 定义四类必需 lane：直接 primary preprint/publisher 检索、独立 academic index、VLA/机器人 curated index、以及官方 lab/project/benchmark/leaderboard 或 related/citation 的反向发现。每个 lane 至少要有一个成功 provider 覆盖整个窗口；某个必需 lane 被限流、阻塞或只完成部分范围时，本轮 discovery 状态必须是 `partial`。

每周先生成真实扫描窗口：

```bash
python scripts/discovery/discovery_coverage.py plan --to YYYY-MM-DD
```

其 `from` 会从 `lastSuccessfulSearchAt` 回退14天，主动重叠扫描以吸收延迟收录与索引更新时间差。完成搜索后，将实际 provider、query/scope、覆盖起止、resultCount、状态与全部候选 disposition 写入 `maintenance/audits/discovery/discovery-FROM-TO*.json`（schema v2）。候选只允许 `selected / deferred / excluded / duplicate`，并按 arXiv ID、DOI、规范标题去重；找到了但尚未全文核验的论文必须留为 deferred，不能从后续周次消失。

```bash
python scripts/discovery/discovery_coverage.py validate maintenance/audits/discovery/discovery-FROM-TO.json
python scripts/discovery/discovery_coverage.py apply maintenance/audits/discovery/discovery-FROM-TO.json
python scripts/discovery/discovery_coverage.py status
```

只有通过四 lane 门禁的 `success` audit 才能推进 `maintenance/state/state.json.lastSuccessfulSearchAt`。partial audit 仍可记录本周尝试，也不阻止已经由一手来源完整核验的论文单独发布，但 checkpoint 保持原值。历史 schema-v1 discovery audit 不重写；状态命令会与新 audit 一起聚合候选，因此旧 deferred 队列继续保留。CI 的 `check_discovery.py` 会阻止“checkpoint 已前移但没有对应完整 audit”这种漏扫状态进入 main。

## Reproducibility Card（2026-09-25）

Resources 与 Reproducibility 分层维护：`catalog/resources.json` 保存稳定的官方 Project / Code 入口，`catalog/reproducibility.json` 保存对 Code、Weights、Dataset、Training、Inference、Evaluation、License 的核验层。

全库采用两级 audit：
- `deep`：逐维读取官方仓库/项目材料，只有明确证据才写 available / partial / unavailable；
- `baseline`：已经完成当前官方入口核验，但没有足够证据的维度继续保持 unknown，不把“没找到”写成“未开放”。

当前 **116 / 116 papers 均有 audit record**：10 篇 deep、106 篇 baseline。构建器要求 reproducibility registry 与当前 paper ID 集合完全一致；新增论文若没有同步创建 baseline/deep audit，CI 会失败，因此全库覆盖不会静默退化。

构建器为每篇论文生成固定8维懒加载卡片；首页只保存 `reproducibilityUrl`，打开论文详情时才加载 `data/reproducibility/pNNN.json`。Project/Code 可由 Resources 作为基础状态，其他未被明确审计的维度保持 unknown。

`unknown` 表示“尚未充分核验”，不是“没有资源”；只有官方 README / 项目页明确声明未发布或无发布计划时才可写 `unavailable`。例如官方 GitHub 仅含 README/assets 而没有执行代码，可标 Code=partial；只开放 post-training、不开放完整 pretraining，可标 Training=partial；论文训练混合数据未完整公开但 benchmark/SFT 数据集公开，可标 Dataset=partial。

Reproducibility Card 只用于帮助读者判断公开复现入口，不生成总分、不参与论文排序，也不把第三方复现冒充官方资源。每次新增论文、官方仓库重大更新、权重/数据/代码新开放时同步复核；旧 audit 的 `verifiedAt` 不能因普通 metadata 更新自动刷新。

## 论文关系层（2026-09-25）

`catalog/relations.json` 是论文 lineage / series 的唯一 canonical 来源。它不改变单篇论文 JSON，也不替代引用网络。方向关系只允许 `extends` 与 `follow-up-of`；同系列采用 series membership，一组 N 篇论文只维护 N 个成员，不生成 N² 条 same-series 边。

构建时 `paper_relations.py` 校验 paper ID、关系类型、自环、重复边、series 成员、核验日期和公开来源，并将紧凑关系摘要注入 `data/library.json` / `data/catalog.json`。详情页由该摘要生成 Previous / Builds on、Follow-up、Same Series；前端不依据标题、作者或机构自行推断。

新增或版本复核论文时检查关系，但证据门槛高于“看起来相关”：只有论文/官方项目/作者机构材料明确支持模型前后继、扩展或系列身份时才写入。引用关系、共同 benchmark、相同 backbone、同机构或名称相似均不足以建立 relation。未收录的外部前作可在阅读笔记里说明，但不能分配虚构 paper ID。

## 详细阅读笔记

笔记分研究问题、贡献与创新、方法机制、训练与评测口径、关键结果、消融与负面结果、局限和阅读重点。每节保存自己的证据来源；阅读标签分 `legacy`（旧笔记）、`expanded`（指定版本已扩展）、`needs_review`（如新版待复核）。当前覆盖与受限项以 canonical 文件和 work-queue 为准，不在维护手册固化易过期的完成数量。

每周自动生成八篇旧记录优先队列，同时处理所有新收录；如果工具或证据不足，保留旧笔记并记录未完成项。以实际核验进展清理积压，不以补长文字冒充证据。旧的 `paper.evidence` 和新 `note` 核验独立，扩展笔记不等于复核所有旧 KEY RESULT。

## 榜单：自动识别候选，核验后入榜

```bash
python scripts/discovery/discover_results.py --paper p021 --source https://arxiv.org/html/2608.00725v1 --version v1 --html /path/to/public-source.html --output maintenance/candidates/p021.json
python scripts/discovery/extract_results.py https://arxiv.org/html/2608.00725v1 --paper p021 --version v1 --table 0 --track robotwin2-selfwam-27500 --columns '{"Clean":1,"Random":2,"Average":3}' --html /path/to/public-source.html --output maintenance/candidates/p021-table.json
```

`--table` 为零起始 HTML table 索引，不是假定与论文“Table 1”等价；核对具体定位。发现器识别附近数据集词和分数列，但不自行推断完整协议。所有抽取都先是候选；合并单元格、多个数字、单位不清、任务子集不明时需读实际表格。候选不能排名，缺失不填0。

榜单记录包括 reporting paper ID、方法名、协议 ID、各列原始值、来源版本、表/节位置、训练预算、评测说明和核验时间。作者自己的方法与同文引用的基线区分显示。相同方法在不同论文或协议下的分数不自动取最大值；同协议修订用 `supersedes` 保留旧行。`protocol` 显示该赛道内的作者报告排序，但不声称预训练/算力完全公平或统计显著；`paper-table` 只陈列原文比较、不生成名次。

当前赛道与结果数量由源数据构建；这些记录不是全领域最新/完整官方榜。后续发现任务同时提取新论文与修订中的结果。

## 维护节奏与状态

每周日早晨约08:00（Asia/Singapore）原有 ChatGPT 任务继续执行，首次2026-09-20。顺序为读取最新默认分支→用 discovery coverage plan 确定重叠窗口→完成四类来源 lane 并写 audit→候选去重与 disposition→全部 arXiv/直接DOI状态扫描→正式出处候选复核→新论文和旧队列笔记→榜单候选与协议核验→源健康轮检→构建校验→PR。没有变更不创建空PR。2026-09-24 以前的完整回补作为 legacy baseline 保留；2026-09-25 起只有 schema-v2 multi-lane audit 可以继续推进完整检索 checkpoint。

```bash
python scripts/discovery/discovery_coverage.py plan --to YYYY-MM-DD
python scripts/discovery/discovery_coverage.py status
python scripts/maintenance/maintenance_queue.py --limit 8
python scripts/maintenance/check_sources.py --limit 100 --due-days 30
python scripts/build/build_catalog.py
python scripts/validate/validate_all.py
```

来源检查是逐周轮转的月龄检查，不是假定一次100条覆盖全部。月底检查队列是否完成一轮；403/429/超时只报告，不阻塞合并或删论文。每季度复查分类、旧笔记、字段兼容与协议定义。状态文件必须说明实际覆盖。`publication-check.json`、`source-health.json`、`work-queue.json` 均不能替代文献发现的 `state.json`。

## PR、CI 与发布

详见 `maintenance/policies/publishing-policy.md`。维护者已授权本轮及每周维护在来源自检和CI全部通过后，经PR正常合并并发布，无需重复确认。必须对精确head检查、写明助手自检而非独立评审，不绕过任何分支或环境保护；阻塞时保留PR并报告，不伪造批准。

`python scripts/validate/validate_all.py` 包括全库分节笔记、来源范围、新论文深度和逐篇榜单引用检查，以及生成一致性、不可变日期、协议与证据约束、Python与Node回归。结构验证不能认证科学结论。

合并后必须核实对应main提交的Pages deploy成功。创建PR、CI通过和artifact上传均不等于上线；浏览器交互未测试时另行注明。来源访问失败只影响对应未核验内容，不阻止其他可靠内容的小批次交付。


## 运行维护与规模（2026-09-18）

具体策略见 `maintenance/docs/operations.md`。发表同步使用端点明确的Accept、官方摘要页Submission history回退、3.1秒间隔、限次和失败熔断；按到期时间轮转，每次默认最多100篇。只检索到期子集不等于全库更新，报告totalTracked/dueCount/metadataChecked/dueRemaining。403/429不开替代通道规避限制。标题身份冲突、首发日期冲突和录用注释仍需源复核。只修改lastCheckedAt不刷新文献内容updatedAt。

每周执行安全分支清理，部署成功后也有独立housekeeping工作流。仅清理同仓库已合并到main、head SHA没有新提交且超过6小时恢复窗口的托管分支，最多10个。main/备份/保护分支、未合并分支、任何open PR的head或base均保留。删除使用精确SHA lease条件删除，不做任何强制历史更新。完整审计包含原SHA、PR、结果，作为30天Actions artifact；未合并旧分支只报告。

主分支保护需GitHub Administration(write)，普通contents:write不能代替。`configure_main_protection.py`默认审计，`--apply`仅为未保护main安装配置，不覆盖现有更强规则。授权不足写明blocked，不关闭保护或伪造独立批准。发布前CI与自检仍必须完成。

性能：轻量目录只保留列表字段，详细笔记/搜索索引/赛道结果分离；带内容哈希文件供浏览器缓存，失败请求从缓存驱逐。详情及结果JSON缓存40项、查询缓存32项，列表12条、榜单20条，搜索在Worker执行、不可用时协作式分块回退。长期网页不无限积累已读全文。旧catalog/papers/leaderboards导出保持可用。

`check_performance.py`检查首屏每篇预算和分片隔离，`test_performance.cjs`使用临时1000/5000/10000条模拟数据，不写入真实文库。记录环境与测量范围；不把Node执行时间当成手机加载速度。公开图表以后按需加载，避免给首页增加重型绘图库或整库高清图。

## 阅读工作台与周更变更记录

详见 maintenance/docs/workspace.md。保存变更前最新main精确SHA后，完成论文/笔记/结果修改，再运行capture_activity.py --base该SHA、build_catalog.py、validate_all.py。只记录实际差异；旧快照不补造首次收录，元数据检查不冒充精读更新。每周继续同步榜单、全文笔记、发表状态与安全分支清理；新工具不降低来源或发布门槛。HTTP浏览器回归还包括reader、compare、updates、coverage、当前协议图表及导出。


## Embodied AI Weekly / 具身智能周报

详见 `maintenance/policies/news-policy.md`。新闻独立于论文和榜单；维护实际来源、事件/报道日期、公告与材料开放边界、背景/对应论文关系。原有每周任务同时检索过去14天的重要具身智能动态，重点最近7天，3–5条编辑精选，不凑数、不重报旧闻。状态和候选分别保存在news-state/news-candidates，部分检索不能推进完整成功检查点。只编辑catalog/news，构建哈希分片；News代码、样式与数据按需加载。发布前执行browser_news.py与既有完整CI，正常PR自检合并后核实Pages。


## 功能收口与日常工具（2026-09-18）

详见 `maintenance/docs/daily-tools.md`。My Radar、全局快捷搜索和多格式引用导出为本轮最后的功能增量，不新增 RSS。此后默认不大改功能或架构：只有明确的实际痛点、性能瓶颈或安全/兼容性问题才做必要变更；日常持续提高内容质量、覆盖率和稳定性。每周保留论文深入阅读、原表核验榜单、发表状态、具身智能周报、活动捕获、来源检查和安全分支清理。新增公开工具索引由正常构建自动同步，浏览器关注和已看标记绝不进入公开数据。书目扩展须有一手来源、身份核对及真实日期，未知作者/卷期不猜补。保持按需加载、原阅读存储键和所有既有测试；新增browser_tools.py也必须通过后才正常自检合并发布。


## 官网反向文献与基准身份

读取 `maintenance/policies/benchmark-content-policy.md` 与 `maintenance/audits/benchmark/benchmark-source-audit-20260918.json`。周更将当前数据集官网/官方榜单作为发现论文的入口，按实际完成的深读小批次入库。必须将RoboCasa与RoboCasa365分别显示，并保留365的运行版本（1.0.0/1.0.1）、episode horizon、目标/预训练厨房和示范预算。不同版本或同名方法不同设置不覆盖取最大值；官方/论文同源记录不视为独立复现。未取得完整论文/身份或协议不明的条目保留候选，局部审计不推进完整文献检索检查点。

## 榜单交互维护（2026-09-19）

按`maintenance/docs/leaderboard-analysis.md`保留任意成绩列排序、名次/显示方向分离和协议内时间—成绩图。内容更新使用现有firstPublished/verifiedAt，不从图表需要倒推日期或分数。新增browser_leaderboard.py须与现有五套浏览器测试一起通过；没有扩大主库/新闻的自动入库范围。


## Benchmark 协议族与 Recipe 层级（2026-09-20）

Benchmark 导航不再把“来源论文 / 训练 recipe / 评测协议”全部提升为同一级 setting。新的信息模型为：

`Benchmark → Protocol Family → Method → Recipe / Subprotocol → Evidence`

`familyId` 只用于组织评测可比性或明确标注的子协议系列；原始 `track.id`、结果记录和证据定位仍是不可替代的精确层。训练数据量、per-task / multi-task、训练步数、base model、部署方式等优先放在 recipe 层，而不是自动产生新的 Benchmark 入口。真正改变任务集合、评测 split 或指标定义的情况仍保留为子协议。

`familyMode=aligned` 可在方法层显示按人工指定 `familyPrimaryTrackId` 选择的代表报告；代表报告只为导航，不自动取最高分，也不把不同训练预算解释为公平同条件排名。若指定主 track 没有某方法，则使用该方法在协议族 track 顺序中的第一条记录。`familyMode=series` 用于任务子集、部署消融等不可直接合并的系列，只展开各子协议 / 变体，不生成跨子协议代表分数、平均值或名次。

当前先对 RoboTwin 完成人工整理；没有 family 元数据的数据集继续使用原来源分组兼容路径，后续必须人工核对协议后再迁移，禁止仅依据论文名、URL 或字段相似度自动合并。


## Benchmark Setting / Result Report 层级（2026-09-20）

默认 Benchmark 页面采用：

`Benchmark → Setting → Result Report`

其中 **Setting = Evaluation Protocol + Training Data identity**。Evaluation Protocol 至少区分任务集合、评测 split、metric/unit/direction 等真正影响结果可比性的条件；跨原始 track 的评测等价关系只能通过人工核验的 `settingEvalId` 或已对齐的 protocol family 建立，不能根据论文名、URL 或字段相似度自动猜测。

Training Data identity 只保留训练数据本身（例如数据集、示范量、任务范围）；batch、steps、learning rate、action horizon、模型结构、checkpoint、部署方式等属于 Recipe，不应仅因这些差异产生新的 Setting。若训练数据未完整披露，则 Setting 必须按来源论文隔离，禁止跨论文假定训练预算一致。

**Result Report** 是页面上的一行：`Method + Score + Source paper`。同一 Method 被不同论文或不同 recipe 报告出不同结果时必须保留为多行，不去重、不自动挑最高分。每行的 Recipe / Evidence 可展开查看完整 trainingData 原文、track trainingRegime、evaluation notes、locator、verifiedAt 与原始证据。

原始 `track.id` 与 `result.id` 仍是 canonical 精确证据层。Setting 是由构建器确定性生成的展示/比较层；`track=` 深链接、原 track 排序、图表与 CSV 高级视图继续保留。Setting 默认排序仅是 reported score 排列，不产生跨来源的公平名次。

当前生成 Setting 覆盖全部有核验结果的 Benchmark 数据集；无法安全归并的 track/结果保守保持独立。


## Benchmark Evaluation Setting 最终语义（2026-09-20）

本节**取代同日上方“Benchmark Setting / Result Report 层级”中 Setting = Evaluation Protocol + Training Data identity 的定义**。最终默认模型为：

`Benchmark → Evaluation Setting → Result Report`

**Setting = Evaluation Protocol only**。Training Data、训练 recipe、base model、checkpoint、来源论文均不得成为 Setting identity。Setting 只回答“这些报告是否在回答同一个 Benchmark 评测问题”，由 benchmark/dataset、任务集合、评测 split、metric/unit/direction 与必要的评测上下文共同决定。

训练数据改为 Result Report 的行级属性与筛选维度。页面默认可同时展示不同 Training Data 的公开报告，并提供 Training Data / Method / Source 三类筛选。Training Data 未完整披露时使用来源标识明确标记“未知”，但**未知训练数据不会再把 Setting 按论文拆开**。限定同一 Training Data 只能提高可比性，不自动证明训练 recipe、预训练、模型规模或计算预算完全一致。

以下差异属于真实 Evaluation Protocol，必须继续拆分或加护栏：任务子集、VM/VA、相机扰动、异步延迟 d、真实物理场景、干扰物条件、特殊语言评测、不同 metric、不同 task schema 等。以下差异不拆 Setting：示范量、训练数据来源、per-task/multi-task、SFT/cotrain、batch、steps、LR、action horizon、架构、base model、checkpoint 与来源论文；这些内容全部保留在结果行和 Recipe / Evidence 展开区。

同一 Method 在不同论文、不同 Training Data 或不同 recipe 中报告的分数必须保留为独立行，不去重、不自动选择最高分。默认排序仅表示 reported score 的数值顺序，不产生跨来源公平名次。原始 `track.id` / `result.id`、`track=` 深链接、track 排序、图表与 CSV 继续作为精确 evidence / advanced analysis 层。

当前生成层覆盖 61 个含核验结果的数据集，共 **194 个 Evaluation Setting**；底层仍为 98 papers、1063 checked results、286 canonical tracks。


## Benchmark 搜索（2026-09-20）

Evaluation Setting 默认页提供全局 Benchmark 搜索。检索字段限于已加载的轻量索引元数据：dataset、Setting 名称、tasks、split、metric、columns 与 evalId；多个词按 AND 组合。protocol 正文不参与搜索，避免 episode 数、训练说明等自由文本造成误命中。搜索不得为了命中而加载所有 `data/settings/` 结果分片。

搜索参数使用 `lbSearch` 写入 URL，刷新/分享需保持；切换 Benchmark 时保留搜索词，清除搜索恢复全部数据集入口。搜索仅改变导航可见性，不改变 Setting identity、结果归属、排序语义或 Training Data / Method / Source 行级筛选。


## Benchmark 分类体系（2026-09-20）

Benchmark 分类是独立的 **dataset-level taxonomy**，canonical 来源为 `catalog/benchmark-taxonomy.json`。它不得改变 Evaluation Setting、track 或 result identity，也不得从论文来源自动推断。

每个 Benchmark 必须恰好有：
- 一个 `focus`：General Manipulation / Long-Horizon & Memory / Generalization & Robustness / Dexterous & Contact-Rich / Language, Planning & Compositionality / Efficiency & Deployment；
- 一个 `environment`：Simulation / Real Robot / Mixed / Cross-Environment；
- 零个或多个受控 `tags`。

Focus 表示该 Benchmark 的主要评测侧重点；Environment 表示主要评测环境；Tags 用于补充 Household/Kitchen、Tabletop、Industrial/Assembly、Bimanual、Tactile、Long-horizon、Memory、Multi-task、Robustness/OOD、Sim-to-Real、Latency/Efficiency、Language/Compositionality 等横切属性。

前端分类筛选与 `lbSearch` 搜索组合使用：Focus 与 Environment 单选，Tags 多选并采用 AND 语义。URL 参数为 `lbFocus`、`lbEnv`、`lbTags`。分类只过滤 Benchmark / Setting 导航，不改变结果行、分数排序、Training Data / Method / Source 筛选或原始 `track=` 高级视图。

构建期 `benchmark_taxonomy.py` 必须检查 taxonomy 数据集集合与 `catalog/benchmarks.json` 中实际 dataset 集合完全一致，枚举合法、无重复 tag；新增 Benchmark 未同步分类时阻止发布。
