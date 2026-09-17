# VLA Research Radar

一个公开的 VLA / VA / WAM 论文阅读库，聚焦核心贡献、具体结果、证据边界和一般性阅读启示。

**在线网站：** https://invoidstar.github.io/VLA-Radar/

## 使用

- 检索标题、作者团队、标签、贡献、具体结论和阅读启示。
- 支持中文 / 英文常用术语互查，多关键词交集和英文标题、标签的近似匹配。数字不做模糊纠错。
- 按研究方向、纳入月份、出处、阅读建议和本地阅读状态筛选。
- 卡片 / 表格两种视图；详情页保留原始来源、首发时间和阅读版本。
- 独立的研究方向页、首次公开时间线和本地阅读清单。
- 导出当前结果为 CSV、完整公开数据库为 JSON、单篇基础引用为 BibTeX。
- `Ctrl+K` / `Cmd+K` 聚焦搜索；`Esc` 关闭详情。筛选和论文链接可分享，不携带本地阅读状态。

搜索只发生在已收录数据中，不是实时互联网或论文全文搜索；正文只索引已整理的贡献、结果与笔记。

## 数据与维护

`data/papers.json` 是唯一的公开文献数据源。修改并提交后，GitHub Pages 的现有发布流程会更新网站。**不需要安装 npm 或重新编译界面**。

目录：

```text
VLA-Radar/
  index.html         页面结构
  styles.css         响应式样式
  app.js             本地检索与阅读界面
  favicon.svg
  data/papers.json   唯一文献数据源
  validate.py        结构校验（不验证科学事实）
  README.md
```

### 新增一篇论文

复制一个已有条目，使用新的稳定 ID（如 `p047`），补全公开字段：

- `name`、`title`、`team`：方法简称、原题、署名团队；不清楚的机构明确标注。
- `venue`、`publicationType`、`publicationStatus`：出处、类型和发表状态；投稿不是录用。
- `firstPublished`：`YYYY-MM-DD` 或仅能确认月份时的 `YYYY-MM`；无法确认用 `null`，在 `dateNote` 说明。
- `collectionMonth`：`YYYY-MM`。这是纳入本库的文献批次月份，不是假定的首次发表日期。
- `versionNote`：实际阅读版本和正式发表口径。
- `topics`：第一个为主方向；后续可列交叉方向。方向定义在同一文件的 `topics` 数组中。
- `tags`：方法 / 技术关键词；`priority` 取 `deep`、`selective`、`overview`。
- `contribution`、`findings`、`limitations`：贡献、作者报告的具体结论与证据范围。
- `insight`、`readingFocus`：面向所有读者的一般性阅读启示，不包含私人方案。
- `evidence`：`notes`（笔记待复核）、`metadata`（仅出版/摘要层面）、`checked`（复核了具体片段）；并填写 `evidenceNote`。
- `hasCautionaryResult`：是否包含负面、未显著改善或明确条件性结果。
- `sources`：`[{"label":"原文 · v1","url":"https://…"}]`；`paperUrl` 为论文主链接。
- `arxiv`、`doi`：没有则用空字符串，不猜测。

同时更新根对象的 `updatedAt`，然后运行：

```bash
cd VLA-Radar
python validate.py
```

校验器拒绝未知数据字段和非 HTTP(S) 链接，但**不能自动判断科研事实是否正确**。需要人工对照一手来源，特别注意样本数、统计口径、评测子集和不同论文版本。

## 当前数据边界

首批 46 篇记录覆盖 2026 年 7—8 月首次公开或正式发表的论文。正式发表于这两个月的部分工作拥有更早预印本；时间线因此可能出现更早月份。它不是该时期的穷尽列表。

网站迁移时并未重新逐项核对全部论文全文。“已复核片段”仅适用于明确标出的条目，既不是整篇事实认证，也不是独立复现。文献中未给出或未核验的指标不补造。

阅读建议依据公开的方法价值与证据可解释性，不是论文质量排名。不将不同训练数据、示范预算、硬件或评测协议下的数字直接排序。

## 本地阅读进度

收藏和阅读状态保存在 `localStorage` 的 `vla-radar.reading.v1` 键中，不会提交到 GitHub。没有账号、后端、分析埋点或搜索 API。

“我的阅读”支持备份与恢复；恢复会合并已知论文 ID，相同 ID 以备份内容为准。清空浏览器数据会丢失记录。跨设备需要手动导出/导入。**不要把阅读备份提交到公开仓库**。浏览器存储不加密，同源脚本可能读取它；不适合保存敏感笔记。

GitHub Pages 托管服务仍有常规请求日志。分享筛选链接包含检索词和筛选条件，因此不要分享敏感检索。文献来源链接会跳转到外部网站。

## 本地运行

```bash
cd VLA-Radar
python -m http.server 8080
# 浏览器打开 http://localhost:8080
```

使用原生 HTML/CSS/JavaScript，不依赖 CDN、外部字体、第三方搜索库或构建服务。保持目录内相对路径即可搬到独立仓库或其他静态托管。

## 引用与导出

每条数据保留原始来源。基础 BibTeX 只包含已知的题目、年份和标识符，不把团队机构误写为完整作者。投稿和最终发表信息需从出版平台补齐。

公开 JSON / CSV 导出不包含阅读进度。CSV 对潜在公式起始字符做转义。


## 独立仓库与持续维护

本站现在由 [invoidstar/VLA-Radar](https://github.com/invoidstar/VLA-Radar) 独立维护。

- 维护人员和自动化先阅读 [AGENTS.md](AGENTS.md) 与 [MAINTENANCE.md](MAINTENANCE.md)。
- 每周日早晨的文献维护任务由 ChatGPT 定时任务发起，运行依赖有效的连接与授权；GitHub Actions 负责数据校验与静态发布，不自行生成论文结论。
- 新建仓库需在 Settings → Pages 中将 Source 设为 GitHub Actions，再运行 Validate and deploy VLA Radar。
- 文献唯一数据源仍为 data/papers.json，检索检查点见 maintenance/state.json，修改记录见 CHANGELOG.md。
- 初次维护回补 2026-09-01 起的成果；迁移本身没有执行这轮检索。
- 原个人主页仓库不再用于存放或维护本文献库。
