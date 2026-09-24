/* VLA Radar — dependency-free static application. Search and reading state stay in-browser. */
'use strict';
(() => {
  const $ = s => document.querySelector(s);
  const $$ = s => Array.from(document.querySelectorAll(s));
  const REPO = 'https://github.com/invoidstar/VLA-Radar/tree/main';
  const STORE = 'vla-radar.reading.v1';
  const PAGE_SIZE = 12;
  const Dates = window.RadarDates;
  const TIME_UNKNOWN = 'undated';
  const priorityText = {deep:'精读',selective:'选读',overview:'了解'};
  const priorityOrder = {deep:0,selective:1,overview:2};
  const statusText = {unread:'未读',reading:'阅读中',read:'已读'};
  const evidenceText = {checked:'已复核片段',notes:'笔记待复核',metadata:'出版 / 摘要证据'};
  const views = {radar:'My Radar',papers:'文献库',topics:'研究方向',timeline:'时间线',reading:'我的阅读',leaderboards:'Benchmark',reader:'专注阅读',compare:'论文对比',updates:'更新中心',coverage:'证据地图',news:'具身智能周报',about:'关于与维护'};
  const paths = {
    library:'<path d="M4 4h4v16H4zM10 4h4v16h-4zM16 5l3-1 4 15-3 1z"/>',
    grid:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    bookmark:'<path d="M6 4h12v17l-6-4-6 4z"/>',
    info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
    shield:'<path d="m12 3 8 3v6c0 4-4 7-8 9-4-2-8-5-8-9V6zM8 12l3 3 5-6"/>',
    menu:'<path d="M4 6h16M4 12h16M4 18h16"/>',
    external:'<path d="M14 3h7v7M10 14 21 3M21 14v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h6"/>',
    github:'<path d="M9 19c-4 1-4-2-6-2m12 5v-4a3.5 3.5 0 0 0-1-2.7c3.3-.4 6.8-1.6 6.8-7.3a5.7 5.7 0 0 0-1.5-4 5.3 5.3 0 0 0-.1-4S18 0 15 2a14 14 0 0 0-7 0C5 0 3.8 0 3.8 0a5.3 5.3 0 0 0-.1 4 5.7 5.7 0 0 0-1.5 4c0 5.7 3.5 6.9 6.8 7.3A3.5 3.5 0 0 0 8 18v4" transform="translate(1 1) scale(.91)"/>',
    link:'<path d="m10 13 4-4M8 16l-2 2a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0M16 8l2-2a4 4 0 0 1 6 6l-5 5a4 4 0 0 1-6 0" transform="translate(1 0) scale(.9)"/>',
    download:'<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
    search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    reset:'<path d="M3 10a9 9 0 1 1 2 8M3 3v7h7"/>',
    sort:'<path d="M8 3v18m-4-4 4 4 4-4M15 5h6M15 10h4M15 15h2"/>',
    cards:'<rect x="3" y="3" width="18" height="7" rx="1.5"/><rect x="3" y="14" width="18" height="7" rx="1.5"/>',
    table:'<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M10 3v18"/>',
    edit:'<path d="m16 3 5 5-12 12-6 1 1-6zM13 6l5 5"/>',
    close:'<path d="m6 6 12 12M6 18 18 6"/>',
    arrow:'<path d="M4 12h16m-6-6 6 6-6 6"/>',
    spark:'<path d="m12 3 2.4 6.6L21 12l-6.6 2.4L12 21l-2.4-6.6L3 12l6.6-2.4z"/>',
    check:'<path d="m5 12 4 4L19 6"/>',
    caution:'<path d="m12 3 10 18H2zM12 9v5M12 17h.01"/>',
    book:'<path d="M12 5c-4-3-8-2-10-1v16c3-1 6-2 10 1 4-3 7-2 10-1V4c-2-1-6-2-10 1zM12 5v16"/>'
  };
  const icon = name => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${paths[name]||paths.book}</svg>`;
  const esc = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const math = s => window.RadarMath?.renderParagraphs?window.RadarMath.renderParagraphs(s):`<p>${esc(s)}</p>`;
  const norm = s => String(s||'').normalize('NFKC').toLowerCase().replace(/[‐‑–—]/g,'-').replace(/π/g,'pi').replace(/τ/g,'tau').trim();
  function safeUrl(url){try{const u=new URL(url);return /^https?:$/.test(u.protocol)?u.href:'#';}catch{return '#';}}
  let searchClient, searchScores=new Map(), searchQuery="", renderSequence=0, detailSequence=0;
  let data, index=[], topicMap={}, reading={}, storageAvailable=true;
  let state={view:'papers',q:'',topic:'',month:'',year:'',week:'',venue:'',priority:'',status:'',sort:'recommended',layout:'cards',timeline:'week',page:1};
  let timelineLimit=80;
  let filtered=[], toastTimer, queryTimer, lastFocused=null;
  function readState(){try{const raw=JSON.parse(localStorage.getItem(STORE)||'{}');reading=cleanReading(raw);}catch{reading={};}}
  function cleanReading(raw){
    const out={};if(!raw||typeof raw!=='object'||Array.isArray(raw))return out;
    const allowed=new Set((data?.papers||[]).map(p=>p.id));
    for(const [id,v]of Object.entries(raw)){
      if(!allowed.has(id)||!v||typeof v!=='object')continue;
      out[id]={status:['unread','reading','read'].includes(v.status)?v.status:'unread',saved:v.saved===true};
    }return out;
  }
  function saveState(){try{localStorage.setItem(STORE,JSON.stringify(reading));}catch{storageAvailable=false;notify('浏览器禁止本地保存；关闭页面前请导出备份。');}}
  const local = id => reading[id]||{status:'unread',saved:false};
  function notify(message){$('#toast').textContent=message;$('#toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('show'),3600);}
  function parseUrl(){const q=new URLSearchParams(location.search);state.view=views[q.get('view')]?q.get('view'):'papers';for(const k of ['q','topic','month','year','week','venue','priority'])state[k]=(q.get(k)||'').slice(0,240);state.sort=['recommended','newest','oldest','title'].includes(q.get('sort'))?q.get('sort'):'recommended';state.timeline=q.get('timeline')==='month'?'month':'week';if(state.year&&!/^[1-9]\d{3}$/.test(state.year))state.year='';if(state.week!==TIME_UNKNOWN&&!Dates.fromKey(state.week))state.week='';if(Dates.fromKey(state.week))state.year=Dates.fromKey(state.week).year;state.page=1;}
  function makeUrl(includePaper=true,publicOnly=false){
    const u=new URL(location.href);u.search='';u.hash='';
    const view=publicOnly&&state.view==='reading'?'papers':state.view;
    if(view!=='papers')u.searchParams.set('view',view);
    for(const k of ['q','topic','month','year','week','venue','priority'])if(state[k])u.searchParams.set(k,state[k]);
    if(state.sort!=='recommended')u.searchParams.set('sort',state.sort);
    if(view==='timeline'&&state.timeline==='month')u.searchParams.set('timeline','month');
    if(view==='leaderboards'){const params=new URLSearchParams(location.search);for(const k of ['dataset','track','lbMetric','lbOrder','lbChart','lbTime','lbBrowse']){const v=params.get(k);if(v)u.searchParams.set(k,v);}}
    if(['reader','compare'].includes(view)){const params=new URLSearchParams(location.search);for(const k of ['paper','compare']){const v=params.get(k);if(v)u.searchParams.set(k,v);}}
    if(view==='news'){const params=new URLSearchParams(location.search);for(const k of ['nw','nc','ne','nq','paper','story']){const v=params.get(k);if(v)u.searchParams.set(k,v);}}
    if(includePaper)u.hash=location.hash;
    return u;
  }
  function syncUrl(push=false){try{history[push?'pushState':'replaceState']({},'',makeUrl());}catch{/* local-file preview */}}
  function updateControls(){
    $('#search').value=state.q;
    populateTimeControls();
    for(const k of ['topic','month','year','week','venue','priority','status'])$('#filter-'+k).value=state[k];
    $('#sort').value=state.sort;
    for(const layout of ['cards','table']){const el=$('#layout-'+layout);el.classList.toggle('active',layout===state.layout);el.setAttribute('aria-pressed',String(layout===state.layout));}
    $$('.nav-link[data-view]').forEach(el=>{el.classList.toggle('active',el.dataset.view===state.view);if(el.dataset.view===state.view)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});
    $$('.side-topic').forEach(el=>el.classList.toggle('active',el.dataset.topic===state.topic&&['papers','reading'].includes(state.view)));
    $('#breadcrumb').textContent=views[state.view];
  }
  function showView(){
    if(state.view!=='leaderboards')window.RadarResearch.cancelBoards();
    $('#hero').classList.toggle('hidden',state.view!=='papers');$('#stats').classList.toggle('hidden',state.view!=='papers');
    $('#library-section').classList.toggle('hidden',!['papers','reading'].includes(state.view));
    for(const v of ['radar','topics','timeline','about','leaderboards','reader','compare','updates','coverage','news'])$('#'+v+'-section').classList.toggle('hidden',state.view!==v);
    $('#reading-notice').classList.toggle('hidden',state.view!=='reading');
    $('#section-title').textContent=state.view==='reading'?'我的阅读清单':'论文文库';
    updateControls();renderResults();if(state.view==='timeline')renderTimeline();if(state.view==='leaderboards')window.RadarResearch.renderBoards($('#leaderboards-content'));
    if(state.view==='radar'){window.RadarWorkspace.leave();window.RadarTools.show($('#radar-content'));}else if(['reader','compare','updates','coverage','news'].includes(state.view))window.RadarWorkspace.show(state.view);else window.RadarWorkspace.leave();
    document.title=`${views[state.view]} · VLA Research Radar`;
  }
  function goView(view){state.view=view;state.page=1;if(!['papers','reading'].includes(view)){state.q='';state.topic='';state.month='';state.year='';state.week='';state.venue='';state.priority='';state.status='';}syncUrl(true);showView();closeSidebar();window.scrollTo({top:0,behavior:'smooth'});}
  function closeSidebar(){$('#sidebar').classList.remove('open');$('#mobile-menu').setAttribute('aria-expanded','false');}
  function populate(){
    data.topics.forEach(t=>topicMap[t.id]=t);
    $('#nav-total').textContent=data.papers.length;
    $('#updated-at').textContent='更新 '+data.updatedAt.replaceAll('-','.');
    $('#side-topics').innerHTML=data.topics.map(t=>`<button class="side-topic ${esc(t.color)}" data-topic="${esc(t.id)}"><i class="topic-dot"></i><span>${esc(t.name)}</span><span class="topic-count">${data.papers.filter(p=>p.topics.includes(t.id)).length}</span></button>`).join('');
    const stats=[['library',data.papers.length,'收录论文','PAPERS'],['grid',data.topics.length,'研究方向','TOPICS'],['book',data.papers.filter(p=>p.priority==='deep').length,'建议精读','DEEP READ'],['caution',data.papers.filter(p=>p.hasCautionaryResult).length,'含负面 / 条件性发现','CAUTION']];
    $('#stats').innerHTML=stats.map(([i,n,label,en])=>`<div class="stat"><span class="stat-icon">${icon(i)}</span><div class="stat-number">${n.toString().padStart(2,'0')}</div><div class="stat-label">${label}<small>${en}</small></div></div>`).join('');
    const addOptions=(el,list)=>{$(el).insertAdjacentHTML('beforeend',list.map(([v,t])=>`<option value="${esc(v)}">${esc(t)}</option>`).join(''));};
    addOptions('#filter-topic',data.topics.map(t=>[t.id,t.name]));
    addOptions('#filter-month',[...new Set(data.papers.map(p=>p.collectionMonth))].sort().reverse().map(m=>[m,m]));
    addOptions('#filter-venue',[...new Set(data.papers.map(p=>p.venue))].sort().map(v=>[v,v]));
    index=data.papers.map(p=>({paper:p,year:Dates.yearOf(p.firstPublished),week:Dates.isoWeek(p.firstPublished)}));
    window.RadarResearch.configure(data);
    window.RadarWorkspace.configure(data,{notify,closePaper,navigate:(view,params={})=>{if($('#paper-dialog').open)closePaper();const u=new URL(location.href);u.search='';u.hash='';u.searchParams.set('view',view);for(const [k,v]of Object.entries(params))if(v)u.searchParams.set(k,v);history.pushState({},'',u);parseUrl();showView();closeSidebar();window.scrollTo({top:0,behavior:'instant'});},filtered:()=>filtered,local,setStatus:(id,status)=>{if(!['unread','reading','read'].includes(status))return;reading[id]={...local(id),status};saveState();renderResults();},copy,download});
    searchClient=window.RadarSearchClient.create(data.searchUrl,window.__RADAR_DATA__?data:null);
    populateTimeControls();renderTopics();
  }

  // Week-year is ISO 8601: Monday–Sunday, week 01 contains January 4.
  // Month-only dates are searchable by known year but never assigned to a guessed week.
  function populateTimeControls(){
    const years=[...new Set(data.papers.map(p=>Dates.yearOf(p.firstPublished)).filter(Boolean))];
    if(state.year&&!years.includes(state.year))years.push(state.year);
    $('#filter-year').innerHTML='<option value="">全部年份</option>'+years.sort().reverse().map(y=>`<option value="${esc(y)}">${esc(y)} 年</option>`).join('');
    const counts={};let partial=0;
    for(const p of data.papers){
      if(state.year&&Dates.yearOf(p.firstPublished)!==state.year)continue;
      const w=Dates.isoWeek(p.firstPublished);
      if(w)counts[w.key]=(counts[w.key]||0)+1;else partial++;
    }
    let keys=state.year?Dates.weeksInYear(state.year).map(w=>w.key):Object.keys(counts);
    if(Dates.fromKey(state.week)&&!keys.includes(state.week))keys.push(state.week);
    keys.sort().reverse();
    $('#filter-week').innerHTML='<option value="">全部周次</option>'+keys.map(w=>`<option value="${esc(w)}">${esc(Dates.label(w,true))} (${counts[w]||0})</option>`).join('')+`<option value="${TIME_UNKNOWN}">日期未精确到日 (${partial})</option>`;
    $('#filter-year').value=state.year;$('#filter-week').value=state.week;
    const w=Dates.fromKey(state.week);
    $('#time-context').textContent=w?`首发周：${w.key}｜${w.start} 至 ${w.end}（周一至周日）。各条日期来源见详情。`:state.week===TIME_UNKNOWN?'只显示月份精度或待核验日期；这些记录没有被推算成某一周。':'按论文首发日期筛选；周一至周日，采用 ISO 周历年。收录批次仅表示何时加入文献库。';
  }
  function weekBadge(p){const w=Dates.isoWeek(p.firstPublished);return w?`<button class="week-badge" data-week="${w.key}" title="${esc(Dates.label(w.key))}">${w.key}</button>`:'<span class="date-precision">未归周</span>';}
  function goWeek(key){
    if(!Dates.fromKey(key)&&key!==TIME_UNKNOWN)return;
    if($('#paper-dialog').open)closePaper();
    state.view='papers';state.q='';state.topic='';state.month='';state.venue='';state.priority='';state.status='';
    state.year=Dates.fromKey(key)?.year||'';state.week=key;state.page=1;
    syncUrl(true);showView();closeSidebar();$('#library-section').scrollIntoView({behavior:'smooth',block:'start'});
  }

  // Damerau-Levenshtein is only used for Latin title/tag words; numeric evidence is never fuzzy-matched.
  function highlight(text){
    if(!state.q)return esc(text);
    const terms=norm(state.q).split(/\s+/).filter(x=>x.length>1).sort((a,b)=>b.length-a.length);
    if(!terms.length)return esc(text);
    const pattern=terms.map(s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('|');
    try{const re=new RegExp(pattern,'gi');let out='',at=0;String(text).replace(re,(hit,pos)=>{out+=esc(String(text).slice(at,pos))+'<mark>'+esc(hit)+'</mark>';at=pos+hit.length;return hit;});return out+esc(String(text).slice(at));}catch{return esc(text);}
  }
  function getFiltered(){
    const tokens=norm(state.q).split(/\s+/).filter(Boolean).slice(0,12);
    const matches=[];
    for(const entry of index){const p=entry.paper, l=local(p.id);
      if(state.view==='reading'&&!l.saved&&l.status==='unread')continue;
      if(state.topic&&!p.topics.includes(state.topic))continue;
      if(state.month&&p.collectionMonth!==state.month)continue;
      if(state.year&&entry.year!==state.year)continue;
      const pubWeek=entry.week;
      if(state.week===TIME_UNKNOWN&&pubWeek)continue;
      if(state.week&&state.week!==TIME_UNKNOWN&&pubWeek?.key!==state.week)continue;
      if(state.venue&&p.venue!==state.venue)continue;
      if(state.priority&&p.priority!==state.priority)continue;
      if(state.status==='saved'&&!l.saved)continue;
      if(state.status&&state.status!=='saved'&&l.status!==state.status)continue;
      const relevance=tokens.length?(searchQuery===norm(state.q)?searchScores.get(p.id)||0:0):1;if(!relevance)continue;
      matches.push({paper:p,relevance});
    }
    matches.sort((a,b)=>{
      if(state.sort==='recommended')return (tokens.length?b.relevance-a.relevance:0)||priorityOrder[a.paper.priority]-priorityOrder[b.paper.priority]||(b.paper.firstPublished||'').localeCompare(a.paper.firstPublished||'')||a.paper.id.localeCompare(b.paper.id);
      if(state.sort==='title')return a.paper.name.localeCompare(b.paper.name,'en');
      const ad=a.paper.firstPublished,bd=b.paper.firstPublished;
      if(!ad&&!bd)return a.paper.id.localeCompare(b.paper.id);if(!ad)return 1;if(!bd)return -1;
      return state.sort==='oldest'?ad.localeCompare(bd):bd.localeCompare(ad);
    });return matches.map(x=>x.paper);
  }
  function badge(p){return `<span class="priority ${p.priority}">${p.priority==='deep'?icon('spark'):''}${priorityText[p.priority]}</span>`;}
  function resourcesHtml(p,compact=false){const r=p.resources||{},items=[];if(r.project)items.push(['project','项目主页',r.project,'external']);if(r.code)items.push(['code','开源代码',r.code,'github']);return items.length?`<div class="paper-resources ${compact?'compact':''}" aria-label="官方资源">${items.map(([kind,label,href,ico])=>`<a class="paper-resource ${kind}" href="${esc(safeUrl(href))}" target="_blank" rel="noopener noreferrer">${icon(ico)}${label}</a>`).join('')}</div>`:'';}

  function relationsHtml(p){
    const rel=p.relations||{},previous=rel.previous||[],followups=rel.followups||[],series=rel.series||[];
    if(!previous.length&&!followups.length&&!series.length)return '';
    const relationButton=item=>`<button class="tag" data-paper="${esc(item.paperId)}" title="${esc(item.title||item.name)}">${esc(item.name||item.paperId)}</button>`;
    const evidence=sources=>(sources||[]).slice(0,2).map(s=>`<a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener noreferrer">${icon('external')}${esc(s.label)}</a>`).join('');
    const blocks=[];
    if(previous.length)blocks.push(`<div class="relation-block"><label>Previous / Builds on</label><div class="paper-tags">${previous.map(relationButton).join('')}</div>${previous.map(x=>`<p><strong>${x.type==='extends'?'Extends':'Follow-up of'} · ${esc(x.name)}</strong> — ${esc(x.note)}</p><div class="source-links compact">${evidence(x.sources)}</div>`).join('')}</div>`);
    if(followups.length)blocks.push(`<div class="relation-block"><label>Follow-up</label><div class="paper-tags">${followups.map(relationButton).join('')}</div>${followups.map(x=>`<p><strong>${x.type==='extends'?'Extended by':'Followed by'} · ${esc(x.name)}</strong> — ${esc(x.note)}</p><div class="source-links compact">${evidence(x.sources)}</div>`).join('')}</div>`);
    for(const group of series)blocks.push(`<div class="relation-block"><label>Same Series · ${esc(group.name)}</label><div class="paper-tags">${(group.members||[]).map(relationButton).join('')}</div><p>${esc(group.note)}</p><div class="source-links compact">${evidence(group.sources)}</div></div>`);
    return `<section class="detail-section relation-section"><h3>${icon('link')}论文关系</h3>${blocks.join('')}<small>仅展示已在 VLA-Radar 中收录、并有公开来源核验的直接关系；同机构或仅使用相同 backbone 不自动建立关系。</small></section>`;
  }

  function reproducibilityHtml(p){
    const view=p.reproducibility||{},items=view.items||{};
    const labels={project:'Project',code:'Code',weights:'Weights',dataset:'Dataset',training:'Training',inference:'Inference',evaluation:'Evaluation',license:'License'};
    const statusText={available:'可用',partial:'部分开放',unavailable:'未开放',unknown:'未核验'};
    const order=['project','code','weights','dataset','training','inference','evaluation','license'];
    const cards=order.map(dim=>{
      const item=items[dim]||{status:'unknown',note:'Not yet independently audited in VLA-Radar.',url:null,source:null};
      const action=item.url?`<a href="${esc(safeUrl(item.url))}" target="_blank" rel="noopener noreferrer">访问资源 ${icon('external')}</a>`:'';
      const evidence=item.source&&item.source!==item.url?`<a class="repro-evidence" href="${esc(safeUrl(item.source))}" target="_blank" rel="noopener noreferrer">核验来源</a>`:'';
      return `<div class="repro-item ${esc(item.status)}"><div class="repro-item-top"><span>${esc(labels[dim])}</span><strong>${esc(statusText[item.status]||item.status)}</strong></div><p>${esc(item.note||'')}</p><div class="repro-links">${action}${evidence}</div></div>`;
    }).join('');
    return `<section class="reproducibility-card"><div class="repro-heading"><h3>${icon('check')}Reproducibility Card</h3><small>${view.verifiedAt?`附加资源审计 · ${esc(view.verifiedAt)}`:'Project / Code 来自官方资源 registry；其余维度待逐项核验'}</small></div><div class="repro-grid">${cards}</div><p class="repro-note">可用 = 有公开且可执行资源；部分开放 = 只开放部分复现链路；未开放 = 官方明确未发布；未核验 ≠ 不存在。</p></section>`;
  }

  function saveButton(p){const saved=local(p.id).saved;return `<button class="save-btn ${saved?'saved':''}" data-save="${p.id}" aria-label="${saved?'取消收藏':'收藏'} ${esc(p.name)}" aria-pressed="${saved}">${icon('bookmark')}</button>`;}
  function card(p){const t=topicMap[p.topics[0]],l=local(p.id);return `<article class="paper-card">
    <div class="paper-card-main"><div class="paper-card-top"><button class="paper-name" data-paper="${p.id}">${highlight(p.name)}</button>${badge(p)}</div><p class="paper-title">${highlight(p.title)}</p><div class="paper-meta"><span class="venue-label">${esc(p.venue)}</span><span class="meta-sep">/</span><time>${esc(p.firstPublished||'首发待核验')}</time>${weekBadge(p)}<span class="meta-sep">/</span><span class="team-short" title="${esc(p.team)}">${highlight(p.team.split('\n')[0])}</span></div><div class="finding-preview"><span class="finding-label">KEY RESULT</span><span class="finding-text">${highlight(p.findings)}</span></div></div>
    <div class="paper-card-right"><div><span class="topic-label ${esc(t.color)}"><i class="topic-dot"></i>${esc(t.name)}</span><div class="paper-tags">${p.tags.slice(0,3).map(tag=>`<button class="tag" data-query="${esc(tag)}">${esc(tag)}</button>`).join('')}</div>${resourcesHtml(p,true)}${l.status!=='unread'?`<div class="read-badge">${l.status==='read'?'✓ ':''}${statusText[l.status]} · 本地</div>`:''}</div><div class="paper-card-actions"><button class="detail-btn" data-paper="${p.id}">阅读笔记 ${icon('arrow')}</button><button class="compare-pick" data-compare="${p.id}" aria-label="加入对比 ${esc(p.name)}">＋ 对比</button><button class="focus-pick" data-focus="${p.id}">专注阅读</button><button class="follow-pick" data-follow-paper="${p.id}" aria-pressed="false">＋ 关注</button>${saveButton(p)}</div></div></article>`;}
  function table(papers){return `<div class="table-scroll"><table class="papers-table"><thead><tr><th>论文 / 团队</th><th>方向</th><th>首发 / 出处</th><th>具体结论 · 作者报告</th><th>阅读建议</th><th>收藏</th></tr></thead><tbody>${papers.map(p=>`<tr><td class="table-name"><button class="paper-name" data-paper="${p.id}">${highlight(p.name)}</button><div class="table-sub">${highlight(p.team.split('\n')[0])}</div>${resourcesHtml(p,true)}</td><td>${esc(topicMap[p.topics[0]].name)}</td><td class="table-small">${esc(p.firstPublished||'待核验')}<div>${weekBadge(p)}</div><div>${esc(p.venue)}</div></td><td class="table-finding">${highlight(p.findings)}</td><td>${badge(p)}</td><td>${saveButton(p)}</td></tr>`).join('')}</tbody></table></div>`;}
  async function renderResults(){
    const request=++renderSequence,query=norm(state.q);
    if(query&&query!==searchQuery){
      $('#result-count').textContent='正在检索…';
      try{const found=await searchClient.query(query);if(request!==renderSequence)return;searchScores=new Map(found);searchQuery=query;}
      catch(error){if(request!==renderSequence)return;$('#result-count').textContent='检索索引暂不可用';$('#results').innerHTML='<p class="research-warning">检索暂未完成，不代表没有匹配论文。请重新检索或刷新重试。</p>';return;}
    }
    if(request!==renderSequence)return;
    filtered=getFiltered();const pages=Math.ceil(filtered.length/PAGE_SIZE);state.page=Math.max(1,Math.min(state.page,pages||1));
    $('#result-count').textContent=`${filtered.length} 篇文献`;
    const filters=[['q',state.q&&'检索：'+state.q],['topic',topicMap[state.topic]?.name],['month',state.month&&'收录批次：'+state.month],['year',state.year&&'首发年：'+state.year],['week',state.week&&(state.week===TIME_UNKNOWN?'日期未精确到日':Dates.label(state.week,true))],['venue',state.venue],['priority',priorityText[state.priority]],['status',state.status==='saved'?'已收藏':statusText[state.status]]].filter(([,v])=>v);
    $('#active-filters').innerHTML=filters.map(([key,v])=>`<button class="filter-chip" data-clear="${key}">${esc(v)} ×</button>`).join('');
    if(!filtered.length){const isReading=state.view==='reading'&&!Object.keys(reading).some(id=>local(id).saved||local(id).status!=='unread');$('#results').innerHTML=`<div class="empty-state">${icon(isReading?'bookmark':'search')}<h3>${isReading?'从一篇感兴趣的论文开始':'没有找到匹配的文献'}</h3><p>${isReading?'在文献卡片上点击收藏，或在详情中标记阅读状态。清单只保存在当前浏览器。':'试试减少关键词、改用方法名或清除筛选。搜索仅覆盖当前文献库，不代表外部没有相关研究。'}</p><button class="btn" ${isReading?'data-view="papers"':'data-reset="true"'}>${isReading?'去浏览文献':'清除筛选'}</button></div>`;$('#pagination').innerHTML='';return;}
    const page=filtered.slice((state.page-1)*PAGE_SIZE,state.page*PAGE_SIZE);
    $('#results').innerHTML=state.layout==='table'?table(page):`<div class="paper-list">${page.map(card).join('')}</div>`;
    window.RadarExperience?.refreshPicks();
    $('#pagination').innerHTML=pages<=1?`<span>已显示全部 ${filtered.length} 篇</span>`:`<button data-page="${state.page-1}" ${state.page===1?'disabled':''} aria-label="上一页">←</button>${window.RadarResearch.pageWindow(state.page,pages).map(n=>n===null?'<span>…</span>':`<button data-page="${n}" class="${state.page===n?'active':''}" ${state.page===n?'aria-current="page"':''}>${n}</button>`).join('')}<button data-page="${state.page+1}" ${state.page===pages?'disabled':''} aria-label="下一页">→</button><span>每页 ${PAGE_SIZE} 篇 · 共 ${filtered.length} 篇</span>`;
  }
  function renderTopics(){$('#topic-cards').innerHTML=data.topics.map(t=>{const papers=data.papers.filter(p=>p.topics.includes(t.id));return `<button class="topic-card ${esc(t.color)}" data-topic="${esc(t.id)}"><div class="topic-card-top"><span class="topic-initial">${esc(t.en.toUpperCase())}</span><span class="topic-total">${papers.length.toString().padStart(2,'0')}</span></div><h2>${esc(t.name)}</h2><p>${esc(t.description)}</p><div class="topic-card-foot"><span>${papers.filter(p=>p.priority==='deep').length} 篇建议精读</span><span>进入方向 ${icon('arrow')}</span></div></button>`;}).join('');}
  function renderTimeline(){
    const groups={};const weekly=state.timeline==='week';
    const timelinePapers=[...data.papers].sort((a,b)=>(b.firstPublished||'').localeCompare(a.firstPublished||''));
    for(const p of timelinePapers.slice(0,timelineLimit)){const key=weekly?(Dates.isoWeek(p.firstPublished)?.key||TIME_UNKNOWN):(p.firstPublished?.slice(0,7)||TIME_UNKNOWN);(groups[key]??=[]).push(p);}
    $('#timeline-week').classList.toggle('active',weekly);$('#timeline-month').classList.toggle('active',!weekly);
    $('#timeline-week').setAttribute('aria-pressed',String(weekly));$('#timeline-month').setAttribute('aria-pressed',String(!weekly));
    $('#timeline-mode-note').textContent=weekly?'按首发 ISO 周分组；日期不足一天精度的条目单独列出。点击周次可检索该周。':'按首次公开月份分组；保留月精度条目，不把收录批次当作首发月份。';
    $('#timeline').innerHTML=Object.keys(groups).sort((a,b)=>a===TIME_UNKNOWN?1:b===TIME_UNKNOWN?-1:b.localeCompare(a)).map(key=>{
      const info=weekly&&key!==TIME_UNKNOWN?Dates.fromKey(key):null;
      const title=key===TIME_UNKNOWN?(weekly?'日期未精确到日':'首次公开待核验'):key;
      return `<section class="timeline-group" data-period="${esc(key)}"><h2>${weekly?`<button class="timeline-week-link" data-week="${esc(key)}">${esc(title)}</button>`:esc(title)}<span>${groups[key].length} PAPERS</span></h2>${info?`<p class="timeline-range">${esc(info.start)} — ${esc(info.end)} · 周一至周日</p>`:key===TIME_UNKNOWN?'<p class="timeline-range">保留已知月份或待核验说明，不补造日期。</p>':''}${groups[key].sort((a,b)=>(b.firstPublished||'').localeCompare(a.firstPublished||'')).map(p=>`<div class="timeline-entry"><div><button class="paper-name" data-paper="${p.id}">${esc(p.name)}</button><p>${esc(p.venue)} · ${esc(p.versionNote)}</p></div><span class="timeline-date">${esc(p.firstPublished||'日期待核验')}</span></div>`).join('')}</section>`;
    }).join('')+(timelinePapers.length>timelineLimit?`<button class="btn timeline-more" data-timeline-more="true">继续查看更早的记录（已显示 ${Math.min(timelineLimit,timelinePapers.length)} / ${timelinePapers.length}）</button>`:'');
  }
  function setSearch(q){state.q=q;state.view='papers';state.page=1;syncUrl();showView();$('#search').focus();}
  function resetFilters(){for(const key of ['q','topic','month','year','week','venue','priority','status'])state[key]='';state.page=1;syncUrl();updateControls();renderResults();}
  function toggleSave(id){reading[id]={...local(id),saved:!local(id).saved};saveState();renderResults();if($('#paper-dialog').open)renderDetail(id);notify(local(id).saved?'已加入本地阅读清单':'已取消收藏');}
  async function renderDetail(id){
    const brief=data.papers.find(p=>p.id===id);if(!brief)return;const request=++detailSequence;
    $('#paper-detail').innerHTML='<h2 id="dialog-title">'+esc(brief.name)+'</h2><p role="status">正在载入详细笔记…</p>';
    let p=brief;
    try{const r=await window.RadarResearch.detail(brief);if(request!==detailSequence)return;if(r)p={...r.paper,detailUrl:brief.detailUrl,resultUrl:brief.resultUrl,resources:brief.resources||{},relations:brief.relations||{previous:[],followups:[],series:[]},reproducibility:brief.reproducibility||{verifiedAt:null,items:{}}};}
    catch(error){if(request!==detailSequence)return;$('#paper-detail').innerHTML='<h2 id="dialog-title">'+esc(brief.name)+'</h2><p class="research-warning">详细笔记暂不可用，网站可能已更新。请刷新页面后重试。</p>';return;}
    const l=local(id);
    $('#paper-detail').innerHTML=`<div class="dialog-labels">${badge(p)}<span class="venue-label">${esc(p.venue)}</span>${p.topics.map(t=>`<button class="tag" data-topic="${esc(t)}">${esc(topicMap[t].name)}</button>`).join('')}</div><h2 id="dialog-title">${esc(p.name)}</h2><p class="dialog-full-title">${esc(p.title)}</p><div class="dialog-team">${esc(p.team)}</div>
      <div class="date-grid"><div><label>首次公开</label><span>${esc(p.firstPublished||p.dateNote)}</span></div><div><label>收录批次</label><span>${esc(p.collectionMonth)}</span></div><div class="wide"><label>首发周（ISO 8601）</label><span>${esc(Dates.isoWeek(p.firstPublished)?Dates.label(Dates.isoWeek(p.firstPublished).key):'日期未精确到日，不指定周次')}</span></div><div class="wide"><label>日期口径</label><span>${esc(p.dateNote||'以所列原始来源记录的日期为准；不以修订或收录日期替代。')}</span></div><div class="wide"><label>发表状态与阅读版本</label><span>${esc(p.publicationStatus).replaceAll('\n',' · ')}<br>${esc(p.versionNote)}</span></div></div>
      <section class="detail-section"><h3><span class="num">01</span>核心贡献</h3><div class="detail-prose">${math(p.contribution)}</div></section>
      <section class="detail-section results-box"><h3><span class="num">02</span>具体结论与数据 <small>· 作者报告</small></h3><div class="detail-prose">${math(p.findings)}</div></section>
      <section class="detail-section limit-box"><h3>${icon('info')}适用条件与证据边界</h3><div class="detail-prose">${math(p.limitations)}</div></section>
      <section class="detail-section"><h3><span class="num">03</span>阅读启示</h3><div class="detail-prose">${math(p.insight)}</div></section>
      <section class="detail-section"><h3><span class="num">04</span>重点读什么</h3><div class="detail-prose">${math(p.readingFocus)}</div></section>
      <div class="evidence-status"><strong>${evidenceText[p.evidence]||'待核验'}</strong> · ${esc(p.evidenceNote)}</div>
      ${relationsHtml(p)}
      ${reproducibilityHtml(p)}
      ${resourcesHtml(p)}
      <div class="source-links">${p.sources.map(s=>`<a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener noreferrer">${icon('external')}${esc(s.label)}</a>`).join('')}</div>
      <div class="dialog-actions"><div class="action-group"><a class="btn primary" href="${esc(safeUrl(p.paperUrl))}" target="_blank" rel="noopener noreferrer">阅读原文 ${icon('external')}</a><button class="btn" data-save="${p.id}">${icon('bookmark')}${l.saved?'已收藏':'收藏'}</button><button class="btn" data-bib="${p.id}">BibTeX</button><button class="btn" data-share-paper="${p.id}">${icon('link')}分享</button></div><label class="status-label">本地进度<select class="status-select" id="detail-status" data-id="${p.id}">${Object.entries(statusText).map(([v,t])=>`<option value="${v}" ${l.status===v?'selected':''}>${t}</option>`).join('')}</select></label></div>`;
    $('#paper-detail').insertAdjacentHTML('afterbegin',`<div class="quick-note-tools"><button class="btn primary" data-focus="${p.id}">进入专注阅读 ↗</button><button class="btn" data-compare="${p.id}">＋ 加入对比</button><span>先看结论，再沿章节深入。</span></div>`);
    window.RadarResearch.enhance(p,$('#paper-detail'));
  }
  function openPaper(id,update=true){if(!data.papers.some(p=>p.id===id)){notify('文献记录不存在或已移除');return;}lastFocused=document.activeElement;renderDetail(id);const d=$('#paper-dialog');if(!d.open)d.showModal();$('#paper-detail').parentElement.scrollTop=0;if(update){const u=makeUrl(false);u.hash='paper='+encodeURIComponent(id);try{history.pushState({},'',u);}catch{}}document.title=data.papers.find(p=>p.id===id).name+' · VLA Research Radar';}
  function closePaper(){detailSequence++;const d=$('#paper-dialog');if(d.open)d.close();if(location.hash.startsWith('#paper=')){const u=new URL(location.href);u.hash='';try{history.replaceState({},'',u);}catch{}}document.title=`${views[state.view]} · VLA Research Radar`;if(lastFocused?.isConnected)lastFocused.focus();}
  function hashPaper(){const m=location.hash.match(/^#paper=(p\d+)$/);if(m)openPaper(m[1],false);else if($('#paper-dialog').open)$('#paper-dialog').close();}
  async function copy(text,success){try{if(navigator.clipboard&&window.isSecureContext)await navigator.clipboard.writeText(text);else{const el=document.createElement('textarea');el.value=text;el.style.position='fixed';el.style.opacity='0';document.body.appendChild(el);el.select();const ok=document.execCommand('copy');el.remove();if(!ok)throw new Error('clipboard unavailable');}notify(success);}catch{notify('浏览器未允许复制，请从地址栏或下载文件中获取。');}}
  function download(name,text,type='application/json'){const url=URL.createObjectURL(new Blob([text],{type:type+';charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}
  async function exportCsv(){
    const selected=new Set(filtered.map(p=>p.id));let exportRows;
    try{const response=await fetch('data/papers.json',{credentials:'omit',cache:'no-cache'});if(!response.ok)throw new Error();const all=new Map((await response.json()).papers.map(p=>[p.id,p]));exportRows=filtered.map(p=>all.get(p.id)).filter(Boolean);}
    catch(error){notify('完整导出数据暂不可用，请重试。');return;}
    const cols=[['论文简称','name'],['论文题目','title'],['作者团队','team'],['出处','venue'],['发表状态','publicationStatus'],['首次公开','firstPublished'],['首发周（ISO）',p=>Dates.isoWeek(p.firstPublished)?.key||''],['首发周起止',p=>{const w=Dates.isoWeek(p.firstPublished);return w?w.start+' / '+w.end:'';}],['日期口径','dateNote'],['收录批次','collectionMonth'],['阅读版本','versionNote'],['研究方向',p=>p.topics.map(t=>topicMap[t].name).join(' / ')],['阅读建议',p=>priorityText[p.priority]],['核心贡献','contribution'],['具体结论','findings'],['证据边界','limitations'],['阅读启示','insight'],['重点阅读','readingFocus'],['证据状态',p=>evidenceText[p.evidence]],['原始来源',p=>p.sources.map(s=>s.url).join('\n')]];
    const cell=x=>{let s=String(x??'');if(/^[\s]*[=+\-@]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};
    const lines=[cols.map(c=>cell(c[0])).join(',')];for(const p of exportRows)lines.push(cols.map(([,k])=>cell(typeof k==='function'?k(p):p[k])).join(','));
    download('vla-radar-papers.csv','\uFEFF'+lines.join('\r\n'),'text/csv');notify(`已导出 ${filtered.length} 篇公开记录，不含阅读状态。`);
  }
  function exportReading(){download('vla-radar-reading-backup.json',JSON.stringify({format:'vla-radar-reading',version:1,exportedAt:new Date().toISOString(),papers:reading},null,2));notify('阅读备份已导出；请勿提交到公开仓库。');}
  async function importReading(file){
    if(!file)return;if(file.size>1000000){notify('备份文件过大，未导入。');return;}
    try{const parsed=JSON.parse(await file.text());if(parsed.format!=='vla-radar-reading'||parsed.version!==1||!parsed.papers||typeof parsed.papers!=='object'||Array.isArray(parsed.papers))throw new Error('invalid');
      const recovered=cleanReading(parsed.papers);if(!Object.keys(recovered).length){notify('没有与当前文献库匹配的阅读记录。');return;}
      reading={...reading,...recovered};saveState();renderResults();notify(`已恢复 ${Object.keys(recovered).length} 条本地记录。`);
    }catch{notify('不是有效的 VLA Radar 阅读备份，未修改现有记录。');}finally{$('#reading-file').value='';}
  }
  function bibtex(id){const p=data.papers.find(p=>p.id===id);if(!p)return;const clean=s=>String(s).replace(/[{}\\]/g,'').replaceAll('\n',' ');const year=(p.firstPublished||p.collectionMonth).slice(0,4);let out=`@misc{${p.id}_${year},\n  title = {${clean(p.title)}},\n  year = {${year}},\n  url = {${safeUrl(p.paperUrl)}}`;
    if(p.arxiv)out+=`,\n  eprint = {${p.arxiv}},\n  archivePrefix = {arXiv}`;if(p.doi)out+=`,\n  doi = {${clean(p.doi)}}`;out+='\n}\n';
    // Affiliation strings are not repurposed as a complete author list.
    download(p.id+'.bib',out,'application/x-bibtex');notify('已导出基础 BibTeX；完整作者与最终出版信息请从原文补齐。');
  }
  function bind(){
    document.addEventListener('click',e=>{
      const el=e.target.closest('button,a');if(!el)return;
      if(el.dataset.focus){e.preventDefault();window.RadarWorkspace.action('focus',el.dataset.focus);}
      else if(el.dataset.compare){e.preventDefault();window.RadarWorkspace.action('compare',el.dataset.compare);}
      else if(el.dataset.workspaceExport){window.RadarWorkspace.action('export');}
      else if(el.dataset.view){e.preventDefault();if($('#paper-dialog').open)closePaper();goView(el.dataset.view);}
      else if(el.hasAttribute('data-query')){setSearch(el.dataset.query);}
      else if(el.dataset.topic){if($('#paper-dialog').open)closePaper();state.topic=el.dataset.topic;state.view='papers';state.page=1;syncUrl(true);showView();closeSidebar();$('#library-section').scrollIntoView({behavior:'smooth',block:'start'});}
      else if(el.dataset.week)goWeek(el.dataset.week);
      else if(el.dataset.paper)openPaper(el.dataset.paper);
      else if(el.dataset.save)toggleSave(el.dataset.save);
      else if(el.dataset.timelineMore){timelineLimit+=80;renderTimeline();}
      else if(el.dataset.page){state.page=Number(el.dataset.page);renderResults();$('#library-section').scrollIntoView({behavior:'smooth',block:'start'});}
      else if(el.dataset.clear){state[el.dataset.clear]='';if(el.dataset.clear==='year')state.week='';state.page=1;syncUrl();updateControls();renderResults();}
      else if(el.dataset.reset)resetFilters();
      else if(el.dataset.bib)window.RadarWorkspace.action('cite',el.dataset.bib);
      else if(el.dataset.sharePaper){const u=makeUrl(false,true);u.hash='paper='+el.dataset.sharePaper;copy(u.href,'已复制论文链接，不含本地阅读状态。');}
    });
    $('#search').addEventListener('input',e=>{clearTimeout(queryTimer);queryTimer=setTimeout(()=>{state.q=e.target.value;state.page=1;syncUrl();renderResults();},160);});
    for(const key of ['topic','month','year','week','venue','priority','status'])$('#filter-'+key).addEventListener('change',e=>{state[key]=e.target.value;if(key==='year')state.week='';if(key==='week'&&Dates.fromKey(state.week))state.year=Dates.fromKey(state.week).year;state.page=1;syncUrl();updateControls();renderResults();});
    for(const mode of ['week','month'])$('#timeline-'+mode).addEventListener('click',()=>{state.timeline=mode;timelineLimit=80;syncUrl();renderTimeline();});
    $('#sort').addEventListener('change',e=>{state.sort=e.target.value;state.page=1;syncUrl();renderResults();});
    for(const layout of ['cards','table'])$('#layout-'+layout).addEventListener('click',()=>{state.layout=layout;updateControls();renderResults();});
    $('#reset-filters').addEventListener('click',resetFilters);$('#export-csv').addEventListener('click',exportCsv);
    $('#share-search').addEventListener('click',()=>copy(makeUrl(false,true).href,'已复制筛选链接；不包含收藏或阅读状态。'));
    $('#export-all-json').addEventListener('click',async()=>{try{const r=await fetch('data/papers.json',{credentials:'omit'});if(!r.ok)throw new Error();download('papers.json',await r.text());}catch{notify('公开导出暂不可用，请刷新重试。');}});
    $('#export-reading').addEventListener('click',exportReading);$('#import-reading').addEventListener('click',()=>$('#reading-file').click());$('#reading-file').addEventListener('change',e=>importReading(e.target.files[0]));
    $('#close-dialog').addEventListener('click',closePaper);$('#paper-dialog').addEventListener('cancel',e=>{e.preventDefault();closePaper();});$('#paper-dialog').addEventListener('click',e=>{if(e.target===e.currentTarget){const r=e.currentTarget.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closePaper();}});
    $('#paper-detail').addEventListener('change',e=>{if(e.target.id==='detail-status'){const id=e.target.dataset.id;reading[id]={...local(id),status:e.target.value};saveState();renderResults();notify('阅读状态已保存在当前浏览器。');}});
    $('#mobile-menu').addEventListener('click',()=>{const open=$('#sidebar').classList.toggle('open');$('#mobile-menu').setAttribute('aria-expanded',String(open));});
    document.addEventListener('click',e=>{if($('#sidebar').classList.contains('open')&&!e.target.closest('#sidebar')&&!e.target.closest('#mobile-menu'))closeSidebar();});
    document.addEventListener('keydown',e=>{if(e.key==='Escape')closeSidebar();});
    window.addEventListener('popstate',()=>{parseUrl();showView();hashPaper();});
    window.addEventListener('storage',e=>{if(e.key===STORE){readState();renderResults();const m=location.hash.match(/^#paper=(p\d+)$/);if(m&&$('#paper-dialog').open)renderDetail(m[1]);}});
  }
  async function start(){
    $$('[data-icon]').forEach(el=>el.innerHTML=icon(el.dataset.icon));
    try{
      if(window.__RADAR_DATA__)data=window.__RADAR_DATA__;
      else{const response=await fetch('data/library.json',{cache:'no-cache',credentials:'omit'});if(!response.ok)throw new Error('HTTP '+response.status);data=await response.json();}
      if(!Dates)throw new Error('Week date module failed to load');
      if(data.schemaVersion!==1||!Array.isArray(data.papers)||!Array.isArray(data.topics))throw new Error('Unsupported data format');
      for(const p of data.papers)if(!p.id||!p.name||!p.title||!Array.isArray(p.topics))throw new Error('Invalid paper record');
      readState();parseUrl();populate();bind();showView();hashPaper();
      window.RadarTest={search:async q=>(await searchClient.query(q)).map(e=>e[0]),count:data.papers.length};
    }catch(error){console.error('VLA Radar could not load:',error);$('#updated-at').textContent='数据暂未载入';$('#result-count').textContent='载入失败';$('#results').innerHTML=`<div class="empty-state">${icon('info')}<h3>暂时无法读取文献数据</h3><p>请刷新页面，或检查 data/library.json 是否为有效 JSON。本地预览请先运行 python scripts/build/stage_site.py --output _site，再从 _site 启动 HTTP server。</p><a class="btn" href="${REPO}" target="_blank" rel="noopener noreferrer">前往 GitHub 查看数据</a></div>`;}
  }
  start();
})();
