"""Idempotent, narrowly-scoped upgrade for dataset navigation and sourced note tables."""
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'scripts/build/catalog_core.py';s=p.read_text();old="require(t['dataset'] in {'LIBERO','RoboTwin','RoboCasa'},'supported dataset family')";new="require(isinstance(t['dataset'],str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9 +._-]{1,50}',t['dataset']),'invalid dataset family')"
if old in s:p.write_text(s.replace(old,new),encoding='utf-8')
p=R/'site/js/features/research/research.js';s=p.read_text()
if 'function datasetNames' not in s:
    s=s.replace("let dataset=['LIBERO','RoboTwin','RoboCasa'].includes(query.get('dataset'))?query.get('dataset'):'LIBERO';","const datasets=datasetNames(data);let dataset=datasets.includes(query.get('dataset'))?query.get('dataset'):(datasets[0]||'');")
    s=s.replace("${['LIBERO','RoboTwin','RoboCasa'].map(d=>`<button data-dataset=\"${d}\" aria-pressed=\"${d===dataset}\">${d}</button>`)","${datasets.map(d=>`<button data-dataset=\"${esc(d)}\" aria-pressed=\"${d===dataset}\">${esc(d)}</button>`)")
    s=s.replace("${v==null?'—':esc(v)+'%'}","${esc(formatScore(v,b.tracks.find(t=>t.id===row.trackId)?.unit))}")
    s=s.replace('${para(s.body)}${links(s.sources)}','${noteBlocks(s.body)}${links(s.sources)}')
    helper=r'''  function datasetNames(data){return [...new Set(data.tracks.map(t=>t.dataset))];}
  function formatScore(value,unit){return value==null?'—':String(value)+(unit==='percent'?'%':unit==='seconds'?' s':'');}
  function noteBlocks(text){
    return String(text||'').split(/\n\s*\n/).filter(Boolean).map(block=>{
      const lines=block.trim().split('\n');
      if(lines.length>2&&lines.every(x=>x.trim().startsWith('|')&&x.trim().endsWith('|'))&&/^\|[\s:|\-]+\|$/.test(lines[1].trim())){
        const cells=x=>x.trim().slice(1,-1).split('|').map(x=>x.trim());
        const head=cells(lines[0]),rows=lines.slice(2).map(cells);
        if(rows.every(r=>r.length===head.length))return '<div class="board-table-scroll"><table class="board-table note-data-table"><thead><tr>'+head.map(c=>'<th>'+esc(c)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(c=>'<td>'+esc(c)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
      }
      return para(block);
    }).join('');
  }
'''
    s=s.replace('  const date =',helper+'  const date =').replace('enhance,renderBoards,pageWindow,rankRows,visibleResults','enhance,renderBoards,pageWindow,rankRows,visibleResults,datasetNames,formatScore,noteBlocks')
    assert 'const datasets=datasetNames(data)' in s and '${datasets.map' in s
    assert "esc(v)+'%'" not in s
    p.write_text(s,encoding='utf-8')
p=R/'site/styles/features/research.css';s=p.read_text();marker='/* Expanded benchmark navigation and evidence tables */'
if marker not in s:p.write_text(s+'\n'+marker+'\n.dataset-tabs{flex-wrap:wrap}.note-data-table{font-size:.85rem}.note-section p{line-height:1.85}.note-section .board-table-scroll{max-width:100%;margin:16px 0}.note-section>div{min-width:0}\n',encoding='utf-8')
p=R/'scripts/validate/validate_all.py';s=p.read_text()
if 'test_content.cjs' not in s:p.write_text(s.replace("['node','tests/node/test_research.cjs']]","['node','tests/node/test_research.cjs'],['node','tests/node/test_content.cjs']]"),encoding='utf-8')
print('Dataset navigation, metric units and escaped note tables ready')
