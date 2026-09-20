/* Default Benchmark view: Setting -> result reports. Original track view remains available for protocol-level analysis. */
'use strict';
(function(g){
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safe=v=>{try{const u=new URL(v,location.href);return ['https:','http:'].includes(u.protocol)&&!u.username&&!u.password?u.href:'#';}catch{return '#';}};
  const short=(v,n=72)=>{const s=String(v||'').replace(/\s+/g,' ').trim();return s.length>n?s.slice(0,n-1)+'…':s;};
  const value=(v,unit)=>v==null?'—':esc(v)+(unit==='percent'?'%':unit==='seconds'?' s':'');
  function direction(setting,order){
    if(order==='asc'||order==='desc')return order;
    return setting.direction==='lower'?'asc':'desc';
  }
  function sortRows(rows,setting,metric,order='auto'){
    if(order==='source')return [...rows];
    const dir=direction(setting,order),sign=dir==='asc'?1:-1;
    return rows.map((r,i)=>({r,i,v:Number.isFinite(r.values?.[metric])?r.values[metric]:null}))
      .sort((a,b)=>{
        if(a.v===null&&b.v===null)return a.i-b.i;
        if(a.v===null)return 1;if(b.v===null)return -1;
        return (a.v-b.v)*sign||a.i-b.i;
      }).map(x=>x.r);
  }
  function paperMap(papers){return new Map((papers||[]).map(p=>[p.id,p.name||p.title||p.id]));}
  function setDataset(dataset,host){
    const u=new URL(location.href);u.searchParams.set('view','leaderboards');u.searchParams.set('dataset',dataset);
    for(const k of ['setting','track','lbMetric','lbOrder','lbBrowse','lbChart','lbTime'])u.searchParams.delete(k);
    history.replaceState({},'',u);g.RadarResearch.renderBoards(host);
  }
  async function render(host,ctx){
    const {data,query,token,isCurrent,papers,loadSetting}=ctx,pnames=paperMap(papers);
    const datasets=[...new Set(data.tracks.map(t=>t.dataset))];
    let dataset=datasets.includes(query.get('dataset'))?query.get('dataset'):(datasets.includes('LIBERO')?'LIBERO':datasets[0]);
    let settings=data.settings.filter(s=>s.dataset===dataset);
    if(!settings.length){
      host.innerHTML='<div class="research-empty"><h2>当前数据集还没有可展示的 Setting</h2><p>没有经过核验的结果时，不会生成空分数或虚构协议。</p></div>';return;
    }
    let settingId=settings.some(s=>s.id===query.get('setting'))?query.get('setting'):settings[0].id;
    let metric=(query.get('lbMetric')||'').slice(0,160);
    let order=['auto','asc','desc','source'].includes(query.get('lbOrder'))?query.get('lbOrder'):'auto';
    let page=1,drawVersion=0;
    const settingLabel=s=>{
      const source=!s.trainingKnown&&s.paperIds?.length===1?' · '+(pnames.get(s.paperIds[0])||s.paperIds[0]):'';
      return s.name+' · '+short(s.trainingData,54)+source;
    };
    function updateUrl(){
      const u=new URL(location.href);u.searchParams.set('view','leaderboards');u.searchParams.set('dataset',dataset);
      u.searchParams.set('setting',settingId);u.searchParams.set('lbMetric',metric);u.searchParams.set('lbOrder',order);
      for(const k of ['track','lbBrowse','lbChart','lbTime'])u.searchParams.delete(k);
      history.replaceState({},'',u);
    }
    async function draw(focus){
      const drawId=++drawVersion;
      const setting=settings.find(s=>s.id===settingId)||settings[0];settingId=setting.id;
      if(!setting.columns.includes(metric))metric=setting.columns.includes('Average')?'Average':setting.columns[0];
      let loaded;
      try{loaded=await loadSetting(setting,data);}catch{
        if(drawId!==drawVersion||!isCurrent())return;
        host.innerHTML='<p class="research-warning">当前 Setting 暂未载入；未载入不等于零分。</p><button class="btn" id="retry-setting">重试</button>';
        host.querySelector('#retry-setting').onclick=()=>draw();return;
      }
      if(drawId!==drawVersion||!isCurrent())return;
      const trackmap=new Map(loaded.tracks.map(t=>[t.id,t]));
      const rows=sortRows(loaded.results.filter(r=>r.evidence==='checked'),setting,metric,order);
      const size=20,pages=Math.max(1,Math.ceil(rows.length/size));page=Math.max(1,Math.min(page,pages));
      const dir=direction(setting,order);
      const header=c=>`<th scope="col" ${c===metric&&order!=='source'?`aria-sort="${dir==='asc'?'ascending':'descending'}"`:''}><button class="board-sort-button" data-setting-sort="${esc(c)}" aria-label="按 ${esc(c)} 排序">${esc(c)} <span aria-hidden="true">${c===metric&&order!=='source'?(dir==='asc'?'▲':'▼'):'↕'}</span></button></th>`;
      const current=rows.slice((page-1)*size,page*size);
      host.innerHTML=`<div class="leaderboard-top"><div class="dataset-tabs" role="group" aria-label="数据集">${datasets.map(d=>`<button data-setting-dataset="${esc(d)}" aria-pressed="${d===dataset}">${esc(d)}</button>`).join('')}</div><div class="board-update">目录更新 ${esc(data.updatedAt)} · ${settings.length} settings</div></div>
        <div class="setting-picker"><label><span>SETTING</span><select id="setting-select">${settings.map(s=>`<option value="${esc(s.id)}" ${s.id===settingId?'selected':''}>${esc(settingLabel(s))}</option>`).join('')}</select></label><a class="btn setting-advanced-link" href="?view=leaderboards&amp;dataset=${encodeURIComponent(dataset)}&amp;track=${encodeURIComponent(setting.primaryTrackId)}">高级：原始 track / 图表</a></div>
        <section class="setting-summary" data-setting-id="${esc(setting.id)}"><div class="setting-summary-main"><span class="setting-kicker">SETTING · EVALUATION + TRAINING DATA</span><h2>${esc(setting.name)}</h2><p class="setting-training"><strong>Training data</strong><span>${esc(setting.trainingData)}</span></p>${setting.trainingKnown?'':'<p class="setting-unknown">训练数据未完整披露：本站仅在同一来源论文内归为该 Setting，不跨论文假定训练预算一致。</p>'}</div><div class="setting-facts"><span>Tasks <b>${esc(setting.tasks)}</b></span><span>Eval <b>${esc(setting.split)}</b></span><span>Metric <b>${esc(setting.metric)}</b></span><span>Reports <b>${setting.resultCount}</b></span></div><details class="setting-protocol"><summary>展开评测协议说明</summary><p>${esc(setting.protocol)}</p><small>Setting 只决定哪些报告可以摆在同一结果表；不同来源论文和 recipe 始终保留为独立结果行。</small></details></section>
        <div class="setting-toolbar"><div><strong>Method / Score / Source</strong><span>同一方法可因来源论文或 recipe 不同出现多行；排序不是跨来源公平排名。</span></div><div class="board-controls setting-controls"><label>排序指标<select id="setting-metric">${setting.columns.map(c=>`<option ${c===metric?'selected':''}>${esc(c)}</option>`).join('')}</select></label><label>排列<select id="setting-order"><option value="auto" ${order==='auto'?'selected':''}>按指标优劣</option><option value="desc" ${order==='desc'?'selected':''}>数值降序</option><option value="asc" ${order==='asc'?'selected':''}>数值升序</option><option value="source" ${order==='source'?'selected':''}>原记录顺序</option></select></label><button class="btn" id="export-setting-csv">导出 Setting CSV</button></div></div>
        <p class="board-sort-status" role="status">${order==='source'?'按原记录顺序展示':esc(metric)+' · '+(dir==='asc'?'升序':'降序')} · 缺失值置后 · 不生成跨来源名次。</p>
        <div class="board-table-scroll" role="region" aria-label="Setting 结果表" tabindex="0"><table class="board-table setting-table"><caption>${esc(setting.name)} · ${rows.length} 条独立结果报告</caption><thead><tr><th scope="col">Method</th>${setting.columns.map(header).join('')}<th scope="col">来源论文</th><th scope="col">Recipe / Evidence</th></tr></thead><tbody>${current.map(r=>{const t=trackmap.get(r.trackId),paper=pnames.get(r.paperId)||r.paperId;return `<tr data-result-id="${esc(r.id)}"><td class="setting-method"><strong>${esc(r.method)}</strong><small>${esc(r.attribution==='author-reported'?'作者方法':r.attribution==='reported-baseline'?'论文引用基线':'独立复现')}</small></td>${setting.columns.map(c=>`<td class="numeric ${c===metric?'selected-metric':''}">${value(r.values?.[c],setting.unit)}</td>`).join('')}<td class="setting-source"><button class="board-paper-link" data-paper="${esc(r.paperId)}">${esc(paper)}</button><small>${esc(r.paperId)} · ${esc(r.sourceVersion)}</small></td><td class="setting-recipe"><details><summary>展开 recipe</summary><div class="recipe-evidence-grid"><span>Recipe <b>${esc(t?.recipeName||t?.name||r.trackId)}</b></span><span>Training <b>${esc(r.trainingData)}</b></span><span>Training recipe <b>${esc(t?.trainingRegime||'未单独记录')}</b></span><span>Evaluation <b>${esc(r.evaluationNotes)}</b></span><span>Locator <b>${esc(r.locator)}</b></span><span>Verified <b>${esc(r.verifiedAt)}</b></span></div><div class="recipe-evidence-actions"><a href="${esc(safe(r.source))}" target="_blank" rel="noopener noreferrer">原始证据 ↗</a><a href="?view=leaderboards&amp;dataset=${encodeURIComponent(dataset)}&amp;track=${encodeURIComponent(r.trackId)}">打开原始 track ↗</a></div></details></td></tr>`;}).join('')}</tbody></table></div>
        <div class="pagination">${Array.from({length:pages},(_,i)=>i+1).slice(Math.max(0,page-3),Math.min(pages,page+2)).map(n=>`<button data-setting-page="${n}" class="${n===page?'active':''}">${n}</button>`).join('')}<span>每页20条；同一 Method 的不同报告不去重。</span></div>`;
      host.querySelectorAll('[data-setting-dataset]').forEach(b=>b.onclick=()=>setDataset(b.dataset.settingDataset,host));
      host.querySelector('#setting-select').onchange=e=>{settingId=e.target.value;metric='';order='auto';page=1;draw('#setting-select');};
      host.querySelector('#setting-metric').onchange=e=>{metric=e.target.value;if(order==='source')order='auto';page=1;draw('#setting-metric');};
      host.querySelector('#setting-order').onchange=e=>{order=e.target.value;page=1;draw('#setting-order');};
      host.querySelectorAll('[data-setting-sort]').forEach(b=>b.onclick=()=>{const c=b.dataset.settingSort;order=c===metric&&order!=='source'?(dir==='asc'?'desc':'asc'):'auto';metric=c;page=1;draw({column:c});});
      host.querySelectorAll('[data-setting-page]').forEach(b=>b.onclick=()=>{page=Number(b.dataset.settingPage);draw();});
      host.querySelector('#export-setting-csv').onclick=()=>g.RadarWorkspace.action('csv',{track:{id:setting.id,columns:setting.columns,unit:setting.unit,protocol:setting.id},rows});
      updateUrl();
      const target=typeof focus==='string'?host.querySelector(focus):focus?.column?[...host.querySelectorAll('[data-setting-sort]')].find(b=>b.dataset.settingSort===focus.column):null;
      target?.focus({preventScroll:true});
    }
    await draw();
  }
  g.RadarBenchmarkSettings={render,sortRows,direction};
  if(typeof module!=='undefined')module.exports=g.RadarBenchmarkSettings;
})(typeof window!=='undefined'?window:globalThis);
