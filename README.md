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
python scripts/build_catalog.py
python scripts/validate_all.py
python -m http.server 8080
```

Edit `catalog/papers/pNNN.json`, not generated `data/` files. Use `catalog/benchmarks.json` for protocol definitions and `catalog/results/r-*.json` for result evidence. The build emits a legacy-compatible `data/papers.json`, a searchable `data/catalog.json`, lazy `data/details/` and `data/leaderboards.json`. Public JSON and CSV export remain available; local reading backups must never be committed.

Lifecycle refresh: `python scripts/sync_publications.py --apply-safe` on an update branch. Candidate table discovery: `scripts/discover_results.py`; explicit extraction: `scripts/extract_results.py`. These identify evidence for review, not guaranteed acceptance or automatic scientifically fair rankings. Monthly-age source checks: `python scripts/check_sources.py`; old-note queue: `python scripts/maintenance_queue.py`.

See [MAINTENANCE.md](MAINTENANCE.md) for data semantics, source quality, cadence, API limitations and complete commands; see [AGENTS.md](AGENTS.md) for public-only automated maintenance rules. Weekly updates use source self-review and passing CI, then a normal expected-head PR merge under the maintainer-authorized publication policy; repository protections are never bypassed. GitHub Actions validates PRs and publishes only merged main commits.

## Initial v2 coverage and evidence boundary

The v1 site contains 78 papers, including 46 initially migrated recent entries and 32 added landmarks. V2 preserves all IDs and KEY RESULT summaries, expands six source-reviewed note records and seeds 27 benchmark results across eight distinct tracks. This is not an exhaustive leaderboard or a claim that every legacy paper has been reread. Untouched notes remain explicitly labeled for progressive verification. OpenVLA/CoRL 2024 and OpenVLA-OFT/RSS 2025 lifecycle evidence is recorded independently of the original arXiv dates.

Public sources only. No private research plans, personal reading data, accounts or analytics scripts are used. The static website does not contact arXiv or Crossref in the browser; maintenance tools make bounded public-source requests when run by the reviewer/agent.

## Research workspace

Focused reading (`?view=reader&paper=p001`), cited two-to-four-paper comparison, observed change streams, library evidence coverage, single-protocol charts, and public BibTeX/Markdown/CSV exports are available. Optional code and data load on use. See `maintenance/workspace.md` for semantic boundaries, local preferences and the weekly activity-capture command. Basic BibTeX intentionally does not guess missing authors or final venue metadata.
