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
        assert info["sourceUpdatedAt"]
    assert index["RoboTwin"]["metricSchema"]=="clean-random"
    assert index["RoboDojo"]["metricSchema"]=="score-success"
