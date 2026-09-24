"""Auditable multi-source literature discovery coverage.

This module does not search the network. It validates the public audit produced by a
weekly discovery run and controls when the full-search checkpoint may advance.

A run is "complete" only when every required discovery lane has at least the configured
number of successful sources covering the full requested window and every discovered
candidate has an explicit disposition. Partial/blocked runs may still be recorded, but
must not advance lastSuccessfulSearchAt.
"""
from __future__ import annotations
import argparse,json,re,unicodedata
from datetime import date,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
POLICY_PATH=Path("maintenance/policies/discovery-policy.json")
STATE_PATH=Path("maintenance/state/state.json")
AUDIT_DIR=Path("maintenance/audits/discovery")

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write(path,obj):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def require(ok,msg):
    if not ok: raise ValueError(msg)

def day(value,optional=False):
    if value is None and optional:return None
    require(isinstance(value,str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}",value),f"invalid date: {value}")
    return date.fromisoformat(value)

def norm_title(value):
    return re.sub(r"[\W_]+","",unicodedata.normalize("NFKC",str(value or "")).casefold())

def canonical_doi(value):
    return re.sub(r"^https?://(?:dx\.)?doi\.org/","",str(value or "").strip().lower())

def candidate_key(candidate):
    arxiv=str(candidate.get("arxiv") or "").strip().lower()
    doi=canonical_doi(candidate.get("doi") or "")
    title=norm_title(candidate.get("title") or "")
    if arxiv:return "arxiv:"+arxiv
    if doi:return "doi:"+doi
    require(title,"candidate needs arXiv, DOI or title identity")
    return "title:"+title

def load_policy(root=ROOT):
    p=load(Path(root)/POLICY_PATH)
    require(p.get("schemaVersion")==1,"discovery policy schema")
    require(isinstance(p.get("requiredLanes"),list) and p["requiredLanes"],"required discovery lanes")
    ids=[x.get("id") for x in p["requiredLanes"]]
    require(all(isinstance(x,str) and re.fullmatch(r"[a-z0-9-]+",x) for x in ids),"invalid discovery lane id")
    require(len(ids)==len(set(ids)),"duplicate discovery lane")
    for lane in p["requiredLanes"]:
        require(isinstance(lane.get("label"),str) and lane["label"],"lane label")
        require(type(lane.get("minSuccessful")) is int and lane["minSuccessful"]>=1,"lane minSuccessful")
    day(p["enforceFrom"]);day(p["baselineSuccessfulThrough"])
    require(type(p.get("defaultLookbackDays")) is int and p["defaultLookbackDays"]>=1,"defaultLookbackDays")
    require(type(p.get("minDistinctSuccessfulProviders")) is int and p["minDistinctSuccessfulProviders"]>=2,"minDistinctSuccessfulProviders")
    require(set(p.get("sourceStatuses",[]))=={"success","partial","blocked"},"source status policy")
    require(set(p.get("candidateStatuses",[]))=={"selected","deferred","excluded","duplicate"},"candidate status policy")
    return p

def source_covers(source,start,end):
    if source.get("status")!="success":return False
    coverage=source.get("coverage")
    if not isinstance(coverage,dict):return False
    try:
        a=day(coverage.get("from"));b=day(coverage.get("to"))
    except (ValueError,TypeError):
        return False
    return a<=start and b>=end

def expected_counts(candidates):
    out={"total":len(candidates),"selected":0,"deferred":0,"excluded":0,"duplicate":0,"crossSource":0}
    for c in candidates:
        out[c["status"]]+=1
        if len(set(c["sourceIds"]))>=2:out["crossSource"]+=1
    return out

def validate_audit(audit,policy):
    require(audit.get("schemaVersion")==2,"discovery audit schemaVersion must be 2")
    required={"schemaVersion","id","window","scope","sources","candidates","counts","status","notes"}
    require(set(audit)==required,"unexpected/missing discovery audit fields")
    require(isinstance(audit["id"],str) and re.fullmatch(r"discovery-\d{4}-\d{2}-\d{2}-\d{4}-\d{2}-\d{2}(?:-[a-z0-9-]+)?",audit["id"]),"audit id")
    window=audit["window"]
    require(set(window)=={"from","to","attemptedAt","completedAt"},"discovery window fields")
    start=day(window["from"]);end=day(window["to"]);attempted=day(window["attemptedAt"])
    require(start<=end and attempted>=end,"discovery window order")
    if window["completedAt"] is not None: require(day(window["completedAt"])>=end,"completedAt before window end")
    require(isinstance(audit["scope"],str) and audit["scope"].strip(),"discovery scope")
    require(isinstance(audit["notes"],str),"audit notes")
    require(audit["status"] in {"success","partial"},"audit status")
    require(isinstance(audit["sources"],list) and audit["sources"],"discovery sources required")
    lanes={x["id"]:x for x in policy["requiredLanes"]}
    source_ids=set()
    for s in audit["sources"]:
        req={"id","lane","provider","kind","status","coverage","query","resultCount","note"}
        require(set(s)==req,"unexpected/missing discovery source fields")
        require(isinstance(s["id"],str) and re.fullmatch(r"[a-z0-9][a-z0-9-]*",s["id"]),"source id")
        require(s["id"] not in source_ids,"duplicate source id");source_ids.add(s["id"])
        require(s["lane"] in lanes,"unknown source lane")
        require(isinstance(s["provider"],str) and s["provider"].strip(),"source provider")
        require(isinstance(s["kind"],str) and s["kind"].strip(),"source kind")
        require(s["status"] in policy["sourceStatuses"],"invalid source status")
        require(isinstance(s["coverage"],dict) and set(s["coverage"])=={"from","to"},"source coverage fields")
        if s["coverage"]["from"] is not None:day(s["coverage"]["from"])
        if s["coverage"]["to"] is not None:day(s["coverage"]["to"])
        require(isinstance(s["query"],str) and s["query"].strip(),"source query/scope required")
        require(type(s["resultCount"]) is int and s["resultCount"]>=0,"source resultCount")
        require(isinstance(s["note"],str),"source note")
    candidates=audit["candidates"]
    require(isinstance(candidates,list),"candidates list")
    seen=set()
    for c in candidates:
        req={"title","arxiv","doi","date","sourceIds","status","reason","paperId","duplicateOf"}
        require(set(c)==req,"unexpected/missing candidate fields")
        require(isinstance(c["title"],str) and c["title"].strip(),"candidate title")
        if c["arxiv"]:require(bool(re.fullmatch(r"\d{4}\.\d{4,5}",c["arxiv"])),"candidate arxiv")
        if c["date"] is not None:day(c["date"])
        require(isinstance(c["sourceIds"],list) and c["sourceIds"],"candidate sourceIds")
        require(set(c["sourceIds"])<=source_ids,"candidate references unknown source")
        require(c["status"] in policy["candidateStatuses"],"candidate status")
        require(isinstance(c["reason"],str) and c["reason"].strip(),"candidate disposition reason")
        require(c["paperId"] is None or bool(re.fullmatch(r"p\d{3,}",c["paperId"])),"candidate paperId")
        require(c["duplicateOf"] is None or isinstance(c["duplicateOf"],str),"candidate duplicateOf")
        if c["status"]=="selected":require(c["paperId"],"selected candidate needs paperId")
        if c["status"]=="duplicate":require(c["duplicateOf"],"duplicate candidate needs duplicateOf")
        key=candidate_key(c);require(key not in seen,f"duplicate candidate identity in audit: {key}");seen.add(key)
    counts=expected_counts(candidates)
    require(audit["counts"]==counts,f"discovery counts mismatch: expected {counts}")
    lane_report={}
    complete=True
    successful_providers=set()
    for lane in policy["requiredLanes"]:
        hits=[s for s in audit["sources"] if s["lane"]==lane["id"] and source_covers(s,start,end)]
        successful_providers.update(s["provider"].strip().casefold() for s in hits)
        ok=len(hits)>=lane["minSuccessful"]
        lane_report[lane["id"]]={"required":lane["minSuccessful"],"successful":len(hits),"complete":ok}
        complete=complete and ok
    provider_ok=len(successful_providers)>=policy["minDistinctSuccessfulProviders"]
    lane_report["_providerDiversity"]={"required":policy["minDistinctSuccessfulProviders"],"successful":len(successful_providers),"complete":provider_ok}
    complete=complete and provider_ok
    require((audit["status"]=="success")==complete,"audit status does not match required-lane coverage/provider diversity")
    if complete:require(window["completedAt"] is not None,"successful audit needs completedAt")
    else:require(window["completedAt"] is None,"partial audit cannot claim completedAt")
    return {"complete":complete,"window":{"from":window["from"],"to":window["to"]},"counts":counts,"lanes":lane_report}

def audit_path(root,audit_id):
    return Path(root)/AUDIT_DIR/(audit_id+".json")

def list_v2_audits(root=ROOT,policy=None):
    policy=policy or load_policy(root);out=[]
    directory=Path(root)/AUDIT_DIR
    if not directory.exists():return out
    for path in sorted(directory.glob("*.json")):
        audit=load(path);report=validate_audit(audit,policy);out.append((path,audit,report))
    return out

def _merge_queue_row(queue,c,seen_at,source_count,audit_ref):
    rank={"excluded":0,"duplicate":1,"deferred":2,"selected":3}
    key=candidate_key(c);row=queue.get(key)
    if row is None:
        row={"key":key,"title":c["title"],"firstSeenAt":seen_at,"lastSeenAt":seen_at,
             "status":c["status"],"reason":c["reason"],"sourceCount":0,"audits":[]}
        queue[key]=row
    row["lastSeenAt"]=max(row["lastSeenAt"],seen_at)
    if rank[c["status"]]>=rank[row["status"]]:
        row["status"]=c["status"];row["reason"]=c["reason"];row["title"]=c["title"]
    row["sourceCount"]=max(row["sourceCount"],source_count)
    if audit_ref not in row["audits"]:row["audits"].append(audit_ref)

def aggregate_candidates(root,audits):
    """Build one durable candidate queue from legacy and v2 discovery audits."""
    root=Path(root);queue={}
    for path in sorted((root/"maintenance/audits").glob("discovery-*.json")):
        audit=load(path)
        if audit.get("schemaVersion")!=1 or not isinstance(audit.get("candidates"),list):continue
        seen_at=audit.get("window",{}).get("to") or audit.get("window",{}).get("completedAt")
        if not seen_at:continue
        rel=str(path.relative_to(root)).replace("\\","/")
        for item in audit["candidates"]:
            status=item.get("status")
            if status not in {"selected","deferred","excluded"}:continue
            candidate={
              "title":item.get("title") or "",
              "arxiv":item.get("arxiv") or "",
              "doi":item.get("doi") or "",
              "status":status,
              "reason":item.get("reason") or "legacy discovery audit",
            }
            _merge_queue_row(queue,candidate,seen_at,len(set(item.get("sources") or [])),rel)
    for path,audit,_ in audits:
        seen_at=audit["window"]["to"];rel=str(path.relative_to(root)).replace("\\","/")
        for item in audit["candidates"]:
            _merge_queue_row(queue,item,seen_at,len(set(item["sourceIds"])),rel)
    return queue

def next_window(state,policy,to_value):
    last=day(state["lastSuccessfulSearchAt"]) if state.get("lastSuccessfulSearchAt") else day(policy["baselineSuccessfulThrough"])
    start=last-timedelta(days=policy["defaultLookbackDays"])
    end=day(to_value)
    require(end>=last,"next discovery window cannot end before last successful checkpoint")
    return start.isoformat(),end.isoformat()

def validate_repository(root=ROOT):
    root=Path(root);policy=load_policy(root);state=load(root/STATE_PATH)
    require(state.get("schemaVersion")==1,"maintenance state schema")
    last=state.get("lastSuccessfulSearchAt");day(last) if last else None
    baseline=policy["baselineSuccessfulThrough"]
    audits=list_v2_audits(root,policy)
    complete=[x for x in audits if x[2]["complete"]]
    if last and last>baseline:
        ref=state.get("lastCompleteDiscoveryAudit")
        require(isinstance(ref,str) and ref,"checkpoint beyond rollout baseline needs lastCompleteDiscoveryAudit")
        path=root/ref;require(path.exists(),"lastCompleteDiscoveryAudit missing")
        audit=load(path);report=validate_audit(audit,policy)
        require(report["complete"],"state references incomplete discovery audit")
        require(audit["window"]["to"]==last,"state checkpoint must equal referenced audit window")
        require(state.get("discoveryPolicyVersion")==policy["schemaVersion"],"discovery policy version missing/stale")
    if complete:
        latest=max(complete,key=lambda x:x[1]["window"]["to"])
        require(not last or last>=latest[1]["window"]["to"],"complete discovery audit was not reflected in state checkpoint")
    queue=aggregate_candidates(root,audits)
    counts={k:0 for k in policy["candidateStatuses"]}
    for row in queue.values():counts[row["status"]]+=1
    return {"audits":len(audits),"completeAudits":len(complete),"candidateQueue":counts,"lastSuccessfulSearchAt":last}

def apply_audit(root,path):
    root=Path(root);policy=load_policy(root);path=Path(path)
    if not path.is_absolute():path=root/path
    expected=(root/AUDIT_DIR).resolve()
    require(path.resolve().parent==expected,"audit must live under maintenance/audits/discovery")
    audit=load(path);report=validate_audit(audit,policy)
    state_path=root/STATE_PATH;state=load(state_path)
    state["lastAttemptAt"]=audit["window"]["attemptedAt"]
    state["discoveryPolicyVersion"]=policy["schemaVersion"]
    state["lastDiscoveryAudit"]=str(path.relative_to(root)).replace("\\","/")
    if report["complete"]:
        current=state.get("lastSuccessfulSearchAt")
        require(not current or audit["window"]["to"]>=current,"refusing to move successful discovery checkpoint backward")
        state["lastSuccessfulSearchAt"]=audit["window"]["to"]
        state["lastCompleteDiscoveryAudit"]=str(path.relative_to(root)).replace("\\","/")
        state["lastStatus"]="success"
        state["lastSummary"]=(
            f"完整文献发现窗口 {audit['window']['from']}—{audit['window']['to']} 已通过多来源覆盖门禁；"
            f"{report['counts']['total']} candidates，selected {report['counts']['selected']}，"
            f"deferred {report['counts']['deferred']}，excluded {report['counts']['excluded']}，"
            f"duplicate {report['counts']['duplicate']}。"
        )
    else:
        state["lastStatus"]="partial"
        state["lastSummary"]=(
            f"文献发现窗口 {audit['window']['from']}—{audit['window']['to']} 仅部分完成；"
            "至少一个必需 discovery lane 未完整覆盖，因此 lastSuccessfulSearchAt 未推进。"
        )
    write(state_path,state);return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=ROOT)
    sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("plan");p.add_argument("--to",required=True)
    v=sub.add_parser("validate");v.add_argument("audit")
    a=sub.add_parser("apply");a.add_argument("audit")
    sub.add_parser("status")
    args=ap.parse_args()
    root=args.root
    if args.cmd=="plan":
        policy=load_policy(root);state=load(root/STATE_PATH);start,end=next_window(state,policy,args.to)
        print(json.dumps({"from":start,"to":end,"requiredLanes":[x["id"] for x in policy["requiredLanes"]]},ensure_ascii=False,indent=2))
    elif args.cmd=="validate":
        policy=load_policy(root);audit=load(root/args.audit);print(json.dumps(validate_audit(audit,policy),ensure_ascii=False,indent=2))
    elif args.cmd=="apply":
        print(json.dumps(apply_audit(root,args.audit),ensure_ascii=False,indent=2))
    else:
        print(json.dumps(validate_repository(root),ensure_ascii=False,indent=2))

if __name__=="__main__":main()
