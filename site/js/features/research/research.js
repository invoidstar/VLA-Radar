/* VLA Radar research layer: public evidence only; no accounts, models or external API requests. */
'use strict';
(function (global) {
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function external(v){try{const u=new URL(v);return ['https:','http:'].includes(u.protocol)&&!u.username&&!u.password?u.href:'#';}catch{return '#';}}
  const links = sources => `<div class="note-sources">${sources.map(s=>`<a href="${esc(external(s.url))}" target="_blank" rel="noopener noreferrer">${esc(s.label)} ↗</a>`).join('')}</div>`;
  const para = text => String(text||'').split(/\n+/).filter(Boolean).map(x=>`<p>${esc(x)}</p>`).join('');
  const date = v => v || '未核验 / 未公开';
  const STATUS = {legacy:'沿用旧记录 · 待检查',preprint:'预印本',accepted:'已录用',published:'正式发表',report:'技术报告',withdrawn:'已撤回'};
  const ATTR = {'author-reported':'作者方法','reported-baseline':'同文报告基线','independent-reproduction':'独立复现'};
  const Runtime=global.RadarRuntime||(typeof require==='function'?require('../../core/runtime.js'):null);
  let boardPromise, boardToken=0, boardIndexUrl='data/leaderboards.json', boardPapers=[];
  const getJson=path=>Runtime.loadJson(path);
  function configure(catalog){boardPapers=Array.isArray(catalog.papers)?catalog.papers:[];boardIndexUrl=catalog.boardIndexUrl||'data/leaderboards.json';boardPromise=null;}
  function loadBoards(){if(!boardPromise)boardPromise=getJson(boardIndexUrl).then(x=>{if(x.schemaVersion!==1||!Array.isArray(x.tracks))throw new Error('榜单格式不支持');return x;}).catch(e=>{boardPromise=null;throw e;});return boardPromise;}
  async function loadTrack(t,data){if(Array.isArray(data.results))return data;const x=await getJson(t.resultUrl);if(x.trackId!==t.id||!Array.isArray(x.results))throw new Error('赛道数据不一致');return {...data,results:x.results};}
  async function loadSetting(s,data){if(Array.isArray(data.results)&&Array.isArray(data.tracks))return data;const x=await getJson(s.resultUrl);if(x.settingId!==s.id||!Array.isArray(x.results)||!Array.isArray(x.tracks))throw new Error('Setting 数据不一致');return x;}
  async function loadPaperResults(p){if(!p.resultUrl)return {tracks:[],results:[]};const x=await getJson(p.resultUrl);if(x.paperId!==p.id||!Array.isArray(x.results))throw new Error('论文结果不一致');return x;}
  function pageWindow(current,total){const pages=new Set([1,total]);for(let i=Math.max(1,current-2);i<=Math.min(total,current+2);i++)pages.add(i);let prev=0,out=[];for(const i of [...pages].filter(i=>i>0).sort((a,b)=>a-b)){if(prev&&i-prev>1)out.push(null);out.push(i);prev=i;}return out;}
  function visibleResults(data,trackId){const superseded=new Set([...(data.supersededIds||[]),...data.results.filter(r=>r.evidence==='checked'&&r.supersedes).map(r=>r.supersedes)]);return data.results.filter(r=>r.trackId===trackId&&r.evidence==='checked'&&!superseded.has(r.id));}
  // Display order is independent of scientific rank. Missing/invalid values stay last.
  function metricDirection(track,column){return (track.columnDirections?.[column]||track.direction)==='lower'?'lower':'higher';}
  function sortDirection(track,column,order='auto'){return order==='asc'?'asc':order==='desc'?'desc':metricDirection(track,column)==='lower'?'asc':'desc';}
  function sortRows(rows,column,order='desc'){
    return [...rows].sort((a,b)=>{
      const av=a.values?.[column],bv=b.values?.[column],af=Number.isFinite(av),bf=Number.isFinite(bv);
      if(af!==bf)return af?-1:1;
      return (af&&av!==bv?(order==='asc'?av-bv:bv-av):0)||String(a.method).localeCompare(String(b.method))||String(a.id).localeCompare(String(b.id));
    });
  }
  function rankRows(rows,column,direction='higher'){
    let prior,rank=0;
    return sortRows(rows,column,direction==='lower'?'asc':'desc').map((r,i)=>{
      const v=r.values?.[column];if(Number.isFinite(v)&&v!==prior)rank=i+1;prior=v;
      return {...r,rank:Number.isFinite(v)?rank:null};
    });
  }
  function boardRows(rows,track,column,order='auto'){
    const ranked=rankRows(rows,column,metricDirection(track,column)),ranks=new Map(ranked.map(r=>[r.id,r.rank]));
    const ordered=order==='source'?[...rows]:sortRows(rows,column,sortDirection(track,column,order));
    return ordered.map(r=>({...r,rank:track.comparisonScope==='protocol'?ranks.get(r.id):null}));
  }

  // Navigation families never combine results, metrics, versions or fair ranks.
  function sourceKey(value){
    try{
      const u=new URL(value);if(!['https:','http:'].includes(u.protocol)||u.username||u.password)return '';
      const host=u.hostname.toLowerCase(),path=u.pathname;
      if(['arxiv.org','www.arxiv.org','export.arxiv.org','ar5iv.labs.arxiv.org','ar5iv.org'].includes(host)){
        const m=path.match(/\/(?:abs|html|pdf)\/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?\/?$/);
        if(m)return 'arxiv:'+m[1];
      }
      if(host==='doi.org'||host==='dx.doi.org')return 'doi:'+path.slice(1).toLowerCase();
      if(host==='proceedings.mlr.press')return 'pmlr:'+path.replace(/\.pdf$/i,'.html').replace(/\/([^/]+)\/\1\.html$/,'/$1.html');
      if(['proceedings.neurips.cc','papers.nips.cc','proceedings.iclr.cc'].includes(host)){
        const m=path.match(/\/([a-f0-9]{32})-/i);if(m)return host+':'+m[1].toLowerCase();
      }
      if(host==='openreview.net'&&u.searchParams.get('id'))return 'openreview:'+u.searchParams.get('id');
      u.hash='';for(const k of [...u.searchParams.keys()])if(k.startsWith('utm_'))u.searchParams.delete(k);
      return u.href;
    }catch{return '';}
  }
  function boardGroups(tracks,papers=[]){
    const names=new Map();
    for(const p of papers){
      if(p.arxiv)names.set('arxiv:'+p.arxiv.replace(/v\d+$/,''),p.name||p.title||p.id);
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
      const short=String(t.name||t.id).split(/\s*[·｜|]\s*/)[0];
      g.label=name||short;g.kind=g.tracks.every(t=>t.comparisonScope==='protocol')?'协议内结果':g.tracks.every(t=>t.comparisonScope==='paper-table')?'原文证据':'多类证据';
      return g;
    });
  }
  function protocolGroups(tracks,papers=[]){
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
  async function detail(p){
    if(!p.detailUrl)return null;
    // Only static detail paths from the public catalog are fetched; no arbitrary network target.
    if(!/^data\/details\/p\d{3,}(?:\.[a-f0-9]{16}\.json|\.json\?v=[a-f0-9]{16})$/.test(p.detailUrl))throw new Error('无效详情路径');
    const r=await getJson(p.detailUrl);
    if(r.schemaVersion!==2||r.paper?.id!==p.id||!r.publication||!Array.isArray(r.note?.sections))throw new Error('详情版本不一致，请刷新');
    return r;
  }
  function lifecycle(pub,p){
    const grid=[['首次公开（保留原值）',p.firstPublished],['最早 arXiv',pub.firstArxivAt],['arXiv 最新版本',pub.latestArxivVersion],['最新修订日期',pub.latestArxivAt],['当前状态',STATUS[pub.status]],['会议 / 期刊',pub.venue],['录用日期',pub.acceptedAt],['出版日期',pub.publishedAt],['最近元数据检查',pub.lastCheckedAt]];
    return `<div class="life-grid">${grid.map(([k,v])=>`<div><span>${esc(k)}</span><strong>${esc(date(v))}</strong></div>`).join('')}</div><p class="note-small">出版日期可以精确到年或月，不补造日期。元数据检查不等于全文复核；会议年份不一定等于论文集出版年份。</p>${pub.firstArxivSource?links([{label:'最早 arXiv 版本',url:pub.firstArxivSource}]):''}${pub.alerts.map(s=>`<div class="research-warning">${esc(s)}</div>`).join('')}<h3>可追溯的发表历程</h3><ol class="life-events">${[...pub.history].sort((a,b)=>(a.date||a.observedAt).localeCompare(b.date||b.observedAt)).map(e=>`<li><span class="event-dot"></span><div><small>${esc(e.date||'事件日期未确认')} · 发现于 ${esc(e.observedAt)}</small><strong>${esc(({imported:'原记录迁移',arxiv_first:'arXiv 首发',arxiv_version:'arXiv 修订',published:'正式发表',accepted:'录用',withdrawn:'撤回'})[e.kind]||e.kind)} ${esc(e.venue)}</strong>${para(e.note)}${links([{label:'事件来源',url:e.source}])}</div></li>`).join('')}</ol>`;
  }

  // Source-scoped deep-note rendering. All imported text is escaped, never executed.
  function metricValue(v,unit){return v==null?'—':esc(v)+(unit==='percent'?'%':unit==='seconds'?' s':'');}
  function benchmarkFamilies(data){return [...new Set(data.tracks.map(t=>t.dataset))];}
  function scopeNotice(note){
    const c=note.coverage;if(!c)return '';
    const labels={'primary-methods-experiments':'已阅读原文方法与实验指定范围','primary-theory':'理论原文与证明范围解读；不产生实验排名','official-technical-report':'官方技术报告解读；公开细节范围见下文','official-abstract-only':'仅依据官方摘要：全文方法、实验细节仍待核验','author-materials-partial':'作者供稿与正式摘要导读：未取得完整期刊正文'};
    return `<p class="note-coverage ${c.level==='limited'?'limited':''}">${esc(labels[c.scope]||c.scope)} · ${note.sections.length} 个解释章节。所有数值为指定来源报告，不代表本站独立复现。</p>`;
  }
  function richEvidence(note){
    const source=note.coverage?.source||note.sections[0]?.sources[0]?.url;
    const tables=(note.tables||[]).map((t,i)=>`<section class="note-table-block"><h3>结果与推理对照 ${i+1} · ${esc(t.title)}</h3><div class="note-table-scroll" tabindex="0" role="region" aria-label="${esc(t.title)}"><table class="note-table"><thead><tr>${t.columns.map(c=>`<th scope="col">${esc(c)}</th>`).join('')}</tr></thead><tbody>${t.rows.map(row=>`<tr>${row.map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p class="note-small">${esc(t.caption)}</p>${links([{label:t.locator+' · 原文依据',url:source}])}</section>`).join('');
    const figures=(note.figures||[]).map(f=>`<figure class="note-figure"><h3>${esc(f.title)}</h3>${f.imageUrl?`<a href="${esc(external(f.url))}" target="_blank" rel="noopener noreferrer"><img src="${esc(external(f.imageUrl))}" alt="${esc(f.title)}" loading="lazy" decoding="async" referrerpolicy="no-referrer"></a>`:''}<figcaption>${para(f.caption)}${f.license?`<p class="note-small">原作者图像 · ${esc(f.license)} · 未修改。图片不可达时仍可访问下方原文。</p>`:'<p class="note-small">提供原图定位和阅读说明，不复制未确认再分发许可的图像。</p>'}${links([{label:'查看论文原图 / 上下文',url:f.url}])}</figcaption></figure>`).join('');
    const br=note.benchmarkReview;const labels={pending:'待检查',extracted:'已有提取记录', 'not-applicable':'无适用标准榜单','protocol-unresolved':'协议或数据待核验'};
    const review=br?`<aside class="note-benchmark-review"><strong>评测提取：${esc(labels[br.status])}</strong><p>${esc(br.note)}</p><small>检查时间：${esc(br.checkedAt||'尚未完成')}</small></aside>`:'';
    return tables+figures+review;
  }

  function datasetNames(data){return benchmarkFamilies(data);}
  function formatScore(value,unit){return metricValue(value,unit);}
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
  async function enhance(p,root){
    root.dataset.paperId=p.id;
    const token=Symbol(p.id);root._researchToken=token;
    const hint=document.createElement('div');hint.className='research-loading';hint.setAttribute('role','status');hint.textContent='正在载入详细笔记与发表历程…';root.querySelector('.date-grid')?.after(hint);
    try{
      const r=await detail(p);if(root._researchToken!==token)return;if(!r){hint.remove();return;}
      const note=r.note, stale=note.status==='needs_review';
      root.querySelectorAll('.detail-section,.evidence-status').forEach(e=>e.remove());
      const panel=document.createElement('div');panel.className='research-detail';
      panel.innerHTML=`<div class="note-heading"><span class="note-badge ${note.status==='expanded'?'verified':''}">${note.coverage?.level==='limited'?'受限材料导读 · 正文待核验':stale?'深入笔记 · 新版本待复核':note.coverage?.level==='deep'?'深入笔记 · 分节原文依据':note.status==='expanded'?'已扩展 · 有原文定位':'既有笔记 · 待深化核验'}</span><small>笔记核验 ${esc(date(note.verifiedAt))}</small></div><div class="research-tabs" role="tablist" aria-label="论文详情内容"><button id="tab-notes" role="tab" aria-selected="true" aria-controls="panel-notes" data-note-tab="notes">阅读笔记</button><button id="tab-life" role="tab" aria-selected="false" aria-controls="panel-life" tabindex="-1" data-note-tab="life">发表历程</button><button id="tab-results" role="tab" aria-selected="false" aria-controls="panel-results" tabindex="-1" data-note-tab="results">评测记录</button></div><div id="panel-notes" role="tabpanel" aria-labelledby="tab-notes"><div class="note-context"><strong>阅读版本：${esc(note.version)}</strong>${scopeNotice(note)}<p>${note.coverage?.level==='limited'?'可核读材料及其边界已在各节说明；未取得完整正文，不将机制说明、分析或摘要扩写冒充全文实验核验。':note.status==='legacy'?'下面保留原有公开笔记，尚未逐篇重新读全文。周更会按优先级和核验时间补齐研究问题、方法机制、创新差异、实验和消融；不会用重复模板冒充完整精读。':stale?'下方结论有具体来源，但阅读版本早于当前 arXiv 版本。旧版结果保留，版本差异待核验。':'以下是公开原文指定片段的结构化总结，并非独立复现或整篇认证。'}</p></div><section class="key-result-full"><small>KEY RESULT · 原记录保留</small>${para(p.findings)}</section><div class="note-toc" aria-label="笔记章节">${note.sections.map((s,i)=>`<button data-note-anchor="note-${esc(s.id)}">${String(i+1).padStart(2,'0')} ${esc(s.title)}</button>`).join('')}</div>${note.sections.map((s,i)=>`<section class="note-section" id="note-${esc(s.id)}"><span class="note-number">${String(i+1).padStart(2,'0')}</span><div><h3>${esc(s.title)}</h3>${noteBlocks(s.body)}${links(s.sources)}</div></section>`).join('')}${richEvidence(note)}</div><div id="panel-life" role="tabpanel" aria-labelledby="tab-life" hidden>${lifecycle(r.publication,p)}</div><div id="panel-results" role="tabpanel" aria-labelledby="tab-results" hidden><p class="research-loading">正在载入公开评测记录…</p></div>`;
      hint.replaceWith(panel);
      const choose=key=>{panel.querySelectorAll('[data-note-tab]').forEach(b=>{const yes=b.dataset.noteTab===key;b.setAttribute('aria-selected',yes);b.tabIndex=yes?0:-1;});for(const k of ['notes','life','results'])panel.querySelector('#panel-'+k).hidden=k!==key;};
      panel.addEventListener('click',e=>{const b=e.target.closest('button');if(b?.dataset.noteTab)choose(b.dataset.noteTab);if(b?.dataset.noteAnchor)panel.querySelector('#'+b.dataset.noteAnchor)?.scrollIntoView({block:'start',behavior:'smooth'});});
      panel.querySelector('[role=tablist]').addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;const tabs=[...panel.querySelectorAll('[data-note-tab]')];let i=tabs.indexOf(document.activeElement);if(i<0)return;e.preventDefault();i=e.key==='Home'?0:e.key==='End'?2:(i+(e.key==='ArrowRight'?1:2))%3;tabs[i].click();tabs[i].focus();});
      // Results load only when needed, not for every paper click.
      let resultsLoaded=false;
      panel.addEventListener('click',async e=>{if(e.target.closest('[data-note-tab]')?.dataset.noteTab!=='results'||resultsLoaded)return;resultsLoaded=true;const target=panel.querySelector('#panel-results');try{const b=await loadPaperResults(p);if(root._researchToken!==token)return;const rows=b.tracks.flatMap(t=>visibleResults(b,t.id)).filter(x=>x.paperId===p.id);target.innerHTML=rows.length?`<p class="note-small">共 ${rows.length} 条核验记录；含作者方法及论文引用基线。下列分数不能跨赛道直接比较。</p>`+rows.map(row=>`<article class="paper-result"><strong>${esc(row.method)}</strong><span class="note-badge">${esc(ATTR[row.attribution])}</span><p>${esc(b.tracks.find(t=>t.id===row.trackId)?.name)}</p><div class="result-values">${Object.entries(row.values).map(([k,v])=>`<span>${esc(k)} <b>${metricValue(v,b.tracks.find(t=>t.id===row.trackId)?.unit)}</b></span>`).join('')}</div><p class="note-small">${esc(row.trainingData)} · ${esc(row.locator)} · ${esc(row.sourceVersion)}</p>${links([{label:'原文表格／设置',url:row.source}])}</article>`).join(''):'<div class="research-empty"><h3>暂无可追溯的榜单记录</h3><p>未提取、协议不明或仅有摘要的结果不会自动填零、生成名次。论文原有 KEY RESULT 仍完整保留。</p></div>';}
        catch(err){resultsLoaded=false;target.innerHTML='<p class="research-warning">榜单暂未载入。重新点击此标签可重试。</p>';}});
    }catch(err){if(root._researchToken!==token)return;hint.className='research-warning';hint.textContent='详细笔记暂不可用，以下展示原有笔记。刷新后可重试。';console.warn('Paper detail:',err.message);}
  }
  async function renderBoards(host){
    const token=++boardToken;host.innerHTML='<p class="research-loading" role="status">正在载入经过核验的评测记录…</p>';
    try{
      const data=await loadBoards();if(token!==boardToken)return;
      const query=new URLSearchParams(location.search),families=benchmarkFamilies(data);
      if(!query.get('track')&&Array.isArray(data.settings)&&global.RadarBenchmarkSettings){
        await global.RadarBenchmarkSettings.render(host,{data,query,token,isCurrent:()=>token===boardToken,papers:boardPapers,loadSetting});
        return;
      }
      let dataset=families.includes(query.get('dataset'))?query.get('dataset'):(families.includes('LIBERO')?'LIBERO':families[0]);
      let trackId=query.get('track')||'',metric=(query.get('lbMetric')||'').slice(0,160),page=1,drawVersion=0;
      let order=['auto','asc','desc','source'].includes(query.get('lbOrder'))?query.get('lbOrder'):'auto';
      let chartType=['bar','scatter'].includes(query.get('lbChart'))?query.get('lbChart'):'';
      let dateBasis=query.get('lbTime')==='verifiedAt'?'verifiedAt':'firstPublished';
      let browseAll=query.get('lbBrowse')==='all';
      const selected=(v,x)=>v===x?'selected':'';
      function updateUrl(){
        if(token!==boardToken)return;
        const u=new URL(location.href);u.searchParams.set('dataset',dataset);u.searchParams.set('track',trackId);
        u.searchParams.set('lbMetric',metric);u.searchParams.set('lbOrder',order);
        if(browseAll)u.searchParams.set('lbBrowse','all');else u.searchParams.delete('lbBrowse');
        if(chartType)u.searchParams.set('lbChart',chartType);else u.searchParams.delete('lbChart');
        if(chartType==='scatter')u.searchParams.set('lbTime',dateBasis);else u.searchParams.delete('lbTime');
        history.replaceState({},'',u);
      }
      async function draw(focus){
        const drawId=++drawVersion,scrollLeft=host.querySelector('.board-table-scroll')?.scrollLeft||0;
        const tracks=data.tracks.filter(t=>t.dataset===dataset);if(!tracks.some(t=>t.id===trackId))trackId=tracks[0]?.id||'';
        const groups=protocolGroups(tracks,boardPapers),group=groups.find(g=>g.tracks.some(x=>x.id===trackId));
        const choices=browseAll?tracks:(group?.tracks||tracks);
        const t=tracks.find(t=>t.id===trackId);if(!t){host.innerHTML='<p>暂时没有此数据集的已定义赛道。</p>';return;}
        if(!t.columns.includes(metric))metric=t.columns.includes('Average')?'Average':t.columns[0];
        let loaded;
        try{loaded=await loadTrack(t,data);}catch(error){
          if(drawId!==drawVersion||token!==boardToken)return;
          host.innerHTML='<p class="research-warning">此赛道暂未载入，未载入不等于零分。</p><button id="retry-track" class="btn">重试当前赛道</button>';
          host.querySelector('#retry-track').onclick=()=>draw();return;
        }
        if(drawId!==drawVersion||token!==boardToken)return;
        const accepted=visibleResults(loaded,t.id),rows=boardRows(accepted,t,metric,order);
        const size=20,pages=Math.max(1,Math.ceil(rows.length/size));page=Math.max(1,Math.min(page,pages));
        const candidates=loaded.results.filter(r=>r.trackId===t.id&&r.evidence==='candidate').length;
        const direction=sortDirection(t,metric,order),directionLabel=direction==='asc'?'升序':'降序';
        const header=c=>`<th scope="col" ${c===metric&&order!=='source'?`aria-sort="${direction==='asc'?'ascending':'descending'}"`:''}><button class="board-sort-button" data-sort-column="${esc(c)}" aria-label="按 ${esc(c)} 排序，重复点击切换升降序">${esc(c)} <span aria-hidden="true">${c===metric&&order!=='source'?(direction==='asc'?'▲':'▼'):'↕'}</span></button></th>`;
        host.innerHTML=`<div class="leaderboard-top"><div class="dataset-tabs" role="group" aria-label="数据集">${families.map(d=>`<button data-dataset="${esc(d)}" aria-pressed="${d===dataset}">${esc(d)}</button>`).join('')}</div><div class="board-update">目录更新 ${esc(data.updatedAt)} · <a href="data/leaderboards.json" download>公开 JSON ↗</a></div></div>
          <div class="board-browse-card"><div class="board-browse-heading"><div><strong>${group?.explicit?'先选评测协议族，再看方法与 Recipe':'先选来源，再选设置'}</strong><p>${group?.explicit?`${tracks.length} 个原始 track 收拢为 ${groups.length} 个协议族；训练 recipe 下沉，原始证据仍逐条保留。`:`${tracks.length} 项具体设置，整理为 ${groups.length} 个来源组；分组只简化入口，不合并成绩。`}</p></div><button class="btn" id="lb-all" aria-pressed="${browseAll}">${browseAll?(group?.explicit?'返回协议族':'返回来源分组'):(group?.explicit?'高级：全部 '+tracks.length+' 个原始 track':'查看全部 '+tracks.length+' 项设置')}</button></div><div class="board-controls board-group-controls"><label>${group?.explicit?'评测协议族':'来源论文 / 官方榜单'}<select id="lb-group" ${browseAll?'disabled':''}>${groups.map((g,i)=>`<option value="${i}" ${selected(g.id,group?.id)}>${esc(g.label)} · ${g.tracks.length} ${g.explicit?(g.mode==='series'?'子协议':'recipes'):'项设置'} · ${esc(g.explicit?(g.mode==='series'?'系列':'协议族'):g.kind)}</option>`).join('')}</select></label><p class="board-group-help">${browseAll?'当前列出全部原始 track，深链接和精确证据定位保持可用。':group?.explicit?(group.mode==='series'?'当前为子协议系列：任务/部署条件不同，只展开原始变体，不合并成绩。':'同一评测口径下，训练预算、base model、steps 等下沉到 Recipe；展开方法即可查看来源与训练差异。'):'同一来源的预算、划分、版本和指标放在下方切换，具体设置仍独立保存。'}</p></div></div>
          ${group?.explicit&&!browseAll?'<div id="protocol-family-overview"><p class="research-loading">正在整理方法与 Recipe…</p></div>':''}
          <div class="board-controls board-sort-controls"><label>${browseAll?'全部原始 track':group?.explicit?(group.mode==='series'?'当前子协议 / 原始 track':'当前 Recipe / 原始 track'):'当前来源的具体设置'}<select id="lb-track">${choices.map(x=>`<option value="${esc(x.id)}" ${selected(x.id,trackId)}>${esc(x.recipeName||x.name)}</option>`).join('')}</select></label><label>排序 / 图表指标<select id="lb-metric">${t.columns.map(x=>`<option ${selected(x,metric)}>${esc(x)}</option>`).join('')}</select></label><label>排列方式<select id="lb-order"><option value="auto" ${selected(order,'auto')}>优先较优值（自动）</option><option value="desc" ${selected(order,'desc')}>数值降序 ↓</option><option value="asc" ${selected(order,'asc')}>数值升序 ↑</option><option value="source" ${selected(order,'source')}>原记录顺序</option></select></label></div>
          <div class="protocol-card"><div><span class="note-badge">${t.comparisonScope==='protocol'?'协议内结果榜':'论文对照表 · 不给名次'}</span><h2>${esc(t.name)}</h2><p class="protocol-brief">${esc(t.version)} · ${esc(t.metric)} (${esc(t.unit)}) · ${esc(t.split)}</p></div><details class="protocol-details"><summary>展开完整协议、训练预算与原始来源</summary><p>${esc(t.protocol)}</p><div class="protocol-facts"><span>版本 <b>${esc(t.version)}</b></span><span>任务 <b>${esc(t.tasks)}</b></span><span>训练 <b>${esc(t.trainingRegime)}</b></span></div>${links([{label:'协议原始来源',url:t.source}])}</details></div>
          <div class="research-warning">${t.comparisonScope==='protocol'?'名次按所选指标的优劣方向计算；改变显示升降序不颠倒名次。仅覆盖本赛道已核验报告，不是官方全量榜、统计显著性结论或本站复现。预训练数据与计算预算仍可能不同。':'支持按数值整理原文记录，但训练预算或评测细节未统一，不将排列顺序解释为公平名次。'} 未核验候选 ${candidates} 条，不参与排序或绘图。</div>
          <div class="board-visual-tools"><button class="btn" id="show-protocol-chart" aria-expanded="${chartType==='bar'}" aria-controls="protocol-chart">查看当前协议图表</button><button class="btn" id="show-time-scatter" aria-expanded="${chartType==='scatter'}" aria-controls="protocol-chart">时间—成绩散点图</button><button class="btn" id="export-protocol-csv">导出当前协议 CSV</button><span>点开列名可排序；图表与表格使用同一指标。</span></div><div id="protocol-chart" hidden></div>
          <p class="board-sort-status" role="status">${order==='source'?'按原记录顺序展示':`${esc(metric)} · ${directionLabel}`} · 指标${metricDirection(t,metric)==='lower'?'越低越好':'越高越好'} · 数值排序时缺失值置后，真实零分保留。</p>
          <div class="board-table-scroll" role="region" aria-label="可横向滚动的评测结果表" tabindex="0"><table class="board-table"><caption>${esc(t.name)} · ${rows.length} 条核验结果 · ${esc(t.metric)} (${esc(t.unit)}) · 点击指标列标题切换排序</caption><thead><tr><th scope="col">${t.comparisonScope==='protocol'?'名次':'记录'}</th><th scope="col">模型 / 来源论文</th>${t.columns.map(header).join('')}<th scope="col">证据与设置</th></tr></thead><tbody>${rows.slice((page-1)*size,page*size).map((r,i)=>`<tr data-result-id="${esc(r.id)}"><td class="rank-cell">${t.comparisonScope==='protocol'?(r.rank??'—'):(page-1)*size+i+1}</td><td><strong>${esc(r.method)}</strong><button class="board-paper-link" data-paper="${esc(r.paperId)}">${esc(r.paperId)} · 阅读来源论文 ↗</button><small>${esc(ATTR[r.attribution])}</small></td>${t.columns.map(c=>`<td class="numeric ${c===metric?'selected-metric':''}">${Number.isFinite(r.values[c])?esc(r.values[c]):'—'}</td>`).join('')}<td><details><summary>${esc(r.sourceVersion)} · ${esc(r.locator)}</summary><p>${esc(r.trainingData)}</p><p>${esc(r.evaluationNotes)}</p><p>核验：${esc(r.verifiedAt)}</p>${links([{label:'结果来源',url:r.source}])}</details></td></tr>`).join('')}</tbody></table>${rows.length?'':'<p class="research-empty">暂时没有此协议下已核验的结果。</p>'}</div><div class="pagination">${pageWindow(page,pages).map(n=>n===null?'<span>…</span>':`<button data-lb-page="${n}" class="${n===page?'active':''}">${n}</button>`).join('')}<span>每页20条；先排序全部记录，再分页。</span></div>`;
        if(group?.explicit&&!browseAll){
          const mount=host.querySelector('#protocol-family-overview');
          Promise.all(group.tracks.map(async track=>({track,data:await loadTrack(track,data)}))).then(loadedFamily=>{
            if(drawId!==drawVersion||token!==boardToken||!mount?.isConnected)return;
            mount.innerHTML=familyMethodsHtml(group,loadedFamily);
          }).catch(()=>{
            if(drawId!==drawVersion||token!==boardToken||!mount?.isConnected)return;
            mount.innerHTML='<p class="research-warning">协议族中的部分 Recipe 暂未载入；下方当前原始 track 仍可独立查看。</p>';
          });
        }
        const toggleChart=type=>{chartType=chartType===type?'':type;draw('#show-'+(type==='bar'?'protocol-chart':'time-scatter'));};
        host.querySelector('#show-protocol-chart').onclick=()=>toggleChart('bar');
        host.querySelector('#show-time-scatter').onclick=()=>toggleChart('scatter');
        host.querySelector('#export-protocol-csv').onclick=()=>global.RadarWorkspace.action('csv',{track:t,rows});
        host.querySelectorAll('[data-dataset]').forEach(b=>b.onclick=()=>{dataset=b.dataset.dataset;trackId='';metric='';order='auto';page=1;draw();});
        host.querySelector('#lb-all').onclick=()=>{browseAll=!browseAll;draw('#lb-all');};
        host.querySelector('#lb-group').onchange=e=>{const g=groups[Number(e.target.value)];if(!g)return;trackId=(g.primaryTrackId&&g.tracks.some(t=>t.id===g.primaryTrackId)?g.primaryTrackId:g.tracks[0].id);metric='';order='auto';page=1;draw('#lb-group');};
        host.querySelector('#lb-track').onchange=e=>{trackId=e.target.value;metric='';order='auto';page=1;draw('#lb-track');};
        host.querySelector('#lb-metric').onchange=e=>{metric=e.target.value;if(order==='source')order='auto';page=1;draw('#lb-metric');};
        host.querySelector('#lb-order').onchange=e=>{order=e.target.value;page=1;draw('#lb-order');};
        host.querySelectorAll('[data-sort-column]').forEach(b=>b.onclick=()=>{
          const c=b.dataset.sortColumn;order=c===metric&&order!=='source'?(direction==='asc'?'desc':'asc'):'auto';metric=c;page=1;draw({column:c});
        });
        host.querySelectorAll('[data-lb-page]').forEach(b=>b.onclick=()=>{page=Number(b.dataset.lbPage);draw();});
        host.querySelector('.board-table-scroll').scrollLeft=scrollLeft;
        updateUrl();
        if(chartType){
          await global.RadarWorkspace.action('chart',{track:t,rows,host:host.querySelector('#protocol-chart'),metric,chartType,dateBasis,toggle:false,onChange:change=>{
            if(token!==boardToken||drawId!==drawVersion)return;
            if(change.metric){metric=change.metric;if(order==='source')order='auto';page=1;}
            if(change.chartType)chartType=change.chartType;if(change.dateBasis)dateBasis=change.dateBasis;
            draw(change.focus);
          }});
        }
        if(drawId!==drawVersion||token!==boardToken)return;
        const target=typeof focus==='string'?host.querySelector(focus):focus?.column?[...host.querySelectorAll('[data-sort-column]')].find(b=>b.dataset.sortColumn===focus.column):null;
        target?.focus({preventScroll:true});
      }
      await draw();
    }catch(err){if(token!==boardToken)return;host.innerHTML='<div class="research-empty"><h2>榜单暂未载入</h2><p>请刷新重试。未载入不代表没有结果或分数为零。</p><button id="retry-board" class="btn">重试</button></div>';host.querySelector('#retry-board').onclick=()=>renderBoards(host);console.warn('Leaderboard:',err.message);}
  }
  global.RadarResearch={cancelBoards:()=>{boardToken++;},loadBoards,loadTrack,loadSetting,loadPaperResults,lifecycle,links,scopeNotice,configure,detail,enhance,renderBoards,sourceKey,boardGroups,protocolGroups,methodKey,methodGroups,familyMethodsHtml,pageWindow,rankRows,sortRows,boardRows,sortDirection,metricDirection,visibleResults,metricValue,benchmarkFamilies,richEvidence,datasetNames,formatScore,noteBlocks};
  if(typeof module!=='undefined')module.exports=global.RadarResearch;
})(typeof window!=='undefined'?window:globalThis);
