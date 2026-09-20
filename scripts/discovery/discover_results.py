"""Discover potential benchmark tables automatically; never invent a protocol or rank.
For newly read papers use --paper and the public HTML already retrieved by the agent.
All recognized tables, including ambiguous ones, remain a review queue, not leaderboard data.
"""
from __future__ import annotations
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import argparse, html as html_module, re
from pathlib import Path
from catalog_core import load, today, write
from extract_results import Tables, number
from http_public import fetch
ALIASES={'Clean':'clean','Random':'random','Spatial':'spatial','Object':'object','Goal':'goal','Long':'long','Average':'average','Average SR':'average','Avg.':'average','Overall':'average','Success Rate':'success'}
def discover(text,paper_id,source,version):
    parser=Tables();parser.feed(text);starts=list(re.finditer(r'<table\b',text,re.I));found=[]
    for i,t in enumerate(parser.tables):
        if not t['rows']:continue
        start=starts[i].start() if i<len(starts) else 0
        context=html_module.unescape(re.sub(r'<[^>]+>',' ',text[max(0,start-2500):start+1500]));context=' '.join(context.split())
        families=[name for name in ['RoboTwin','RoboCasa','LIBERO'] if name.lower() in context.lower()]
        header_idx=None;columns={}
        for j,row in enumerate(t['rows'][:5]):
            mapping={}
            for pos,cell in enumerate(row):
                c=cell.lower().replace('(%)','').strip()
                for alias,normalized in ALIASES.items():
                    if c==alias.lower():mapping[normalized]=pos;break
            if mapping:header_idx=j;columns=mapping;break
        if not columns or not families:continue
        candidates=[]
        for row in t['rows'][header_idx+1:]:
            if len(row)<=max(columns.values()) or not row[0]:continue
            try:values={k:number(row[pos]) for k,pos in columns.items()}
            except ValueError:continue
            if any(v is not None and 0<=v<=100 for v in values.values()):candidates.append({'methodCell':row[0],'values':values})
        found.append({'tableIndex':i,'tableId':t['id'],'possibleDatasets':families,'columns':columns,'mergedCells':t['merged'],'rows':candidates,
                      'protocolStatus':'unresolved','evidence':'candidate','context':context[:600]})
    return {'schemaVersion':1,'extractedAt':today(),'paperId':paper_id,'source':source,'sourceVersion':version,'tables':found,
            'reviewRequired':True,'note':'Dataset detection uses surrounding text, not proof of protocol identity. Check caption/header/units, original vs quoted results, training/evaluation, then use extract_results.py or structured evidence to add result files.'}
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--paper',required=True);ap.add_argument('--source',required=True);ap.add_argument('--version',required=True);ap.add_argument('--html',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    text=a.html.read_text(encoding='utf-8') if a.html else fetch(a.source)[0];report=discover(text,a.paper,a.source,a.version);write(a.output,report);print(f'{len(report["tables"])} potential benchmark tables; none auto-ranked.')
