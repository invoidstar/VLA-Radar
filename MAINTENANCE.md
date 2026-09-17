# 文献维护手册

## 固定入口

- 唯一仓库：https://github.com/invoidstar/VLA-Radar
- Pages 地址：https://invoidstar.github.io/VLA-Radar/
- 文献源：`data/papers.json`
- 代理维护约定：`AGENTS.md`
- 检索检查点：`maintenance/state.json`
- 变更记录：`CHANGELOG.md`

只维护公开文献事实、作者报告的结果、证据边界和一般性阅读启示。不写私人项目相关性、未公开策略、实验计划或聊天内容。

## 周更与即时更新

ChatGPT 定时任务每周日早晨约 08:00（Asia/Singapore，UTC+8）执行公开文献检索和核验，首次为 2026-09-20。

**周更采用人工审核模式：**定时任务不得直接修改 `main`，也不得自动合并。若有真实内容变化，应创建 `weekly-update-YYYY-MM-DD` 分支，在该分支完成数据更新和验证，然后创建 Pull Request 到 `main`，由维护者人工审核后决定是否合并。若没有真实变化，不创建空 PR，只发送检索简报。

只有维护者在交互式对话中明确要求“立即更新并直接提交 main”时，才允许在完整验证后进行正常的 fast-forward 提交。禁止 force push。

GitHub Actions 只负责校验和发布静态网站，不自行检索论文，也不调用外部模型做无人监管更新。任务执行仍依赖届时可用的检索工具、GitHub 连接与授权；失败必须明确报告，不得标记为已完成。

首次周更回补 2026-09-01 至实际运行日，衔接已有历史记录。后续从最近成功检索日期向前回退 14 天，以覆盖延迟收录和重要修订。单次搜索无法保证穷尽；记录实际检查范围和不可用来源。

## 纳入与修订

优先使用 arXiv 原文、公司官方报告、会议论文集、出版商页面及作者正式项目页。博客和聚合榜单只能帮助发现，不能替代关键结论的一手证据。

核对标题、作者团队、首发日期、阅读版本、出处及状态。arXiv 修订不算新论文；正式发表通常更新同一条记录。先按 arXiv ID / DOI / 规范化标题去重。缺失机构或未核验指标应写清楚，不补造。

量化结论尽量写成“基准与设置 + 方法/基线 + 数字和单位 + 表/节/版本 + 结论范围”。保留失败或未显著改善的结果，不跨硬件、数据预算、评测协议机械比较。只有摘要时用 `metadata`，已有笔记未重新核验用 `notes`；核对具体片段后才可标 `checked` 并说明核对范围。

保持原有 `p001` 等 ID 不变，新增使用下一个编号。复制已有条目作为字段模板，不添加未获支持的根字段或私人字段。`collectionMonth` 表示纳入的批次月份；`firstPublished` 独立保留原始首发日期。周检索基于可核实的具体日期计算 ISO 周；只有月份的记录不得推算周次。

## 提交前

```bash
python validate.py
python scripts/check_catalog.py
node --check app.js
node --check dates.js
node scripts/test_dates.cjs
node scripts/test_urls.cjs
python -m http.server 8080
```

检查新增条目可检索、分类可筛选、年份/周次筛选正确、来源可追溯，没有把投稿写成录用。上述程序检查结构、重复项、日期逻辑和语法，不能自动验证科研事实。

仅在文献内容变更时修改 `data/papers.json` 的 `updatedAt`；检索完成但没有新条目时只记录检索检查点。每次内容更新在 CHANGELOG.md 记录日期、新增/修订 ID、数量和公开来源范围，不复制完整论文内容。

`lastSuccessfulSearchAt` 只在计划检索和核验完整完成时更新；`lastAttemptAt` 可记录失败。`lastStatus` 可为 `not_run`、`success`、`partial` 或 `failed`。部分结果可保留，但不得据此跳过后续回补。

## 周更 PR 流程

1. 从最新 `main` 创建 `weekly-update-YYYY-MM-DD`。
2. 检索、去重、核验并更新公开数据。
3. 运行全部校验；失败则不创建可合并结论。
4. 将候选变化提交到周更分支。
5. 创建 PR 到 `main`，正文列出新增/修订/待核验数量、主要论文、检索范围、验证结果和已知限制。
6. 等待维护者人工审核与合并；自动任务不得 merge。
7. 合并后由 `main` 的 Pages workflow 验证并部署。

## 发布

`.github/workflows/site.yml` 在 `main` push 或 PR 时校验数据与前端。PR 阶段只做验证；实际 Pages 发布仅发生在变化进入 `main` 后。发布制品包含公开网站文件和 `data/papers.json`，维护说明本身不进入网页制品。

维护者必须区分：候选 PR、已合并 commit、验证成功和 Pages 实际发布。不要把定时任务存在、PR 创建成功或 artifact 上传成功当作网站已更新。

如果 Pages 尚未启用，需要在 Settings → Pages → Build and deployment → Source 选择 **GitHub Actions**：https://github.com/invoidstar/VLA-Radar/settings/pages 。

## 阅读进度

阅读记录使用浏览器 localStorage，不入库、不上云。清理存储、换浏览器或换设备需自行备份恢复。分享链接会包含搜索条件，请勿分享敏感检索。

## 可追溯迁移

`scripts/import_legacy.py` 仅用于一次性导入固定公开快照，逐文件校验 Git blob SHA；不覆盖已存在的网站文件。原始来源与导入后哈希写入 `maintenance/migration.json`。迁移不是重新核验全部论文，更不会升级旧记录的证据等级。
