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

## 2026-11-14 首次真实运行结论

- [Actions run 43588136357](https://github.com/invoidstar/VLA-Radar/actions/runs/43588136357) 的公共源探测已运行，原始数据下载为 GitHub Artifact `bounded-p1-evidence-probe-43588136357`（保留14天）。
- 官方 `leaderboard.generated.json` **完整下载39,464字节**，内容SHA-256为 `a64fec25b9c19734cc1e7785655031729090f331214108449abea2c2a902bdab`；原始更新日期为2026-11-03。实测结构：Sim 66项、Real 14项，模型名称均未重复，7项Sim平均/维度及4项Real维度的Score/SR数值范围与内部Average一致。
- 与此前Git SHA固定的Sim57、Real11条目相比，出现9项新Sim模型、3项新Real模型。**官方JSON的Sim数组并非按Overall Score全序排序**（部分新增模型追加在尾部）；迁移时必须重新按官方Score排序、核验新旧共同模型记录，保留各项元信息，不得按JSON序号当排行榜排名。
- OpenAlex公开API的3个查询均返回100条第一页结果（`vision language action`、`world action model`、`robot manipulation`），但匹配总数分别为1137/2406/1671，尚未分页完成；Semantic Scholar三次返回HTTP429。论文完整四lane仍为partial，`lastSuccessfulSearchAt`不得前移。
- 原始结果、状态和新增身份已另行保存在 [p1-evidence-probe-20261114.json](../audits/maintenance/p1-evidence-probe-20261114.json)。`fetched-unverified`表示传输成功与机器可解析，不等于来源规范迁移已经完成。当前 canonical 仍保留57/11，下一轮应基于官方原始字节进行字段和对照核验并以独立PR发布。
