"""Official benchmark snapshot integrity and source provenance regression."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts/build"))
from catalog_core import read_catalog
from official_boards import load_snapshots, official_board_outputs

def test_official_snapshot_schema_independent_of_paper_results():
    manifest,records,tracks,results=read_catalog(ROOT)
    ids={rec["paper"]["id"] for rec in records}
    boards=load_snapshots(ROOT,ids)
    assert len(boards)==3
    assert len({x["benchmark"] for x in boards})==3
    assert all(x["sourceBlobSha"] and x["sourceRepoRevision"] for x in boards)
    assert all(x["entries"] for x in boards)
    assert all("model" in e and "values" in e for b in boards for e in b["entries"])

def test_original_paper_results_not_replaced_by_official_model_submissions():
    manifest,records,tracks,results=read_catalog(ROOT)
    ids={rec["paper"]["id"] for rec in records}
    boards=load_snapshots(ROOT,ids)
    assert not any(e.get("resultId") or e.get("trackId") for b in boards for e in b["entries"])
    sim=next(b for b in boards if b["id"]=="robodojo-sim")
    assert any(x["model"]=="VPP2" for x in sim["entries"])
    assert any(x["model"]=="VPP2-Preview" for x in sim["entries"])
    assert next(x for x in sim["entries"] if x["model"]=="VPP2")["values"]["Average"]["score"]==39.26
    twin=next(b for b in boards if b["id"]=="robotwin2")
    links={x["model"]:x.get("paperLink",{}).get("paperId") for x in twin["entries"]}
    assert links["ViGAR"]=="p131" and links["PatchWAM"]=="p132" and links["ME-Dex-1.0"]=="p133"
    no_paper={x["model"]:x for x in sim["entries"] if x["model"] in {"PhysicalRSI","Awomo-0.5"}}
    assert len(no_paper)==2 and all(x.get("resourceLink") and not x.get("paperLink") for x in no_paper.values())

def test_unpublished_robodojo_preview_submissions_keep_source_without_papers():
    _,records,_,_=read_catalog(ROOT)
    ids={r["paper"]["id"] for r in records}
    sim=next(b for b in load_snapshots(ROOT,ids) if b["id"]=="robodojo-sim")
    requested={"Simate-beta":(33.95,27.96),"Rex-M1 Preview":(33.79,27.44),
               "Liber-0 Preview":(30.74,25.52),"Liber-0 Lite":(29.24,24.23)}
    found={x["model"]:x for x in sim["entries"] if x["model"] in requested}
    assert set(found)==set(requested)
    for name,(score,sr) in requested.items():
        item=found[name]
        assert item["values"]["Average"]=={"score":score,"sr":sr}
        assert item.get("resourceKind") and item.get("resourceNote")
        assert item["resourceCheckedAt"]=="2026-10-14"
        assert not item.get("paperLink")
    assert sum(bool(x.get("resourceLink")) for x in found.values())==3


def test_generation_shards_are_lazy_and_do_not_leak_all_official_rows():
    manifest,records,tracks,results=read_catalog(ROOT)
    ids={rec["paper"]["id"] for rec in records}
    output={}
    def writer(prefix,obj,out):
        out[prefix+".json"]=obj
        return prefix+".json"
    index=official_board_outputs(ROOT,output,ids,writer)
    assert len(index)==3
    for dataset,info in index.items():
        assert info["entryCount"]>=len(info["topThree"])>0
        assert info["resultUrl"] in output
        assert "entries" not in info
        assert len(info["modelNames"])==info["entryCount"]
        assert info["sourceUpdatedAt"]
    assert index["RoboTwin"]["metricSchema"]=="clean-random"
    assert index["RoboDojo"]["metricSchema"]=="score-success"
