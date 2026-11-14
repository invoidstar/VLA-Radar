"""Bounded, read-only external source probe for VLA-Radar P1 evidence recovery.

This script NEVER updates the canonical catalog or advances lastSuccessfulSearchAt.
GitHub Actions artifacts are temporary evidence candidates for editor review.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

MAX_BYTES = 5_000_000
TIMEOUT_SECONDS = 12
USER_AGENT = "VLA-Radar-P1-evidence-probe/1.0 (public scholarly-source audit)"
ROBO_URL = "https://robodojo-benchmark.com/data/leaderboard.generated.json"
OPENALEX_URL = "https://api.openalex.org/works"
SEMANTIC_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
QUERIES = ("vision language action", "world action model", "robot manipulation")
ALLOWED_HOSTS = {"robodojo-benchmark.com", "api.openalex.org", "api.semanticscholar.org"}


def read_public_json(url: str, max_bytes: int = MAX_BYTES):
    """Read bounded original-source JSON with no credentials or hidden fallbacks."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("source host not on read-only allowlist")
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
        final_url = response.geturl()
        final = urlparse(final_url)
        if final.scheme != "https" or final.hostname not in ALLOWED_HOSTS:
            raise ValueError("unexpected source redirect")
        raw = response.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise ValueError("JSON exceeds bounded response limit")
        if response.status != 200:
            raise ValueError("source response not HTTP 200")
    decoded = json.loads(raw.decode("utf-8"))
    return decoded, raw


def short_error(error: Exception) -> str:
    if isinstance(error, HTTPError):
        return "http-" + str(error.code)
    if isinstance(error, (URLError, TimeoutError)):
        return type(error).__name__.lower()
    return (type(error).__name__ + ": " + str(error))[:170]


def probe_robodojo(output: Path):
    item = {"source": ROBO_URL, "status": "blocked", "immutable": False,
            "note": "Original bytes are required before canonical source migration."}
    try:
        obj, raw = read_public_json(ROBO_URL)
        if not isinstance(obj, (dict, list)):
            raise ValueError("JSON root is neither object nor array")
        sha = hashlib.sha256(raw).hexdigest()
        path = output / "robodojo-original-generated.json"
        path.write_bytes(raw)
        item.update(status="fetched-unverified", sha256=sha, bytes=len(raw),
                    rootType=type(obj).__name__, topLevelKeys=list(obj)[:20] if isinstance(obj, dict) else [],
                    artifact=path.name, immutable=True,
                    note="Full original response preserved in Actions artifact. Manual schema, model IDs, Score/SR, Sim/Real and version audit STILL required; no catalogue change.")
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError, HTTPError, URLError) as exc:
        item["error"] = short_error(exc)
    return item


def openalex_query(query: str, first: str, last: str):
    params = {
        "search.title_and_abstract": query,
        "filter": "from_publication_date:" + first + ",to_publication_date:" + last,
        "select": "id,display_name,publication_date,doi,ids",
        "per_page": "100",
        "page": "1",
        "corpus": "all",
    }
    url = OPENALEX_URL + "?" + urlencode(params)
    body, _ = read_public_json(url)
    if not isinstance(body, dict) or not isinstance(body.get("results"), list):
        raise ValueError("OpenAlex payload lacks results")
    results = body["results"]
    matches = []
    for paper in results:
        if not isinstance(paper, dict):
            continue
        matches.append({
            "title": str(paper.get("display_name") or "")[:300],
            "publicationDate": paper.get("publication_date"),
            "openalex": paper.get("id"),
            "doi": paper.get("doi"),
            "arxiv": (paper.get("ids") or {}).get("arxiv"),
        })
    return {"provider": "OpenAlex", "query": query, "source": url,
            "status": "first-page-only", "reportedCount": (body.get("meta") or {}).get("count"),
            "returned": len(results), "page": 1, "perPage": 100,
            "hasMore": len(results) >= 100,
            "candidates": matches,
            "note": "This query covers only page 1; source publication dates are not arXiv v1 dates. Does not certify full four-lane coverage."}


def semantic_query(query: str, first: str, last: str):
    params = {"query": query, "fields": "title,publicationDate,externalIds,url", "limit": "100",
              "year": first[:4] + "-" + last[:4]}
    url = SEMANTIC_URL + "?" + urlencode(params)
    body, _ = read_public_json(url)
    if not isinstance(body, dict) or not isinstance(body.get("data"), list):
        raise ValueError("Semantic Scholar payload lacks data")
    papers = []
    for p in body["data"]:
        if not isinstance(p, dict):
            continue
        day = p.get("publicationDate")
        if day and not (first <= day <= last):
            continue
        ids = p.get("externalIds") or {}
        papers.append({"title": str(p.get("title") or "")[:300],
                       "publicationDate": day,
                       "arxiv": ids.get("ArXiv"),
                       "doi": ids.get("DOI"), "source": p.get("url")})
    return {"provider": "Semantic Scholar", "query": query, "source": url,
            "status": "first-page-only", "returned": len(papers),
            "note": "Year-filtered and first page only; search is not a complete day-scoped audit.",
            "candidates": papers}


def execute(output: Path, start: str, end: str):
    start_day = dt.date.fromisoformat(start)
    end_day = dt.date.fromisoformat(end)
    if end_day < start_day or (end_day - start_day).days > 100:
        raise ValueError("invalid bounded date window")
    output.mkdir(parents=True, exist_ok=True)
    findings = []
    for name, handler in (("OpenAlex", openalex_query), ("Semantic Scholar", semantic_query)):
        for query in QUERIES:
            try:
                findings.append(handler(query, start, end))
            except (ValueError, OSError, UnicodeError, json.JSONDecodeError, HTTPError, URLError) as exc:
                findings.append({"provider": name, "query": query, "status": "blocked",
                                 "error": short_error(exc), "candidates": []})
    result = {
        "schemaVersion": 1, "generatedDate": dt.datetime.now(dt.timezone.utc).date().isoformat(),
        "window": {"from": start, "to": end},
        "scope": "READ-ONLY bounded provider connectivity and candidate identity intake, not a four-lane success audit",
        "robodojo": probe_robodojo(output),
        "academicIndex": findings,
        "checkpointAdvanced": False,
        "publicationOrRankingUpdated": False,
        "requiresHumanSourceReview": True,
        "notes": [
            "Never infer RoboDojo Sim/Real model completeness, Score/SR or version from an unvalidated JSON response.",
            "OpenAlex publication_date may differ from original arXiv first-publication date.",
            "Even successful provider queries are sampled page-1 only; four-lane discovery cannot be marked complete.",
            "All candidate identities must be matched to original arXiv/publisher before inclusion.",
        ],
    }
    (output / "probe-report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "robodojo": result["robodojo"]["status"],
        "academicProviderRequests": len(findings),
        "academicResponded": sum(x["status"] == "first-page-only" for x in findings),
        "academicBlocked": sum(x["status"] == "blocked" for x in findings),
        "checkpointAdvanced": False,
        "artifact": str(output / "probe-report.json"),
    }, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="first", default="2026-09-20")
    parser.add_argument("--to", dest="last", default=dt.date.today().isoformat())
    parser.add_argument("--output", type=Path, default=Path("/tmp/vla-radar-p1-probe"))
    args = parser.parse_args()
    execute(args.output, args.first, args.last)


if __name__ == "__main__":
    main()
