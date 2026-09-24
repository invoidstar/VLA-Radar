# Discovery audits (schema v2)

From 2026-09-25 onward, full literature discovery windows are recorded here.

A successful audit must cover the whole planned date window in every lane required by
`maintenance/policies/discovery-policy.json`:

1. `primary-preprints` — direct primary preprint/publisher search;
2. `academic-index` — at least one independent broad academic index;
3. `curated-robotics` — at least one robotics/VLA-specific curated index;
4. `reverse-discovery` — official lab/project/benchmark/leaderboard pages or related/citation expansion.

Every source entry records its exact provider, query/scope, date coverage, result count
and whether the source succeeded, was partial, or was blocked. A blocked/partial required
lane makes the whole audit partial. A complete audit must also satisfy the configured
minimum number of distinct successful providers, so one aggregator cannot masquerade as
four independent lanes. Verified papers from a partial run may still be published, but
the global full-search checkpoint does not move.

Every candidate is deduplicated by canonical arXiv ID, DOI, then normalized title and has
one explicit disposition: `selected`, `deferred`, `excluded`, or `duplicate`.
Deferred candidates remain part of the durable queue across later audits.

Typical flow:

```bash
python scripts/discovery/discovery_coverage.py plan --to 2026-10-04
# perform the searches and write the schema-v2 JSON audit
python scripts/discovery/discovery_coverage.py validate maintenance/audits/discovery/discovery-2026-09-20-2026-10-04.json
python scripts/discovery/discovery_coverage.py apply maintenance/audits/discovery/discovery-2026-09-20-2026-10-04.json
python scripts/discovery/discovery_coverage.py status
```

Do not edit `lastSuccessfulSearchAt` by hand to represent a partial search. CI verifies
that any checkpoint after the 2026-09-24 legacy baseline is backed by a complete v2 audit.
