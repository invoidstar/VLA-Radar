# VLA Radar · 长期维护手册 v2

仓库：https://github.com/invoidstar/VLA-Radar  
网站：https://invoidstar.github.io/VLA-Radar/

## 数据与构建

```
catalog/manifest.json       公共元信息、稳定论文顺序
catalog/first-public.json   最早公开日期的迁移保护值
catalog/papers/p001.json    单篇源记录（paper / publication / note）
catalog/benchmarks.json     显式评测协议与指标定义
catalog/results/r-*.json    单条结果与证据
            ↓ python scripts/build_catalog.py
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
python scripts/build_catalog.py
python scripts/validate_all.py
python -m http.server 8080
```

直接双击 HTML 受浏览器 fetch 限制，请使用本地 HTTP 服务器。网站公开导出不包含私人阅读进度；阅读备份仍使用原键，只留本地。

## 发表历程：四种日期不混用

`paper.firstPublished` 保留首次公开口径。`publication.firstArxivAt` 来自可核对的 arXiv v1；如果旧数据只有“首次公开”，不推断它一定就是 arXiv 日期。`acceptedAt` 只来自正式录用证据；`publishedAt` 保留出版方年月日精度。期刊卷期日期、online-first、会议年份、发现日期均不互相替代。

`latestArxivVersion/latestArxivAt` 表示元数据当前版本；`note.version/verifiedAt` 表示笔记实际阅读版本和核验日期。新版本会触发 `needs_review`，不把旧笔记直接认证为最新版。历史事件带原文链接、事件日期与发现日期，保留新增/修订/录用/正式发表信息。

```bash
python scripts/sync_publications.py                 # 预览，不写源文件
python scripts/sync_publications.py --apply-safe    # 仅在候选分支更新安全元数据
```

arXiv 按精确 ID 分批、间隔请求；Crossref 只核对直接关联的 DOI 及高相似标题。无 DOI 的论文、改题论文、仅在作者评论中出现的录用消息进入待核验队列，由维护任务查看会议、期刊或 OpenReview 的正式证据后更新。脚本不是无遗漏的录用识别器。不用 arXiv 的 DataCite DOI 证明会议发表，不根据 Crossref deposit 日期猜录用时间。部分失败不标成全量成功。

## 详细阅读笔记

笔记分研究问题、贡献与创新、方法机制、训练与评测口径、关键结果、消融与负面结果、局限和阅读重点。每节保存自己的证据来源；阅读标签分 `legacy`（旧笔记）、`expanded`（指定版本已扩展）、`needs_review`（如新版待复核）。当前覆盖与受限项以 canonical 文件和 work-queue 为准，不在维护手册固化易过期的完成数量。

每周自动生成八篇旧记录优先队列，同时处理所有新收录；如果工具或证据不足，保留旧笔记并记录未完成项。以实际核验进展清理积压，不以补长文字冒充证据。旧的 `paper.evidence` 和新 `note` 核验独立，扩展笔记不等于复核所有旧 KEY RESULT。

## 榜单：自动识别候选，核验后入榜

```bash
python scripts/discover_results.py --paper p021 --source https://arxiv.org/html/2608.00725v1 --version v1 --html /path/to/public-source.html --output maintenance/candidates/p021.json
python scripts/extract_results.py https://arxiv.org/html/2608.00725v1 --paper p021 --version v1 --table 0 --track robotwin2-selfwam-27500 --columns '{"Clean":1,"Random":2,"Average":3}' --html /path/to/public-source.html --output maintenance/candidates/p021-table.json
```

`--table` 为零起始 HTML table 索引，不是假定与论文“Table 1”等价；核对具体定位。发现器识别附近数据集词和分数列，但不自行推断完整协议。所有抽取都先是候选；合并单元格、多个数字、单位不清、任务子集不明时需读实际表格。候选不能排名，缺失不填0。

榜单记录包括 reporting paper ID、方法名、协议 ID、各列原始值、来源版本、表/节位置、训练预算、评测说明和核验时间。作者自己的方法与同文引用的基线区分显示。相同方法在不同论文或协议下的分数不自动取最大值；同协议修订用 `supersedes` 保留旧行。`protocol` 显示该赛道内的作者报告排序，但不声称预训练/算力完全公平或统计显著；`paper-table` 只陈列原文比较、不生成名次。

当前赛道与结果数量由源数据构建；这些记录不是全领域最新/完整官方榜。后续发现任务同时提取新论文与修订中的结果。

## 维护节奏与状态

每周日早晨约08:00（Asia/Singapore）原有 ChatGPT 任务继续执行，首次2026-09-20。顺序为读取最新默认分支→文献发现→全部 arXiv/直接DOI状态扫描→正式出处候选复核→新论文和旧队列笔记→榜单候选与协议核验→源健康轮检→构建校验→PR。没有变更不创建空PR。检索首次从2026-09-01回补，此后从最近完整成功日期回退14天；本次工程升级不前移这个检查点。

```bash
python scripts/maintenance_queue.py --limit 8
python scripts/check_sources.py --limit 100 --due-days 30
python scripts/build_catalog.py
python scripts/validate_all.py
```

来源检查是逐周轮转的月龄检查，不是假定一次100条覆盖全部。月底检查队列是否完成一轮；403/429/超时只报告，不阻塞合并或删论文。每季度复查分类、旧笔记、字段兼容与协议定义。状态文件必须说明实际覆盖。`publication-check.json`、`source-health.json`、`work-queue.json` 均不能替代文献发现的 `state.json`。

## PR、CI 与发布

详见 `maintenance/publishing-policy.md`。维护者已授权本轮及每周维护在来源自检和CI全部通过后，经PR正常合并并发布，无需重复确认。必须对精确head检查、写明助手自检而非独立评审，不绕过任何分支或环境保护；阻塞时保留PR并报告，不伪造批准。

`python scripts/validate_all.py` 包括全库分节笔记、来源范围、新论文深度和逐篇榜单引用检查，以及生成一致性、不可变日期、协议与证据约束、Python与Node回归。结构验证不能认证科学结论。

合并后必须核实对应main提交的Pages deploy成功。创建PR、CI通过和artifact上传均不等于上线；浏览器交互未测试时另行注明。来源访问失败只影响对应未核验内容，不阻止其他可靠内容的小批次交付。


## 运行维护与规模（2026-09-18）

具体策略见 `maintenance/operations.md`。发表同步使用端点明确的Accept、官方摘要页Submission history回退、3.1秒间隔、限次和失败熔断；按到期时间轮转，每次默认最多100篇。只检索到期子集不等于全库更新，报告totalTracked/dueCount/metadataChecked/dueRemaining。403/429不开替代通道规避限制。标题身份冲突、首发日期冲突和录用注释仍需源复核。只修改lastCheckedAt不刷新文献内容updatedAt。

每周执行安全分支清理，部署成功后也有独立housekeeping工作流。仅清理同仓库已合并到main、head SHA没有新提交且超过6小时恢复窗口的托管分支，最多10个。main/备份/保护分支、未合并分支、任何open PR的head或base均保留。删除使用精确SHA lease条件删除，不做任何强制历史更新。完整审计包含原SHA、PR、结果，作为30天Actions artifact；未合并旧分支只报告。

主分支保护需GitHub Administration(write)，普通contents:write不能代替。`configure_main_protection.py`默认审计，`--apply`仅为未保护main安装配置，不覆盖现有更强规则。授权不足写明blocked，不关闭保护或伪造独立批准。发布前CI与自检仍必须完成。

性能：轻量目录只保留列表字段，详细笔记/搜索索引/赛道结果分离；带内容哈希文件供浏览器缓存，失败请求从缓存驱逐。详情及结果JSON缓存40项、查询缓存32项，列表12条、榜单20条，搜索在Worker执行、不可用时协作式分块回退。长期网页不无限积累已读全文。旧catalog/papers/leaderboards导出保持可用。

`check_performance.py`检查首屏每篇预算和分片隔离，`test_performance.cjs`使用临时1000/5000/10000条模拟数据，不写入真实文库。记录环境与测量范围；不把Node执行时间当成手机加载速度。公开图表以后按需加载，避免给首页增加重型绘图库或整库高清图。

## 阅读工作台与周更变更记录

详见 maintenance/workspace.md。保存变更前最新main精确SHA后，完成论文/笔记/结果修改，再运行capture_activity.py --base该SHA、build_catalog.py、validate_all.py。只记录实际差异；旧快照不补造首次收录，元数据检查不冒充精读更新。每周继续同步榜单、全文笔记、发表状态与安全分支清理；新工具不降低来源或发布门槛。HTTP浏览器回归还包括reader、compare、updates、coverage、当前协议图表及导出。


## Embodied AI Weekly / 具身智能周报

详见 `maintenance/news-policy.md`。新闻独立于论文和榜单；维护实际来源、事件/报道日期、公告与材料开放边界、背景/对应论文关系。原有每周任务同时检索过去14天的重要具身智能动态，重点最近7天，3–5条编辑精选，不凑数、不重报旧闻。状态和候选分别保存在news-state/news-candidates，部分检索不能推进完整成功检查点。只编辑catalog/news，构建哈希分片；News代码、样式与数据按需加载。发布前执行browser_news.py与既有完整CI，正常PR自检合并后核实Pages。


## 功能收口与日常工具（2026-09-18）

详见 `maintenance/daily-tools.md`。My Radar、全局快捷搜索和多格式引用导出为本轮最后的功能增量，不新增 RSS。此后默认不大改功能或架构：只有明确的实际痛点、性能瓶颈或安全/兼容性问题才做必要变更；日常持续提高内容质量、覆盖率和稳定性。每周保留论文深入阅读、原表核验榜单、发表状态、具身智能周报、活动捕获、来源检查和安全分支清理。新增公开工具索引由正常构建自动同步，浏览器关注和已看标记绝不进入公开数据。书目扩展须有一手来源、身份核对及真实日期，未知作者/卷期不猜补。保持按需加载、原阅读存储键和所有既有测试；新增browser_tools.py也必须通过后才正常自检合并发布。
