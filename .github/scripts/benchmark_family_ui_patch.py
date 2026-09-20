from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def replace_once(path,old,new):
    p=ROOT/path
    s=p.read_text(encoding='utf-8')
    if old not in s:
        raise RuntimeError(f'anchor missing in {path}: {old[:80]!r}')
    if s.count(old)!=1:
        raise RuntimeError(f'anchor not unique in {path}')
    p.write_text(s.replace(old,new),encoding='utf-8')

research=ROOT/'site/js/features/research/research.js'
s=research.read_text(encoding='utf-8')
anchor='''  function boardGroups(tracks,papers=[]){
    const names=new Map();
    for(const p of papers){
      if(p.arxiv)names.set('arxiv:'+p.arxiv.replace(/v\\d+$/,''),p.name||p.title||p.id);
      if(p.doi)names.set('doi:'+p.doi.toLowerCase(),p.name||p.title||p.id);
      const key=sourceKey(p.paperUrl);if(key)names.set(key,p.name||p.title||p.id);
    }
    const grouped=new Map();
    for(const t of tracks){
      const key=JSON.stringify([t.dataset,sourceKey(t.source)||'track:'+t.id]);
      if(!grouped.has(key))grouped.set(key,{id:key,tracks:[],label:''});
      grouped.get(key).tracks.push(t);
    }
    return [...grouped.values()].map(g=>{
      const t=g.tracks[0],name=names.get(sourceKey(t.source));
      const short=String(t.name||t.id).split(/\\s*[·｜|]\\s*/)[0];
      g.label=name||short;g.kind=g.tracks.every(t=>t.comparisonScope==='protocol')?'协议内结果':g.tracks.every(t=>t.comparisonScope==='paper-table')?'原文证据':'多类证据';
      return g;
    });
  }
'''
helpers='''  function protocolGroups(tracks,papers=[]){
    const explicit=new Map(),loose=[];
    for(const t of tracks){
      if(!t.familyId){loose.push(t);continue;}
      if(!explicit.has(t.familyId))explicit.set(t.familyId,{
        id:t.familyId,label:t.familyName,summary:t.familySummary,kind:t.familyKind,
        mode:t.familyMode,primaryTrackId:t.familyPrimaryTrackId,explicit:true,tracks:[]
      });
      explicit.get(t.familyId).tracks.push(t);
    }
    const fallback=boardGroups(loose,papers).map(g=>({...g,explicit:false,summary:'尚未整理为协议族；当前仍按来源组织，具体成绩保持 track-scoped。',mode:'source',primaryTrackId:g.tracks[0]?.id||''}));
    return [...explicit.values(),...fallback];
  }
  function methodKey(value){return String(value||'').normalize('NFKC').toLowerCase().replaceAll('π','pi').replace(/[^a-z0-9]+/g,'');}
  function methodGroups(group,loadedTracks){
    const order=new Map(group.tracks.map((t,i)=>[t.id,i])),groups=new Map();
    for(const item of loadedTracks){
      for(const row of visibleResults(item.data,item.track.id)){
        const key=methodKey(row.method)||row.id;
        if(!groups.has(key))groups.set(key,{key,name:row.method,variants:[]});
        groups.get(key).variants.push({track:item.track,row});
      }
    }
    const out=[...groups.values()];
    for(const item of out){
      item.variants.sort((a,b)=>(order.get(a.track.id)??999)-(order.get(b.track.id)??999)||a.row.id.localeCompare(b.row.id));
      item.primary=item.variants.find(v=>v.track.id===group.primaryTrackId)||item.variants[0];
      item.name=item.primary?.row.method||item.name;
    }
    return out.sort((a,b)=>a.name.localeCompare(b.name,'en',{numeric:true,sensitivity:'base'}));
  }
  function recipeTypeLabel(type){return ({report:'报告 recipe',training:'训练 recipe',subprotocol:'子协议',deployment:'部署变体'})[type]||'recipe';}
  function familyMethodsHtml(group,loadedTracks){
    const methods=methodGroups(group,loadedTracks),primary=group.tracks.find(t=>t.id===group.primaryTrackId)||group.tracks[0];
    const columns=group.mode==='aligned'?(primary?.columns||[]):[];
    const sourceCount=new Set(group.tracks.map(t=>sourceKey(t.source)||t.source)).size;
    const variantCount=methods.reduce((n,m)=>n+m.variants.length,0);
    const badge=group.mode==='aligned'?'评测口径已对齐 · Recipe 可展开':'子协议系列 · 不合并成绩';
    const rule=group.mode==='aligned'
      ?'代表报告优先使用本协议族指定的主 track；若该方法不在主 track 中，则使用该方法在协议族中的第一条来源记录。不会自动挑最高分。'
      :'这些记录的任务子集或部署条件不同。这里只把它们收纳到同一研究系列，不生成跨子协议代表分数、排名或平均值。';
    return `<section class="protocol-family-panel" data-family="${esc(group.id)}"><header class="family-header"><div><span class="note-badge">${esc(badge)}</span><h2>${esc(group.label)}</h2><p>${esc(group.summary)}</p></div><div class="family-stats"><span><b>${methods.length}</b> METHODS</span><span><b>${variantCount}</b> RECIPES</span><span><b>${sourceCount}</b> SOURCES</span></div></header><p class="family-rule">${esc(rule)}</p><div class="family-method-list">${methods.map(m=>{
      const p=m.primary,values=columns.map(col=>`<span><small>${esc(col)}</small><b>${metricValue(p?.row.values[col],p?.track.unit)}</b></span>`).join('');
      return `<article class="family-method"><div class="family-method-main"><div class="family-method-name"><strong>${esc(m.name)}</strong><small>${m.variants.length} ${m.variants.length===1?'reported recipe':'reported recipes'}</small></div>${group.mode==='aligned'?`<div class="family-method-values">${values}</div>`:`<div class="family-series-count"><b>${m.variants.length}</b><span>子协议 / 变体</span></div>`}</div><details class="family-recipes"><summary>展开 ${m.variants.length} 个 ${group.mode==='series'?'子协议 / 变体':'Recipe / Evidence'}</summary><div class="recipe-list">${m.variants.map(v=>`<section class="recipe-item"><div class="recipe-title"><span class="recipe-kind">${esc(recipeTypeLabel(v.track.recipeType))}</span><strong>${esc(v.track.recipeName||v.track.name)}</strong>${v.track.id===group.primaryTrackId&&group.mode==='aligned'?'<em>代表报告</em>':''}</div><div class="recipe-values">${v.track.columns.map(col=>`<span>${esc(col)} <b>${metricValue(v.row.values[col],v.track.unit)}</b></span>`).join('')}</div><p>${esc(v.row.trainingData)}</p><small>${esc(v.row.sourceVersion)} · ${esc(v.row.locator)} · ${esc(v.track.name)}</small><div class="recipe-actions"><button class="board-paper-link" data-paper="${esc(v.row.paperId)}">${esc(v.row.paperId)} · 阅读来源论文 ↗</button>${links([{label:'原始证据',url:v.row.source}])}</div></section>`).join('')}</div></details></article>`;
    }).join('')}</div></section>`;
  }
'''
if anchor not in s: raise RuntimeError('boardGroups anchor missing')
s=s.replace(anchor,anchor+helpers)

s=s.replace(
"const groups=boardGroups(tracks,boardPapers),group=groups.find(g=>g.tracks.some(x=>x.id===trackId));",
"const groups=protocolGroups(tracks,boardPapers),group=groups.find(g=>g.tracks.some(x=>x.id===trackId));"
)

old='''          <div class="board-browse-card"><div class="board-browse-heading"><div><strong>先选来源，再选设置</strong><p>${tracks.length} 项具体设置，整理为 ${groups.length} 个来源组；分组只简化入口，不合并成绩。</p></div><button class="btn" id="lb-all" aria-pressed="${browseAll}">${browseAll?'返回来源分组':'查看全部 '+tracks.length+' 项设置'}</button></div><div class="board-controls board-group-controls"><label>来源论文 / 官方榜单<select id="lb-group" ${browseAll?'disabled':''}>${groups.map((g,i)=>`<option value="${i}" ${selected(g.id,group?.id)}>${esc(g.label)} · ${g.tracks.length} 项设置 · ${esc(g.kind)}</option>`).join('')}</select></label><p class="board-group-help">${browseAll?'当前列出该数据集全部设置，原链接仍可直接定位。':'同一来源的预算、划分、版本和指标放在下方切换，具体设置仍独立保存。'}</p></div></div>
          <div class="board-controls board-sort-controls"><label>${browseAll?'全部具体设置':'当前来源的具体设置'}<select id="lb-track">${choices.map(x=>`<option value="${esc(x.id)}" ${selected(x.id,trackId)}>${esc(x.name)}</option>`).join('')}</select></label><label>排序 / 图表指标<select id="lb-metric">${t.columns.map(x=>`<option ${selected(x,metric)}>${esc(x)}</option>`).join('')}</select></label><label>排列方式<select id="lb-order"><option value="auto" ${selected(order,'auto')}>优先较优值（自动）</option><option value="desc" ${selected(order,'desc')}>数值降序 ↓</option><option value="asc" ${selected(order,'asc')}>数值升序 ↑</option><option value="source" ${selected(order,'source')}>原记录顺序</option></select></label></div>'''
new='''          <div class="board-browse-card"><div class="board-browse-heading"><div><strong>${group?.explicit?'先选评测协议族，再看方法与 Recipe':'先选来源，再选设置'}</strong><p>${group?.explicit?`${tracks.length} 个原始 track 收拢为 ${groups.length} 个协议族；训练 recipe 下沉，原始证据仍逐条保留。`:`${tracks.length} 项具体设置，整理为 ${groups.length} 个来源组；分组只简化入口，不合并成绩。`}</p></div><button class="btn" id="lb-all" aria-pressed="${browseAll}">${browseAll?(group?.explicit?'返回协议族':'返回来源分组'):(group?.explicit?'高级：全部 '+tracks.length+' 个原始 track':'查看全部 '+tracks.length+' 项设置')}</button></div><div class="board-controls board-group-controls"><label>${group?.explicit?'评测协议族':'来源论文 / 官方榜单'}<select id="lb-group" ${browseAll?'disabled':''}>${groups.map((g,i)=>`<option value="${i}" ${selected(g.id,group?.id)}>${esc(g.label)} · ${g.tracks.length} ${g.explicit?(g.mode==='series'?'子协议':'recipes'):'项设置'} · ${esc(g.explicit?(g.mode==='series'?'系列':'协议族'):g.kind)}</option>`).join('')}</select></label><p class="board-group-help">${browseAll?'当前列出全部原始 track，深链接和精确证据定位保持可用。':group?.explicit?(group.mode==='series'?'当前为子协议系列：任务/部署条件不同，只展开原始变体，不合并成绩。':'同一评测口径下，训练预算、base model、steps 等下沉到 Recipe；展开方法即可查看来源与训练差异。'):'同一来源的预算、划分、版本和指标放在下方切换，具体设置仍独立保存。'}</p></div></div>
          ${group?.explicit&&!browseAll?'<div id="protocol-family-overview"><p class="research-loading">正在整理方法与 Recipe…</p></div>':''}
          <div class="board-controls board-sort-controls"><label>${browseAll?'全部原始 track':group?.explicit?(group.mode==='series'?'当前子协议 / 原始 track':'当前 Recipe / 原始 track'):'当前来源的具体设置'}<select id="lb-track">${choices.map(x=>`<option value="${esc(x.id)}" ${selected(x.id,trackId)}>${esc(x.recipeName||x.name)}</option>`).join('')}</select></label><label>排序 / 图表指标<select id="lb-metric">${t.columns.map(x=>`<option ${selected(x,metric)}>${esc(x)}</option>`).join('')}</select></label><label>排列方式<select id="lb-order"><option value="auto" ${selected(order,'auto')}>优先较优值（自动）</option><option value="desc" ${selected(order,'desc')}>数值降序 ↓</option><option value="asc" ${selected(order,'asc')}>数值升序 ↑</option><option value="source" ${selected(order,'source')}>原记录顺序</option></select></label></div>'''
if old not in s: raise RuntimeError('browse block missing')
s=s.replace(old,new)

s=s.replace(
"host.querySelector('#lb-group').onchange=e=>{const g=groups[Number(e.target.value)];if(!g)return;trackId=g.tracks[0].id;metric='';order='auto';page=1;draw('#lb-group');};",
"host.querySelector('#lb-group').onchange=e=>{const g=groups[Number(e.target.value)];if(!g)return;trackId=(g.primaryTrackId&&g.tracks.some(t=>t.id===g.primaryTrackId)?g.primaryTrackId:g.tracks[0].id);metric='';order='auto';page=1;draw('#lb-group');};"
)

toggle="        const toggleChart=type=>{chartType=chartType===type?'':type;draw('#show-'+(type==='bar'?'protocol-chart':'time-scatter'));};\n"
family_load="""        if(group?.explicit&&!browseAll){
          const mount=host.querySelector('#protocol-family-overview');
          Promise.all(group.tracks.map(async track=>({track,data:await loadTrack(track,data)}))).then(loadedFamily=>{
            if(drawId!==drawVersion||token!==boardToken||!mount?.isConnected)return;
            mount.innerHTML=familyMethodsHtml(group,loadedFamily);
          }).catch(()=>{
            if(drawId!==drawVersion||token!==boardToken||!mount?.isConnected)return;
            mount.innerHTML='<p class="research-warning">协议族中的部分 Recipe 暂未载入；下方当前原始 track 仍可独立查看。</p>';
          });
        }
"""
if toggle not in s: raise RuntimeError('toggle anchor missing')
s=s.replace(toggle,family_load+toggle)

old_export="global.RadarResearch={cancelBoards:()=>{boardToken++;},loadBoards,loadTrack,loadPaperResults,lifecycle,links,scopeNotice,configure,detail,enhance,renderBoards,sourceKey,boardGroups,pageWindow,rankRows,sortRows,boardRows,sortDirection,metricDirection,visibleResults,metricValue,benchmarkFamilies,richEvidence,datasetNames,formatScore,noteBlocks};"
new_export="global.RadarResearch={cancelBoards:()=>{boardToken++;},loadBoards,loadTrack,loadPaperResults,lifecycle,links,scopeNotice,configure,detail,enhance,renderBoards,sourceKey,boardGroups,protocolGroups,methodKey,methodGroups,familyMethodsHtml,pageWindow,rankRows,sortRows,boardRows,sortDirection,metricDirection,visibleResults,metricValue,benchmarkFamilies,richEvidence,datasetNames,formatScore,noteBlocks};"
if old_export not in s: raise RuntimeError('export anchor missing')
s=s.replace(old_export,new_export)
research.write_text(s,encoding='utf-8')

css=ROOT/'site/styles/features/research.css'
css.write_text(css.read_text(encoding='utf-8')+r'''

/* Protocol-family hierarchy: Benchmark -> evaluation family -> method -> recipe/evidence. */
.protocol-family-panel{margin:16px 0 18px;border:1px solid #e6e5f2;background:#fbfbfe;border-radius:14px;padding:20px}
.family-header{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}
.family-header h2{font-size:18px;margin:9px 0 6px;color:#555b73}
.family-header p{font-size:10px;line-height:1.9;color:#8b92a7;max-width:760px;margin:0}
.family-stats{display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end}
.family-stats span{min-width:72px;border:1px solid #e6e5f1;background:#fff;border-radius:8px;padding:7px 9px;text-align:center;font-size:7px;letter-spacing:.6px;color:#9ba0b1}
.family-stats b{display:block;font-size:16px;line-height:1.2;color:#68628e;letter-spacing:0}
.family-rule{margin:14px 0 11px;padding:9px 11px;border-left:2px solid #b6afe7;background:#f5f4fc;color:#7d7f95;font-size:9px;line-height:1.8}
.family-method-list{display:grid;gap:8px}
.family-method{background:#fff;border:1px solid #ececf4;border-radius:10px;overflow:hidden}
.family-method-main{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:12px 14px}
.family-method-name strong{display:block;font-size:12px;color:#535a70}
.family-method-name small{display:block;margin-top:3px;font-size:8px;color:#a1a6b6}
.family-method-values{display:flex;align-items:center;gap:14px;flex-wrap:wrap;justify-content:flex-end}
.family-method-values span{min-width:60px;text-align:right}
.family-method-values small{display:block;font-size:7px;color:#a2a7b7}
.family-method-values b{font-size:12px;color:#676d83;font-variant-numeric:tabular-nums}
.family-series-count{display:flex;align-items:center;gap:7px;color:#8f95a7}
.family-series-count b{font-size:18px;color:#746ca2}
.family-series-count span{font-size:8px}
.family-recipes{border-top:1px solid #f0f0f6}
.family-recipes>summary{list-style:none;padding:9px 14px;font-size:9px;color:#8179a5;cursor:pointer;background:#fdfdff}
.family-recipes>summary::-webkit-details-marker{display:none}
.family-recipes>summary:after{content:"＋";float:right;color:#aaa5c6}
.family-recipes[open]>summary:after{content:"−"}
.recipe-list{display:grid;gap:8px;padding:10px;background:#f8f8fc}
.recipe-item{border:1px solid #e8e8f1;background:#fff;border-radius:8px;padding:11px 12px}
.recipe-title{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.recipe-title strong{font-size:10px;color:#626980}
.recipe-title em{font-style:normal;font-size:7px;color:#7066a1;background:#efedfb;padding:2px 5px;border-radius:4px}
.recipe-kind{font-size:7px;color:#8b91a4;border:1px solid #e5e7ef;border-radius:4px;padding:1px 5px}
.recipe-values{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
.recipe-values span{font-size:8px;color:#989daf;background:#f7f7fb;border-radius:4px;padding:3px 6px}
.recipe-values b{color:#646b82;font-weight:600}
.recipe-item p{font-size:9px;line-height:1.8;color:#858ca1;margin:6px 0}
.recipe-item>small{font-size:8px;color:#a0a5b5}
.recipe-actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:8px}
.recipe-actions .note-sources{margin:0}
.recipe-actions .note-sources a{font-size:8px}
@media(max-width:700px){
 .protocol-family-panel{padding:14px 12px}
 .family-header{flex-direction:column}
 .family-stats{justify-content:flex-start}
 .family-method-main{align-items:flex-start;flex-direction:column}
 .family-method-values{justify-content:flex-start;width:100%}
 .family-method-values span{text-align:left}
}
''',encoding='utf-8')

node=ROOT/'tests/node/test_leaderboard_controls.cjs'
n=node.read_text(encoding='utf-8')
needle="ok('grouping 10000 tracks keeps every record',()=>{const x=Array.from({length:10000},(_,i)=>({...nav[0],id:'x'+i}));const g=R.boardGroups(x);a.equal(g.length,1);a.equal(g[0].tracks.length,10000);});\n"
addition="""ok('RoboTwin 19 tracks collapse to six explicit protocol families',()=>{const rt=actual.filter(t=>t.dataset==='RoboTwin'),g=R.protocolGroups(rt);a.equal(rt.length,19);a.equal(g.length,6);a(g.every(x=>x.explicit));a.equal(g.flatMap(x=>x.tracks).length,19);});
ok('RoboTwin subset studies are a non-aggregating series',()=>{const g=R.protocolGroups(actual.filter(t=>t.dataset==='RoboTwin')).find(x=>x.id==='robotwin2-partial-subset-studies');a.equal(g.mode,'series');a.equal(g.tracks.length,4);});
ok('method aliases group recipes without score selection',()=>{const g={primaryTrackId:'a',tracks:[{id:'a'},{id:'b'}]},loaded=[{track:{id:'a'},data:{results:[{id:'x',trackId:'a',method:'pi0.5',evidence:'checked',supersedes:''}]}},{track:{id:'b'},data:{results:[{id:'y',trackId:'b',method:'π0.5',evidence:'checked',supersedes:''}]}}];const m=R.methodGroups(g,loaded);a.equal(m.length,1);a.equal(m[0].variants.length,2);a.equal(m[0].primary.row.id,'x');});
"""
if needle not in n: raise RuntimeError('node test anchor missing')
node.write_text(n.replace(needle,needle+addition),encoding='utf-8')

browser=ROOT/'scripts/browser/browser_leaderboard.py'
b=browser.read_text(encoding='utf-8')
needle="""        open_track(page,'robocasa365-paper-v1-target-50')
        yes('related budgets share navigation entry',page.locator('#lb-track option[value="robocasa365-paper-v1-target-500"]').count()==1)
"""
addition="""        open_track(page,'robotwin2-selfwam-27500')
        page.wait_for_selector('.protocol-family-panel')
        yes('RoboTwin uses six protocol families',page.locator('#lb-group option').count()==6)
        yes('standard family hides nineteen-track clutter',page.locator('#lb-track option').count()==6)
        yes('family view is method-first','先选评测协议族' in page.locator('.board-browse-heading').inner_text() and page.locator('.family-method').count()>0)
        pi=page.locator('.family-method').filter(has_text='pi0.5').first
        yes('same method exposes multiple reported recipes','reported recipes' in pi.inner_text())
        pi.locator('.family-recipes summary').click()
        yes('recipe expansion preserves evidence',pi.locator('.recipe-item').count()>=3 and pi.locator('.recipe-actions').count()>=3)
        partial=page.locator('#lb-group option').evaluate_all('(ops)=>String(ops.findIndex(o=>o.textContent.includes("Partial / Subset")))')
        page.locator('#lb-group').select_option(partial);page.wait_for_selector('.protocol-family-panel')
        yes('subset series refuses representative score aggregation','不合并成绩' in page.locator('.protocol-family-panel').inner_text() and page.locator('.family-method-values').count()==0)
        page.locator('#lb-all').click();page.wait_for_function('document.querySelector("#lb-track")?.options.length===19')
        yes('advanced mode still exposes all original RoboTwin tracks',page.locator('#lb-track option').count()==19)
        page.locator('#lb-all').click();page.wait_for_function('!document.querySelector("#lb-group").disabled')
        page.screenshot(path=str(OUT/'robotwin-protocol-family.png'))

"""
if needle not in b: raise RuntimeError('browser anchor missing')
browser.write_text(b.replace(needle,addition+needle),encoding='utf-8')

print('benchmark protocol-family UI patch applied')

# trigger one-shot migration after workflow definition exists
