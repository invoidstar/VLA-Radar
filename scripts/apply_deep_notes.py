"""Import explicitly authored public notes, preserving all original paper facts.

Input files contain original summaries, not downloaded paper bodies. A successful
schema check is not scientific verification. The final catalog is the source of
truth; input batches may be removed after a release.
"""
from __future__ import annotations
import argparse, re
from pathlib import Path
from catalog_core import load, write, today, read_catalog
from note_quality import install as install_schema
from install_reading_ui import install as install_ui


def apply(root: Path, inputs: Path):
    install_schema(root); install_ui(root)
    when=today();seen=set();changed=[]
    results=[load(p) for p in (root/'catalog/results').glob('*.json')]
    for path in sorted(inputs.glob('batch-*.json')):
        batch=load(path)
        if not isinstance(batch,list):raise ValueError('note batch must be a list')
        for x in batch:
            pid=x['id']
            if not re.fullmatch(r'p\d{3,}',pid) or pid in seen:raise ValueError('invalid or repeated staged paper: '+pid)
            seen.add(pid);target=root/'catalog/papers'/f'{pid}.json';rec=load(target)
            if rec['paper']['id']!=pid:raise ValueError('ID mismatch')
            status='expanded'
            readver=re.search(r'v(\d+)(?:$|[#?])',x['source'])
            latest=rec['publication']['latestArxivVersion']
            if readver and latest and int(latest[1:])>int(readver[1]):status='needs_review'
            n={'status':status,'updatedAt':when,'verifiedAt':when,'version':x['version'],
               'sections':[{'id':s['id'],'title':s['title'],'body':s['body'],'sources':[{'label':s['locator']+' · 指定版本原文','url':x['source']}]} for s in x['sections']],
               'coverage':{'level':'deep','scope':x['scope'],'source':x['source']},'figures':x.get('figures',[]),'tables':x.get('tables',[])}
            oldreview=rec['note'].get('benchmarkReview')
            count=sum(r['paperId']==pid and r['evidence']=='checked' for r in results)
            if oldreview and oldreview['status']!='pending':n['benchmarkReview']=oldreview
            elif x['scope']=='primary-theory':n['benchmarkReview']={'status':'not-applicable','checkedAt':when,'note':'理论能力与识别条件分析，无可填入机器人任务榜的实验成功率；构造例子的遗憾界不是基准分数。'}
            elif count:n['benchmarkReview']={'status':'extracted','checkedAt':when,'note':f'已有{count}条带原文定位的评测记录。不同预算、子集和单位分开；该计数不表示已穷尽论文全部结果。'}
            else:n['benchmarkReview']={'status':'pending','checkedAt':None,'note':'深入笔记已整理；标准基准结果仍需逐表核对任务集合、预算与指标，再加入对应赛道。缺失记录不按零分处理。'}
            # Stable input never silently upgrades legacy paper.evidence or publication status.
            old=rec['note']
            if {k:v for k,v in old.items() if k not in {'updatedAt','verifiedAt'}} == {k:v for k,v in n.items() if k not in {'updatedAt','verifiedAt'}}:
                n['updatedAt']=old['updatedAt'];n['verifiedAt']=old['verifiedAt']
            if old!=n:rec['note']=n;write(target,rec);changed.append(pid)
    m,records,tracks,results=read_catalog(root)
    if changed:m['updatedAt']=when;write(root/'catalog/manifest.json',m)
    deep=[r for r in records if r['note'].get('coverage',{}).get('level')=='deep']
    limited=[r['paper']['id'] for r in deep if r['note']['coverage']['scope']=='official-abstract-only']
    report={'schemaVersion':1,'checkedAt':when,'totalPapers':len(records),'deepNotes':len(deep),'fullMethodOrTheoryOrReportNotes':len(deep)-len(limited),'abstractOnlyNotes':limited,
            'remainingIds':[r['paper']['id'] for r in records if r['note'].get('coverage',{}).get('level')!='deep'],
            'noteSections':sum(len(r['note']['sections']) for r in deep),'noteFigures':sum(len(r['note'].get('figures',[])) for r in deep),'noteTables':sum(len(r['note'].get('tables',[])) for r in deep),
            'benchmarkFamilies':len({t['dataset'] for t in tracks}),'benchmarkTracks':len(tracks),'checkedResultRecords':sum(r['evidence']=='checked' for r in results),
            'statement':'Counts concern imported, source-linked reading content. Validation checks structure only. Abstract-only entries are not full-paper certification; lifecycle and discovery checkpoints are independent.'}
    write(root/'maintenance/deep-notes-progress.json',report)
    print('Applied changes:',changed);print(report)
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--input',type=Path)
    a=ap.parse_args();apply(a.root,a.input or a.root/'maintenance/release-notes')
