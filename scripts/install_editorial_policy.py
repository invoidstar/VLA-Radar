"""Install the maintainer-authorized publication policy once; preserve scientific metadata."""
from pathlib import Path
from catalog_core import load, write, require
ROOT=Path(__file__).resolve().parents[1]

DELIVERY='''## Delivery and safety

The maintainer authorized self-reviewed publication on 2026-09-18, including weekly maintenance. Work in a small `weekly-update-YYYY-MM-DD[-batch]` or explicitly authorized `release/batch-*` branch. Create a PR, inspect the actual changes and primary-source evidence, require passing CI on the exact head, record an honest self-review comment, then merge the expected head normally and verify the main commit's Pages deployment. Do not wait for a further maintainer approval when all these conditions hold.

This is agent self-review, not independent third-party approval. Never fabricate an approving identity, remove a required review, disable checks, bypass repository/environment protection, force-push or modify another repository. If GitHub requires an independent approval, checks fail, a source is insufficient, or permissions are blocked, preserve the candidate and report the precise limitation. A blocked paper must not prevent delivery of other completed, verified work.

Re-read main and the PR head before writing or merging. Reconcile concurrent changes normally; never overwrite newer notes, metadata or result rows with an old snapshot. Direct pushes to main are not the default publication path. Branch preparation workflows only write validated generated files to their own release branch and do not themselves approve or publish content.

Every newly admitted paper must have full-source deep notes and an explicit benchmark disposition under `maintenance/content-standard.md`. Access-limited new discoveries stay in the candidate queue until adequately supported; two explicitly documented historical partial-source guides are not a blanket exemption for future papers. Source versions and limited-reading notices must remain visible.

No real content changes: do not create an empty literature PR. Record actual discovery, publication, note and source-check progress independently. Failed/partial discovery must NOT advance `maintenance/state.json.lastSuccessfulSearchAt`; content `updatedAt` is not a run heartbeat. A queue or metadata refresh is not completed literature review.

Use `python scripts/build_catalog.py` and `python scripts/validate_all.py`. Structural checks do not certify research truth. Distinguish committed branch, PR, CI pass, merge and successful Pages deployment; only retained canonical records count as completed content. Preserve private-data boundaries, original paper IDs/dates, KEY RESULT and browser reading-state keys.
'''
POLICY='''# 发表、深入阅读与自动自检发布规则（2026-09-18）

当前范围仅限公开仓库 invoidstar/VLA-Radar。本轮及后续每周维护采用：来源核验 → 小批次分支 → 构建与测试 → PR → 助手自检记录 → 对精确head正常合并 → 核实Pages实际发布。通过条件后无需再次等待维护者逐次确认。

这不是独立第三方审稿。不得伪造批准身份、撤销必需审核、关闭检查、绕过分支或环境保护、force push或修改其他仓库。若平台要求独立批准、权限不足、CI失败或事实证据不够，保留候选并明确报告；一个受阻条目不阻塞其他合格内容。

每篇新增论文须至少8个实质章节，通常约2000–4000中文正文字符或相当信息量。解释问题、创新差异、输入输出和模块关系、训练监督、部署可用信息、实验协议、主要结果、消融与负结果、限制和读图路线。每节有实际阅读来源与版本。不能靠重复摘要或通用套话凑字符，未读到的参数和实验不得猜测。

全库均检查分节内容与来源范围。历史76篇正文／理论／官方报告笔记维持至少1500字正文的结构底线；另有DMS作者材料和VLAbot官方摘要两项明确的受限导读，不将其认证为完整期刊正文。该两项保持needs_review，不放宽未来新论文标准。详细例子或编辑分析必须与作者实验结论分开。

原图优先提供原文图号/页面链接与阅读说明；确有再分发许可时才内嵌局部原图并署名。表格重排注明原表、指标、预算与局限。不上载完整受版权保护PDF，不从图像像素估计精确榜单数值。

每篇新增、深化或修订的论文都需检查全部相关基准，维护note.benchmarkReview及maintenance/benchmark-review.json：extracted必须指向实际checked结果ID与track ID；deferred应说明缺少原表、精确值或协议；not-applicable应说明为什么不适用。原文对照表、异构预算及不同指标不自动形成公平排名。

保留最早公开与arXiv v1日期；新版本、录用与正式出版另建有来源事件，不用最新修订覆盖首发日期。元数据更新不自动提升笔记验证时间，旧笔记遇新版本保持待复核。检索、元数据、来源健康及笔记进度分别记录，不因部分完成前移完整检索检查点。

对每批执行build_catalog.py与validate_all.py；新论文还受check_editorial.py的全源深读、正文长度和榜单引用检查。CI仅检验结构和逻辑，不替代科研事实核验。只报告实际保留并已合并／部署的成果。
'''
EXPLANATIONS={
'p058':'例如，识别新标志后把已有抓取技能用于对应对象，是语义组合迁移，不等于学到了全新的控制原语。',
'p062':'实际使用时应保留每条轨迹的成功标记和标定来源，避免把采集质量差异当成模型能力差异。',
'p063':'可换头是接口能力；新动作空间的适配仍是需要数据与验证的学习问题。',
'p066':'同一片段存在多种可行执行方式时，动作分布建模与硬件控制约束仍需共同保证实际动作可执行。',
'p072':'例如选对了盘子却抓取滑脱，是执行问题；没有识别出待整理物体，则属于观察或任务理解问题。两者需要不同证据分析。'
}


def install(root=ROOT):
    marker=root/'maintenance/publishing-policy-applied.json'
    if marker.exists():print('Editorial publication policy already installed.');return
    for pid,body in EXPLANATIONS.items():
        p=root/f'catalog/papers/{pid}.json';r=load(p)
        require(r['note'].get('coverage',{}).get('level')=='deep','Apply completion before installing policy')
        if body not in r['note']['sections'][-1]['body']:
            r['note']['sections'][-1]['body']+='\n'+body
            write(p,r)
    p=root/'AGENTS.md';s=p.read_text(encoding='utf-8');require('## Delivery and safety' in s,'Unexpected AGENTS layout')
    s=s[:s.index('## Delivery and safety')]+DELIVERY
    s=s.replace('maintenance/content-standard.md,','maintenance/content-standard.md, maintenance/publishing-policy.md,')
    p.write_text(s,encoding='utf-8')
    p=root/'MAINTENANCE.md';s=p.read_text(encoding='utf-8');require('## PR、CI 与发布' in s,'Unexpected maintenance layout')
    s=s[:s.index('## PR、CI 与发布')]+'''## PR、CI 与发布

详见 `maintenance/publishing-policy.md`。维护者已授权本轮及每周维护在来源自检和CI全部通过后，经PR正常合并并发布，无需重复确认。必须对精确head检查、写明助手自检而非独立评审，不绕过任何分支或环境保护；阻塞时保留PR并报告，不伪造批准。

`python scripts/validate_all.py` 包括全库分节笔记、来源范围、新论文深度和逐篇榜单引用检查，以及生成一致性、不可变日期、协议与证据约束、Python与Node回归。结构验证不能认证科学结论。

合并后必须核实对应main提交的Pages deploy成功。创建PR、CI通过和artifact上传均不等于上线；浏览器交互未测试时另行注明。来源访问失败只影响对应未核验内容，不阻止其他可靠内容的小批次交付。
'''
    p.write_text(s,encoding='utf-8')
    p=root/'README.md';s=p.read_text(encoding='utf-8')
    old='Weekly updates are proposed as PRs; no automated merge or direct scheduled write to main.'
    new='Weekly updates use source self-review and passing CI, then a normal expected-head PR merge under the maintainer-authorized publication policy; repository protections are never bypassed.'
    require(old in s or new in s,'Unexpected README publication wording');s=s.replace(old,new);p.write_text(s,encoding='utf-8')
    p=root/'maintenance/content-standard.md';s=p.read_text(encoding='utf-8')
    s=s.replace('该授权不自动扩展为其他仓库写入或更改每周定时任务的合并权限。','2026-09-18起，该来源自检、CI后合并授权也适用于每周维护；仍不允许其他仓库写入或绕过保护。详细条件见publishing-policy.md。')
    s+='\n## 全库检查与受限材料\n\n`check_editorial.py`检查全库每篇分节笔记与逐篇榜单处理引用。历史正文级笔记最低1500字符、8节；新增论文最低2000字符、8节，且需完整方法／理论／报告来源。该结构底线不替代信息质量。DMS与VLAbot为明确受限的历史例外，保持needs_review并注明实际来源；新发现仅有摘要时先放候选，不以例外身份进入主库。\n'
    p.write_text(s,encoding='utf-8')
    (root/'maintenance/publishing-policy.md').write_text(POLICY,encoding='utf-8')
    write(marker,{'schemaVersion':1,'effectiveAt':'2026-09-18','weeklyMode':'source-self-review-ci-pr-merge-pages','independentReview':False,'bypassProtection':False})
    print('Installed explicit weekly self-review and source-scoped editorial policy.')

if __name__=='__main__':install()
