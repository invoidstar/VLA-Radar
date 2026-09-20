# VLA Research Radar

An open, evidence-linked reading library for vision-language-action, world-action and robot foundation models. 中文阅读笔记、可追溯发表历程、按协议分组的评测结果。

**Website:** https://invoidstar.github.io/VLA-Radar/  
**Repository:** https://github.com/invoidstar/VLA-Radar

## Read, trace, compare

- Full-text search of public catalog summaries, topic/year/ISO-week filters, timeline and local-only reading progress.
- Three paper-detail tabs: structured reading notes, publication lifecycle and source-located benchmark records. Existing KEY RESULT summaries remain visible.
- Separate original public date, first arXiv date, current revision, acceptance/publication dates and actual note-verification version.
- Leaderboards for LIBERO, RoboTwin and RoboCasa are split by protocol. Heterogeneous paper comparison tables do not get fairness ranks. Missing values, unverified extractions and incompatible subsets are never converted to zero or merged into a universal score.

## Maintain

Python 3.10+ and Node 18+; no framework/build dependencies or model API keys are required for the offline site build.

```bash
python scripts/build/build_catalog.py
python scripts/validate/validate_all.py
python scripts/build/stage_site.py --output _site
python -m http.server 8080 -d _site
```

Edit `catalog/papers/pNNN.json`, not generated `data/` files. Use `catalog/benchmarks.json` for protocol definitions and `catalog/results/r-*.json` for result evidence. The build emits a legacy-compatible `data/papers.json`, a searchable `data/catalog.json`, lazy `data/details/` and `data/leaderboards.json`. Public JSON and CSV export remain available; local reading backups must never be committed.

Lifecycle refresh: `python scripts/maintenance/sync_publications.py --apply-safe` on an update branch. Candidate table discovery: `scripts/discovery/discover_results.py`; explicit extraction: `scripts/discovery/extract_results.py`. These identify evidence for review, not guaranteed acceptance or automatic scientifically fair rankings. Monthly-age source checks: `python scripts/maintenance/check_sources.py`; old-note queue: `python scripts/maintenance/maintenance_queue.py`.

See [MAINTENANCE.md](MAINTENANCE.md) for data semantics, source quality, cadence, API limitations and complete commands; see [AGENTS.md](AGENTS.md) for public-only automated maintenance rules. Weekly updates use source self-review and passing CI, then a normal expected-head PR merge under the maintainer-authorized publication policy; repository protections are never bypassed. GitHub Actions validates PRs and publishes only merged main commits.

## Initial v2 coverage and evidence boundary

The v1 site contains 78 papers, including 46 initially migrated recent entries and 32 added landmarks. V2 preserves all IDs and KEY RESULT summaries, expands six source-reviewed note records and seeds 27 benchmark results across eight distinct tracks. This is not an exhaustive leaderboard or a claim that every legacy paper has been reread. Untouched notes remain explicitly labeled for progressive verification. OpenVLA/CoRL 2024 and OpenVLA-OFT/RSS 2025 lifecycle evidence is recorded independently of the original arXiv dates.

Public sources only. No private research plans, personal reading data, accounts or analytics scripts are used. The static website does not contact arXiv or Crossref in the browser; maintenance tools make bounded public-source requests when run by the reviewer/agent.

## Research workspace

Focused reading (`?view=reader&paper=p001`), cited two-to-four-paper comparison, observed change streams, library evidence coverage, single-protocol charts, and public BibTeX/Markdown/CSV exports are available. Optional code and data load on use. See `maintenance/docs/workspace.md` for semantic boundaries, local preferences and the weekly activity-capture command. Basic BibTeX intentionally does not guess missing authors or final venue metadata.


## Embodied AI Weekly / 具身智能周报

详见 `maintenance/policies/news-policy.md`。新闻独立于论文和榜单；维护实际来源、事件/报道日期、公告与材料开放边界、背景/对应论文关系。原有每周任务同时检索过去14天的重要具身智能动态，重点最近7天，3–5条编辑精选，不凑数、不重报旧闻。状态和候选分别保存在news-state/news-candidates，部分检索不能推进完整成功检查点。只编辑catalog/news，构建哈希分片；News代码、样式与数据按需加载。发布前执行browser_news.py与既有完整CI，正常PR自检合并后核实Pages。
