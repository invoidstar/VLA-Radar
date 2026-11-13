"""ActPrune source-version, scoped evaluation and negative-result regression."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"catalog"


def row(track,variant):
    path=SRC/"results"/("r-"+track+"-"+variant+".json")
    return json.loads(path.read_text(encoding="utf-8"))


def test_actprune_v1_results_and_v2_publication_are_separate():
    paper=json.loads((SRC/"papers/p154.json").read_text(encoding="utf-8"))
    assert paper["paper"]["firstPublished"]=="2026-11-06"
    assert paper["publication"]["latestArxivVersion"]=="v2"
    assert paper["publication"]["latestArxivAt"]=="2026-11-11"
    assert paper["note"]["version"].startswith("ActPrune arXiv 2611.08827v2")
    assert paper["note"]["coverage"]["level"]=="deep"
    assert len(paper["note"]["sections"])>=12
    assert row("actprune-v1-libero-oft-sr","quarter")["sourceVersion"]=="arXiv 2611.08827v1"


def test_actprune_backbone_specific_speed_and_failure_cases():
    oft=row("actprune-v1-libero-oft-sr","quarter")
    pi=row("actprune-v1-libero-pi05-sr","quarter")
    vl=row("actprune-v1-vlabench-pi05-sr","half")
    real=row("actprune-v1-real-franka4-sr","half")
    assert oft["values"]["Average"]==96.1
    assert pi["values"]["Average"]==91.8
    assert vl["values"]["Average"]==26.3
    assert real["values"]["Average"]==50
    assert row("actprune-v1-real-franka4-sr","full")["values"]["Average"]==60
    assert row("actprune-v1-libero-oft-latency","quarter")["values"]["LatencySeconds"]==0.05361
    assert row("actprune-v1-libero-pi05-latency","quarter")["values"]["LatencySeconds"]==0.1729
    assert row("actprune-v1-real-franka4-latency","half")["values"]["LatencySeconds"]==0.1664


def test_actprune_results_all_have_attribution_and_case_study_registry():
    registry=json.loads((SRC/"benchmark-quality.json").read_text(encoding="utf-8"))
    assert registry["benchmarks"]["ActPrune Real"]["kind"]=="case-study"
    records=[json.loads(p.read_text(encoding="utf-8"))
             for p in (SRC/"results").glob("r-actprune-v1-*.json")]
    assert len(records)==40
    assert all(r["paperId"]=="p154" and r["attribution"] in
               {"author-reported","reported-baseline"} for r in records)
    tracks={r["trackId"] for r in records}
    assert len(tracks)==10
    assert all(r["source"].endswith("2611.08827v1") for r in records)
