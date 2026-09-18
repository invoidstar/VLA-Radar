"""Recover source-linked notes from an immutable commit in this public repository.
Never change paper metadata, first-public dates, or existing result rows.
"""
from pathlib import Path
import json, subprocess, argparse
PIN = '0f8d8938457f169bcb4a92da9c3df89f1945d3aa'
PRESERVE = {'p051','p055','p056','p061','p067','p068'}
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(root,retained=None):
    marker=root/'maintenance/library-recovery.json'
    if marker.exists(): print('Recovery already committed; canonical records remain authoritative.');return
    def get(path):
        return (retained/path).read_text(encoding='utf-8') if retained else subprocess.check_output(['git','show',PIN+':'+path],cwd=root,text=True)
    records={p.stem:read(p) for p in (root/'catalog/papers').glob('*.json')}
    before={pid:rec['paper'] for pid,rec in records.items()}
    results={p.name:p.read_bytes() for p in (root/'catalog/results').glob('*.json')}
    adopted=[]
    for pid in sorted(records):
        if int(pid[1:])>42:continue
        prior=json.loads(get('catalog/papers/'+pid+'.json'));n=prior['note']
        if n.get('coverage',{}).get('level')!='deep':continue
        if pid in {'p006','p041','p042'}:n['figures']=[]
        records[pid]['note']=n;write(root/'catalog/papers'/f'{pid}.json',records[pid]);adopted.append(pid)
    for pid in PRESERVE:
        n=records[pid]['note'];n['coverage']={'level':'deep','scope':'primary-methods-experiments','source':n['sections'][0]['sources'][0]['url']}
        n.setdefault('figures',[]);n.setdefault('tables',[])
        write(root/'catalog/papers'/f'{pid}.json',records[pid])
    for name in ['scripts/note_quality.py','scripts/catalog_core.py','research.js','research.css','scripts/test_research.cjs']:
        (root/name).write_text(get(name),encoding='utf-8')
    p=root/'scripts/note_quality.py';s=p.read_text();s=s.replace("require(cov['level'] == 'deep' and cov['scope'] in SCOPES, 'note coverage level/scope')", "require(cov['level'] in {'deep','limited'} and cov['scope'] in SCOPES, 'note coverage level/scope')\n        require((cov['level']=='limited') == (cov['scope']=='official-abstract-only'), 'abstract-only cannot be promoted to full-source notes')")
    s=s.replace("require(len(note['sections']) >= 8, 'deep notes need eight substantive sections')", "require(len(note['sections']) >= (8 if cov['level']=='deep' else 3), 'source-scoped section count')")
    s=s.replace("require(sum(len(s['body']) for s in note['sections']) >= 1200, 'deep note is too short')", "require(sum(len(s['body']) for s in note['sections']) >= (1200 if cov['level']=='deep' else 300), 'source-scoped note is too short')")
    s=s.replace("len(s['body']) >= 90", "len(s['body']) >= (90 if cov['level']=='deep' else 40)");p.write_text(s)
    p=root/'scripts/catalog_core.py';s=p.read_text().replace('from pathlib import Path','from pathlib import Path\nfrom zoneinfo import ZoneInfo')
    s=s.replace('def today(): return datetime.now(timezone.utc).date().isoformat()',"def today(at=None):\n    now=at if at is not None else datetime.now(timezone.utc)\n    if now.tzinfo is None: raise ValueError('Editorial clock must be timezone-aware')\n    return now.astimezone(ZoneInfo('Asia/Singapore')).date().isoformat()")
    p.write_text(s)
    p=root/'research.js';s=p.read_text()
    helper='''  function datasetNames(data){return benchmarkFamilies(data);}
  function formatScore(value,unit){return metricValue(value,unit);}
  function noteBlocks(text){
    return String(text||'').split(/\\n\\s*\\n/).filter(Boolean).map(block=>{
      const lines=block.trim().split('\\n');
      if(lines.length>2&&lines.every(x=>x.trim().startsWith('|')&&x.trim().endsWith('|'))&&/^\\|[\\s:|\\-]+\\|$/.test(lines[1].trim())){
        const cells=x=>x.trim().slice(1,-1).split('|').map(x=>x.trim());
        const head=cells(lines[0]),rows=lines.slice(2).map(cells);
        if(rows.every(r=>r.length===head.length))return '<div class="board-table-scroll"><table class="board-table note-data-table"><thead><tr>'+head.map(c=>'<th>'+esc(c)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(c=>'<td>'+esc(c)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
      }
      return para(block);
    }).join('');
  }
'''
    s=s.replace('  async function enhance(p,root){',helper+'  async function enhance(p,root){').replace('${para(s.body)}','${noteBlocks(s.body)}')
    s=s.replace('metricValue,benchmarkFamilies,richEvidence};','metricValue,benchmarkFamilies,richEvidence,datasetNames,formatScore,noteBlocks};')
    s=s.replace("${note.status==='legacy'?'下面保留原有公开笔记", "${note.coverage?.scope==='official-abstract-only'?'已核读可访问的官方摘要；正文、实验表格和消融仍待取得。以下为有限证据导读，不作为全文结论或榜单数值依据。':note.status==='legacy'?'下面保留原有公开笔记")
    p.write_text(s)
    p=root/'research.css';p.write_text(p.read_text()+'\n.note-data-table{font-size:.85rem}.note-section p{line-height:1.95}.note-section .board-table-scroll{max-width:100%;margin:16px 0}\n')
    for pid in records:assert read(root/'catalog/papers'/f'{pid}.json')['paper']==before[pid],pid
    for name,raw in results.items():assert (root/'catalog/results'/name).read_bytes()==raw,name
    m=read(root/'catalog/manifest.json');m['updatedAt']='2026-09-18';write(root/'catalog/manifest.json',m)
    report={'schemaVersion':1,'recoveredAt':'2026-09-18','retainedCommit':PIN,'recoveredIds':adopted,'preservedCurrentMainDeepIds':sorted(PRESERVE),'paperCount':len(records),'existingResultsPreserved':len(results),'note':'Source-linked retained work recovered, not a fresh literature search or new-version certification.'}
    write(marker,report)
    p=root/'CHANGELOG.md';p.write_text('## 2026-09-18 — 深入笔记恢复批次\n\n从固定保留提交恢复42篇分节原文笔记，保留当前main六篇更详细的动作/空间笔记及全部既有榜单结果。增加来源范围、解释性表格与原图定位展示；不把恢复操作计为全网检索或新版本核验。\n\n'+p.read_text())
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--retained',type=Path);a=ap.parse_args();run(a.root,a.retained)
