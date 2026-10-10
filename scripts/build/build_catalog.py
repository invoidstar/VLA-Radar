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

def curated_benchmark(root, tracks, results):
    """Keep ablation evidence in canonical records; publish independent-method comparisons."""
    registry=json.loads((Path(root)/'catalog/benchmark-method-curation.json').read_text(encoding='utf-8'))
    expected={'schemaVersion','scope','excludedDatasets','excludedTracks','excludedResults','methodLabels'}
    if registry.get('schemaVersion')!=1 or set(registry)!=expected:
        raise ValueError('Benchmark method curation has an unexpected schema')
    blocked_datasets=registry['excludedDatasets']
    blocked_tracks=registry['excludedTracks'];blocked_results=registry['excludedResults'];labels=registry['methodLabels']
    if not all(isinstance(v,list) and all(isinstance(x,str) for x in v)
               for v in (blocked_datasets,blocked_tracks,blocked_results)) or not isinstance(labels,dict):
        raise ValueError('Benchmark curation requires dataset/track/result ID lists and labels')
    trackmap={t['id']:t for t in tracks};resultmap={r['id']:r for r in results}
    known_datasets={t['dataset'] for t in tracks};known_results=set(resultmap)
    if (any(len(items)!=len(set(items)) for items in (blocked_datasets,blocked_tracks,blocked_results))
            or set(blocked_datasets)-known_datasets or set(blocked_tracks)-set(trackmap)
            or set(blocked_results)-known_results or set(labels)-known_results):
        raise ValueError('Stale or duplicated Benchmark curation identity')
    blocked_d=set(blocked_datasets);blocked_t=set(blocked_tracks);blocked_r=set(blocked_results)
    # A hidden dataset may already have per-row ablations excluded. Keep
    # those existing curation decisions for any future re-admission.
    if any(r['trackId'] in blocked_t for r in results if r['id'] in blocked_r):
        raise ValueError('Track and row exclusions must not overlap')
    if any(rid in blocked_r or resultmap[rid]['trackId'] in blocked_t for rid in labels):
        raise ValueError('Benchmark canonical label must refer to a retained row')
    if any(not isinstance(s,str) or not s.strip() for s in labels.values()):
        raise ValueError('Benchmark canonical labels must be nonempty text')
    # An isolated paper-specific evaluation should be reconsidered once another
    # reporting paper supplies independently checked results for that dataset.
    for dataset in blocked_d:
        reporting={r['paperId'] for r in results
                   if r['evidence']=='checked' and trackmap[r['trackId']]['dataset']==dataset}
        if len(reporting)>1:
            raise ValueError('Re-review now-shared Benchmark before excluding: '+dataset)
    display=[]
    for row in results:
        if row['id'] in blocked_r or row['trackId'] in blocked_t or trackmap[row['trackId']]['dataset'] in blocked_d:
            continue
        if row['id'] not in labels:
            display.append(row)
            continue
        copy=dict(row)
        copy['method']=labels[row['id']]
        copy['evaluationNotes']='原表 Method / 配置：'+row['method']+'。'+copy['evaluationNotes']
        display.append(copy)
    active={r['trackId'] for r in display}
    curated_tracks=[t for t in tracks if t['id'] in active]
    audited_papers={r['paperId'] for r in results if r['evidence']=='checked'}
    comparison_papers={r['paperId'] for r in display if r['evidence']=='checked'}
    if not comparison_papers<=audited_papers:
        raise ValueError('Benchmark comparison references an unaudited paper')
    # Some papers have only internal experiments; their original checked rows
    # remain in catalog/results and hashed per-paper evidence archives.
    return curated_tracks,display


def outputs(root):
    m,records,tracks,results=read_catalog(root)
    comparison_tracks,comparison_results=curated_benchmark(root,tracks,results)
    full_taxonomy=load_taxonomy(root,tracks)  # full catalog stays academically auditable
    visible_datasets={t['dataset'] for t in comparison_tracks}
    taxonomy={**full_taxonomy,'benchmarks':{
        name:item for name,item in full_taxonomy['benchmarks'].items() if name in visible_datasets
    }}
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
    bytrack={t['id']:[] for t in comparison_tracks};bypaper={r['paper']['id']:[] for r in records}
    for row in results:bypaper[row['paperId']].append(row)
    for row in comparison_results:bytrack[row['trackId']].append(row)
    indexed_tracks=[]
    for t in comparison_tracks:
        rows=bytrack[t['id']]
        path=hashed(f'data/boards/{t["id"]}',{'schemaVersion':1,'trackId':t['id'],'results':rows},out)
        indexed_tracks.append({**t,'resultUrl':path,'resultCount':len(rows)})
    setting_records=build_settings(comparison_tracks,comparison_results)
    trackmap={t['id']:t for t in comparison_tracks};resultmap={r['id']:r for r in comparison_results};indexed_settings=[]
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
    boardurl=hashed('data/board-index',{'schemaVersion':1,'updatedAt':m['updatedAt'],'tracks':indexed_tracks,'settings':indexed_settings,'taxonomy':taxonomy,'resultCount':len(comparison_results),'settingCount':len(indexed_settings)},out)
    # Coverage and follow/navigation use the same public comparison universe.
    # Canonical Result Reports and paper-detail evidence above remain complete.
    experience,indexurl=experience_outputs(root,records,comparison_tracks,comparison_results);out.update(experience)
    news,newsurl=news_outputs(root,records);out.update(news)
    tools,toolsurl=tools_outputs(root,records,comparison_tracks,comparison_results,experience,indexurl);out.update(tools)
    out['data/library.json']=compact({'schemaVersion':1,**meta,'searchUrl':searchurl,'boardIndexUrl':boardurl,'experienceUrl':indexurl,'newsUrl':newsurl,'toolsUrl':toolsurl,'papers':light})
    out['data/leaderboards.json']=dumps({'schemaVersion':1,'updatedAt':m['updatedAt'],'tracks':comparison_tracks,'settings':setting_records,'taxonomy':taxonomy,'results':comparison_results})
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
