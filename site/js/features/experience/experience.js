/* Optional research workspace. All content is public; preferences remain local. */
'use strict';
(function(g){
 const C=g.RadarExperienceCore,R=g.RadarResearch,{esc,url}=C;
 let lib,api,byId,ids,token=0,cleanup=()=>{},compare=[],indexPromise;
 const keys={compare:'vla-radar.compare.v1',reader:'vla-radar.reader.v1',settings:'vla-radar.reader-settings.v1',seen:'vla-radar.updates-seen.v1'};
 const kindNames={all:'全部动态',collected:'新收录',revision:'版本修订',publication:'录用与出版',note:'笔记更新',result:'评测结果',site:'网站更新'};
 const buttons=(id)=>`<button class="btn primary" data-focus="${esc(id)}">专注阅读 ↗</button><button class="btn" data-compare="${esc(id)}">＋ 对比</button>`;
 const heading=(en,title,desc)=>`<header class="workspace-header"><div class="eyebrow">${en}</div><h1 tabindex="-1">${title}</h1><p>${desc}</p></header>`;
 const sourceLinks=s=>R.links(s||[]);
 const resourceButtons=p=>{const r=p.resources||{};return (r.project?`<a class="btn" href="${esc(url(r.project))}" target="_blank" rel="noopener noreferrer">项目主页 ↗</a>`:'')+(r.code?`<a class="btn" href="${esc(url(r.code))}" target="_blank" rel="noopener noreferrer">开源代码 ↗</a>`:'');};
 const lookup=id=>byId.get(id);
 async function record(id){const p=lookup(id);if(!p)throw new Error('Unknown paper');const r=await R.detail(p);return {...r,paper:{...r.paper,resources:p.resources||{}}};}
 function configure(c,a){lib=c;api=a;byId=new Map(c.papers.map(p=>[p.id,p]));ids=new Set(byId.keys());compare=C.uniqueIds(C.localJSON(keys.compare,[]),ids);updatePicks();}
 function leave(){token++;cleanup();cleanup=()=>{};document.body.classList.remove('reader-active');}
 function updatePicks(){const n=document.getElementById('compare-count');if(n)n.textContent=compare.length?String(compare.length):'';document.querySelectorAll('[data-compare]').forEach(b=>{const yes=compare.includes(b.dataset.compare);b.setAttribute('aria-pressed',yes);b.classList.toggle('is-picked',yes);b.textContent=yes?'✓ 已选':'＋ 对比';});}
 function writeCompare(){C.store(keys.compare,compare);updatePicks();}
 function addCompare(id){if(!ids.has(id))return;if(compare.includes(id))compare=compare.filter(x=>x!==id);else{if(compare.length>=4){api.notify('最多对比4篇，请先移除一篇。');return;}compare.push(id);}writeCompare();api.notify(`已选 ${compare.length} 篇；在「论文对比」中查看差异。`);}
 function settings(){const x=C.localJSON(keys.settings,{});return {font:[16,18,20,22].includes(x?.font)?x.font:18,line:[1.75,1.95,2.15].includes(x?.line)?x.line:1.95,theme:['paper','light','night'].includes(x?.theme)?x.theme:'paper'};}
 function readerStore(){const x=C.localJSON(keys.reader,{});return x&&typeof x==='object'&&!Array.isArray(x)?x:{};}
 function savePosition(id,value){const x=readerStore();x[id]=value;const entries=Object.entries(x).sort((a,b)=>String(b[1]?.at||'').localeCompare(String(a[1]?.at||''))).slice(0,100);C.store(keys.reader,Object.fromEntries(entries));}
 function setReaderStyle(host,s){host.style.setProperty('--reader-font',s.font+'px');host.style.setProperty('--reader-line',s.line);host.dataset.theme=s.theme;C.store(keys.settings,s);}
 async function reader(host,t){
  const pid=new URLSearchParams(location.search).get('paper');if(!ids.has(pid)){host.innerHTML=heading('FOCUS READING','选一篇，深入读。','在文献卡片或论文详情中点击“专注阅读”。')+'<button class="btn primary" data-view="papers">返回文献库</button>';return;}
  const r=await record(pid);if(t!==token)return;const p=r.paper,n=r.note,s=settings(),saved=readerStore()[pid];
  document.body.classList.add('reader-active');
  const anchor=name=>'read-'+name;
  host.innerHTML=`<div class="reader-toolbar"><button class="btn" data-view="papers">← 文献库</button><span class="reader-toolbar-title">${esc(p.name)}</span><div class="reader-actions"><label>字号<select id="reader-font">${[16,18,20,22].map(v=>`<option ${s.font===v?'selected':''}>${v}</option>`).join('')}</select></label><label>行距<select id="reader-line">${[1.75,1.95,2.15].map(v=>`<option ${s.line===v?'selected':''}>${v}</option>`).join('')}</select></label><label>背景<select id="reader-theme">${[['paper','纸色'],['light','浅色'],['night','夜读']].map(([v,label])=>`<option value="${v}" ${s.theme===v?'selected':''}>${label}</option>`).join('')}</select></label><button class="btn" data-reader-export>引用 / 导出</button></div></div><div class="reader-progress" role="progressbar" aria-label="本文滚动进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><span></span></div><div class="reader-layout"><aside class="reader-outline"><details open><summary>章节导航 <small>${n.sections.length} 节</small></summary><nav aria-label="当前论文目录">${n.sections.map((x,i)=>`<button data-reader-jump="${esc(anchor(x.id))}"><span>${String(i+1).padStart(2,'0')}</span>${esc(x.title)}</button>`).join('')}<button data-reader-jump="reader-evidence">图表与来源</button></nav></details><p class="reader-position-note">阅读位置仅保存在本机。</p><label class="reader-status">阅读状态<select id="reader-status">${[['unread','未读'],['reading','阅读中'],['read','已读']].map(([v,label])=>`<option value="${v}" ${api.local(pid).status===v?'selected':''}>${label}</option>`).join('')}</select></label></aside><article class="reader-article"><header class="reader-title"><div class="eyebrow">PAPER / ${esc(pid.toUpperCase())}</div><h1 tabindex="-1">${esc(p.name)}</h1><p class="reader-full-title">${esc(p.title)}</p><p class="reader-meta">首次公开 ${esc(p.firstPublished||'未核验')} · ${esc(p.venue)}</p><div class="reader-intro">${R.richParagraphs(p.contribution)}</div><div class="reader-evidence-label ${n.coverage?.level==='limited'?'limited':''}">${n.coverage?.level==='limited'?'受限材料导读 · 完整正文待核验':n.status==='needs_review'?'指定版本深入笔记 · 新版本待复核':'指定版本深入笔记 · 作者报告与编辑解读'}</div><details class="reader-source-info"><summary>阅读版本与证据范围</summary><p>${esc(n.version)}</p><p>实际核验：${esc(n.verifiedAt||'未记录')}。元数据更新不等于全文重读；本文不是独立复现。</p>${sourceLinks(p.sources)}</details><div class="reader-title-tools"><a class="btn" href="${esc(url(p.paperUrl))}" target="_blank" rel="noopener noreferrer">阅读原文 ↗</a>${resourceButtons(p)}<button class="btn" data-follow-paper="${esc(pid)}">＋ 关注</button><button class="btn" data-compare="${esc(pid)}">＋ 对比</button><a class="btn" href="?view=news&amp;paper=${esc(pid)}">相关新闻</a><button class="btn" id="reader-share">分享本篇</button><button class="btn" id="reader-print">打印</button></div></header><section class="reader-key"><span>KEY RESULT</span>${R.noteBlocks(p.findings)}</section>${saved?`<div class="resume-notice">${saved.version===n.version?'已保存上次阅读位置。':'上次记录来自不同阅读版本，未自动跳转。'} <button id="reader-resume" class="text-link">${saved.version===n.version?'继续上次阅读':'查看原记录位置'}</button><button id="reader-restart" class="text-link">从头读</button></div>`:''}${n.sections.map((x,i)=>`<section class="reader-chapter" id="${esc(anchor(x.id))}"><div class="chapter-kicker">CHAPTER ${String(i+1).padStart(2,'0')}</div><h2>${R.richText(x.title)}</h2>${R.noteBlocks(x.body)}<details class="chapter-sources"><summary>原文依据 · ${x.sources.length} 项</summary>${sourceLinks(x.sources)}</details></section>`).join('')}<section id="reader-evidence" class="reader-chapter"><div class="chapter-kicker">EVIDENCE & FIGURES</div><h2>把结论放回原图、原表。</h2><p class="reader-muted">下列图表保留来源、适用条件和解释；原图以可追溯链接为主，不补造未核验图像。</p>${R.richEvidence(n)}</section><details class="reader-source-info"><summary>发表历程与版本记录</summary>${R.lifecycle(r.publication,p)}</details><div class="reader-bottom"><span>你已经读到本篇末尾。</span><button class="btn" id="reader-done">标记已读</button><button class="btn" data-reader-export>导出这篇笔记</button></div></article></div>`;
  setReaderStyle(host,s);updatePicks();
  const media=matchMedia('(max-width:800px)'),outline=host.querySelector('.reader-outline details');const sizeOutline=()=>{outline.open=!media.matches;};sizeOutline();media.addEventListener('change',sizeOutline);
  let active='',timer,raf=0;
  const sections=[...host.querySelectorAll('.reader-chapter')];
  const persist=()=>{if(active&&document.getElementById(active))savePosition(pid,{anchor:active,offset:Math.max(0,Math.round(-document.getElementById(active).getBoundingClientRect().top+110)),version:n.version,at:new Date().toISOString()});};
  const tick=()=>{raf=0;if(t!==token)return;let current=null;for(const el of sections)if(el.getBoundingClientRect().top<=170)current=el;active=current?.id||'';host.querySelectorAll('[data-reader-jump]').forEach(b=>b.setAttribute('aria-current',b.dataset.readerJump===active?'location':'false'));const first=host.getBoundingClientRect().top+scrollY,last=host.getBoundingClientRect().bottom+scrollY-innerHeight;const value=Math.max(0,Math.min(100,Math.round((scrollY-first)/Math.max(1,last-first)*100)));const prog=host.querySelector('.reader-progress');prog.setAttribute('aria-valuenow',value);prog.firstElementChild.style.width=value+'%';clearTimeout(timer);timer=setTimeout(persist,400);};
  const scroll=()=>{if(!raf)raf=requestAnimationFrame(tick);};
  const jump=(id,offset=0)=>{const el=sections.find(x=>x.id===id);if(!el)return;scrollTo({top:el.getBoundingClientRect().top+scrollY-110+Math.max(0,Math.min(offset,el.offsetHeight)),behavior:'instant'});tick();};
  host.querySelectorAll('[data-reader-jump]').forEach(b=>b.onclick=()=>{jump(b.dataset.readerJump);const u=new URL(location.href);u.hash=b.dataset.readerJump;history.replaceState({},'',u);});
  for(const k of ['font','line','theme'])host.querySelector('#reader-'+k).onchange=e=>{s[k]=k==='theme'?e.target.value:Number(e.target.value);setReaderStyle(host,s);};
  host.querySelector('#reader-status').onchange=e=>api.setStatus(pid,e.target.value);
  host.querySelector('#reader-done').onclick=()=>{api.setStatus(pid,'read');host.querySelector('#reader-status').value='read';api.notify('已标记为已读，仅保存在当前浏览器。');};
  host.querySelector('#reader-share').onclick=()=>api.copy(new URL('?view=reader&paper='+pid,location.href).href,'已复制公开阅读链接，不含本地进度。');
  host.querySelector('#reader-print').onclick=()=>print();host.querySelectorAll('[data-reader-export]').forEach(b=>b.onclick=()=>exportDialog([pid]));
  host.querySelector('#reader-resume')?.addEventListener('click',()=>jump(saved.anchor,saved.offset));
  host.querySelector('#reader-restart')?.addEventListener('click',()=>scrollTo({top:0,behavior:'instant'}));
  addEventListener('scroll',scroll,{passive:true});addEventListener('pagehide',persist);
  cleanup=()=>{media.removeEventListener('change',sizeOutline);clearTimeout(timer);cancelAnimationFrame(raf);persist();removeEventListener('scroll',scroll);removeEventListener('pagehide',persist);};
  document.title=p.name+' · 专注阅读 · VLA Radar';host.querySelector('h1').focus({preventScroll:true});
  if(location.hash.startsWith('#read-'))jump(location.hash.slice(1));else if(saved?.version===n.version)jump(saved.anchor,saved.offset);else tick();
 }
 async function compareView(host,t){
  const param=new URLSearchParams(location.search).get('compare');if(param!==null){compare=C.uniqueIds(param.split(','),ids);writeCompare();}
  host.innerHTML=heading('COMPARE IDEAS, NOT JUST SCORES','看清论文之间的区别。','选择2–4篇，按问题、方法、训练与证据并排阅读。这里不是综合能力排名。')+`<div class="compare-builder"><div id="compare-selected"></div><label class="compare-find">添加论文<input id="compare-search" type="search" placeholder="输入简称或标题，最多选择4篇" autocomplete="off"></label><div id="compare-candidates"></div><div class="compare-tools"><label><input type="checkbox" id="compare-differences"> 隐藏完全相同的摘录行</label><button class="btn" id="compare-share">分享对比</button><button class="btn" id="compare-export">导出所选笔记</button><button class="btn" id="compare-clear">清空</button></div></div><div id="compare-table" role="status"></div>`;
  const setURL=()=>{const u=new URL(location.href);u.searchParams.set('compare',compare.join(','));history.replaceState({},'',u);};
  const candidates=()=>{const q=host.querySelector('#compare-search').value.trim().toLowerCase();host.querySelector('#compare-candidates').innerHTML=q?lib.papers.filter(p=>!compare.includes(p.id)&&(p.name+' '+p.title).toLowerCase().includes(q)).slice(0,10).map(p=>`<button class="compare-candidate" data-add-paper="${p.id}"><b>${esc(p.name)}</b><span>${esc(p.title)}</span><i>＋</i></button>`).join('')||'<p>未找到匹配的标题。</p>':'<p class="workspace-hint">也可以在文献卡片上点击“＋ 对比”。选择信息仅存本机，分享前请确认所选内容。</p>';host.querySelectorAll('[data-add-paper]').forEach(b=>b.onclick=()=>{addCompare(b.dataset.addPaper);setURL();draw();candidates();});};
  let drawId=0;
  async function draw(){const seq=++drawId;host.querySelector('#compare-selected').innerHTML=compare.map(id=>`<span class="compare-chip">${esc(lookup(id).name)}<button data-remove-paper="${id}" aria-label="移除 ${esc(lookup(id).name)}">×</button></span>`).join('')+`<small>${compare.length} / 4 已选</small>`;host.querySelectorAll('[data-remove-paper]').forEach(b=>b.onclick=()=>{compare=compare.filter(x=>x!==b.dataset.removePaper);writeCompare();setURL();draw();candidates();});
   const table=host.querySelector('#compare-table');if(compare.length<2){table.innerHTML='<div class="workspace-empty"><span>02 — 04</span><h2>从两篇论文开始。</h2><p>并排看见机制与证据，而不只是名字和分数。</p></div>';return;}
   table.innerHTML='<p class="workspace-loading">正在读取所选论文，其他笔记不会加载…</p>';const selected=await Promise.all(compare.map(record));if(t!==token||seq!==drawId)return;
   const dims=C.dimensions.filter(([key])=>!host.querySelector('#compare-differences').checked||new Set(selected.map(r=>C.signature(r,key))).size>1);
   table.innerHTML=`<p class="workspace-hint">以下按现有笔记章节标题匹配原文摘录，未找到的维度明确留空；同一章节可能涉及多个维度。不同文字不代表效果优劣，请展开全文和来源核对。</p><div class="comparison-scroll" tabindex="0" role="region" aria-label="论文并排对比"><table class="comparison-table" style="--compare-columns:${selected.length}"><thead><tr><th scope="col">比较维度</th>${selected.map(r=>`<th scope="col"><span>${esc(r.paper.firstPublished||'日期未核验')}</span><h2>${esc(r.paper.name)}</h2><p>${esc(r.paper.title)}</p><small>${r.note.coverage?.level==='limited'?'受限来源':r.note.status==='needs_review'?'新版本待复核':'指定版本深读'}</small><button class="text-link" data-focus="${r.paper.id}">阅读全文 ↗</button></th>`).join('')}</tr></thead><tbody><tr><th scope="row">阅读版本</th>${selected.map(r=>`<td><p>${esc(r.note.version)}</p><small>核验 ${esc(r.note.verifiedAt||'未知')}</small></td>`).join('')}</tr>${dims.map(([key,label])=>{const same=new Set(selected.map(r=>C.signature(r,key))).size===1;return `<tr class="${same?'same-row':'different-row'}"><th scope="row">${label}<small>${same?'摘录相同':'摘录不同'}</small></th>${selected.map(r=>{const secs=C.sectionsFor(r,key);return `<td>${secs.length?secs.map(s=>`<details class="compare-excerpt"><summary><b>${R.richText(s.title)}</b><span>${esc(s.body.slice(0,150))}${s.body.length>150?'…':''}</span><em>展开该节全文与来源</em></summary>${R.noteBlocks(s.body)}${sourceLinks(s.sources)}<button class="text-link" data-focus="${r.paper.id}">进入专注阅读</button></details>`).join(''):'<p class="missing-field">当前笔记未单独提供此维度；不从其他论文补猜。</p>'}</td>`;}).join('')}</tr>`;}).join('')}<tr><th scope="row">KEY RESULT</th>${selected.map(r=>`<td>${R.noteBlocks(r.paper.findings)}<small>保留各自协议，不直接合成排名。</small></td>`).join('')}</tr></tbody></table></div>`;
  }
  host.querySelector('#compare-search').oninput=candidates;host.querySelector('#compare-differences').onchange=draw;
  host.querySelector('#compare-clear').onclick=()=>{compare=[];writeCompare();setURL();draw();candidates();};
  host.querySelector('#compare-share').onclick=()=>{if(compare.length<2)return api.notify('请先选择至少2篇。');setURL();api.copy(new URL('?view=compare&compare='+compare.join(','),location.href).href,'已复制对比链接；不含收藏和阅读状态。');};
  host.querySelector('#compare-export').onclick=()=>exportDialog(compare);candidates();await draw();
 }
 async function manifest(){if(!lib.experienceUrl)throw new Error('网站版本不一致，请刷新');if(!indexPromise)indexPromise=g.RadarRuntime.loadJson(lib.experienceUrl).catch(e=>{indexPromise=null;throw e;});return indexPromise;}
 async function updates(host,t){
  const m=await manifest(),data=await g.RadarRuntime.loadJson(m.updatesUrl);if(t!==token)return;
  let type='all',only=false,page=0,loaded=[],seq=0;const marked=C.localJSON(keys.seen,null),since=typeof marked==='string'&&Number.isFinite(Date.parse(marked))?marked:api.previousVisit;
  host.innerHTML=heading('WHAT CHANGED & WHY','让每一次更新，都有来处。','新收录、论文版本、发表状态、笔记与评测分开展示。日期不够明确的历史快照不会冒充新事件。')+`<div class="updates-controls"><label>更新类型<select id="updates-kind">${Object.entries(kindNames).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label><label><input id="updates-since" type="checkbox" ${since?'':'disabled'}> 上次访问后</label><span>${since?'比较基线：'+esc(new Date(since).toISOString().slice(0,19).replace('T',' '))+' UTC':'首次访问：尚无本地比较基线'}</span><button class="btn" id="updates-mark">标记已看</button></div><p class="workspace-hint">“发现日期”与“事件日期”分别保留。只精确到日的记录采用保守比较，同日可能重复提示；现存笔记快照不表示首次收录日。</p><div id="updates-list"></div><button class="btn" id="updates-more">加载更多记录</button>`;
  const draw=()=>{const shown=loaded.filter(e=>!only||C.isNew(e,since));host.querySelector('#updates-list').innerHTML=shown.length?shown.map(e=>`<article class="update-event"><div class="update-marker ${esc(e.kind)}">${esc(kindNames[e.kind]||e.kind)}</div><div><div class="update-date">${e.observedAt?'发现于 '+esc(e.observedAt):'历史快照 · '+esc(e.date||'日期未知')} ${e.date&&e.observedAt?' / 事件日期 '+esc(e.date):''}</div><h2>${esc(e.title)}</h2><p>${esc(e.summary||'')}</p>${e.changes?.length?`<details class="update-diff"><summary>查看记录差异 · ${e.changes.length} 项</summary>${e.changes.map(c=>`<section><h3>${esc(c.field)}</h3><div class="diff-before"><b>之前</b><p>${esc(c.before??'未记录')}</p></div><div class="diff-after"><b>之后</b><p>${esc(c.after??'未记录')}</p></div></section>`).join('')}</details>`:''}<div class="update-links">${e.paperId?`<button class="text-link" data-focus="${esc(e.paperId)}">阅读 ${esc(lookup(e.paperId)?.name||e.paperId)} ↗</button>`:''}<a class="text-link" href="${esc(url(e.source))}" target="_blank" rel="noopener noreferrer">追溯来源 ↗</a></div></div></article>`).join(''):'<div class="workspace-empty"><h2>当前已加载范围没有匹配记录。</h2><p>可调整类型或继续加载更早记录；不代表外部没有新论文。</p></div>';const more=host.querySelector('#updates-more');more.hidden=page>=(data.streams[type]||[]).length;more.disabled=false;more.textContent='加载更多记录';};
  async function more(reset=false){const id=++seq;if(reset){page=0;loaded=[];}const pages=data.streams[type]||[];if(page>=pages.length){draw();return;}const b=host.querySelector('#updates-more');b.disabled=true;b.textContent='读取中…';try{const chunk=await g.RadarRuntime.loadJson(pages[page].url);if(t!==token||id!==seq)return;loaded.push(...chunk.events);page++;draw();}catch(e){if(t!==token||id!==seq)return;b.disabled=false;b.textContent='加载失败，点击重试';}}
  host.querySelector('#updates-kind').onchange=e=>{type=e.target.value;more(true);};host.querySelector('#updates-since').onchange=e=>{only=e.target.checked;draw();};host.querySelector('#updates-more').onclick=()=>more();
  host.querySelector('#updates-mark').onclick=()=>{const ok=C.store(keys.seen,new Date().toISOString());api.notify(ok?'已记录查看时间，仅存本机。重新打开更新中心使用新基线。':'当前浏览器无法保存查看时间。');};await more();
 }
 async function coverage(host,t){
  const m=await manifest(),d=await g.RadarRuntime.loadJson(m.coverageUrl);if(t!==token)return;let measure='papers';const cells=new Map(d.cells.map(c=>[c.topic+'|'+c.dataset,c]));
  host.innerHTML=heading('EVIDENCE COVERAGE','研究方向 × 评测证据。','这是本站已核验结果的覆盖地图，不是全领域热度榜。点击格子，查看支撑它的来源论文。')+`<div class="coverage-summary"><article><strong>${d.paperCount}</strong><span>收录论文</span></article><article><strong>${d.datasets.length}</strong><span>数据集系列</span></article><article><strong>${d.activeResultCount}</strong><span>当前有效结果</span></article><article><strong>${d.dispositions.deferred}</strong><span>待映射论文</span></article></div><div class="coverage-tools"><label>格子显示<select id="coverage-measure"><option value="papers">不同来源论文数</option><option value="results">有效结果记录数</option></select></label><span class="heat-legend">低 <i class="heat-1"></i><i class="heat-2"></i><i class="heat-3"></i><i class="heat-4"></i> 高</span></div><div id="coverage-matrix"></div><p class="workspace-hint">按“报告这条结果的论文”的研究方向归属，引用基线不重复算成来源论文。跨方向标签有重叠；0 表示本站尚无映射证据，不代表没有研究。待提取论文不凭关键词猜测数据集归属。</p><div id="coverage-papers" aria-live="polite"></div>`;
  function draw(){const value=c=>!c?0:measure==='papers'?c.paperIds.length:c.resultCount;const max=Math.max(1,...d.cells.map(value));host.querySelector('#coverage-matrix').innerHTML=`<div class="heat-scroll" role="region" tabindex="0" aria-label="可滚动的证据覆盖表"><table class="heatmap"><thead><tr><th>研究方向 / 数据集</th>${d.datasets.map(name=>`<th scope="col">${esc(name)}</th>`).join('')}</tr></thead><tbody>${lib.topics.map(topic=>`<tr><th scope="row">${esc(topic.name)}</th>${d.datasets.map(dataset=>{const c=cells.get(topic.id+'|'+dataset),n=value(c),level=n?Math.max(1,Math.ceil(4*n/max)):0;return `<td><button class="heat-cell heat-${level}" data-cell="${esc(topic.id+'|'+dataset)}" aria-label="${esc(topic.name)}，${esc(dataset)}，${n}${measure==='papers'?'篇来源论文':'条结果'}">${n||'—'}</button></td>`;}).join('')}</tr>`).join('')}</tbody></table></div>`;host.querySelectorAll('[data-cell]').forEach(b=>b.onclick=()=>{const c=cells.get(b.dataset.cell),[topic,dataset]=b.dataset.cell.split('|'),name=lib.topics.find(x=>x.id===topic).name;const target=host.querySelector('#coverage-papers');target.innerHTML=`<div class="coverage-selection"><h2>${esc(name)} · ${esc(dataset)} <small>${c?c.paperIds.length:0} 篇（首30篇）</small></h2><button class="btn" id="coverage-board">查看该数据集榜单 ↗</button></div>`+(c?c.paperIds.slice(0,30).map(id=>`<article class="coverage-paper"><div><h3>${esc(lookup(id).name)}</h3><p>${esc(lookup(id).title)}</p></div>${buttons(id)}</article>`).join(''):'<p class="workspace-empty">本站尚无已核验的对应结果映射。</p>');target.querySelector('#coverage-board').onclick=()=>api.navigate('leaderboards',{dataset});target.scrollIntoView({block:'nearest',behavior:'smooth'});});}
  host.querySelector('#coverage-measure').onchange=e=>{measure=e.target.value;draw();};draw();
 }
 function chart({track,rows,host,metric,chartType='bar',dateBasis='firstPublished',toggle=true,onChange}){
  if(!host?.isConnected)return;
  if(toggle){host.hidden=!host.hidden;if(host.hidden)return;}else host.hidden=false;
  metric=track.columns.includes(metric)?metric:track.columns.includes('Average')?'Average':track.columns[0];
  chartType=chartType==='scatter'?'scatter':'bar';dateBasis=dateBasis==='verifiedAt'?'verifiedAt':'firstPublished';
  const unit=track.unit==='percent'?'%':track.unit==='seconds'?' s':'',selected=(a,b)=>a===b?'selected':'';
  function change(patch){
   if(onChange){onChange(patch);return;}
   metric=patch.metric||metric;chartType=patch.chartType||chartType;dateBasis=patch.dateBasis||dateBasis;draw();
  }
  function draw(){
   if(!host.isConnected)return;
   const c=C.chartData(track,rows,metric);
   host.innerHTML=`<section class="protocol-visual"><div class="chart-heading"><div class="eyebrow">ONE PROTOCOL. ONE METRIC.</div><h2>${esc(track.name)}</h2></div>
    <div class="protocol-chart-controls"><label>图表类型<select id="chart-type"><option value="bar" ${selected(chartType,'bar')}>成绩条形图</option><option value="scatter" ${selected(chartType,'scatter')}>时间—成绩散点图</option></select></label>
    <label>图表指标<select id="chart-metric">${track.columns.map(k=>`<option ${selected(k,metric)}>${esc(k)}</option>`).join('')}</select></label>
    ${chartType==='scatter'?`<label>横轴时间口径<select id="chart-time"><option value="firstPublished" ${selected(dateBasis,'firstPublished')}>来源论文首次公开日期</option><option value="verifiedAt" ${selected(dateBasis,'verifiedAt')}>本站结果核验日期</option></select></label>`:''}</div>
    <p class="workspace-hint">${track.comparisonScope==='protocol'?'只展示本赛道已核验的报告，差异不代表统计显著。':'数值排列仅帮助阅读；训练预算或评测细节不完全一致，不赋予公平名次。'} 原文未统一提供误差，不补造误差条，不合成跨协议总分。</p><div id="protocol-plot"></div></section>`;
   host.querySelector('#chart-type').onchange=e=>change({chartType:e.target.value,focus:'#chart-type'});
   host.querySelector('#chart-metric').onchange=e=>change({metric:e.target.value,focus:'#chart-metric'});
   if(chartType==='scatter'){
    host.querySelector('#chart-time').onchange=e=>change({dateBasis:e.target.value,focus:'#chart-time'});
    scatter(host.querySelector('#protocol-plot'));return;
   }
   host.querySelector('#protocol-plot').innerHTML=`<div class="chart-scale"><span>${c.min}${unit}</span><span>${c.max}${unit}</span></div><div class="protocol-bars" role="list">${c.rows.slice(0,40).map(r=>`<div class="chart-row" role="listitem"><div class="chart-model"><strong>${esc(r.method)}</strong><a href="${esc(url(r.source))}" target="_blank" rel="noopener noreferrer">${esc(r.locator)} ↗</a></div><div class="bar-lane" aria-hidden="true"><span style="margin-left:${r.offset}%;width:${r.width}%"></span></div><b class="chart-value">${esc(r.values[c.metric])}${unit}</b></div>`).join('')}</div><p class="workspace-hint">${Math.min(c.rows.length,40)} / ${rows.length} 条记录绘图（最多40条，随表格排列）；${c.missing} 条缺失值不画成零分。完整记录见表格或 CSV。训练条件：${esc(track.trainingRegime)}</p>`;
  }
  function scatter(target){
   const d=C.scatterData(track,rows,metric,byId,dateBasis),timeLabel=dateBasis==='verifiedAt'?'本站结果核验日期':'来源论文首次公开日期';
   const explanation=dateBasis==='verifiedAt'?'横轴是本站核验这条结果的日期，不是实验执行日、模型发布日或论文首发日。':'横轴来自记录所归属的报告论文，不一定是被引用基线的方法首发日期，也不代表这条成绩实际测得的日期。同一论文的基线会共用日期。';
   const summary=`${d.plottedCount} / ${d.eligible} 条结果可见 · 成绩缺失 ${d.missingScore} 条 · 缺少精确日期 ${d.missingDate} 条`;
   target.innerHTML=`<p class="scatter-time-note">${explanation} 未知或仅有年/月的日期不补造为某一天，不进入图中；原记录仍可查。此图不是技术进步趋势认证。</p><p class="scatter-summary" role="status">${summary}</p><div id="scatter-drawing"></div><div class="scatter-footer"><span>${d.groups.length} / ${d.totalGroups} 个日期—成绩坐标（最多${d.limit}个）；重合坐标合并显示条数，展开可逐条核对。</span><button class="btn" id="export-scatter-csv">导出散点数据 CSV</button></div><div class="scatter-detail" id="scatter-detail" aria-live="polite"><p>悬停、点选或使用 Tab 聚焦数据点，查看方法、日期和原始证据。相同坐标内的记录不做平均。</p></div>`;
   target.querySelector('#export-scatter-csv').onclick=()=>api.download(track.id+'-'+metric.replace(/[^a-zA-Z0-9_-]/g,'_')+'-time.csv',C.scatterCSV(track,rows,metric,byId,dateBasis),'text/csv;charset=utf-8');
   if(!d.validCount){target.querySelector('#scatter-drawing').innerHTML='<p class="workspace-empty">当前指标没有同时具备数值和精确日期的记录。可以切换时间口径或指标；不使用今天的日期填补空缺。</p>';return;}
   const W=880,H=420,L=74,T=36,PW=770,PH=290;
   const x=v=>L+(v-d.start)/(d.end-d.start)*PW,y=v=>T+PH-(v-d.min)/(d.max-d.min)*PH;
   const fmt=n=>Number.isInteger(n)?String(n):Number(n.toFixed(2)).toString();
   const xticks=Array.from({length:d.oneDate?3:5},(_,i)=>d.start+(d.end-d.start)*i/(d.oneDate?2:4));
   const yticks=Array.from({length:5},(_,i)=>d.min+(d.max-d.min)*i/4);
   const tickDate=n=>new Date(n).toISOString().slice(0,10);
   target.querySelector('#scatter-drawing').innerHTML=`${d.oneDate?'<p class="workspace-hint">当前只有一个日期：纵向分布代表同日记录，不是随时间变化的趋势。</p>':''}
    <div class="scatter-scroll" role="region" tabindex="0" aria-label="可横向滚动的时间—成绩散点图"><svg class="score-scatter" viewBox="0 0 ${W} ${H}" role="group" aria-labelledby="scatter-title scatter-description">
    <title id="scatter-title">${esc(track.name)}：${esc(metric)}随${timeLabel}的分布</title><desc id="scatter-description">${summary}。不连接数据点，不跨协议拟合趋势。每个可聚焦点可展开原始记录。</desc>
    ${yticks.map(v=>`<line class="scatter-grid" x1="${L}" y1="${y(v)}" x2="${L+PW}" y2="${y(v)}"/><text class="scatter-tick" x="${L-12}" y="${y(v)+4}" text-anchor="end">${fmt(v)}${unit}</text>`).join('')}
    ${xticks.map(v=>`<line class="scatter-grid" x1="${x(v)}" y1="${T}" x2="${x(v)}" y2="${T+PH}"/><text class="scatter-tick" x="${x(v)}" y="${T+PH+25}" text-anchor="middle">${tickDate(v)}</text>`).join('')}
    <line class="scatter-axis" x1="${L}" y1="${T+PH}" x2="${L+PW}" y2="${T+PH}"/><text class="scatter-axis-title" x="${L}" y="18">${esc(metric)}${unit?' ('+unit.trim()+')':''} · ${R.metricDirection(track,metric)==='lower'?'越低越好':'越高越好'}</text><text class="scatter-axis-title" x="${L+PW/2}" y="395" text-anchor="middle">${timeLabel} · UTC 日期</text>
    ${d.groups.map((group,i)=>`<g class="scatter-point" data-scatter-point="${i}" tabindex="0" role="button" aria-controls="scatter-detail" aria-label="${esc(group.points.length===1?group.points[0].row.method:group.points.length+'条重合记录')}，${group.date}，${esc(metric)} ${group.value}${unit}，查看来源"><title>${esc(group.points.map(p=>p.row.method).slice(0,8).join(' / '))} · ${group.date} · ${group.value}${unit}</title><circle class="scatter-hit" cx="${x(group.time)}" cy="${y(group.value)}" r="14"/><circle class="scatter-dot" cx="${x(group.time)}" cy="${y(group.value)}" r="${group.points.length>1?11:6}"/>${group.points.length>1?`<text class="scatter-count" x="${x(group.time)}" y="${y(group.value)+4}" text-anchor="middle" aria-hidden="true">${group.points.length>99?'99+':group.points.length}</text>`:''}</g>`).join('')}</svg></div>`;
   let active=-1;
   function show(i){
    if(active===i)return;active=i;let count=10;const group=d.groups[i];
    target.querySelectorAll('[data-scatter-point]').forEach(p=>p.classList.toggle('is-active',Number(p.dataset.scatterPoint)===i));
    function detail(){
     target.querySelector('#scatter-detail').innerHTML=`<h3>${group.date} · ${esc(metric)} ${group.value}${unit} <small>${group.points.length} 条原始记录</small></h3>`+group.points.slice(0,count).map(p=>`<article class="scatter-record"><strong>${esc(p.row.method)}</strong><p>${timeLabel}：${p.date} · 来源论文：${esc(p.paperName)} (${esc(p.row.paperId)})</p><p>${esc(p.row.trainingData)}</p><p>${esc(p.row.evaluationNotes)}</p><small>${esc(p.row.sourceVersion)} · ${esc(p.row.locator)}</small>${sourceLinks([{label:'原始结果与设置',url:p.row.source}])}<a class="board-paper-link" href="?view=reader&amp;paper=${esc(p.row.paperId)}">阅读来源论文 ↗</a></article>`).join('')+(count<group.points.length?'<button id="scatter-more" class="btn">显示更多重合记录</button>':'');
     const more=target.querySelector('#scatter-more');if(more)more.onclick=()=>{count+=10;detail();};
    }detail();
   }
   const svg=target.querySelector('.score-scatter'),points=[...target.querySelectorAll('[data-scatter-point]')];
   // Dense points may overlap visually: pointer selection uses the nearest true coordinate,
   // not whichever SVG circle happens to be painted last. No coordinate jitter is applied.
   function nearest(event,focus){
    const matrix=svg.getScreenCTM();if(!matrix)return;
    const pos=new DOMPoint(event.clientX,event.clientY).matrixTransform(matrix.inverse());
    let index=-1,best=18*18;
    d.groups.forEach((g,i)=>{const dist=(x(g.time)-pos.x)**2+(y(g.value)-pos.y)**2;if(dist<best){best=dist;index=i;}});
    if(index>=0){show(index);if(focus)points[index].focus({preventScroll:true});}
   }
   svg.onpointermove=e=>nearest(e,false);svg.onclick=e=>nearest(e,true);
   points.forEach(p=>{
    const showPoint=()=>show(Number(p.dataset.scatterPoint));p.onfocus=showPoint;
    p.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();showPoint();}};
   });
  }
  draw();
 }
 function exportDialog(selected){return g.RadarTools.export(selected);}
 async function action(type,arg){if(type==='focus'){api.navigate('reader',{paper:arg});return;}if(type==='compare'){addCompare(arg);return;}if(type==='export')return exportDialog();if(type==='cite')return exportDialog([arg]);if(type==='chart')return chart(arg);if(type==='csv')return api.download(arg.track.id+'.csv',C.csv(arg.track,arg.rows),'text/csv;charset=utf-8');}
 async function render(view,host){const t=token;try{await ({reader,compare:compareView,updates,coverage})[view](host,t);}catch(e){if(t!==token)return;host.innerHTML=heading('RETRY','内容暂时没有载入。','请检查网络后重试；加载失败不表示论文或数据不存在。')+`<button class="btn" data-view="${esc(view)}">重试</button>`;console.warn('Workspace:',e.message);}}
 g.RadarExperience={configure,leave,render,action,refreshPicks:updatePicks};
})(window);
