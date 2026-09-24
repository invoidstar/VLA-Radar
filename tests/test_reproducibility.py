import copy,json,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/build"))
from catalog_core import read_catalog,load_resources
from reproducibility import load_reproducibility,build_reproducibility_views
from build_catalog import outputs

def catalog_context():
    manifest,records,_,_=read_catalog(ROOT)
    ids={r["paper"]["id"] for r in records}
    resources=load_resources(ROOT,ids)
    return manifest,records,ids,resources

def test_reproducibility_registry_and_dimensions():
    _,_,ids,resources=catalog_context()
    audits=load_reproducibility(ROOT,ids,resources)
    assert len(audits)==116
    assert sum(x["level"]=="deep" for x in audits.values())==10
    assert sum(x["level"]=="baseline" for x in audits.values())==106
    assert audits["p064"]["items"]["weights"]["status"]=="available"
    assert audits["p004"]["items"]["training"]["status"]=="partial"
    assert audits["p114"]["items"]["weights"]["status"]=="unavailable"
    assert audits["p115"]["items"]["weights"]["status"]=="unavailable"

def test_default_unknown_is_not_invented_unavailable():
    manifest,_,ids,resources=catalog_context()
    audits=load_reproducibility(ROOT,ids,resources)
    views=build_reproducibility_views(manifest["paperOrder"],resources,audits)
    assert views["p116"]["items"]["weights"]["status"]=="unknown"
    assert views["p116"]["items"]["code"]["status"]=="unknown"
    assert views["p116"]["items"]["project"]["status"]=="available"
    assert views["p001"]["items"]["weights"]["status"]=="unknown"

def test_code_link_can_be_partial_when_repo_is_information_only():
    manifest,_,ids,resources=catalog_context()
    audits=load_reproducibility(ROOT,ids,resources)
    views=build_reproducibility_views(manifest["paperOrder"],resources,audits)
    assert views["p113"]["items"]["code"]["status"]=="partial"
    assert views["p114"]["items"]["code"]["status"]=="partial"
    assert views["p115"]["items"]["code"]["status"]=="partial"
    assert views["p113"]["items"]["code"]["url"]=="https://github.com/QwenLM/Qwen-VLA"

def test_public_library_lazy_loads_reproducibility_cards():
    out=outputs(ROOT)
    lib=json.loads(out["data/library.json"])
    byid={p["id"]:p for p in lib["papers"]}
    assert byid["p064"]["reproducibilityUrl"]=="data/reproducibility/p064.json"
    assert byid["p114"]["reproducibilityUrl"]=="data/reproducibility/p114.json"
    assert byid["p116"]["reproducibilityUrl"]=="data/reproducibility/p116.json"
    openvla=json.loads(out["data/reproducibility/p064.json"])
    assert openvla["paperId"]=="p064" and openvla["verifiedAt"]=="2026-09-25"
    assert openvla["items"]["weights"]["status"]=="available"
    assert openvla["items"]["license"]["status"]=="partial"
    qwen=json.loads(out["data/reproducibility/p114.json"])
    assert qwen["items"]["weights"]["status"]=="unavailable"
    assert qwen["items"]["training"]["status"]=="unknown"
    baseline=json.loads(out["data/reproducibility/p116.json"])
    assert baseline["level"]=="baseline"
    assert baseline["items"]["weights"]["status"]=="unknown"
    assert len([k for k in out if k.startswith("data/reproducibility/")])==116

def test_audited_unknown_status_is_rejected():
    _,_,ids,resources=catalog_context()
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);(root/"catalog").mkdir()
        data=json.loads((ROOT/"catalog/reproducibility.json").read_text())
        data["papers"]["p064"]["items"]["weights"]["status"]="unknown"
        (root/"catalog/reproducibility.json").write_text(json.dumps(data,ensure_ascii=False))
        try:load_reproducibility(root,ids,resources)
        except ValueError as exc:assert "cannot be unknown" in str(exc)
        else:raise AssertionError("audited unknown status accepted")

def test_unavailable_resource_cannot_have_action_url():
    _,_,ids,resources=catalog_context()
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);(root/"catalog").mkdir()
        data=json.loads((ROOT/"catalog/reproducibility.json").read_text())
        data["papers"]["p114"]["items"]["weights"]["url"]="https://example.com/weights"
        (root/"catalog/reproducibility.json").write_text(json.dumps(data,ensure_ascii=False))
        try:load_reproducibility(root,ids,resources)
        except ValueError as exc:assert "unavailable item cannot have resource url" in str(exc)
        else:raise AssertionError("unavailable resource with url accepted")

def test_unknown_paper_audit_is_rejected():
    _,_,ids,resources=catalog_context()
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);(root/"catalog").mkdir()
        data=json.loads((ROOT/"catalog/reproducibility.json").read_text())
        data["papers"]["p999"]=copy.deepcopy(data["papers"]["p064"])
        (root/"catalog/reproducibility.json").write_text(json.dumps(data,ensure_ascii=False))
        try:load_reproducibility(root,ids,resources)
        except ValueError as exc:assert "unknown paper" in str(exc)
        else:raise AssertionError("unknown paper audit accepted")


def test_baseline_audit_may_preserve_all_unknown_dimensions():
    _,_,ids,resources=catalog_context()
    audits=load_reproducibility(ROOT,ids,resources)
    assert audits["p006"]["level"]=="baseline"
    assert audits["p006"]["items"]=={}
    views=build_reproducibility_views(sorted(ids),resources,audits)
    assert all(item["status"]=="unknown" for item in views["p006"]["items"].values())

def test_deep_audit_requires_explicit_dimension_evidence():
    _,_,ids,resources=catalog_context()
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);(root/"catalog").mkdir()
        data=json.loads((ROOT/"catalog/reproducibility.json").read_text())
        data["papers"]["p064"]["items"]={}
        (root/"catalog/reproducibility.json").write_text(json.dumps(data,ensure_ascii=False))
        try:load_reproducibility(root,ids,resources)
        except ValueError as exc:assert "deep audit requires explicit items" in str(exc)
        else:raise AssertionError("empty deep audit accepted")
