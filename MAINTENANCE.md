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

维护任务由已设置的 ChatGPT 定时任务发起：每周日早晨约 08:00，Asia/Singapore（UTC+8）；首次为 2026-09-20。它负责检索、筛选、核验、写入和简报，而不是仅提醒维护者。任务运行仍依赖届时可用的检索工具、GitHub 连接与授权；失败需要明确报告，不得标记为已完成。

这里没有偷偷配置一个可自行调用付费模型的 GitHub cron。GitHub Actions 的职责是校验数据和发布静态网站；论文搜索由定时维护任务或明确的即时维护请求执行。新条目提交并通过发布流程后才会出现在网站上，并非持续实时抓取全网。

首次维护回补 2026-09-01 至实际运行日，衔接已有 7—8 月首批记录。后续从最近成功检索日期向前回退 14 天，以覆盖延迟收录和重要修订。单次搜索无法保证穷尽；记录实际检查范围和不可用来源。

## 纳入与修订

优先使用 arXiv 原文、公司官方报告、会议论文集、出版商页面及作者正式项目页。博客和聚合榜单只能帮助发现，不能替代关键结论的一手证据。

核对标题、作者团队、首发日期、阅读版本、出处及状态。arXiv 修订不算新论文；正式发表通常更新同一条记录。先按 arXiv ID / DOI / 规范化标题去重。缺失机构或未核验指标应写清楚，不补造。

量化结论尽量写成“基准与设置 + 方法/基线 + 数字和单位 + 表/节/版本 + 结论范围”。保留失败或未显著改善的结果，不跨硬件、数据预算、评测协议机械比较。只有摘要时用 `metadata`，已有笔记未重新核验用 `notes`；核对具体片段后才可标 `checked` 并说明核对范围。

保持原有 `p001` 等 ID 不变，新增使用下一个编号。复制已有条目作为字段模板，不添加未获支持的根字段或私人字段。`collectionMonth` 表示纳入的批次月份；`firstPublished` 独立保留原始首发日期。

## 提交前

```bash
python validate.py
python scripts/check_catalog.py
node --check app.js
python -m http.server 8080
```

检查新增条目可检索、分类可筛选、来源可追溯，没有把投稿写成录用。上述程序检查结构、重复项和语法，不能自动验证科研事实。

仅在文献内容变更时修改 `data/papers.json` 的 `updatedAt`；检索完成但没有新条目时只记录检索检查点。每次内容更新在 CHANGELOG.md 记录日期、新增/修订 ID、数量和公开来源范围，不复制完整论文内容。

`lastSuccessfulSearchAt` 只在计划检索和核验完整完成时更新；`lastAttemptAt` 可记录失败。`lastStatus` 可为 `not_run`、`success`、`partial` 或 `failed`。部分结果可保留，但不得据此跳过后续回补。

## 发布与首次启用

本仓库已提供 `.github/workflows/site.yml`。每次 main 分支 push 或手动运行都会先校验；Pages 启用后再发布白名单静态文件。文档和维护日志不进入部署制品，但它们作为公开仓库文件仍然公开。

新建仓库需要所有者在 Settings → Pages → Build and deployment → Source 选择 **GitHub Actions**。入口：https://github.com/invoidstar/VLA-Radar/settings/pages 。启用后在 Actions 中运行 **Validate and deploy VLA Radar**，或提交一次正常修改。不要添加个人令牌到公开文件。

Pages 尚未启用时，工作流保留成功的校验并明确跳过发布；这不等于网站已经上线。分支保护或环境审批按 GitHub 设置处理，不绕过。

维护者必须报告实际结果：新增/修订数量、核验范围、提交链接、校验结果、Pages 发布状态与阻塞项。不要把定时任务存在、git commit 成功或 artifact 上传成功当作已完成网站发布。

## 阅读进度

阅读记录仍使用原 localStorage 键，不入库、不上云。新旧 Pages 路径位于同一站点来源，保留存储键有利于同一浏览器延续记录；清理存储、换浏览器或换设备则需自行备份恢复。分享链接会包含搜索条件，请勿分享敏感检索。

## 可追溯迁移

`scripts/import_legacy.py` 仅用于一次性导入固定公开快照，逐文件校验 Git blob SHA；不覆盖已存在的网站文件。原始来源与导入后哈希写入 `maintenance/migration.json`。迁移不是重新核验全部论文，更不会升级旧记录的证据等级。
