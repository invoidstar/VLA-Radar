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
data/catalog.json          首页搜索目录（不包含详细笔记）
data/details/p001.json      点击论文后按需载入
data/leaderboards.json      榜单视图按需载入
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

笔记分研究问题、贡献与创新、方法机制、训练与评测口径、关键结果、消融与负面结果、局限和阅读重点。每节保存自己的证据来源；阅读标签分 `legacy`（旧笔记）、`expanded`（指定版本已扩展）、`needs_review`（如新版待复核）。本次先扩展 VLAct、Xiaomi-Robotics-1、SelfWAM、OpenVLA、OpenVLA-OFT、Cosmos Policy 六篇，其他旧记录不冒充已经重新精读。

每周自动生成八篇旧记录优先队列，同时处理所有新收录；如果工具或证据不足，保留旧笔记并记录未完成项。以实际核验进展清理积压，不以补长文字冒充证据。旧的 `paper.evidence` 和新 `note` 核验独立，扩展笔记不等于复核所有旧 KEY RESULT。

## 榜单：自动识别候选，核验后入榜

```bash
python scripts/discover_results.py --paper p021 --source https://arxiv.org/html/2608.00725v1 --version v1 --html /path/to/public-source.html --output maintenance/candidates/p021.json
python scripts/extract_results.py https://arxiv.org/html/2608.00725v1 --paper p021 --version v1 --table 0 --track robotwin2-selfwam-27500 --columns '{"Clean":1,"Random":2,"Average":3}' --html /path/to/public-source.html --output maintenance/candidates/p021-table.json
```

`--table` 为零起始 HTML table 索引，不是假定与论文“Table 1”等价；核对具体定位。发现器识别附近数据集词和分数列，但不自行推断完整协议。所有抽取都先是候选；合并单元格、多个数字、单位不清、任务子集不明时需读实际表格。候选不能排名，缺失不填0。

榜单记录包括 reporting paper ID、方法名、协议 ID、各列原始值、来源版本、表/节位置、训练预算、评测说明和核验时间。作者自己的方法与同文引用的基线区分显示。相同方法在不同论文或协议下的分数不自动取最大值；同协议修订用 `supersedes` 保留旧行。`protocol` 显示该赛道内的作者报告排序，但不声称预训练/算力完全公平或统计显著；`paper-table` 只陈列原文比较、不生成名次。

本次初始8赛道、27结果；这是有证据定位的初始覆盖，不是全领域最新/完整官方榜。后续发现任务同时提取新论文与修订中的结果。

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
