import copy,json,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/discovery"))
from discovery_coverage import apply_audit,load_policy,next_window,validate_audit,validate_repository

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def base_state():
    return {
      "schemaVersion":1,"timezone":"Asia/Singapore","initialBackfillFrom":"2026-09-01",
      "lookbackDays":14,"lastSuccessfulSearchAt":"2026-09-24","lastAttemptAt":"2026-09-24",
      "lastStatus":"success","lastSummary":"legacy baseline","discoveryPolicyVersion":1,
      "lastDiscoveryAudit":"maintenance/audits/discovery-2026-09-01-2026-09-24.json",
      "lastCompleteDiscoveryAudit":None
    }

def source(sid,lane,status="success"):
    return {
      "id":sid,"lane":lane,"provider":sid,"kind":"search","status":status,
      "coverage":{"from":"2026-09-10" if status=="success" else None,"to":"2026-09-25" if status=="success" else None},
      "query":"VLA / WAM / robot foundation policy","resultCount":3 if status=="success" else 0,
      "note":"" if status=="success" else "provider blocked"
    }

def audit(partial_lane=None):
    sources=[
      source("arxiv-direct","primary-preprints"),
      source("openalex","academic-index"),
      source("robotics-daily","curated-robotics"),
      source("official-reverse","reverse-discovery"),
    ]
    if partial_lane:
        idx=next(i for i,x in enumerate(sources) if x["lane"]==partial_lane)
        sources[idx]=source(sources[idx]["id"],partial_lane,"blocked")
    candidate={
      "title":"Example VLA Paper","arxiv":"2609.99999","doi":"","date":"2026-09-25",
      "sourceIds":["arxiv-direct","robotics-daily"],"status":"deferred",
      "reason":"Needs full primary-source review before admission.","paperId":None,"duplicateOf":None
    }
    counts={"total":1,"selected":0,"deferred":1,"excluded":0,"duplicate":0,"crossSource":1}
    complete=partial_lane is None
    return {
      "schemaVersion":2,"id":"discovery-2026-09-10-2026-09-25",
      "window":{"from":"2026-09-10","to":"2026-09-25","attemptedAt":"2026-09-25","completedAt":"2026-09-25" if complete else None},
      "scope":"VLA / WAM / robot foundation policy discovery",
      "sources":sources,"candidates":[candidate],"counts":counts,
      "status":"success" if complete else "partial","notes":"Synthetic coverage audit."
    }

def fixture():
    tmp=tempfile.TemporaryDirectory();root=Path(tmp.name)
    dump(root/"maintenance/policies/discovery-policy.json",json.loads((ROOT/"maintenance/policies/discovery-policy.json").read_text()))
    dump(root/"maintenance/state/state.json",base_state())
    return tmp,root

def test_current_repository_keeps_legacy_candidates_visible():
    report=validate_repository(ROOT)
    assert report["lastSuccessfulSearchAt"]=="2026-09-24"
    assert report["candidateQueue"]["deferred"]>=244
    assert report["candidateQueue"]["selected"]>=12

def test_plan_rewinds_success_checkpoint_by_policy_lookback():
    policy=load_policy(ROOT)
    state=json.loads((ROOT/"maintenance/state/state.json").read_text())
    assert next_window(state,policy,"2026-09-25")==("2026-09-10","2026-09-25")

def test_complete_multilane_audit_advances_checkpoint():
    tmp,root=fixture()
    try:
        path=root/"maintenance/audits/discovery/discovery-2026-09-10-2026-09-25.json"
        dump(path,audit())
        report=apply_audit(root,path)
        state=json.loads((root/"maintenance/state/state.json").read_text())
        assert report["complete"]
        assert state["lastSuccessfulSearchAt"]=="2026-09-25"
        assert state["lastStatus"]=="success"
        assert state["lastCompleteDiscoveryAudit"]=="maintenance/audits/discovery/discovery-2026-09-10-2026-09-25.json"
        assert validate_repository(root)["completeAudits"]==1
    finally:tmp.cleanup()

def test_blocked_required_lane_records_partial_without_advancing_checkpoint():
    tmp,root=fixture()
    try:
        path=root/"maintenance/audits/discovery/discovery-2026-09-10-2026-09-25.json"
        dump(path,audit("academic-index"))
        report=apply_audit(root,path)
        state=json.loads((root/"maintenance/state/state.json").read_text())
        assert not report["complete"]
        assert state["lastSuccessfulSearchAt"]=="2026-09-24"
        assert state["lastStatus"]=="partial"
        assert state["lastDiscoveryAudit"].endswith("discovery-2026-09-10-2026-09-25.json")
    finally:tmp.cleanup()

def test_success_label_cannot_hide_missing_required_lane():
    policy=load_policy(ROOT);bad=audit("academic-index");bad["status"]="success";bad["window"]["completedAt"]="2026-09-25"
    try:validate_audit(bad,policy)
    except ValueError as exc:assert "status" in str(exc)
    else:raise AssertionError("missing discovery lane was accepted as success")

def test_candidate_counts_are_derived_not_trusted():
    policy=load_policy(ROOT);bad=audit();bad["counts"]["deferred"]=0
    try:validate_audit(bad,policy)
    except ValueError as exc:assert "counts mismatch" in str(exc)
    else:raise AssertionError("stale discovery counts were accepted")

def test_duplicate_candidate_identity_in_one_audit_is_rejected():
    policy=load_policy(ROOT);bad=audit();other=copy.deepcopy(bad["candidates"][0]);other["title"]="Renamed title"
    bad["candidates"].append(other);bad["counts"]={"total":2,"selected":0,"deferred":2,"excluded":0,"duplicate":0,"crossSource":2}
    try:validate_audit(bad,policy)
    except ValueError as exc:assert "duplicate candidate identity" in str(exc)
    else:raise AssertionError("duplicate arXiv candidate was accepted")


def test_one_provider_cannot_fake_four_lanes():
    policy=load_policy(ROOT);bad=audit()
    for s in bad["sources"]:s["provider"]="same-aggregator"
    try:validate_audit(bad,policy)
    except ValueError as exc:assert "provider diversity" in str(exc)
    else:raise AssertionError("one provider satisfied all discovery lanes")


def test_narrow_success_window_cannot_advance_checkpoint():
    tmp,root=fixture()
    try:
        bad=audit()
        bad["id"]="discovery-2026-09-24-2026-09-25"
        bad["window"]["from"]="2026-09-24"
        for s in bad["sources"]:s["coverage"]["from"]="2026-09-24"
        path=root/"maintenance/audits/discovery/discovery-2026-09-24-2026-09-25.json"
        dump(path,bad)
        try:apply_audit(root,path)
        except ValueError as exc:assert "overlap from 2026-09-10" in str(exc)
        else:raise AssertionError("narrow discovery window advanced checkpoint")
    finally:tmp.cleanup()

def test_audit_filename_identity_dates_match_window():
    policy=load_policy(ROOT);bad=audit();bad["id"]="discovery-2026-09-09-2026-09-25"
    try:validate_audit(bad,policy)
    except ValueError as exc:assert "id/window mismatch" in str(exc)
    else:raise AssertionError("audit id/window mismatch was accepted")
