"""Canonical paper relations: validated lineage links and compact series membership."""
from __future__ import annotations
import re
from pathlib import Path
from catalog_core import load,public_url,require,day

LINK_TYPES={"extends","follow-up-of"}

def _sources(value,context):
    require(isinstance(value,list) and value,context+": sources required")
    out=[]
    for src in value:
        require(isinstance(src,dict) and set(src)=={"label","url"},context+": invalid source")
        require(isinstance(src["label"],str) and src["label"].strip(),context+": source label")
        out.append({"label":src["label"],"url":public_url(src["url"])})
    return out

def load_relations(root,paper_ids):
    path=Path(root)/"catalog/relations.json";data=load(path)
    require(isinstance(data,dict) and set(data)=={"schemaVersion","links","series"},"relations: unexpected/missing fields")
    require(data["schemaVersion"]==1,"relations schema version")
    known=set(paper_ids)
    require(isinstance(data["links"],list) and isinstance(data["series"],list),"relations arrays")
    link_ids=set();triples=set();links=[]
    for item in data["links"]:
        req={"id","type","fromPaperId","toPaperId","verifiedAt","note","sources"}
        require(isinstance(item,dict) and set(item)==req,"relation link fields")
        require(re.fullmatch(r"rel-[a-z0-9-]+",item["id"]) and item["id"] not in link_ids,"relation link id")
        link_ids.add(item["id"])
        require(item["type"] in LINK_TYPES,"relation link type")
        require(item["fromPaperId"] in known and item["toPaperId"] in known,"relation references unknown paper")
        require(item["fromPaperId"]!=item["toPaperId"],"relation self-link")
        sig=(item["type"],item["fromPaperId"],item["toPaperId"])
        require(sig not in triples,"duplicate relation link");triples.add(sig)
        day(item["verifiedAt"],False)
        require(isinstance(item["note"],str) and item["note"].strip(),"relation note")
        links.append({**item,"sources":_sources(item["sources"],item["id"])})
    series_ids=set();member_sets=set();series=[]
    for item in data["series"]:
        req={"id","name","paperIds","verifiedAt","note","sources"}
        require(isinstance(item,dict) and set(item)==req,"relation series fields")
        require(re.fullmatch(r"series-[a-z0-9-]+",item["id"]) and item["id"] not in series_ids,"relation series id")
        series_ids.add(item["id"])
        require(isinstance(item["name"],str) and item["name"].strip(),"series name")
        require(isinstance(item["paperIds"],list) and len(item["paperIds"])>=2,"series needs at least two papers")
        require(len(item["paperIds"])==len(set(item["paperIds"])),"duplicate paper in series")
        require(set(item["paperIds"])<=known,"series references unknown paper")
        signature=tuple(sorted(item["paperIds"]));require(signature not in member_sets,"duplicate series membership set");member_sets.add(signature)
        day(item["verifiedAt"],False)
        require(isinstance(item["note"],str) and item["note"].strip(),"series note")
        series.append({**item,"sources":_sources(item["sources"],item["id"])})
    return {"schemaVersion":1,"links":links,"series":series}

def build_relation_views(records,registry):
    papers={r["paper"]["id"]:r["paper"] for r in records}
    out={pid:{"previous":[],"followups":[],"series":[]} for pid in papers}
    def ref(pid):
        p=papers[pid]
        return {"paperId":pid,"name":p["name"],"title":p["title"],"firstPublished":p["firstPublished"]}
    for link in registry["links"]:
        source=link["fromPaperId"];target=link["toPaperId"]
        base={"type":link["type"],"note":link["note"],"verifiedAt":link["verifiedAt"],"sources":link["sources"]}
        out[source]["previous"].append({**ref(target),**base})
        out[target]["followups"].append({**ref(source),**base})
    for series in registry["series"]:
        members=sorted((ref(pid) for pid in series["paperIds"]),key=lambda x:((x["firstPublished"] or "9999"),x["paperId"]))
        for pid in series["paperIds"]:
            out[pid]["series"].append({
              "id":series["id"],"name":series["name"],"note":series["note"],"verifiedAt":series["verifiedAt"],
              "sources":series["sources"],"members":[m for m in members if m["paperId"]!=pid]
            })
    return out
