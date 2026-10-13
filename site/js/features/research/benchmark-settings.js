/* Default Benchmark view: Evaluation Setting -> independent result reports. */
'use strict';
(function(g){
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safe=v=>{try{const u=new URL(v,location.href);return ['https:','http:'].includes(u.protocol)&&!u.username&&!u.password?u.href:'#';}catch{return '#';}};
  const value=(v,unit)=>v==null?'—':esc(v)+(unit==='percent'?'%':unit==='seconds'?' s':'');
  function direction(setting,order,metric){if(order==='asc'||order==='desc')return order;const dir=setting?.columnMeta?.[metric]?.direction||setting.direction;return dir==='lower'?'asc':'desc';}
  function sortRows(rows,setting,metric,order='auto'){
    if(order==='source')return [...rows];
    const dir=direction(setting,order,metric),sign=dir==='asc'?1:-1;
    return rows.map((r,i)=>({r,i,v:Number.isFinite(r.values?.[metric])?r.values[metric]:null}))
      .sort((a,b)=>{if(a.v===null&&b.v===null)return a.i-b.i;if(a.v===null)return 1;if(b.v===null)return -1;return (a.v-b.v)*sign||a.i-b.i;})
      .map(x=>x.r);
  }
  function searchNorm(value){return String(value||'').normalize('NFKC').toLowerCase().replace(/[·｜|/_,—–-]+/g,' ').replace(/\s+/g,' ').trim();}
  function protocolFacts(setting){
    const scope=String(setting?.evalId||'reported').replace(/^auto:/,'');
    const match=String(setting?.id||'').match(/([a-f0-9]{12})$/i);
    const fingerprint=match?`ep1-${match[1].toLowerCase()}`:String(setting?.id||scope);
    return {
      fingerprint,scope,
      fields:[
        ['Benchmark',setting?.dataset||'—'],
        ['Task scope',scope||'reported'],
        ['Tasks',setting?.tasks||'—'],
        ['Split / conditions',setting?.split||'—'],
        ['Metric',setting?.metric||'—'],
        ['Unit',setting?.unit||'—'],
        ['Direction',setting?.direction||'—'],
        ['Reported columns',(setting?.columns||[]).join(' / ')||'—']
      ]
    };
  }
  function canonicalColumns(track){return (track?.columns||[]).map(x=>searchNorm(x).replace(/\s+/g,''));}
  function knownTaskCount(track){
    const m=String(track?.tasks||track?.name||'').match(/(^|\D)(\d{1,3})\s*(?:tasks?|任务|skills?|skill types?|atomic tasks?)(\D|$)/i);
    if(m)return Number(m[2]);
    const raw=String(track?.tasks||'').trim();return /^\d{1,3}$/.test(raw)?Number(raw):null;
  }
  function compatibilityLevel(primary,track){
    if(!primary||!track)return 'compatible';
    if(primary.dataset!==track.dataset||primary.unit!==track.unit||primary.direction!==track.direction)return 'incompatible';
    const a=canonicalColumns(primary),b=canonicalColumns(track);
    if(a.length!==b.length||a.some((x,i)=>x!==b[i]))return 'partial';
    const ac=knownTaskCount(primary),bc=knownTaskCount(track);
    if(ac!==null&&bc!==null&&ac!==bc)return 'partial';
    if(searchNorm(primary.tasks)===searchNorm(track.tasks)&&searchNorm(primary.split)===searchNorm(track.split))return 'exact';
    return 'compatible';
  }
  function compatibilitySummary(setting,tracks){
    const primary=(tracks||[]).find(t=>t.id===setting?.primaryTrackId)||(tracks||[])[0];
    const counts={exact:0,compatible:0,partial:0,incompatible:0};
    for(const track of tracks||[])counts[compatibilityLevel(primary,track)]++;
    return counts;
  }
  function searchSettings(settings,query){
    const tokens=searchNorm(query).split(' ').filter(Boolean);
    if(!tokens.length)return [...settings];
    return settings.filter(s=>{
      const hay=searchNorm([s.dataset,s.name,s.tasks,s.split,s.metric,s.evalId,...(s.columns||[]),...(s.methodNames||[])].join(' '));
      return tokens.every(token=>hay.includes(token));
    });
  }
  function searchBarHtml(term,settingCount,datasetCount){
    const active=Boolean(searchNorm(term));
    return `<form class="benchmark-search" id="benchmark-search-form" role="search"><label for="benchmark-search-input"><span>SEARCH BENCHMARKS</span><div class="benchmark-search-box"><input id="benchmark-search-input" type="search" value="${esc(term)}" placeholder="搜索 Benchmark、模型 π0.5、Method、评测协议…" autocomplete="off"><button class="btn" type="submit">搜索</button>${active?'<button class="btn benchmark-search-clear" id="benchmark-search-clear" type="button">清除</button>':''}</div></label><p>${active?`匹配 <b>${datasetCount}</b> 个 Benchmark · <b>${settingCount}</b> 个 Evaluation Setting`:'支持搜索 Benchmark、Method、任务、评测条件及指标；多个关键词可组合。'}</p></form>`;
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
  function modeBarHtml(registry,mode){
    const list=Object.values(registry?.benchmarks||{});
    const b=list.filter(x=>x.kind==='benchmark').length, c=list.filter(x=>x.kind==='case-study').length;
    return '<nav class="benchmark-mode-switch" aria-label="Benchmark 视图">'+
      '<button type="button" data-board-kind="benchmark" aria-pressed="'+String(mode==='benchmark')+'">标准 Benchmark <b>'+b+'</b></button>'+
      '<button type="button" data-board-kind="case-study" aria-pressed="'+String(mode==='case-study')+'">论文实验 / 真机案例 <b>'+c+'</b></button></nav>';
  }
  function datasetContextHtml(registry,dataset){
    const meta=registry?.benchmarks?.[dataset]||{},kind=meta.kind==='case-study'?'论文专属实验 / 非统一榜单':'公共 Benchmark / 来源报告比较';
    const official=meta.officialUrl?'<a href="'+esc(safe(meta.officialUrl))+'" target="_blank" rel="noopener noreferrer">官方主页 / 榜单 ↗</a>':'';
    return '<section class="benchmark-dataset-context"><strong>'+esc(dataset)+'</strong><span>'+kind+'</span>'+official+'</section>';
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
    const registry=data.benchmarkRegistry||{},kind=query.get('lbType')==='cases'?'case-study':'benchmark',modeHtml=modeBarHtml(registry,kind);
    let rowMode=query.get('lbRows')==='all'||kind==='case-study'?'all':'main',columnMode=query.get('lbCols')==='all'?'all':'focus';
    const focusIds=new Set((taxonomy?.focuses||[]).map(x=>x.id)),envIds=new Set((taxonomy?.environments||[]).map(x=>x.id)),tagIds=new Set((taxonomy?.tags||[]).map(x=>x.id));
    const focusFilter=focusIds.has(query.get('lbFocus'))?query.get('lbFocus'):'all',environmentFilter=envIds.has(query.get('lbEnv'))?query.get('lbEnv'):'all';
    const tagFilters=[...new Set((query.get('lbTags')||'').split(',').filter(x=>tagIds.has(x)))];
    const scopeSettings=data.settings.filter(s=>(registry.benchmarks?.[s.dataset]?.kind||'benchmark')===kind);
    const taxonomySettings=taxonomy?filterSettingsByTaxonomy(scopeSettings,taxonomy,focusFilter,environmentFilter,tagFilters):scopeSettings;
    const matchedSettings=searchSettings(taxonomySettings,searchTerm);
    const visibleDatasets=[...new Set(matchedSettings.map(s=>s.dataset))];
    let dataset=datasets.includes(query.get('dataset'))?query.get('dataset'):(datasets.includes('LIBERO')?'LIBERO':datasets[0]);
    if(visibleDatasets.length&&!visibleDatasets.includes(dataset))dataset=visibleDatasets[0];
    let settings=matchedSettings.filter(s=>s.dataset===dataset);
    settings.sort((a,b)=>(b.primaryPaperCount||0)-(a.primaryPaperCount||0)||(b.primaryResultCount||0)-(a.primaryResultCount||0)||a.name.localeCompare(b.name));
    const settingLabel=s=>s.name+(settings.filter(x=>x.name===s.name).length>1?' · '+s.evalId.replace(/^auto:/,''):'');
    if(!settings.length){
      host.innerHTML=modeHtml+searchBarHtml(searchTerm,matchedSettings.length,visibleDatasets.length)+taxonomyBarHtml(taxonomy,focusFilter,environmentFilter,tagFilters,visibleDatasets.length,matchedSettings.length)+'<div class="research-empty benchmark-search-empty"><h2>没有匹配的 Benchmark / Setting</h2><p>可以清除部分分类条件，或尝试更短的关键词，例如 “RoboTwin”、“18 tasks”、“success rate” 或 “long”。</p></div>';
      bindExploreControls();
      return;
    }
    const requestedSetting=query.get('setting'),legacyTrack=registry.legacySettingTracks?.[requestedSetting];
    let settingId=settings.find(s=>s.id===requestedSetting||(legacyTrack&&s.trackIds.includes(legacyTrack)))?.id||settings.find(s=>(s.primaryResultCount||0)>0)?.id||settings[0].id;
    let metric=(query.get('lbMetric')||'').slice(0,160),order=['auto','asc','desc','source'].includes(query.get('lbOrder'))?query.get('lbOrder'):'auto';
    let trainFilter=(query.get('lbTrain')||'all').slice(0,180),methodFilter=(query.get('lbMethod')||'all').slice(0,180),sourceFilter=(query.get('lbSource')||'all').slice(0,180);
    let page=1,drawVersion=0,renderedSettingId=null;
    function navigate(mutator){
      const u=new URL(location.href);mutator(u.searchParams);
      for(const k of ['setting','track','lbTrain','lbMethod','lbSource'])u.searchParams.delete(k);
      history.replaceState({},'',u);g.RadarResearch.renderBoards(host);
    }
    function bindExploreControls(){
      host.querySelectorAll('[data-board-kind]').forEach(b=>b.onclick=()=>navigate(p=>{const v=b.dataset.boardKind;v==='benchmark'?p.delete('lbType'):p.set('lbType','cases');p.delete('dataset');p.delete('lbRows');p.delete('lbCols');}));
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
      kind==='case-study'?u.searchParams.set('lbType','cases'):u.searchParams.delete('lbType');
      rowMode==='all'?u.searchParams.set('lbRows','all'):u.searchParams.delete('lbRows');
      columnMode==='all'?u.searchParams.set('lbCols','all'):u.searchParams.delete('lbCols');
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
      const protocolView=protocolFacts(fullSetting),compatibility=compatibilitySummary(fullSetting,loaded.tracks);
      const allChecked=loaded.results.filter(r=>r.evidence==='checked');
      const selectedRows=rowMode==='all'?allChecked:allChecked.filter(r=>(r.displayTier||'primary')==='primary');
      const accepted=selectedRows.length?selectedRows:allChecked;
      if(!selectedRows.length&&allChecked.length)rowMode='all';
      const trainMap=fullSetting.trainingByResult||{},trainMeta=new Map((fullSetting.trainingOptions||setting.trainingOptions||[]).map(x=>[x.id,x]));
      const trainLabel=r=>trainMeta.get(trainMap[r.id])?.label||'训练数据未完整披露';
      const methods=[...new Set(accepted.map(r=>r.method))].sort((a,b)=>a.localeCompare(b,'en',{numeric:true,sensitivity:'base'}));
      if(methodFilter==='all'&&searchTerm){const same=methods.find(m=>searchNorm(m)===searchNorm(searchTerm));if(same)methodFilter=same;}
      const sources=[...new Set(accepted.map(r=>r.paperId))].map(id=>[id,pnames.get(id)||id]).sort((a,b)=>a[1].localeCompare(b[1],'en',{numeric:true,sensitivity:'base'}));
      const trains=[...new Set(accepted.map(r=>trainMap[r.id]).filter(Boolean))].map(id=>[id,trainMeta.get(id)?.label||id]);
      if(trainFilter!=='all'&&!trains.some(x=>x[0]===trainFilter))trainFilter='all';
      if(methodFilter!=='all'&&!methods.includes(methodFilter))methodFilter='all';
      if(sourceFilter!=='all'&&!sources.some(x=>x[0]===sourceFilter))sourceFilter='all';
      const filtered=accepted.filter(r=>(trainFilter==='all'||trainMap[r.id]===trainFilter)&&(methodFilter==='all'||r.method===methodFilter)&&(sourceFilter==='all'||r.paperId===sourceFilter));
      const rows=sortRows(filtered,setting,metric,order),size=20,pages=Math.max(1,Math.ceil(rows.length/size));page=Math.max(1,Math.min(page,pages));const dir=direction(setting,order,metric);const displayColumns=columnMode==='all'||setting.columns.length<=7?setting.columns:[...new Set([metric,...(setting.columns.includes('Average')&&metric!=='Average'?['Average']:[])])];
      const header=c=>`<th scope="col" ${c===metric&&order!=='source'?`aria-sort="${dir==='asc'?'ascending':'descending'}"`:''}><button class="board-sort-button" data-setting-sort="${esc(c)}">${esc(c)} <span aria-hidden="true">${c===metric&&order!=='source'?(dir==='asc'?'▲':'▼'):'↕'}</span></button></th>`;
      const current=rows.slice((page-1)*size,page*size),comparable=trainFilter!=='all';
      // Prepare only the visible rows once. Sort/filter/page changes keep the
      // Benchmark navigation, taxonomy and protocol DOM alive instead of
      // reparsing the entire screen (and collapsing expanded protocol details).
      const tableRows=current.map(r=>{const t=trackmap.get(r.trackId),paper=pnames.get(r.paperId)||r.paperId;return `<tr data-result-id="${esc(r.id)}"><td class="setting-method"><strong>${esc(r.method)}</strong><small>${esc(r.sourceClass==='official-snapshot'?'官方快照':r.attribution==='author-reported'?'作者报告':r.attribution==='reported-baseline'?'论文引用基线':'独立复现')}${r.displayTier==='reference'?' · 重复引用':r.displayTier==='sweep'?' · 预算实验':r.displayTier==='paper'?' · 专项实验':''}</small></td>${displayColumns.map(c=>`<td class="numeric ${c===metric?'selected-metric':''}">${value(r.values?.[c],setting.columnMeta?.[c]?.unit||setting.unit)}</td>`).join('')}<td class="setting-training-cell"><strong>${esc(trainLabel(r))}</strong><small>${trainMeta.get(trainMap[r.id])?.known?'已识别训练数据':'来源未完整披露'}</small></td><td class="setting-source"><button class="board-paper-link" data-paper="${esc(r.paperId)}">${esc(paper)}</button><small>${esc(r.paperId)} · ${esc(r.sourceVersion)}</small></td><td class="setting-recipe"><details><summary>展开 recipe</summary><div class="recipe-evidence-grid"><span>Recipe <b>${esc(t?.recipeName||t?.name||r.trackId)}</b></span><span>原始 Training 字段 <b>${esc(r.trainingData)}</b></span><span>Training recipe <b>${esc(t?.trainingRegime||'未单独记录')}</b></span><span>Evaluation <b>${esc(r.evaluationNotes)}</b></span><span>Locator <b>${esc(r.locator)}</b></span><span>Verified <b>${esc(r.verifiedAt)}</b></span></div><div class="recipe-evidence-actions"><a href="${esc(safe(r.source))}" target="_blank" rel="noopener noreferrer">原始证据 ↗</a><a href="?view=leaderboards&amp;dataset=${encodeURIComponent(dataset)}&amp;track=${encodeURIComponent(r.trackId)}">打开原始 track ↗</a></div></details></td></tr>`;}).join('');
      const bindResultControls=()=>{
      bindExploreControls();
      host.querySelectorAll('[data-setting-dataset]').forEach(b=>b.onclick=()=>setDataset(b.dataset.settingDataset,host));
      host.querySelectorAll('[data-rows-mode]').forEach(b=>b.onclick=()=>{rowMode=b.dataset.rowsMode;page=1;draw();});
      host.querySelector('#setting-columns-toggle')?.addEventListener('click',()=>{columnMode=columnMode==='all'?'focus':'all';renderedSettingId=null;draw();});
      host.querySelector('#setting-select').onchange=e=>{settingId=e.target.value;metric='';order='auto';trainFilter=methodFilter=sourceFilter='all';page=1;draw('#setting-select');};
      host.querySelector('#setting-train').onchange=e=>{trainFilter=e.target.value;page=1;draw('#setting-train');};
      host.querySelector('#setting-method').onchange=e=>{methodFilter=e.target.value;page=1;draw('#setting-method');};
      host.querySelector('#setting-source').onchange=e=>{sourceFilter=e.target.value;page=1;draw('#setting-source');};
      host.querySelector('#setting-metric').onchange=e=>{metric=e.target.value;if(order==='source')order='auto';page=1;renderedSettingId=null;draw('#setting-metric');};
      host.querySelector('#setting-order').onchange=e=>{order=e.target.value;page=1;draw('#setting-order');};
      host.querySelectorAll('[data-setting-sort]').forEach(b=>b.onclick=()=>{const c=b.dataset.settingSort;if(columnMode!=='all'&&c!==metric)renderedSettingId=null;order=c===metric&&order!=='source'?(dir==='asc'?'desc':'asc'):'auto';metric=c;page=1;draw({column:c});});
      host.querySelectorAll('[data-setting-page]').forEach(b=>b.onclick=()=>{page=Number(b.dataset.settingPage);draw();});
      host.querySelector('#export-setting-csv').onclick=()=>g.RadarWorkspace.action('csv',{track:{id:setting.id,columns:setting.columns,unit:setting.unit,protocol:setting.id},rows});
      updateUrl();const target=typeof focus==='string'?host.querySelector(focus):focus?.column?[...host.querySelectorAll('[data-setting-sort]')].find(b=>b.dataset.settingSort===focus.column):null;target?.focus({preventScroll:true});
      };
      const existing=renderedSettingId===setting.id?host.querySelector('.setting-table'):null;
      if(existing && host.querySelector('#setting-select')){
        existing.querySelector('tbody').innerHTML=tableRows;
        existing.querySelector('caption').textContent=setting.name+' · '+rows.length+' 条当前筛选结果';
        host.querySelector('.board-sort-status').textContent=(comparable?'已筛选训练数据 · ':'')+(order==='source'?'原记录顺序':metric+' · '+(dir==='asc'?'升序':'降序'))+' · '+rows.length+'/'+accepted.length+' 当前视图 / 全部 '+allChecked.length+' 条 · 不生成跨来源公平名次。';
        host.querySelectorAll('[data-rows-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.rowsMode===rowMode)));
        host.querySelector('.setting-toolbar span').textContent=comparable?'已限定 Training Data；仍需核对实现及训练差异。':rowMode==='main'?'默认仅展示独立主比较记录；所有来源报告可切换查看。':'完整来源记录；含训练扫描、论文专项实验和重复引用。';
        const pager=host.querySelector('.pagination');
        pager.innerHTML=Array.from({length:pages},(_,i)=>i+1).slice(Math.max(0,page-3),Math.min(pages,page+2)).map(n=>`<button data-setting-page="${n}" class="${n===page?'active':''}">${n}</button>`).join('')+'<span>每页20条；同一 Method 的不同论文 / recipe 报告始终保留。</span>';
        const empty=host.querySelector('.board-table-scroll > .research-empty');
        if(rows.length)empty?.remove();
        else if(!empty)host.querySelector('.board-table-scroll').insertAdjacentHTML('beforeend','<p class="research-empty">当前筛选条件下没有结果。</p>');
        host.querySelector('#setting-metric').value=metric;
        host.querySelector('#setting-order').value=order;
        host.querySelector('#setting-train').value=trainFilter;
        host.querySelector('#setting-method').value=methodFilter;
        host.querySelector('#setting-source').value=sourceFilter;
        host.querySelectorAll('[data-setting-sort]').forEach(button=>{
          const col=button.dataset.settingSort,selected=col===metric&&order!=='source',th=button.closest('th');
          button.querySelector('span').textContent=selected?(dir==='asc'?'▲':'▼'):'↕';
          if(selected)th.setAttribute('aria-sort',dir==='asc'?'ascending':'descending');
          else th.removeAttribute('aria-sort');
        });
        bindResultControls();
        return;
      }
      host.innerHTML=modeHtml+searchBarHtml(searchTerm,matchedSettings.length,visibleDatasets.length)+taxonomyBarHtml(taxonomy,focusFilter,environmentFilter,tagFilters,visibleDatasets.length,matchedSettings.length)+`<div class="leaderboard-top"><div class="dataset-tabs" role="group" aria-label="数据集">${visibleDatasets.map(d=>`<button data-setting-dataset="${esc(d)}" aria-pressed="${d===dataset}">${esc(d)}</button>`).join('')}</div><div class="board-update">目录更新 ${esc(data.updatedAt)} · ${settings.length} evaluation settings</div></div>
        ${datasetContextHtml(registry,dataset)}
        <div class="setting-picker"><label><span>SETTING · EVALUATION PROTOCOL</span><select id="setting-select">${settings.map(s=>`<option value="${esc(s.id)}" ${s.id===settingId?'selected':''}>${esc(settingLabel(s))} · 主 ${s.primaryResultCount??s.resultCount} / 全 ${s.resultCount} 条</option>`).join('')}</select></label><a class="btn setting-advanced-link" href="?view=leaderboards&amp;dataset=${encodeURIComponent(dataset)}&amp;track=${encodeURIComponent(setting.primaryTrackId)}">高级：原始 track / 图表</a></div>
        <section class="setting-summary" data-setting-id="${esc(setting.id)}"><div class="setting-summary-main"><span class="setting-kicker">SETTING · EVALUATION PROTOCOL ONLY</span><h2>${esc(setting.name)}</h2><p class="setting-definition">Training Data、训练 recipe、base model 与来源论文不再拆 Setting；它们直接显示在下方结果行。</p></div><div class="setting-facts"><span>Tasks <b>${esc(setting.tasks)}</b></span><span>Eval <b>${esc(setting.split)}</b></span><span>Metric <b>${esc(setting.metric)}</b></span><span>主比较 / 全记录 <b>${setting.primaryResultCount??setting.resultCount} / ${setting.resultCount}</b></span><span>Papers <b>${setting.paperCount}</b></span><span>最近一条结果核验 <b>${esc(setting.latestReportVerifiedAt||'未知')}</b></span><span>Training Data <b>${(setting.trainingOptions||[]).length} variants</b></span></div><details class="setting-protocol"><summary>展开结构化评测协议</summary><div class="recipe-evidence-grid">${protocolView.fields.map(([k,v])=>`<span>${esc(k)} <b>${esc(v)}</b></span>`).join('')}</div><p>${esc(setting.protocol)}</p><small>Protocol fingerprint <b>${esc(protocolView.fingerprint)}</b> · Track compatibility: exact ${compatibility.exact} / compatible ${compatibility.compatible} / partial ${compatibility.partial}. Training Data、recipe、base model、来源论文以及仅报告层的回合数/种子差异不会单独制造新 Setting；真实任务范围、评测条件或指标变化仍会拆分。</small></details></section>
        <div class="setting-filter-bar"><label>Training Data<select id="setting-train">${options(trains,trainFilter,'全部训练数据')}</select></label><label>Method<select id="setting-method">${options(methods.map(x=>[x,x]),methodFilter,'全部方法')}</select></label><label>Source<select id="setting-source">${options(sources,sourceFilter,'全部来源')}</select></label></div>
        <div class="setting-row-modes" role="group" aria-label="结果展示层级"><button type="button" data-rows-mode="main" aria-pressed="${rowMode==='main'}">主方法比较 · ${setting.primaryResultCount??setting.resultCount}</button><button type="button" data-rows-mode="all" aria-pressed="${rowMode==='all'}">完整原始报告 · ${setting.resultCount}</button></div>
        <div class="setting-toolbar"><div><strong>Method / Score / Training Data / Source</strong><span>${comparable?'已筛选 Training Data；仍需核对实现及训练差异。':rowMode==='main'?'默认仅展示独立主比较记录；所有来源报告可切换查看。':'完整来源记录；含训练扫描、论文专项实验和重复引用。'}</span></div><div class="board-controls setting-controls"><label>排序指标<select id="setting-metric">${setting.columns.map(c=>`<option ${c===metric?'selected':''}>${esc(c)}</option>`).join('')}</select></label><label>排列<select id="setting-order"><option value="auto" ${order==='auto'?'selected':''}>按指标优劣</option><option value="desc" ${order==='desc'?'selected':''}>数值降序</option><option value="asc" ${order==='asc'?'selected':''}>数值升序</option><option value="source" ${order==='source'?'selected':''}>原记录顺序</option></select></label><button class="btn" id="export-setting-csv">导出当前结果 CSV</button></div></div>
        <div class="setting-columns-bar"><span>${displayColumns.length} / ${setting.columns.length} 指标列 · 单位与升降方向独立核验</span><button type="button" id="setting-columns-toggle">${columnMode==='all'?'只看主要指标':'展开全部任务列'}</button></div>
        <p class="board-sort-status" role="status">${comparable?'已筛选 Training Data · ':''}${order==='source'?'按原记录顺序展示':esc(metric)+' · '+(dir==='asc'?'升序':'降序')} · ${rows.length}/${accepted.length} 当前视图 / 全部 ${allChecked.length} 条 · 不生成跨来源公平名次。</p>
        <div class="board-table-scroll" role="region" aria-label="Setting 结果表" tabindex="0"><table class="board-table setting-table"><caption>${esc(setting.name)} · ${rows.length} 条当前筛选结果</caption><thead><tr><th scope="col">Method</th>${displayColumns.map(header).join('')}<th scope="col">Training Data</th><th scope="col">来源论文</th><th scope="col">Recipe / Evidence</th></tr></thead><tbody>${tableRows}</tbody></table>${rows.length?'':'<p class="research-empty">当前筛选条件下没有结果。</p>'}</div>
        <div class="pagination">${Array.from({length:pages},(_,i)=>i+1).slice(Math.max(0,page-3),Math.min(pages,page+2)).map(n=>`<button data-setting-page="${n}" class="${n===page?'active':''}">${n}</button>`).join('')}<span>每页20条；同一 Method 的不同论文 / recipe 报告始终保留。</span></div>`;
      renderedSettingId=setting.id;
      bindResultControls();
    }
    await draw();
  }
  g.RadarBenchmarkSettings={render,sortRows,direction,searchNorm,searchSettings,filterSettingsByTaxonomy,protocolFacts,compatibilityLevel,compatibilitySummary};
  if(typeof module!=='undefined')module.exports=g.RadarBenchmarkSettings;
})(typeof window!=='undefined'?window:globalThis);
