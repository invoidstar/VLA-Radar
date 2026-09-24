# 发表、深入阅读与自动自检发布规则（2026-09-18）

当前范围仅限公开仓库 invoidstar/VLA-Radar。本轮及后续每周维护采用：来源核验 → 小批次分支 → PR exact-head 完整离线/浏览器门禁 → 助手自检记录 → 对精确head正常合并 → main 轻量 generated-files check → Pages部署 → production smoke。通过条件后无需再次等待维护者逐次确认；main 不再重复安装浏览器并重跑已经在 exact PR head 通过的完整测试。

交付前先读 `maintenance/docs/github-delivery.md`：完整发现本次GitHub操作清单，实际调用已授权的分支写入/PR/合并接口。区分工具发现、远端授权与保护、本地DNS/网络、CI和部署阶段。筛选未列出操作或本地git网络失败不能被表述成仓库写权限撤销；现成远端分支优先核对，不重传旧包覆盖后续修订。

这不是独立第三方审稿。不得伪造批准身份、撤销必需审核、关闭检查、绕过分支或环境保护、force push或修改其他仓库。若平台要求独立批准、权限不足、CI失败或事实证据不够，保留候选并明确报告；一个受阻条目不阻塞其他合格内容。

每篇新增论文须至少8个实质章节，通常约2000–4000中文正文字符或相当信息量。解释问题、创新差异、输入输出和模块关系、训练监督、部署可用信息、实验协议、主要结果、消融与负结果、限制和读图路线。每节有实际阅读来源与版本。不能靠重复摘要或通用套话凑字符，未读到的参数和实验不得猜测。

全库均检查分节内容与来源范围。历史76篇正文／理论／官方报告笔记维持至少1500字正文的结构底线；另有DMS作者材料和VLAbot官方摘要两项明确的受限导读，不将其认证为完整期刊正文。该两项保持needs_review，不放宽未来新论文标准。详细例子或编辑分析必须与作者实验结论分开。

原图优先提供原文图号/页面链接与阅读说明；确有再分发许可时才内嵌局部原图并署名。表格重排注明原表、指标、预算与局限。不上载完整受版权保护PDF，不从图像像素估计精确榜单数值。

每篇新增、深化或修订的论文都需检查全部相关基准，维护note.benchmarkReview及maintenance/state/benchmark-review.json：extracted必须指向实际checked结果ID与track ID；deferred应说明缺少原表、精确值或协议；not-applicable应说明为什么不适用。原文对照表、异构预算及不同指标不自动形成公平排名。

保留最早公开与arXiv v1日期；新版本、录用与正式出版另建有来源事件，不用最新修订覆盖首发日期。元数据更新不自动提升笔记验证时间，旧笔记遇新版本保持待复核。检索、元数据、来源健康及笔记进度分别记录，不因部分完成前移完整检索检查点。

对每批执行build_catalog.py与validate_all.py；新论文还受check_editorial.py的全源深读、正文长度和榜单引用检查。CI仅检验结构和逻辑，不替代科研事实核验。只报告实际保留并已合并／部署的成果。

## 精简后的CI / 发布职责（2026-09-25）

- Pull Request 是唯一完整质量门禁：执行 `validate_all.py`、Firefox/WebKit 安装以及全部 HTTP/browser regressions。只有精确 PR head 全绿才允许 expected-head merge。
- main push 不重复上述完整测试。它只执行 `build_catalog.py --check`，确认合并后的 canonical/generated 文件一致，然后 stage、上传 Pages artifact 并部署。
- production smoke 保留，用真实 Pages URL 检查当前资产与 deep link，作为“已上线”的最终证据。
- 直接 push main 仍不是常规发布路径；精简 main CI 的前提是正常变更已经经过 PR exact-head 完整门禁。
- merged-branch housekeeping 不再由每次 Pages workflow 自动触发，只在每周 schedule 或维护者手动 dispatch 时执行；它不是网站发布成功的组成部分。
