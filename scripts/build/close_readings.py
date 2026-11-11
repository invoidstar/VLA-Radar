"""Build and validate public, source-linked, copyright-conscious close readings.

Only the canonical catalog/close-readings/*.json is edited. Site JSON is generated.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
CATEGORIES = {"thesis", "concept", "evidence", "concession", "method"}
KINDS = {"paragraph", "figure", "table"}


def require(ok, msg):
    if not ok:
        raise ValueError("Close reading: " + msg)


def valid_http(url):
    if not isinstance(url, str) or len(url) > 500:
        return False
    parsed = urlparse(url)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password


def check_text(value, name, min_length=1, max_length=4000):
    require(isinstance(value, str) and min_length <= len(value.strip()) <= max_length, name)
    require(not any(tag in value.lower() for tag in ("<script", "<iframe", "data:image/", "base64,")), name + " has untrusted markup or embedded media")


def validate_reading(data, known_papers, known_tracks):
    require(data.get("schemaVersion") == 1, "schemaVersion")
    require(re.fullmatch(r"p\d{3,}", data.get("paperId", "")), "paperId format")
    pid = data["paperId"]
    require(pid in known_papers, pid + " has no catalog paper")
    require(data.get("readingKind") == "argument-annotation", "reading kind")
    for k in ("title", "subtitle", "sourceVersion", "curatedAt"):
        check_text(data.get(k), pid + "." + k, 4, 500)
    require(re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["curatedAt"]), "curatedAt")
    require(valid_http(data.get("sourceUrl")) and valid_http(data.get("pdfUrl")), "source URLs")
    rights = data.get("copyright", {})
    require(rights.get("mode") == "commentary-and-reference", "public rights mode")
    for k in ("originalFullTextRepublished", "fullTranslationRepublished", "figuresMirrored"):
        require(rights.get(k) is False, "unlicensed redistribution is blocked: " + k)
    check_text(rights.get("notes"), "copyright.notes", 20)
    argument = data.get("argument", {})
    check_text(argument.get("claim"), "argument.claim", 20)
    check_text(argument.get("strength"), "argument.strength", 20)
    check_text(argument.get("weakness"), "argument.weakness", 20)
    require(isinstance(argument.get("chain"), list) and len(argument["chain"]) >= 3, "argument chain")
    for part in argument["chain"]:
        check_text(part.get("step"), "argument step")
        check_text(part.get("detail"), "argument detail", 5)
    sections = data.get("sections")
    require(isinstance(sections, list) and sections, "sections")
    ids = set()
    section_ids = set()
    counts = {"paragraphs": 0, "figures": 0, "tables": 0}
    for sec in sections:
        sid = sec.get("id")
        require(isinstance(sid, str) and re.fullmatch(r"[a-z][a-z0-9-]*", sid) and sid not in section_ids, "section id")
        section_ids.add(sid)
        check_text(sec.get("title"), "section title")
        check_text(sec.get("englishTitle"), "section English title")
        require(isinstance(sec.get("units"), list) and sec["units"], "empty section")
        for unit in sec["units"]:
            uid = unit.get("id")
            require(isinstance(uid, str) and re.fullmatch(r"(?:P\d{3}|FIG\d+|TAB\d+)", uid) and uid not in ids, "duplicate/invalid unit")
            ids.add(uid)
            kind = unit.get("kind")
            require(kind in KINDS, "unit kind")
            if kind == "paragraph":
                require(uid.startswith("P"), uid + " mismatch")
                counts["paragraphs"] += 1
            elif kind == "figure":
                require(uid.startswith("FIG"), uid + " mismatch")
                counts["figures"] += 1
            else:
                require(uid.startswith("TAB"), uid + " mismatch")
                counts["tables"] += 1
            require(unit.get("dimension") in CATEGORIES, uid + " classification")
            for k in ("title", "sourcePageLabel", "argumentRole", "function", "criticalNote"):
                check_text(unit.get(k), uid + "." + k, 2, 1600)
            page = unit.get("pdfPage")
            require(type(page) is int and 1 <= page <= 150, uid + " page")
            require(unit.get("sourceUrl") == data["pdfUrl"] + "#page=" + str(page), uid + " PDF page location")
            terms = unit.get("englishKeywords", [])
            require(isinstance(terms, list) and len(terms) <= 4, uid + " keywords")
            for term in terms:
                require(term.get("dimension") in CATEGORIES, uid + " keyword class")
                check_text(term.get("text"), uid + " keyword", 2, 48)
                require(len(term["text"].split()) <= 6, uid + " keyword quote too long")
            refs = unit.get("evidenceTracks", [])
            require(isinstance(refs, list) and all(ref in known_tracks for ref in refs), uid + " unknown Benchmark track")
    require(counts == data.get("totals"), "stored totals do not match source records: " + repr(counts))
    require(counts["paragraphs"] > 0, "no original paragraph locations")
    require(data.get("origin", {}).get("kind") == "user-provided-bilingual-annotation-HTML", "source provenance")
    return counts


def outputs(root, records, tracks):
    root = Path(root)
    papers = {rec["paper"]["id"] for rec in records}
    ids = {t["id"] for t in tracks}
    generated = {}
    listed = []
    source_dir = root / "catalog" / "close-readings"
    for path in sorted(source_dir.glob("p*.json")) if source_dir.exists() else []:
        doc = json.loads(path.read_text(encoding="utf-8"))
        require(path.stem == doc.get("paperId"), "filename identity")
        count = validate_reading(doc, papers, ids)
        pid = doc["paperId"]
        listed.append({
            "paperId": pid,
            "title": doc["title"],
            "subtitle": doc["subtitle"],
            "sourceVersion": doc["sourceVersion"],
            "curatedAt": doc["curatedAt"],
            "sections": len(doc["sections"]),
            "units": sum(count.values()),
            "href": "close-reading/" + pid + "/",
            "detailUrl": "data/close-readings/" + pid + ".json",
        })
        generated["data/close-readings/" + pid + ".json"] = json.dumps(
            doc, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ) + "\n"
    index = {"schemaVersion": 1, "papers": listed}
    generated["data/close-readings/index.json"] = json.dumps(
        index, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ) + "\n"
    return generated, listed


if __name__ == "__main__":
    import argparse
    from catalog_core import read_catalog
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args()
    _, records, tracks, _ = read_catalog(args.root)
    generated, index = outputs(args.root, records, tracks)
    print("PASS close-reading", len(index), "papers", sum(x["units"] for x in index), "source-anchored units", len(generated), "generated JSON files")
