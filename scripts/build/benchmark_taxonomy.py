"""Benchmark-level taxonomy loader and invariants."""
from __future__ import annotations
import json,re
from pathlib import Path

SLUG=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

def load_taxonomy(root,tracks):
    root=Path(root)
    data=json.loads((root/'catalog/benchmark-taxonomy.json').read_text(encoding='utf-8'))
    if data.get('schemaVersion')!=1:raise ValueError('benchmark taxonomy schemaVersion must be 1')
    focuses=data.get('focuses');envs=data.get('environments');tags=data.get('tags');bench=data.get('benchmarks')
    if not isinstance(focuses,list) or not focuses:raise ValueError('taxonomy focuses required')
    if not isinstance(envs,list) or not envs:raise ValueError('taxonomy environments required')
    if not isinstance(tags,list):raise ValueError('taxonomy tags required')
    if not isinstance(bench,dict):raise ValueError('taxonomy benchmarks required')
    def registry(items,name):
        ids=[]
        for item in items:
            if set(item)-{'id','label','description'}:raise ValueError(f'unknown {name} fields')
            if not isinstance(item.get('id'),str) or not SLUG.fullmatch(item['id']):raise ValueError(f'invalid {name} id')
            if not isinstance(item.get('label'),str) or not item['label'].strip():raise ValueError(f'{name} label required')
            if 'description' in item and (not isinstance(item['description'],str) or not item['description'].strip()):raise ValueError(f'{name} description')
            ids.append(item['id'])
        if len(ids)!=len(set(ids)):raise ValueError(f'duplicate {name} id')
        return set(ids)
    focus_ids=registry(focuses,'focus');env_ids=registry(envs,'environment');tag_ids=registry(tags,'tag')
    datasets={t['dataset'] for t in tracks}
    if set(bench)!=datasets:
        missing=sorted(datasets-set(bench));extra=sorted(set(bench)-datasets)
        raise ValueError(f'taxonomy coverage mismatch missing={missing} extra={extra}')
    for dataset,item in bench.items():
        if set(item)!={'focus','environment','tags'}:raise ValueError(f'{dataset}: taxonomy assignment fields')
        if item['focus'] not in focus_ids:raise ValueError(f'{dataset}: unknown focus')
        if item['environment'] not in env_ids:raise ValueError(f'{dataset}: unknown environment')
        if not isinstance(item['tags'],list):raise ValueError(f'{dataset}: tags list required')
        if len(item['tags'])!=len(set(item['tags'])):raise ValueError(f'{dataset}: duplicate tags')
        unknown=set(item['tags'])-tag_ids
        if unknown:raise ValueError(f'{dataset}: unknown tags {sorted(unknown)}')
    return data
