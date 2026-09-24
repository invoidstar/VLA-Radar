"""Deterministic static catalog: compact bootstrap, hashed details and per-track results."""
from __future__ import annotations
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import argparse,hashlib,json
from pathlib import Path
from catalog_core import dumps,read_catalog,load_resources
from paper_relations import load_relations,build_relation_views
from reproducibility import load_reproducibility,build_reproducibility_views
from benchmark_settings import build_settings
from benchmark_taxonomy import load_taxonomy
from experience_build import outputs as experience_outputs
from news_core import outputs as news_outputs
from tools_build import outputs as tools_outputs

def compact(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n'
def hashed(prefix,obj,out):
    text=compact(obj);digest=hashlib.sha256(text.encode()).hexdigest()[:16]
    path=f'{prefix}.{digest}.json';out[path]=text;return path

def outputs(root):
    m,records,tracks,results=read_catalog(root)
    taxonomy=load_taxonomy(root,tracks)
    paper_ids={r['paper']['id'] for r in records}
    resources=load_resources(root,paper_ids)
    relations=load_relations(root,paper_ids)
    relation_views=build_relation_views(records,relations)
    reproducibility=load_reproducibility(root,paper_ids,resources)
    reproducibility_views=build_reproducibility_views(m['paperOrder'],resources,reproducibility)
    meta={k:m[k] for k in ('updatedAt','title','collection','description','topics')}
    legacy={'schemaVersion':1,**meta,'papers':[r['paper'] for r in records]}
    out={'data/papers.json':dumps(legacy)};summaries=[];light=[]
    cardkeys={'id','name','title','team','venue','firstPublished','collectionMonth','topics','tags','priority','hasCautionaryResult','findings','versionNote','arxiv','doi','paperUrl'}
    superseded={x['supersedes'] for x in results if x['evidence']=='checked' and x['supersedes']}
    bytrack={t['id']:[] for t in tracks};bypaper={r['paper']['id']:[] for r in records}
    for row in results:bytrack[row['trackId']].append(row);bypaper[row['paperId']].append(row)
    indexed_tracks=[]
    for t in tracks:
        rows=bytrack[t['id']]
        path=hashed(f'data/boards/{t["id"]}',{'schemaVersion':1,'trackId':t['id'],'results':rows},out)
        indexed_tracks.append({**t,'resultUrl':path,'resultCount':len(rows)})
    setting_records=build_settings(tracks,results)
    trackmap={t['id']:t for t in tracks};resultmap={r['id']:r for r in results};indexed_settings=[]
    for setting in setting_records:
        setting_tracks=[trackmap[tid] for tid in setting['trackIds']]
        setting_rows=[resultmap[rid] for rid in setting['resultIds']]
        shard_setting={k:v for k,v in setting.items() if k!='resultIds'}
        path=hashed(f'data/settings/{setting["id"]}',{'schemaVersion':1,'settingId':setting['id'],'setting':shard_setting,'tracks':setting_tracks,'results':setting_rows},out)
        public={k:v for k,v in setting.items() if k not in {'resultIds','trainingByResult'}}
        indexed_settings.append({**public,'resultUrl':path})
    for r in records:
        p=r['paper'];out[f'data/details/{p["id"]}.json']=dumps(r) # stable public compatibility URL
        detail=hashed(f'data/details/{p["id"]}',r,out)
        paperresults=bypaper[p['id']]
        tids={x['trackId'] for x in paperresults}
        result=hashed(f'data/paper-results/{p["id"]}',{'schemaVersion':1,'paperId':p['id'],'tracks':[t for t in tracks if t['id'] in tids],'results':paperresults,'supersededIds':[x['id'] for x in paperresults if x['id'] in superseded]},out) if paperresults else None
        repro_url=None
        if p['id'] in reproducibility:
            repro_url=f'data/reproducibility/{p["id"]}.json'
            out[repro_url]=compact({'schemaVersion':1,'paperId':p['id'],**reproducibility_views[p['id']]})
        extra={'detailUrl':detail,'resultUrl':result,'noteStatus':r['note']['status'],'resources':resources.get(p['id'],{}),
               'relations':relation_views[p['id']],'reproducibilityUrl':repro_url,
               'lifecycle':{k:r['publication'][k] for k in ('firstArxivAt','latestArxivVersion','status','lastCheckedAt')}}
        summaries.append({**p,**extra,'detailUrl':f'data/details/{p["id"]}.json?v={hashlib.sha256(dumps(r).encode()).hexdigest()[:16]}'});light.append({**{k:p[k] for k in sorted(cardkeys)},**extra})
    out['data/catalog.json']=dumps({'schemaVersion':1,**meta,'papers':summaries}) # old integrations
    searchkeys={'id','name','title','team','tags','topics','contribution','findings','insight','limitations','venue','publicationStatus','arxiv','firstPublished'}
    searchurl=hashed('data/search-index',{'schemaVersion':1,'topics':m['topics'],'papers':[{k:r['paper'][k] for k in sorted(searchkeys)} for r in records]},out)
    boardurl=hashed('data/board-index',{'schemaVersion':1,'updatedAt':m['updatedAt'],'tracks':indexed_tracks,'settings':indexed_settings,'taxonomy':taxonomy,'resultCount':len(results),'settingCount':len(indexed_settings)},out)
    experience,indexurl=experience_outputs(root,records,tracks,results);out.update(experience)
    news,newsurl=news_outputs(root,records);out.update(news)
    tools,toolsurl=tools_outputs(root,records,tracks,results,experience,indexurl);out.update(tools)
    out['data/library.json']=compact({'schemaVersion':1,**meta,'searchUrl':searchurl,'boardIndexUrl':boardurl,'experienceUrl':indexurl,'newsUrl':newsurl,'toolsUrl':toolsurl,'papers':light})
    out['data/leaderboards.json']=dumps({'schemaVersion':1,'updatedAt':m['updatedAt'],'tracks':tracks,'settings':setting_records,'taxonomy':taxonomy,'results':results})
    return out

def build(root,check=False):
    root=Path(root);generated=outputs(root);stale=[]
    for path,text in generated.items():
        f=root/path
        if not f.exists() or f.read_text(encoding='utf-8')!=text:
            stale.append(path)
            if not check:f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text,encoding='utf-8')
    patterns=['data/tools/*.json','data/news/*.json','data/experience/*.json','data/details/p*.json','data/boards/*.json','data/settings/*.json','data/paper-results/*.json','data/reproducibility/*.json','data/search-index.*.json','data/board-index.*.json']
    for pattern in patterns:
        for p in root.glob(pattern):
            if str(p.relative_to(root)) not in generated:
                stale.append(str(p.relative_to(root)))
                if not check:p.unlink()
    if check and stale:raise ValueError('Generated files are stale: '+', '.join(stale[:12]))
    print(f'PASS: {len(generated)} deterministic files; lightweight bootstrap, content-hashed details and per-track/per-setting shards.')
    return generated
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);ap.add_argument('--check',action='store_true');a=ap.parse_args();build(a.root,a.check)
