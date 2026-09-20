# V2 GitHub validation · 2026-09-17

## Actual completed run

Run: https://github.com/invoidstar/VLA-Radar/actions/runs/35222762092

The one-time feature-branch preparation job completed successfully. It verified the source payload and baseline checksums, materialized public source files, preserved the existing catalog, built deterministic outputs, ran regression tests, attempted bounded public metadata checks, rebuilt and revalidated, and pushed a normal commit to `feature/lifecycle-notes-leaderboards-2026-09-17`. It did not update main or deploy Pages. The temporary payload and one-time workflow have been removed from the branch tip after use.

## Verified implementation scope

- 78 original paper IDs, firstPublished values and KEY RESULT findings preserved.
- Canonical per-paper source files, generated searchable catalog, lazy details and result data.
- Six detailed source-linked note records; the other 72 remain legacy notes, not newly reread papers. OpenVLA-OFT's detailed note identifies its older reading version and needs review for the newer revision.
- Two manually source-checked publication examples: OpenVLA in CoRL 2024 proceedings (volume publication in 2025), and OpenVLA-OFT in RSS 2025, with original arXiv dates kept separately.
- 27 source-located result records across eight protocol tracks for LIBERO, RoboTwin and RoboCasa. The heterogeneous RoboCasa comparison table is explicitly unranked. This is an initial collection, not an official or exhaustive leaderboard.

## Regression results

Both build/validation passes in this GitHub job succeeded:

- Strict schema, identity, immutable first-public date, duplicate and generated-output checks.
- 26 Python unit tests.
- 37,289 ISO-calendar assertions covering 18,628 dates in 1990–2040.
- Legacy URL/week/month and public leaderboard URL tests.
- Bounded pagination, ties, missing versus zero scores, protocol isolation, candidate exclusion and supersession tests.
- JavaScript syntax checks.

The 15 local Chromium offline DOM checks are separately documented in `v2-validation.md`. They are not a live HTTP browser test or proof of Pages deployment.

## Live metadata attempt: partial, no batch refresh completed

The arXiv API requests for 75 selected arXiv-linked records returned HTTP 406 (Not Acceptable). `maintenance/state/publication-check.json` records `status: partial`, no successfully returned metadata records and no automatic publication changes. This run does not certify the latest publication status of the full catalog. The three entries without an arXiv identifier still require their official-source review path. No original dates, existing publication decisions or successful literature-discovery checkpoint were overwritten because of the provider failure. A zero script exit reports completion of the attempt, not success of every provider.

## Live source-health sample

Twenty selected source URLs returned HTTP 200 and were recorded as reachable. Another 149 unique URLs remain due. This checks reachability only; it does not validate paper claims or publication status. See `maintenance/state/source-health.json`. Future checks rotate by age instead of repeatedly checking the same first twenty URLs.

## Release boundary

Review and merge the feature PR manually. The ordinary site workflow validates PRs without deployment; only a merged main commit can publish the V2 site. The weekly task must continue using the current default-branch schema until this PR is merged.
