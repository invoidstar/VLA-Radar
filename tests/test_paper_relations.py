import copy,json,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/build"))
from catalog_core import read_catalog
from paper_relations import load_relations,build_relation_views

def test_relation_registry_is_referentially_closed():
    _,records,_,_=read_catalog(ROOT)
    ids={r["paper"]["id"] for r in records}
    rel=load_relations(ROOT,ids)
    assert rel["schemaVersion"]==1
    assert len(rel["links"])==3
    assert len(rel["series"])==6
    assert all(x["fromPaperId"] in ids and x["toPaperId"] in ids for x in rel["links"])
    assert all(set(x["paperIds"])<=ids for x in rel["series"])

def test_key_lineages_are_explicit_and_directional():
    _,records,_,_=read_catalog(ROOT)
    rel=load_relations(ROOT,{r["paper"]["id"] for r in records})
    triples={(x["type"],x["fromPaperId"],x["toPaperId"]) for x in rel["links"]}
    assert ("extends","p069","p064") in triples
    assert ("extends","p072","p066") in triples
    assert ("follow-up-of","p087","p086") in triples

def test_series_membership_covers_initial_verified_families():
    _,records,_,_=read_catalog(ROOT)
    rel=load_relations(ROOT,{r["paper"]["id"] for r in records})
    byid={x["id"]:x for x in rel["series"]}
    assert byid["series-xiaomi-robotics"]["paperIds"]==["p112","p004"]
    assert set(byid["series-qwen-robotics"]["paperIds"])=={"p113","p114","p115","p116"}
    assert set(byid["series-openvla"]["paperIds"])=={"p064","p069"}
    assert set(byid["series-pi"]["paperIds"])=={"p066","p072"}
    assert set(byid["series-rvt"]["paperIds"])=={"p086","p087"}
    assert set(byid["series-rt"]["paperIds"])=={"p052","p058"}

def test_relation_views_expose_previous_followup_and_same_series():
    _,records,_,_=read_catalog(ROOT)
    rel=load_relations(ROOT,{r["paper"]["id"] for r in records})
    views=build_relation_views(records,rel)
    assert views["p069"]["previous"][0]["paperId"]=="p064"
    assert views["p064"]["followups"][0]["paperId"]=="p069"
    openvla_series=next(x for x in views["p069"]["series"] if x["id"]=="series-openvla")
    assert [x["paperId"] for x in openvla_series["members"]]==["p064"]
    qwen=next(x for x in views["p113"]["series"] if x["id"]=="series-qwen-robotics")
    assert {x["paperId"] for x in qwen["members"]}=={"p114","p115","p116"}

def test_invalid_relation_self_link_is_rejected():
    _,records,_,_=read_catalog(ROOT);ids={r["paper"]["id"] for r in records}
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);(root/"catalog").mkdir()
        data=json.loads((ROOT/"catalog/relations.json").read_text())
        bad=copy.deepcopy(data["links"][0]);bad["id"]="rel-invalid-self";bad["toPaperId"]=bad["fromPaperId"]
        data["links"].append(bad)
        (root/"catalog/relations.json").write_text(json.dumps(data,ensure_ascii=False))
        try:load_relations(root,ids)
        except ValueError as exc:assert "self-link" in str(exc)
        else:raise AssertionError("self relation accepted")

def test_invalid_series_unknown_paper_is_rejected():
    _,records,_,_=read_catalog(ROOT);ids={r["paper"]["id"] for r in records}
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);(root/"catalog").mkdir()
        data=json.loads((ROOT/"catalog/relations.json").read_text())
        data["series"][0]["paperIds"].append("p999")
        (root/"catalog/relations.json").write_text(json.dumps(data,ensure_ascii=False))
        try:load_relations(root,ids)
        except ValueError as exc:assert "unknown paper" in str(exc)
        else:raise AssertionError("unknown series paper accepted")
