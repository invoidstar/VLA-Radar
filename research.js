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
  const details = new Map(); let boardPromise, boardToken=0;
  async function getJson(path){const r=await fetch(path,{credentials:'omit',cache:'no-cache'});if(!r.ok)throw new Error('HTTP '+r.status);return r.json();}
  function loadBoards(){if(!boardPromise)boardPromise=getJson('data/leaderboards.json').then(x=>{if(x.schemaVersion!==1||!Array.isArray(x.tracks)||!Array.isArray(x.results))throw new Error('榜单格式不支持');return x;}).catch(e=>{boardPromise=null;throw e;});return boardPromise;}
  function pageWindow(current,total){const pages=new Set([1,total]);for(let i=Math.max(1,current-2);i<=Math.min(total,current+2);i++)pages.add(i);let prev=0,out=[];for(const i of [...pages].filter(i=>i>0).sort((a,b)=>a-b)){if(prev&&i-prev>1)out.push(null);out.push(i);prev=i;}return out;}
  function visibleResults(data,trackId){const superseded=new Set(data.results.filter(r=>r.evidence==='checked'&&r.supersedes).map(r=>r.supersedes));return data.results.filter(r=>r.trackId===trackId&&r.evidence==='checked'&&!superseded.has(r.id));}
  function rankRows(rows,column,direction='higher'){
    let prior, rank=0;
    return [...rows].sort((a,b)=>{const av=a.values[column],bv=b.values[column];if(av==null)return bv==null?a.method.localeCompare(b.method):1;if(bv==null)return -1;return (direction==='higher'?bv-av:av-bv)||a.method.localeCompare(b.method);}).map((r,i)=>{const v=r.values[column];if(v!=null&&v!==prior)rank=i+1;prior=v;return {...r,rank:v==null?null:rank};});
  }
  async function detail(p){
    if(!p.detailUrl)return null;
    // Only static detail paths from the public catalog are fetched; no arbitrary network target.
    if(!/^data\/details\/p\d{3,}\.json\?v=[a-f0-9]{16}$/.test(p.detailUrl))throw new Error('无效详情路径');
    if(!details.has(p.detailUrl))details.set(p.detailUrl,getJson(p.detailUrl).then(r=>{if(r.schemaVersion!==2||r.paper?.id!==p.id||!r.publication||!Array.isArray(r.note?.sections))throw new Error('详情版本不一致，请刷新');return r;}).catch(e=>{details.delete(p.detailUrl);throw e;}));
    return details.get(p.detailUrl);
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
    const labels={'primary-methods-experiments':'已阅读原文方法与实验指定范围','primary-theory':'理论原文与证明范围解读；不产生实验排名','official-technical-report':'官方技术报告解读；公开细节范围见下文','official-abstract-only':'仅依据官方摘要：全文方法、实验细节仍待核验'};
    return `<p class="note-coverage ${c.scope==='official-abstract-only'?'limited':''}">${esc(labels[c.scope]||c.scope)} · ${note.sections.length} 个解释章节。所有数值为指定来源报告，不代表本站独立复现。</p>`;
  }
  function richEvidence(note){
    const source=note.coverage?.source||note.sections[0]?.sources[0]?.url;
    const tables=(note.tables||[]).map((t,i)=>`<section class="note-table-block"><h3>结果与推理对照 ${i+1} · ${esc(t.title)}</h3><div class="note-table-scroll" tabindex="0" role="region" aria-label="${esc(t.title)}"><table class="note-table"><thead><tr>${t.columns.map(c=>`<th scope="col">${esc(c)}</th>`).join('')}</tr></thead><tbody>${t.rows.map(row=>`<tr>${row.map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p class="note-small">${esc(t.caption)}</p>${links([{label:t.locator+' · 原文依据',url:source}])}</section>`).join('');
    const figures=(note.figures||[]).map(f=>`<figure class="note-figure"><h3>${esc(f.title)}</h3>${f.imageUrl?`<a href="${esc(external(f.url))}" target="_blank" rel="noopener noreferrer"><img src="${esc(external(f.imageUrl))}" alt="${esc(f.title)}" loading="lazy" decoding="async" referrerpolicy="no-referrer"></a>`:''}<figcaption>${para(f.caption)}${f.license?`<p class="note-small">原作者图像 · ${esc(f.license)} · 未修改。图片不可达时仍可访问下方原文。</p>`:'<p class="note-small">提供原图定位和阅读说明，不复制未确认再分发许可的图像。</p>'}${links([{label:'查看论文原图 / 上下文',url:f.url}])}</figcaption></figure>`).join('');
    const br=note.benchmarkReview;const labels={pending:'待检查',extracted:'已有提取记录', 'not-applicable':'无适用标准榜单','protocol-unresolved':'协议或数据待核验'};
    const review=br?`<aside class="note-benchmark-review"><strong>评测提取：${esc(labels[br.status])}</strong><p>${esc(br.note)}</p><small>检查时间：${esc(br.checkedAt||'尚未完成')}</small></aside>`:'';
    return tables+figures+review;
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
      panel.innerHTML=`<div class="note-heading"><span class="note-badge ${note.status==='expanded'?'verified':''}">${note.coverage?.scope==='official-abstract-only'?'摘要解读 · 全文待核验':stale?'深入笔记 · 新版本待复核':note.coverage?.level==='deep'?'深入笔记 · 分节原文依据':note.status==='expanded'?'已扩展 · 有原文定位':'既有笔记 · 待深化核验'}</span><small>笔记核验 ${esc(date(note.verifiedAt))}</small></div><div class="research-tabs" role="tablist" aria-label="论文详情内容"><button id="tab-notes" role="tab" aria-selected="true" aria-controls="panel-notes" data-note-tab="notes">阅读笔记</button><button id="tab-life" role="tab" aria-selected="false" aria-controls="panel-life" tabindex="-1" data-note-tab="life">发表历程</button><button id="tab-results" role="tab" aria-selected="false" aria-controls="panel-results" tabindex="-1" data-note-tab="results">评测记录</button></div><div id="panel-notes" role="tabpanel" aria-labelledby="tab-notes"><div class="note-context"><strong>阅读版本：${esc(note.version)}</strong>${scopeNotice(note)}<p>${note.status==='legacy'?'下面保留原有公开笔记，尚未逐篇重新读全文。周更会按优先级和核验时间补齐研究问题、方法机制、创新差异、实验和消融；不会用重复模板冒充完整精读。':stale?'下方结论有具体来源，但阅读版本早于当前 arXiv 版本。旧版结果保留，版本差异待核验。':'以下是公开原文指定片段的结构化总结，并非独立复现或整篇认证。'}</p></div><section class="key-result-full"><small>KEY RESULT · 原记录保留</small>${para(p.findings)}</section><div class="note-toc" aria-label="笔记章节">${note.sections.map((s,i)=>`<button data-note-anchor="note-${esc(s.id)}">${String(i+1).padStart(2,'0')} ${esc(s.title)}</button>`).join('')}</div>${note.sections.map((s,i)=>`<section class="note-section" id="note-${esc(s.id)}"><span class="note-number">${String(i+1).padStart(2,'0')}</span><div><h3>${esc(s.title)}</h3>${para(s.body)}${links(s.sources)}</div></section>`).join('')}${richEvidence(note)}</div><div id="panel-life" role="tabpanel" aria-labelledby="tab-life" hidden>${lifecycle(r.publication,p)}</div><div id="panel-results" role="tabpanel" aria-labelledby="tab-results" hidden><p class="research-loading">正在载入公开评测记录…</p></div>`;
      hint.replaceWith(panel);
      const choose=key=>{panel.querySelectorAll('[data-note-tab]').forEach(b=>{const yes=b.dataset.noteTab===key;b.setAttribute('aria-selected',yes);b.tabIndex=yes?0:-1;});for(const k of ['notes','life','results'])panel.querySelector('#panel-'+k).hidden=k!==key;};
      panel.addEventListener('click',e=>{const b=e.target.closest('button');if(b?.dataset.noteTab)choose(b.dataset.noteTab);if(b?.dataset.noteAnchor)panel.querySelector('#'+b.dataset.noteAnchor)?.scrollIntoView({block:'start',behavior:'smooth'});});
      panel.querySelector('[role=tablist]').addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;const tabs=[...panel.querySelectorAll('[data-note-tab]')];let i=tabs.indexOf(document.activeElement);if(i<0)return;e.preventDefault();i=e.key==='Home'?0:e.key==='End'?2:(i+(e.key==='ArrowRight'?1:2))%3;tabs[i].click();tabs[i].focus();});
      // Results load only when needed, not for every paper click.
      let resultsLoaded=false;
      panel.addEventListener('click',async e=>{if(e.target.closest('[data-note-tab]')?.dataset.noteTab!=='results'||resultsLoaded)return;resultsLoaded=true;const target=panel.querySelector('#panel-results');try{const b=await loadBoards();if(root._researchToken!==token)return;const rows=b.tracks.flatMap(t=>visibleResults(b,t.id)).filter(x=>x.paperId===p.id);target.innerHTML=rows.length?`<p class="note-small">共 ${rows.length} 条核验记录；含作者方法及论文引用基线。下列分数不能跨赛道直接比较。</p>`+rows.map(row=>`<article class="paper-result"><strong>${esc(row.method)}</strong><span class="note-badge">${esc(ATTR[row.attribution])}</span><p>${esc(b.tracks.find(t=>t.id===row.trackId)?.name)}</p><div class="result-values">${Object.entries(row.values).map(([k,v])=>`<span>${esc(k)} <b>${metricValue(v,b.tracks.find(t=>t.id===row.trackId)?.unit)}</b></span>`).join('')}</div><p class="note-small">${esc(row.trainingData)} · ${esc(row.locator)} · ${esc(row.sourceVersion)}</p>${links([{label:'原文表格／设置',url:row.source}])}</article>`).join(''):'<div class="research-empty"><h3>暂无可追溯的榜单记录</h3><p>未提取、协议不明或仅有摘要的结果不会自动填零、生成名次。论文原有 KEY RESULT 仍完整保留。</p></div>';}
        catch(err){resultsLoaded=false;target.innerHTML='<p class="research-warning">榜单暂未载入。重新点击此标签可重试。</p>';}});
    }catch(err){if(root._researchToken!==token)return;hint.className='research-warning';hint.textContent='详细笔记暂不可用，以下展示原有笔记。刷新后可重试。';console.warn('Paper detail:',err.message);}
  }
  async function renderBoards(host){
    const token=++boardToken;host.innerHTML='<p class="research-loading" role="status">正在载入经过核验的评测记录…</p>';
    try{
      const data=await loadBoards();if(token!==boardToken)return;
      const query=new URLSearchParams(location.search);const families=benchmarkFamilies(data);let dataset=families.includes(query.get('dataset'))?query.get('dataset'):(families.includes('LIBERO')?'LIBERO':families[0]);let trackId=query.get('track')||'',metric='',page=1;
      function draw(){
        const tracks=data.tracks.filter(t=>t.dataset===dataset);if(!tracks.some(t=>t.id===trackId))trackId=tracks[0]?.id||'';
        const t=tracks.find(t=>t.id===trackId);if(!t){host.innerHTML='<p>暂时没有此数据集的已定义赛道。</p>';return;}
        if(!t.columns.includes(metric))metric=t.columns.includes('Average')?'Average':t.columns[0];
        const accepted=visibleResults(data,t.id),ranked=rankRows(accepted,metric,t.direction),rows=t.comparisonScope==='protocol'?ranked:accepted;
        const size=20,pages=Math.max(1,Math.ceil(rows.length/size));page=Math.min(page,pages);
        const candidates=data.results.filter(r=>r.trackId===t.id&&r.evidence==='candidate').length;
        host.innerHTML=`<div class="leaderboard-top"><div class="dataset-tabs" role="group" aria-label="数据集">${families.map(d=>`<button data-dataset="${esc(d)}" aria-pressed="${d===dataset}">${esc(d)}</button>`).join('')}</div><div class="board-update">目录更新 ${esc(data.updatedAt)} · <a href="data/leaderboards.json" download>公开 JSON ↗</a></div></div><div class="board-controls"><label>评测赛道 / 协议<select id="lb-track">${tracks.map(x=>`<option value="${esc(x.id)}" ${x.id===trackId?'selected':''}>${esc(x.name)}</option>`).join('')}</select></label><label>排序指标<select id="lb-metric" ${t.comparisonScope==='paper-table'?'disabled':''}>${t.columns.map(x=>`<option ${x===metric?'selected':''}>${esc(x)}</option>`).join('')}</select></label></div><div class="protocol-card"><div><span class="note-badge">${t.comparisonScope==='protocol'?'协议内结果榜':'论文对照表 · 不给名次'}</span><h2>${esc(t.name)}</h2><p>${esc(t.protocol)}</p></div><div class="protocol-facts"><span>版本 <b>${esc(t.version)}</b></span><span>任务 <b>${esc(t.tasks)}</b></span><span>训练 <b>${esc(t.trainingRegime)}</b></span></div>${links([{label:'协议原始来源',url:t.source}])}</div><div class="research-warning">${t.comparisonScope==='protocol'?'名次仅覆盖此赛道已核验的作者报告，不是官方全量榜，也不代表统计显著差异或本站复现。预训练数据与计算预算仍可能不同。':'不同训练预算或评测细节未统一；下面保留论文对照记录，不将其解释为公平排名。'} 未核验候选 ${candidates} 条，不参与排序。</div><div class="board-table-scroll"><table class="board-table"><caption>${esc(t.name)} · ${rows.length} 条核验结果 · ${esc(t.metric)} (${esc(t.unit)})</caption><thead><tr><th>${t.comparisonScope==='protocol'?'名次':'记录'}</th><th>模型 / 来源论文</th>${t.columns.map(c=>`<th>${esc(c)}</th>`).join('')}<th>证据与设置</th></tr></thead><tbody>${rows.slice((page-1)*size,page*size).map((r,i)=>`<tr><td class="rank-cell">${t.comparisonScope==='protocol'?(r.rank??'—'):(page-1)*size+i+1}</td><td><strong>${esc(r.method)}</strong><button class="board-paper-link" data-paper="${esc(r.paperId)}">${esc(r.paperId)} · 阅读来源论文 ↗</button><small>${esc(ATTR[r.attribution])}</small></td>${t.columns.map(c=>`<td class="numeric ${c===metric?'selected-metric':''}">${r.values[c]==null?'—':esc(r.values[c])}</td>`).join('')}<td><details><summary>${esc(r.sourceVersion)} · ${esc(r.locator)}</summary><p>${esc(r.trainingData)}</p><p>${esc(r.evaluationNotes)}</p><p>核验：${esc(r.verifiedAt)}</p>${links([{label:'结果来源',url:r.source}])}</details></td></tr>`).join('')}</tbody></table>${rows.length?'':'<p class="research-empty">暂时没有此协议下已核验的结果。</p>'}</div><div class="pagination">${pageWindow(page,pages).map(n=>n===null?'<span>…</span>':`<button data-lb-page="${n}" class="${n===page?'active':''}">${n}</button>`).join('')}<span>每页20条；空缺不是零分。</span></div>`;
        host.querySelectorAll('[data-dataset]').forEach(b=>b.onclick=()=>{dataset=b.dataset.dataset;trackId='';metric='';page=1;sync();});
        host.querySelector('#lb-track').onchange=e=>{trackId=e.target.value;metric='';page=1;sync();};
        host.querySelector('#lb-metric').onchange=e=>{metric=e.target.value;page=1;draw();};
        host.querySelectorAll('[data-lb-page]').forEach(b=>b.onclick=()=>{page=Number(b.dataset.lbPage);draw();});
      }
      function sync(){draw();const u=new URL(location.href);u.searchParams.set('dataset',dataset);u.searchParams.set('track',trackId);history.replaceState({},'',u);}
      draw();
    }catch(err){if(token!==boardToken)return;host.innerHTML='<div class="research-empty"><h2>榜单暂未载入</h2><p>请刷新重试。未载入不代表没有结果或分数为零。</p><button id="retry-board" class="btn">重试</button></div>';host.querySelector('#retry-board').onclick=()=>renderBoards(host);console.warn('Leaderboard:',err.message);}
  }
  global.RadarResearch={enhance,renderBoards,pageWindow,rankRows,visibleResults,metricValue,benchmarkFamilies,richEvidence};
  if(typeof module!=='undefined')module.exports=global.RadarResearch;
})(typeof window!=='undefined'?window:globalThis);
