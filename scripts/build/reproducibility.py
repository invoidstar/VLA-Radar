"""Build reproducibility/resource-status cards without conflating links with full release completeness."""
from __future__ import annotations
from pathlib import Path
from catalog_core import load,public_url,require,day

DIMENSIONS=("project","code","weights","dataset","training","inference","evaluation","license")
STATUSES=("available","partial","unavailable","unknown")

def validate_reproducibility_data(data,paper_ids):
    require(isinstance(data,dict) and set(data)=={"schemaVersion","dimensions","statuses","papers"},"reproducibility: unexpected/missing fields")
    require(data["schemaVersion"]==2,"reproducibility schema version")
    require(tuple(data["dimensions"])==DIMENSIONS,"reproducibility dimensions")
    require(tuple(data["statuses"])==STATUSES,"reproducibility statuses")
    known=set(paper_ids);audits={}
    require(isinstance(data["papers"],dict),"reproducibility papers must be an object")
    require(set(data["papers"])==known,"reproducibility audits must cover every catalog paper exactly")
    for pid,audit in data["papers"].items():
        require(pid in known,f"reproducibility audit for unknown paper {pid}")
        require(isinstance(audit,dict) and set(audit)=={"verifiedAt","level","note","items"},f"{pid}: reproducibility audit fields")
        day(audit["verifiedAt"],False)
        require(audit["level"] in {"baseline","deep"},f"{pid}: reproducibility audit level")
        require(isinstance(audit["note"],str) and audit["note"].strip(),f"{pid}: reproducibility audit note")
        require(isinstance(audit["items"],dict),f"{pid}: reproducibility items must be an object")
        if audit["level"]=="deep":require(audit["items"],f"{pid}: deep audit requires explicit items")
        require(set(audit["items"])<=set(DIMENSIONS),f"{pid}: unknown reproducibility dimension")
        clean={}
        for dim,item in audit["items"].items():
            require(isinstance(item,dict) and set(item)=={"status","note","url","source"},f"{pid}.{dim}: invalid reproducibility item")
            require(item["status"] in set(STATUSES)-{"unknown"},f"{pid}.{dim}: audited item cannot be unknown")
            require(isinstance(item["note"],str) and item["note"].strip(),f"{pid}.{dim}: note required")
            require(item["url"] is None or isinstance(item["url"],str),f"{pid}.{dim}: url must be text/null")
            if item["url"] is not None: public_url(item["url"])
            public_url(item["source"])
            if item["status"] in {"available","partial"}:require(item["url"],f"{pid}.{dim}: actionable status requires url")
            if item["status"]=="unavailable":require(item["url"] is None,f"{pid}.{dim}: unavailable item cannot have resource url")
            clean[dim]=item
        audits[pid]={"verifiedAt":audit["verifiedAt"],"level":audit["level"],"note":audit["note"],"items":clean}
    return audits

def load_reproducibility(root,paper_ids,resources=None):
    data=load(Path(root)/"catalog/reproducibility.json")
    return validate_reproducibility_data(data,paper_ids)

def build_reproducibility_views(paper_ids,resources,audits):
    out={}
    labels={
      "project":"Official project page",
      "code":"Official public code repository/link",
    }
    for pid in paper_ids:
        base={}
        for dim in DIMENSIONS:
            if dim=="project" and resources.get(pid,{}).get("project"):
                url=resources[pid]["project"];base[dim]={"status":"available","note":labels[dim],"url":url,"source":url}
            elif dim=="code" and resources.get(pid,{}).get("code"):
                url=resources[pid]["code"];base[dim]={"status":"available","note":labels[dim],"url":url,"source":url}
            else:
                base[dim]={"status":"unknown","note":"Not yet independently audited in VLA-Radar.","url":None,"source":None}
        audit=audits.get(pid)
        if audit:
            for dim,item in audit["items"].items():base[dim]=item
        out[pid]={"verifiedAt":audit["verifiedAt"] if audit else None,"level":audit["level"] if audit else None,"note":audit["note"] if audit else "No reproducibility audit record yet.","items":base}
    return out
