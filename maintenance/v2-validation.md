# V2 validation record · 2026-09-17

Scope: 78 preserved paper IDs and KEY RESULT fields; per-paper catalog build; publication metadata logic; structured notes; 8 protocol tracks / 27 evidence-located result rows; public static UI.

## Completed locally

- Source schema, generated-file equality, canonical identity / duplicate checks passed.
- 26 Python unit tests passed: first-public immutability, lifecycle date precision, arXiv identity and version changes, acceptance as candidate, DOI/title checks, future dates, partial-network-failure state, source boundary checks, candidate extraction, discovery and queue construction.
- Existing ISO calendar logic cross-checked with Python for 18,628 dates (1990–2040), 37,289 assertions.
- URL tests include existing ISO week / month links and private-reading exclusions, plus public leaderboard track selectors.
- Node research tests cover bounded pagination with 10,000 pages, tied ranks, missing versus zero scores, protocol isolation, candidate exclusion and superseded records.
- Chromium offline DOM fixtures: 15 checks passed, no page JavaScript errors. Desktop 1440px / mobile 390px. Details, source links, tabs, keyboard result loading, dataset controls, unranked heterogeneous tables, original search and responsive layout were exercised. No document-level horizontal overflow on mobile; wide tables scroll within their container.

## Limits

The local environment blocks browser HTTP navigation and external DNS. UI checks used injected local public fixtures, not live-site navigation; real localStorage persistence across page reload was not revalidated here (the existing storage key and read/write interface are unchanged). API adapters were unit-tested with fixtures; do not infer a successful live arXiv/Crossref/source-health run from this report. GitHub CI and live metadata refresh must be reported separately from their actual workflow results. A new PR does not deploy Pages until manually merged.

The six expanded notes cover identified source sections, not all 78 full papers. Existing literature-discovery checkpoint remains `not_run`; this engineering/content upgrade is not a complete weekly search sweep.
