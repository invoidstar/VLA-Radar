"""Safely migrate the complete RoboDojo official JSON to source-pinned boards.

Only a fixed SHA256 and complete, schema-matched 66/14 official response is accepted.
Run inside an isolated release branch with two local Git commits:
  1) source raw response (SHA-pinned archive)
  2) transformed, quality-validated canonical snapshots and audit
No automatic live data is allowed to overwrite canonical without full regression.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_URL = "https://robodojo-benchmark.com/data/leaderboard.generated.json"
SOURCE_PATH = "maintenance/source-snapshots/robodojo-generated-20261103.json"
EXPECTED_SHA256 = "a64fec25b9c19734cc1e7785655031729090f331214108449abea2c2a902bdab"
EXPECTED_DATE = "2026-11-03"
MAPS = {
    "robodojo-sim": ("sim", 66, {
        "Average": "average", "Average no Open": "sft", "Generalization": "generalization",
        "Precision": "precision", "Long Horizon": "longHorizon",
        "Memory": "memory", "Open": "open"}),
    "robodojo-real": ("realworld", 14, {
        "Average": "average", "ARX X5": "arxX5", "Piper": "piper", "Piper X": "piperX"}),
}

def ensure(ok, message):
    if not ok:
        raise ValueError("RoboDojo canonical sync: " + message)

def source_bytes():
    request = Request(OFFICIAL_URL, headers={
        "User-Agent": "VLA-Radar-evidence-sync/1.0",
        "Accept": "application/json",
    })
    with urlopen(request, timeout=20) as response:
        host = urlparse(response.geturl())
        ensure(host.scheme == "https" and host.hostname == "robodojo-benchmark.com", "unexpected redirect")
        raw = response.read(1_500_001)
        ensure(response.status == 200 and len(raw) <= 1_500_000, "invalid original response")
    return raw

def parse_source(raw):
    digest = hashlib.sha256(raw).hexdigest()
    ensure(digest == EXPECTED_SHA256, "official SHA256 drift: " + digest)
    data = json.loads(raw)
    ensure(isinstance(data,dict) and set(data)=={"updatedAt","sim","realworld"}, "root keys")
    iso = data["updatedAt"]["iso"]
    ensure(isinstance(iso,str) and iso.startswith(EXPECTED_DATE), "official data date")
    for board, (key, expected, mapping) in MAPS.items():
        models = data[key]
        ensure(isinstance(models,list) and len(models)==expected, board+" model count")
        ensure(len({row["model"] for row in models})==expected, board+" duplicate model")
        for row in models:
            ensure(set(row["dimensions"])==set(mapping.values()), board+" dimensions")
            ensure(isinstance(row.get("team"),str) and row["team"], board+" author/team")
            for dim in row["dimensions"].values():
                ensure(set(dim)=={"score","successRate"}, board+" score/sr pair")
                for val in dim.values():
                    ensure(type(val) in {int,float} and 0 <= val <= 100, board+" invalid metric")
            assert row["score"] == row["dimensions"]["average"]["score"]
            assert row["successRate"] == row["dimensions"]["average"]["successRate"]
    return data

def git_blob_sha(raw):
    # Git object identity of the exact bytes as committed in SOURCE_PATH.
    return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()

def collect_boards(root:Path, data, raw, revision:str):
    ensure(bool(re.fullmatch(r"[0-9a-f]{40}",revision)), "invalid source snapshot revision")
    results={}
    summaries={}
    raw_blob=git_blob_sha(raw)
    for board, (key, count, mapping) in MAPS.items():
        path=root/"catalog"/"official-boards"/(board+".json")
        prior=json.loads(path.read_text(encoding="utf-8"))
        old={r["model"]:r for r in prior["entries"]}
        latest={r["model"]:r for r in data[key]}
        ensure(set(old)<=set(latest), board+" previously confirmed models missing")
        mismatches=[]
        for model,former in old.items():
            fresh=latest[model]
            for col,field in mapping.items():
                for metric,raw_name in (("score","score"),("sr","successRate")):
                    pval=former["values"][col][metric]
                    nval=fresh["dimensions"][field][raw_name]
                    if abs(pval-nval)>0.035:
                        mismatches.append((model,col,metric,pval,nval))
        ensure(not mismatches, board+" unexpected changed previously pinned scores: "+repr(mismatches[:3]))
        entries=[]
        for item in sorted(data[key],key=lambda x:(-x["score"],x["model"].casefold())):
            inherited=copy.deepcopy(old.get(item["model"],{}))
            inherited["model"]=item["model"]
            inherited["rank"]=len(entries)+1
            inherited["contributor"]=item["team"]
            inherited["values"]={col:{
                "score":item["dimensions"][src]["score"],
                "sr":item["dimensions"][src]["successRate"],
            } for col,src in mapping.items()}
            entries.append(inherited)
        meta=copy.deepcopy(prior)
        meta["entries"]=entries
        meta["capturedAt"]="2026-11-14"
        meta["officialUpdatedAt"]=EXPECTED_DATE
        meta["sourceUrl"]=OFFICIAL_URL
        meta["sourceRepoRevision"]=revision
        meta["sourceBlobSha"]=raw_blob
        meta["sourceRepoUrl"]="https://github.com/invoidstar/VLA-Radar/blob/"+revision+"/"+SOURCE_PATH
        meta["sourceRawPath"]=SOURCE_PATH
        meta["sourceContentSha256"]=EXPECTED_SHA256
        meta["provenance"]="RoboDojo Benchmark Committee official generated JSON; exact original bytes archived in VLA-Radar at sourceRepoRevision and sourceBlobSha"
        meta["sourceOfRecord"]="RoboDojo Benchmark Committee (official direct JSON)"
        meta["boardUrl"]="https://robodojo-benchmark.com/leaderboard?bench="+("sim" if key=="sim" else "realworld")
        meta["notes"]=prior["notes"]+" Official 2026-11-03 raw source contains "+str(count)+" complete model entries; re-ranked strictly by overall Score. Original author/code identity metadata from verified earlier models is preserved; new preview/agent identities have no automatic paper link."
        results[board]=meta
        summaries[board]={
            "models":count,"prior":len(old),
            "newModels":sorted(set(latest)-set(old)),
            "priorModelsRemoved":0,
            "priorScoreChangesAboveTolerance":0,
        }
    return results,summaries

def cmd_fetch(root):
    raw=source_bytes()
    parse_source(raw)
    target=root/SOURCE_PATH
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(raw)
    print("PINNED_SOURCE",len(raw),hashlib.sha256(raw).hexdigest(),git_blob_sha(raw),target)

def cmd_apply(root,revision):
    raw=(root/SOURCE_PATH).read_bytes()
    data=parse_source(raw)
    converted,summary=collect_boards(root,data,raw,revision)
    for board,obj in converted.items():
        path=root/"catalog"/"official-boards"/(board+".json")
        path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    audit={
      "schemaVersion":1,"checkedAt":"2026-11-14",
      "status":"official-source-pinned-canonical-migrated-pending-ci",
      "officialSourceUrl":OFFICIAL_URL,"sourceUpdatedAt":EXPECTED_DATE,
      "sourceRawPath":SOURCE_PATH,"sourceRepoRevision":revision,
      "sourceBlobSha":git_blob_sha(raw),"sourceSha256":EXPECTED_SHA256,
      "sourceBytes":len(raw),"boards":summary,
      "explicitChecks":[
       "Exact official bytes and date SHA256 matched probe artifact 2026-11-14.",
       "66 Sim and 14 Real distinct named models, complete dimensions, valid Score/SR.",
       "All prior 57 Sim/11 Real identities retained and source metric delta <=0.035; only OpenWAM-alpha Piper X SR +0.03 historical rounding.",
       "Official raw sim array appended some entries unsorted; canonical ranking sorted by Overall Score descending.",
       "Pre-existing paper/resource provenance preserved, no automatic paper link for 12 novel official submissions.",
       "Research paper original Results are unchanged; independent source-backed official board only.",
      ],"completeDiscovery":False,
    }
    path=root/"maintenance"/"audits"/"benchmark"/"robodojo-official-pinned-20261114.json"
    path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("MIGRATED_OFFICIAL_BOARDS",json.dumps(summary,ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=["fetch","apply"])
    ap.add_argument("--root",type=Path,default=ROOT)
    ap.add_argument("--source-revision",default="")
    args=ap.parse_args()
    if args.mode=="fetch":
        cmd_fetch(args.root)
    else:
        cmd_apply(args.root,args.source_revision)

if __name__=="__main__":
    main()
