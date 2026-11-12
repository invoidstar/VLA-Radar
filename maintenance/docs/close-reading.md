# VLA-Radar V3.1 — Paper Deep Reading 论文精读规范

## 目标与边界

为已有论文库提供一个独立的、可版本化的长篇**论证精读层**。这不替代
`catalog/papers/pNNN.json` 中的方法/结果笔记、论文发现、Benchmark 或 Result Report，
也不承诺全部论文自动完成逐段译注。

首篇 SLA 绑定既有 p148，不增建论文 ID，也不修改作者原稿、发表时间或结果数值。
来源为使用者提供的 `SLA_Bilingual_Annotated_Full.html`。抽取范围严格限制为
**101 个原文段落、16 张表、6 幅图的定位信息、中文原创论证批注和少量英文关键词**。
上传的完整英文段落、全文中文翻译和 Base64 PDF 图表均不复制进公开源库、生成 JSON 或 Pages。
**网站精读数据不等同于上传的完整双语 HTML。** 在没有可核对的转载授权时，这正是公开版有意的限制。

## 数据模型

唯一公开 source of truth：

- `catalog/close-readings/p148.json`：`paperId`、`sourceVersion`、
  `pdfUrl`、`curatedAt`、`copyright`、`argument` 和 `sections[]`。
- `sections[].units[]`：稳定原稿 ID（P001 / TAB3 / FIG1）、类别、
  PDF 页码和官方链接、标题、英文技术关键词（非整段原文）、中文论证逻辑、
  段落功能、批判性评论和可选 `evidenceTracks[]`。
- 数据中的 `copyright` 记录三项不得误导的状态：
  `originalFullTextRepublished=false`、
  `fullTranslationRepublished=false`、
  `figuresMirrored=false`。V3.1 的校验会拒绝这些值变成 true；
  后续授权模式必须先设计正式许可来源和安全验证机制。

源记录编辑流程：在原稿版本、页码及对应评论实际核对后，修改上述 JSON；
执行 `python scripts/build/build_catalog.py` 和
`python scripts/validate/validate_all.py`。
生成的 `data/close-readings/p148.json` / `index.json` 以及
`data/library.json` 的 `closeReadings` 目录索引由构建器维护，不手工改动。
`scripts/build/close_readings.py` 检查 paper ID、图表/段落 ID、总数、页码一致性、
Benchmark track 身份、文本长度以及没有 HTML/iframe/Base64 嵌入内容。

## 页面与静态链接

- 主站入口：`?view=close-reading`，`DISCOVER → 论文精读`。
- 直接阅读：`close-reading/p148/`；生成器
  `scripts/build/stage_site.py` 根据已校验的论文索引输出每个独立目录的
  `index.html`，引用共享 `reader.js` / `reader.css`。
- 既有论文详情仍保留“专注阅读”和结果笔记；若有精读版，追加“阅读原稿逐段论证精读”。
- 页面无数据库/账号/API；本轮不修改 `vla-radar.reading.v1`，
  无用户输入写入公开仓库。
- 初始首页仅加载 `data/library.json` 中少量精读元数据；
  大型原稿定位 JSON 只在用户进入单篇精读页后请求。
- 大图不以内嵌 Base64 进入 HTML；原稿图表通过定位到 arXiv
  官方 PDF 页阅读。只有复核过相应再分发许可证的图片可新增独立懒加载资源。
- 主题为深海军蓝+米白，英文 Lora／Georgia，界面 IBM Plex Sans／回退字体；
  免费字体外链失败时应有可读回退，移动端为单栏，打印保留关键批注。

## 工作流程与验收

1. 检查论文稳定 ID、原稿明确版本、首次公开/正式发表证据。
2. 逐节逐段核查原稿页码、术语和论证批注；方法叙述与实验归因分开。
3. 处理许可：没有明确允许转载的许可时，不导出全文与图片，
   不拿“arXiv 可公开阅读”等同于“可以第三方再分发”。
4. 已有 Benchmark 结果仅用 `evidenceTracks` 链接；
   不通过精读 HTML 再造一个独立成绩来源。
5. 源数据通过  `scripts/build/close_readings.py` /
   `tests/test_close_readings.py`，再通过全站 `validate_all.py`。
6. Playwright Chromium / Firefox / WebKit 实际 HTTP 回归：
   文献库 → 精读列表 → p148 页面、101/16/6 数量、源 URL、
   五色切换、搜索、隐藏批注、中文模式、手机视口无横向溢出、
   首页不提前加载精读大文件。单独记录模拟视口非真机测试。
7. 建发布 PR，**exact-head quality** 全绿后记录维护者自检并正常合并，
   核查相同 main SHA 的 Pages stage/deploy/production-smoke。
   不修改分支保护、不绕过已有门禁。

## 为后续新精读优化提示词的指导

分析学术论文时，输出应围绕**研究问题 → 核心主张 → 机制/方法 → 对照证据 →
消融和反例 → 结论边界**，每段至少包含原稿定位、段落功能、论证角色和批判评议。
机器人领域还应区分训练期/部署期、模型骨干/动作头/Agent 编排，
并把评测任务范围、训练预算、metric（Score/SR/AUROC/Latency）和
作者报告/官方提交来源保留在证据层。

若许可不允许再分发全文，**不要生成面向公开发布的英文全文逐段镜像**
或原图 Base64；改为原创中文论证导读、少量非表达性术语以及原文 PDF 定位。
即使私人版本有逐段完整翻译，也不能把它当作公开可发布版直接上传。

当前第一篇为 SLA p148，新增其他论文前先进行原稿及许可证核验，
并沿用同一 JSON Schema 和相同阅读器，不要为每篇另写一套 CSS/JS。

## 2026-11-12 原文同屏阅读

- 精读页新增可折叠的官方原稿 PDF iframe，按 `sections[].units[].pdfPage` 逐单元定位页码。原稿在论文来源域名加载，不在 GitHub Pages、`data/close-readings/` 或 `catalog/close-readings/` 复制 PDF 全文、图片或全文翻译。
- 每个单元保留官方来源链接和新标签后备阅读入口。浏览器可能拒绝跨站 PDF iframe；此时直接在新标签打开，不可将测试桩的成功误称线上嵌入已验证。
- Chromium、Firefox、WebKit 检查初始原稿 URL、页码按钮、折叠展开、原有批注功能与移动端无横向溢出。生产烟雾测试新增精读独立深链接、版本戳、源元数据检查。
- 目前来源段落与 PDF 页码的 101 处对应尚待独立人工逐页复核；不要因为 UI 可跳页而把结构校验升级为原稿逐页完成核验。
