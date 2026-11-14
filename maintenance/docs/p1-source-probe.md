# P1 原始来源可访问性探测（2026-11-14）

## 目的
将目前四来源检索中的**独立学术索引**和RoboDojo官方JSON获取障碍变成可复查的、带日期的真实证据，不以首页标题搜索或脚本成功结束冒充完整覆盖。

- `scripts/maintenance/probe_p1_sources.py` 使用 Python 标准库，从允许的官方域名读取公共JSON；每请求12秒超时、最大5 MB、六次学术索引搜索加一次 RoboDojo 官方源请求，无需GitHub token或外部密钥。
- OpenAlex查检2026-09-20至2026-11-14的论文**出版日期**，并在title+abstract中使用VLA/WAM/robot manipulation三个查询；Semantic Scholar按照出版年份查询再根据可用publicationDate筛选。查询记录候选标题、论文ID、论文日期，但**第一页结果不足以代表整个窗口**，不得将`first-page-only`解释为满足完整四lane的成功证明。其日期不等于原始arXiv首次公开日期。
- RoboDojo使用 **`https://robodojo-benchmark.com/data/leaderboard.generated.json`**。若可以完整取得原JSON，以SHA-256及原始字节保存在CI artifact中，状态为`fetched-unverified`。这依旧**不等于**已核对模型个数、真实模型ID、Score与SR、Sim/Real、Preview/论文及官方更新日期，禁止直接覆盖正式固定SHA快照。
- 错误时只记录真实错误类别、请求源与scope。严禁伪造HTTP状态或把受限抓取标为完全成功。
- 该作业**不更新main、不更改canonical Benchmark、不推进lastSuccessfulSearchAt、不发布结果数值**；仅供后续人工原始证据核查。
- GitHub Actions：`.github/workflows/p1-evidence-probe.yml`，在相关PR修改时触发，也可以在公开仓库手动workflow_dispatch运行；结果上传`bounded-p1-evidence-probe-<runid>`，14日保留。官方源响应如需入库，先审计完整字段、来源哈希和许可证，然后以独立PR经严格CI合并。

## 后续证据闭环
若API成功响应，需要另行执行完整日期窗口、分页和候选来源去重（direct arXiv、independent index、curated feed、official reverse四路均覆盖2026-09-20至运行目标日期），通过`scripts/discovery/discovery_coverage.py validate`，才可申请推进完整成功检查点。中英文新闻有独立日期逐日审计，仍保持自身状态机。RoboDojo全量JSON必须先逐条核对与固定版本，保留旧快照至迁移核验通过。
