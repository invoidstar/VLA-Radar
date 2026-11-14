"""Validated, immutable official leaderboard snapshots, entirely independent of papers.

These source-traceable XPolicyLab/RoboDojo results do not create a new paper,
a canonical Result Report, or a claim of independently reproduced performance.
Updates require refetching official source JSON and recording its Git blob SHA.
"""
from __future__ import annotations
import json
import math
import re
import hashlib
from pathlib import Path

OFFICIAL_BOARD_FILES = ("robotwin2", "robodojo-sim", "robodojo-real")
EXPECTED_DATASETS = {
    "robotwin2": "RoboTwin",
    "robodojo-sim": "RoboDojo",
    "robodojo-real": "RoboDojo real",
}
EXPECTED_COLUMNS = {
    "robotwin2": ["Average", "Clean", "Random"],
    "robodojo-sim": ["Average", "Average no Open", "Generalization", "Precision", "Long Horizon", "Memory", "Open"],
    "robodojo-real": ["Average", "ARX X5", "Piper", "Piper X"],
}

def _score(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100:
        raise ValueError("Invalid official score: " + label)

def load_snapshots(root, paper_ids):
    root = Path(root)
    snapshots = []
    for board_id in OFFICIAL_BOARD_FILES:
        path = root / "catalog" / "official-boards" / (board_id + ".json")
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("schemaVersion") != 1 or record.get("id") != board_id or record.get("benchmark") != EXPECTED_DATASETS[board_id]:
            raise ValueError("Official board identity mismatch: " + board_id)
        if record.get("columns") != EXPECTED_COLUMNS[board_id]:
            raise ValueError("Official board column schema mismatch: " + board_id)
        for key in ("sourceBlobSha", "sourceRepoRevision"):
            if not re.fullmatch(r"[0-9a-f]{40}", str(record.get(key, ""))):
                raise ValueError("Unpinned official source: " + board_id + ":" + key)
        for key in ("sourceUrl", "sourceRepoUrl", "boardUrl"):
            if not str(record.get(key, "")).startswith("https://"):
                raise ValueError("Invalid official source URL: " + board_id)
        raw_path = record.get("sourceRawPath")
        if raw_path:
            # Official direct API source is committed byte-for-byte before
            # converting to canonical rows. Both SHA families are verified.
            if raw_path != "maintenance/source-snapshots/robodojo-generated-20261103.json":
                raise ValueError("Unexpected official source archive path")
            raw = (root / raw_path).read_bytes()
            sha256 = hashlib.sha256(raw).hexdigest()
            blob_sha = hashlib.sha1(f"blob {len(raw)}".encode("utf-8") + bytes([0]) + raw).hexdigest()
            if sha256 != record.get("sourceContentSha256") or blob_sha != record["sourceBlobSha"]:
                raise ValueError("Official RoboDojo source checksum mismatch")
        entries = record.get("entries")
        if not isinstance(entries, list) or not entries:
            raise ValueError("Empty official snapshot: " + board_id)
        distinct = set()
        prior = float("inf")
        for rank, entry in enumerate(entries, start=1):
            model = entry.get("model", "")
            if not isinstance(model, str) or not model.strip() or model in distinct or entry.get("rank") != rank:
                raise ValueError("Duplicate model or invalid rank: " + board_id)
            distinct.add(model)
            values = entry.get("values")
            if not isinstance(values, dict) or not values.get("Average") is not None or set(values)-set(record["columns"]):
                raise ValueError("Bad official score dimensions: " + board_id + ": " + model)
            if record["metricSchema"] == "clean-random":
                for k in ("Clean", "Random", "Average"):
                    _score(values.get(k), board_id + ":" + model + ":" + k)
                mean = (values["Clean"] + values["Random"]) / 2
                if abs(mean - values["Average"]) > 0.005001:
                    raise ValueError("RoboTwin average does not match source definition")
                if entry.get("track") not in ("cotrain", "sft"):
                    raise ValueError("Invalid RoboTwin track mode")
                current = values["Average"]
            elif record["metricSchema"] == "score-success":
                for dim, pair in values.items():
                    if not isinstance(pair, dict) or set(pair) != {"score", "sr"}:
                        raise ValueError("Score/SR dimensions cannot be collapsed: " + dim)
                    _score(pair["score"], board_id + ":" + model + ":" + dim + ":score")
                    _score(pair["sr"], board_id + ":" + model + ":" + dim + ":sr")
                current = values["Average"]["score"]
            else:
                raise ValueError("Unknown official metric scheme")
            if current > prior + 0.000001:
                raise ValueError("Official scores must be sorted descending by overall Average")
            prior = current
            paper = entry.get("paperLink")
            if paper and (paper.get("paperId") not in paper_ids or not paper.get("relation")):
                raise ValueError("Unverified paper link in official model submission: " + model)
        snapshots.append(record)
    return snapshots

def official_board_outputs(root, out, paper_ids, hash_writer):
    """Emit lazy fragments plus a tiny index with top-three preview, not all rows."""
    index = {}
    # A newer live official board may be visible before the source committee
    # publishes a complete, stable SHA-pin for all Score / SR columns.
    # Surface that lag as source-attributed metadata; never merge guessed rows.
    audit_path = Path(root) / "maintenance/audits/benchmark/robodojo-live-20261112-source-gap.json"
    live_audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else None
    if live_audit and (live_audit.get("schemaVersion") != 1 or
                       live_audit.get("status") != "official-live-unpinned-mirror-stale"):
        raise ValueError("Unknown RoboDojo live-source audit")
    for board in load_snapshots(root, paper_ids):
        url = hash_writer("data/official-boards/" + board["id"], board, out)
        first_three = [{"model": x["model"], "rank": x["rank"], "average": x["values"]["Average"]}
                       for x in board["entries"][:3]]
        live_info = None
        if (live_audit and board["id"] in ("robodojo-sim", "robodojo-real")
                and board["officialUpdatedAt"] < live_audit["dataUpdatedAt"]):
            current = live_audit["boards"][board["id"]]
            if (current["pinnedSourceBlobSha"] != board["sourceBlobSha"] or
                current["pinnedUpdatedAt"] != board["officialUpdatedAt"] or
                current["pinnedCount"] != len(board["entries"])):
                raise ValueError("RoboDojo audit mismatch: pinned source changed, recertify live lag")
            if current["liveCount"] <= current["pinnedCount"]:
                raise ValueError("RoboDojo live lag expected to exceed pinned count")
            live_info = {
                "count": current["liveCount"],
                "updatedAt": live_audit["dataUpdatedAt"],
                "checkedAt": live_audit["observedAt"],
                "url": current["source"],
                "status": "live-unpinned",
            }
        index[board["benchmark"]] = {
            "id": board["id"], "benchmark": board["benchmark"],
            **({"liveInfo": live_info} if live_info else {}),
            "sourceUpdatedAt": board["officialUpdatedAt"], "capturedAt": board["capturedAt"],
            "sourceUrl": board["sourceUrl"], "boardUrl": board["boardUrl"],
            "sourceRepoRevision": board["sourceRepoRevision"], "sourceBlobSha": board["sourceBlobSha"],
            "entryCount": len(board["entries"]), "metricSchema": board["metricSchema"],
            "topThree": first_three, "modelNames": [e["model"] for e in board["entries"]], "resultUrl": url,
        }
    return index
