/* Default Benchmark view: Evaluation Setting -> independent result reports. */
'use strict';
(function(g){
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safe=v=>{try{const u=new URL(v,location.href);return ['https:','http:'].includes(u.protocol)&&!u.username&&!u.password?u.href:'#';}catch{return '#';}};
  const value=(v,unit)=>v==null?'—':esc(v)+(unit==='percent'?'%':unit==='seconds'?' s':'');
  function direction(setting,order){if(order==='asc'||order==='desc')return order;return setting.direction==='lower'?'asc':'desc';}
  function sortRows(rows,setting,metric,order='auto'){
    if(order==='source')return [...rows];
    const dir=direction(setting,order),sign=dir==='asc'?1:-1;
    return rows.map((r,i)=>({r,i,v:Number.isFinite(r.values?.[metric])?r.values[metric]:null}))
      .sort((a,b)=>{if(a.v===null&&b.v===null)return a.i-b.i;if(a.v===null)return 1;if(b.v===null)return -1;return (a.v-b.v)*sign||a.i-b.i;})
      .map(x=>x.r);
  }
  function searchNorm(value){return String(value||'').normalize('NFKC').toLowerCase().replace(/[·｜|/_,—–-]+/g,' ').replace(/\s+/g,' ').trim();}
  function searchSettings(settings,query){
    const tokens=searchNorm(query).split(' ').filter(Boolean);
    if(!tokens.length)return [...settings];
    return settings.filter(s=>{
      const hay=searchNorm([s.dataset,s.name,s.tasks,s.split,s.metric,s.evalId,...(s.columns||[])].join(' '));
      return tokens.every(token=>hay.includes(token));
    });
  }
  function searchBarHtml(term,settingCount,datasetCount){
    const active=Boolean(searchNorm(term));
    return `<form class="benchmark-search" id="benchmark-search-form" role="search"><label for="benchmark-search-input"><span>SEARCH BENCHMARKS</span><div class="benchmark-search-box"><input id="benchmark-search-input" type="search" value="${esc(term)}" placeholder="搜索 RoboTwin、18 tasks、Success Rate、Long Horizon…" autocomplete="off"><button class="btn" type="submit">搜索</button>${active?'<button class="btn benchmark-search-clear" id="benchmark-search-clear" type="button">清除</button>':''}</div></label><p>${active?`匹配 <b>${datasetCount}</b> 个 Benchmark · <b>${settingCount}</b> 个 Evaluation Setting`:'按 Benchmark 名称、Setting、任务、split、metric 或列名搜索；多个关键词可组合。'}</p></form>`;
  }
  function filterSettingsByTaxonomy(settings,taxonomy,focus='all',environment='all',tags=[]){
    const benchmarks=taxonomy?.benchmarks||{};
    return settings.filter(s=>{
      const meta=benchmarks[s.dataset];
      if(!meta)return false;
      if(focus!=='all'&&meta.focus!==focus)return false;
      if(environment!=='all'&&meta.environment!==environment)return false;
      return tags.every(tag=>meta.tags.includes(tag));
    });
  }
  function taxonomyBarHtml(taxonomy,focus,environment,tags,datasetCount,settingCount){
    if(!taxonomy?.benchmarks)return '';
    const active=focus!=='all'||environment!=='all'||tags.length>0;
    const focusButtons=['<button type="button" data-tax-focus="all" aria-pressed="'+String(focus==='all')+'">All</button>',...(taxonomy.focuses||[]).map(x=>`<button type="button" data-tax-focus="${esc(x.id)}" aria-pressed="${x.id===focus}">${esc(x.label)}</button>`)].join('');
    const envButtons=['<button type="button" data-tax-env="all" aria-pressed="'+String(environment==='all')+'">All</button>',...(taxonomy.environments||[]).map(x=>`<button type="button" data-tax-env="${esc(x.id)}" aria-pressed="${x.id===environment}">${esc(x.label)}</button>`)].join('');
    const tagBoxes=(taxonomy.tags||[]).map(x=>`<label><input type="checkbox" data-tax-tag="${esc(x.id)}" ${tags.includes(x.id)?'checked':''}><span>${esc(x.label)}</span></label>`).join('');
    return `<section class="benchmark-taxonomy" aria-label="Benchmark 分类筛选"><div class="taxonomy-group"><span>FOCUS</span><div class="taxonomy-chips">${focusButtons}</div></div><div class="taxonomy-group"><span>ENVIRONMENT</span><div class="taxonomy-chips">${envButtons}</div></div><details class="taxonomy-tags" ${tags.length?'open':''}><summary>MORE FILTERS · TAGS${tags.length?` · ${tags.length} selected`:''}</summary><div class="taxonomy-tag-grid">${tagBoxes}</div></details><div class="taxonomy-status"><span>当前范围 <b>${datasetCount}</b> Benchmarks · <b>${settingCount}</b> Settings</span>${active?'<button type="button" class="btn" id="taxonomy-clear">清除分类</button>':''}</div></section>`;
  }
  function paperMap(papers){return new Map((papers||[]).map(p=>[p.id,p.name||p.title||p.id]));}
  function setDataset(dataset,host){
    const u=new URL(location.href);u.searchParams.set('view','leaderboards');u.searchParams.set('dataset',dataset);
    for(const k of ['setting','track','lbMetric','lbOrder','lbBrowse','lbChart','lbTime','lbTrain','lbMethod','lbSource'])u.searchParams.delete(k);
    history.replaceState({},'',u);g.RadarResearch.renderBoards(host);
  }
  function options(values,current,label){
    return '<option value="all">'+esc(label)+'</option>'+values.map(([v,t])=>`<option value="${esc(v)}" ${v===current?'selected':''}>${esc(t)}</option>`).join('');
  }
  async function render(host,ctx){
    const {data,query,isCurrent,papers,loadSetting}=ctx,pnames=paperMap(papers);
    const datasets=[...new Set(data.tracks.map(t=>t.dataset))],searchTerm=(query.get('lbSearch')||'').slice(0,120),taxonomy=data.taxonomy||null;
    const focusIds=new Set((taxonomy?.focuses||[]).map(x=>x.id)),envIds=new Set((taxonomy?.environments||[]).map(x=>x.id)),tagIds=new Set((taxonomy?.tags||[]).map(x=>x.id));
    const focusFilter=focusIds.has(query.get('lbFocus'))?query.get('lbFocus'):'all',environmentFilter=envIds.has(query.get('lbEnv'))?query.get('lbEnv'):'all';
    const tagFilters=[...new Set((query.get('lbTags')||'').split(',').filter(x=>tagIds.has(x)))];
    const taxonomySettings=taxonomy?filterSettingsByTaxonomy(data.settings,taxonomy,focusFilter,environmentFilter,tagFilters):data.settings;
    const matchedSettings=searchSettings(taxonomySettings,searchTerm);
    const visibleDatasets=[...new Set(matchedSettings.map(s=>s.dataset))];
    let dataset=datasets.includes(query.get('dataset'))?query.get('dataset'):(datasets.includes('LIBERO')?'LIBERO':datasets[0]);
    if(visibleDatasets.length&&!visibleDatasets.includes(dataset))dataset=visibleDatasets[0];
    let settings=matchedSettings.filter(s=>s.dataset===dataset);
    if(!settings.length){
      host.innerHTML=searchBarHtml(searchTerm,matchedSettings.length,visibleDatasets.length)+taxonomyBarHtml(taxonomy,focusFilter,environmentFilter,tagFilters,visibleDatasets.length,matchedSettings.length)+'<div class="research-empty benchmark-search-empty"><h2>没有匹配的 Benchmark / Setting</h2><p>可以清除部分分类条件，或尝试更短的关键词，例如 “RoboTwin”、“18 tasks”、“success rate” 或 “long”。</p></div>';
      bindExploreControls();
      return;
    }
    let settingId=settings.some(s=>s.id===query.get('setting'))?query.get('setting'):settings[0].id;
    let metric=(query.get('lbMetric')||'').slice(0,160),order=['auto','asc','desc','source'].includes(query.get('lbOrder'))?query.get('lbOrder'):'auto';
    let trainFilter=(query.get('lbTrain')||'all').slice(0,180),methodFilter=(query.get('lbMethod')||'all').slice(0,180),sourceFilter=(query.get('lbSource')||'all').slice(0,180);
    let page=1,drawVersion=0;
    function navigate(mutator){
      const u=new URL(location.href);mutator(u.searchParams);
      for(const k of ['setting','track','lbTrain','lbMethod','lbSource'])u.searchParams.delete(k);
      history.replaceState({},'',u);g.RadarResearch.renderBoards(host);
    }
    function bindExploreControls(){
      const form=host.querySelector('#benchmark-search-form'),input=host.querySelector('#benchmark-search-input');
      if(form)form.onsubmit=e=>{e.preventDefault();navigate(p=>{const q=input.value.trim().slice(0,120);q?p.set('lbSearch',q):p.delete('lbSearch');});};
      host.querySelector('#benchmark-search-clear')?.addEventListener('click',()=>navigate(p=>p.delete('lbSearch')));
      host.querySelectorAll('[data-tax-focus]').forEach(b=>b.onclick=()=>navigate(p=>{const v=b.dataset.taxFocus;v==='all'?p.delete('lbFocus'):p.set('lbFocus',v);}));
      host.querySelectorAll('[data-tax-env]').forEach(b=>b.onclick=()=>navigate(p=>{const v=b.dataset.taxEnv;v==='all'?p.delete('lbEnv'):p.set('lbEnv',v);}));
      host.querySelectorAll('[data-tax-tag]').forEach(box=>box.onchange=()=>navigate(p=>{const selected=[...host.querySelectorAll('[data-tax-tag]:checked')].map(x=>x.dataset.taxTag);selected.length?p.set('lbTags',selected.join(',')):p.delete('lbTags');}));
      host.querySelector('#taxonomy-clear')?.addEventListener('click',()=>navigate(p=>{p.delete('lbFocus');p.delete('lbEnv');p.delete('lbTags');}));
    }
    function updateUrl(){
      const u=new URL(location.href);u.searchParams.set('view','leaderboards');u.searchParams.set('dataset',dataset);u.searchParams.set('setting',settingId);
      u.searchParams.set('lbMetric',metric);u.searchParams.set('lbOrder',order);
      for(const [k,v] of [['lbTrain',trainFilter],['lbMethod',methodFilter],['lbSource',sourceFilter]])v==='all'?u.searchParams.delete(k):u.searchParams.set(k,v);
      searchTerm?u.searchParams.set('lbSearch',searchTerm):u.searchParams.delete('lbSearch');
      for(const k of ['track','lbBrowse','lbChart','lbTime'])u.searchParams.delete(k);history.replaceState({},'',u);
    }
    async function draw(focus){
      const drawId=++drawVersion,setting=settings.find(s=>s.id===settingId)||settings[0];settingId=setting.id;
      if(!setting.columns.includes(metric))metric=setting.columns.includes('Average')?'Average':setting.columns[0];
      let loaded;
      try{loaded=await loadSetting(setting,data);}catch{
        if(drawId!==drawVersion||!isCurrent())return;
        host.innerHTML='<p class="research-warning">当前 Setting 暂未载入；未载入不等于零分。</p><button class="btn" id="retry-setting">重试</button>';
        host.querySelector('#retry-setting').onclick=()=>draw();return;
      }
      if(drawId!==drawVersion||!isCurrent())return;
      const fullSetting=loaded.setting||setting,trackmap=new Map(loaded.tracks.map(t=>[t.id,t]));
      const accepted=loaded.results.filter(r=>r.evidence==='checked');
      const trainMap=fullSetting.trainingByResult||{},trainMeta=new Map((fullSetting.trainingOptions||setting.trainingOptions||[]).map(x=>[x.id,x]));
      const trainLabel=r=>trainMeta.get(trainMap[r.id])?.label||'训练数据未完整披露';
      const methods=[...new Set(accepted.map(r=>r.method))].sort((a,b)=>a.localeCompare(b,'en',{numeric:true,sensitivity:'base'}));
      const sources=[...new Set(accepted.map(r=>r.paperId))].map(id=>[id,pnames.get(id)||id]).sort((a,b)=>a[1].localeCompare(b[1],'en',{numeric:true,sensitivity:'base'}));
      const trains=[...new Set(accepted.map(r=>trainMap[r.id]).filter(Boolean))].map(id=>[id,trainMeta.get(id)?.label||id]);
      if(trainFilter!=='all'&&!trains.some(x=>x[0]===trainFilter))trainFilter='all';
      if(methodFilter!=='all'&&!methods.includes(methodFilter))methodFilter='all';
      if(sourceFilter!=='all'&&!sources.some(x=>x[0]===sourceFilter))sourceFilter='all';
      const filtered=accepted.filter(r=>(trainFilter==='all'||trainMap[r.id]===trainFilter)&&(methodFilter==='all'||r.method===methodFilter)&&(sourceFilter==='all'||r.paperId===sourceFilter));
      const rows=sortRows(filtered,setting,metric,order),size=20,pages=Math.max(1,Math.ceil(rows.length/size));page=Math.max(1,Math.min(page,pages));const dir=direction(setting,order);
      const header=c=>`<th scope="col" ${c===metric&&order!=='source'?`aria-sort="${dir==='asc'?'ascending':'descending'}"`:''}><button class="board-sort-button" data-setting-sort="${esc(c)}">${esc(c)} <span aria-hidden="true">${c===metric&&order!=='source'?(dir==='asc'?'▲':'▼'):'↕'}</span></button></th>`;
      const current=rows.slice((page-1)*size,page*size),comparable=trainFilter!=='all';
      host.innerHTML=searchBarHtml(searchTerm,matchedSettings.length,visibleDatasets.length)+taxonomyBarHtml(taxonomy,focusFilter,environmentFilter,tagFilters,visibleDatasets.length,matchedSettings.length)+`<div class="leaderboard-top"><div class="dataset-tabs" role="group" aria-label="数据集">${visibleDatasets.map(d=>`<button data-setting-dataset="${esc(d)}" aria-pressed="${d===dataset}">${esc(d)}</button>`).join('')}</div><div class="board-update">目录更新 ${esc(data.updatedAt)} · ${settings.length} evaluation settings</div></div>
        <div class="setting-picker"><label><span>SETTING · EVALUATION PROTOCOL</span><select id="setting-select">${settings.map(s=>`<option value="${esc(s.id)}" ${s.id===settingId?'selected':''}>${esc(s.name)} · ${s.resultCount} reports</option>`).join('')}</select></label><a class="btn setting-advanced-link" href="?view=leaderboards&amp;dataset=${encodeURIComponent(dataset)}&amp;track=${encodeURIComponent(setting.primaryTrackId)}">高级：原始 track / 图表</a></div>
        <section class="setting-summary" data-setting-id="${esc(setting.id)}"><div class="setting-summary-main"><span class="setting-kicker">SETTING · EVALUATION PROTOCOL ONLY</span><h2>${esc(setting.name)}</h2><p class="setting-definition">Training Data、训练 recipe、base model 与来源论文不再拆 Setting；它们直接显示在下方结果行。</p></div><div class="setting-facts"><span>Tasks <b>${esc(setting.tasks)}</b></span><span>Eval <b>${esc(setting.split)}</b></span><span>Metric <b>${esc(setting.metric)}</b></span><span>Reports <b>${setting.resultCount}</b></span><span>Papers <b>${setting.paperCount}</b></span><span>Training Data <b>${(setting.trainingOptions||[]).length} variants</b></span></div><details class="setting-protocol"><summary>展开评测协议说明</summary><p>${esc(setting.protocol)}</p><small>同一 Setting 只表示评测问题一致；不同论文的回合数、种子、训练预算或实现细节仍以每行 Evidence 为准。</small></details></section>
        <div class="setting-filter-bar"><label>Training Data<select id="setting-train">${options(trains,trainFilter,'全部训练数据')}</select></label><label>Method<select id="setting-method">${options(methods.map(x=>[x,x]),methodFilter,'全部方法')}</select></label><label>Source<select id="setting-source">${options(sources,sourceFilter,'全部来源')}</select></label></div>
        <div class="setting-toolbar"><div><strong>Method / Score / Training Data / Source</strong><span>${comparable?'已限定同一 Training Data；仍需注意 recipe 与实现差异。':'默认展示所有公开报告；排序不等于公平排名。'}</span></div><div class="board-controls setting-controls"><label>排序指标<select id="setting-metric">${setting.columns.map(c=>`<option ${c===metric?'selected':''}>${esc(c)}</option>`).join('')}</select></label><label>排列<select id="setting-order"><option value="auto" ${order==='auto'?'selected':''}>按指标优劣</option><option value="desc" ${order==='desc'?'selected':''}>数值降序</option><option value="asc" ${order==='asc'?'selected':''}>数值升序</option><option value="source" ${order==='source'?'selected':''}>原记录顺序</option></select></label><button class="btn" id="export-setting-csv">导出当前结果 CSV</button></div></div>
        <p class="board-sort-status" role="status">${comparable?'同一 Training Data 子集 · ':''}${order==='source'?'按原记录顺序展示':esc(metric)+' · '+(dir==='asc'?'升序':'降序')} · ${rows.length}/${accepted.length} reports · 不生成跨来源名次。</p>
        <div class="board-table-scroll" role="region" aria-label="Setting 结果表" tabindex="0"><table class="board-table setting-table"><caption>${esc(setting.name)} · ${rows.length} 条当前筛选结果</caption><thead><tr><th scope="col">Method</th>${setting.columns.map(header).join('')}<th scope="col">Training Data</th><th scope="col">来源论文</th><th scope="col">Recipe / Evidence</th></tr></thead><tbody>${current.map(r=>{const t=trackmap.get(r.trackId),paper=pnames.get(r.paperId)||r.paperId;return `<tr data-result-id="${esc(r.id)}"><td class="setting-method"><strong>${esc(r.method)}</strong><small>${esc(r.attribution==='author-reported'?'作者方法':r.attribution==='reported-baseline'?'论文引用基线':'独立复现')}</small></td>${setting.columns.map(c=>`<td class="numeric ${c===metric?'selected-metric':''}">${value(r.values?.[c],setting.unit)}</td>`).join('')}<td class="setting-training-cell"><strong>${esc(trainLabel(r))}</strong><small>${trainMeta.get(trainMap[r.id])?.known?'已识别训练数据':'来源未完整披露'}</small></td><td class="setting-source"><button class="board-paper-link" data-paper="${esc(r.paperId)}">${esc(paper)}</button><small>${esc(r.paperId)} · ${esc(r.sourceVersion)}</small></td><td class="setting-recipe"><details><summary>展开 recipe</summary><div class="recipe-evidence-grid"><span>Recipe <b>${esc(t?.recipeName||t?.name||r.trackId)}</b></span><span>原始 Training 字段 <b>${esc(r.trainingData)}</b></span><span>Training recipe <b>${esc(t?.trainingRegime||'未单独记录')}</b></span><span>Evaluation <b>${esc(r.evaluationNotes)}</b></span><span>Locator <b>${esc(r.locator)}</b></span><span>Verified <b>${esc(r.verifiedAt)}</b></span></div><div class="recipe-evidence-actions"><a href="${esc(safe(r.source))}" target="_blank" rel="noopener noreferrer">原始证据 ↗</a><a href="?view=leaderboards&amp;dataset=${encodeURIComponent(dataset)}&amp;track=${encodeURIComponent(r.trackId)}">打开原始 track ↗</a></div></details></td></tr>`;}).join('')}</tbody></table>${rows.length?'':'<p class="research-empty">当前筛选条件下没有结果。</p>'}</div>
        <div class="pagination">${Array.from({length:pages},(_,i)=>i+1).slice(Math.max(0,page-3),Math.min(pages,page+2)).map(n=>`<button data-setting-page="${n}" class="${n===page?'active':''}">${n}</button>`).join('')}<span>每页20条；同一 Method 的不同论文 / recipe 报告始终保留。</span></div>`;
      bindExploreControls();
      host.querySelectorAll('[data-setting-dataset]').forEach(b=>b.onclick=()=>setDataset(b.dataset.settingDataset,host));
      host.querySelector('#setting-select').onchange=e=>{settingId=e.target.value;metric='';order='auto';trainFilter=methodFilter=sourceFilter='all';page=1;draw('#setting-select');};
      host.querySelector('#setting-train').onchange=e=>{trainFilter=e.target.value;page=1;draw('#setting-train');};
      host.querySelector('#setting-method').onchange=e=>{methodFilter=e.target.value;page=1;draw('#setting-method');};
      host.querySelector('#setting-source').onchange=e=>{sourceFilter=e.target.value;page=1;draw('#setting-source');};
      host.querySelector('#setting-metric').onchange=e=>{metric=e.target.value;if(order==='source')order='auto';page=1;draw('#setting-metric');};
      host.querySelector('#setting-order').onchange=e=>{order=e.target.value;page=1;draw('#setting-order');};
      host.querySelectorAll('[data-setting-sort]').forEach(b=>b.onclick=()=>{const c=b.dataset.settingSort;order=c===metric&&order!=='source'?(dir==='asc'?'desc':'asc'):'auto';metric=c;page=1;draw({column:c});});
      host.querySelectorAll('[data-setting-page]').forEach(b=>b.onclick=()=>{page=Number(b.dataset.settingPage);draw();});
      host.querySelector('#export-setting-csv').onclick=()=>g.RadarWorkspace.action('csv',{track:{id:setting.id,columns:setting.columns,unit:setting.unit,protocol:setting.id},rows});
      updateUrl();const target=typeof focus==='string'?host.querySelector(focus):focus?.column?[...host.querySelectorAll('[data-setting-sort]')].find(b=>b.dataset.settingSort===focus.column):null;target?.focus({preventScroll:true});
    }
    await draw();
  }
  g.RadarBenchmarkSettings={render,sortRows,direction,searchNorm,searchSettings,filterSettingsByTaxonomy};
  if(typeof module!=='undefined')module.exports=g.RadarBenchmarkSettings;
})(typeof window!=='undefined'?window:globalThis);
