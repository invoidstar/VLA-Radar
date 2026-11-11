/* VLA-Radar close reading: trusted static JSON rendered as text, no external runtime. */
'use strict';
(() => {
  const root=document.getElementById('reading-root'); if(!root)return;
  const $=s=>document.querySelector(s);
  const safe=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const dimLabels={thesis:'核心论点',concept:'关键概念',evidence:'实证证据',concession:'让步 / 反驳',method:'方法论说明'};
  const dims=Object.keys(dimLabels);
  const key='vla-radar.close-reading.v1';
  const docUrl=root.dataset.url;
  let doc,query='',showNotes=true,zhOnly=false;
  const readPrefs=()=>{try{return JSON.parse(localStorage.getItem(key)||'{}')}catch{return {}}};
  const savePrefs=obj=>{try{localStorage.setItem(key,JSON.stringify({...readPrefs(),...obj}))}catch{}};
  const pdfLink=page=>doc.sourceUrl+'#page='+encodeURIComponent(page);
  const card=u=>'<article class="unit" id="'+safe(u.id)+'" data-search="'+safe([u.id,u.englishKeywords,u.interpretation,u.annotation.role,u.annotation.critique].join(' ').toLowerCase())+'" data-dim="'+safe(u.dimension)+'"><div class="unit-main"><div class="unit-meta"><a href="#'+safe(u.id)+'" class="id">'+safe(u.id)+'</a><span>PDF p.'+safe(u.page)+'</span><span>'+safe(dimLabels[u.dimension])+'</span></div><h3>'+safe(u.annotation.function)+'</h3><div class="english" data-dim="'+safe(u.dimension)+'"><span class="mini-label">EN · INDEX TERMS / 非原文全文</span><p><mark>'+safe(u.englishKeywords)+'</mark></p></div><div class="translation"><div class="zh-card"><span class="mini-label">ZH · 原创学术解读 / 非逐段原文译文</span><p>'+safe(u.interpretation)+'</p></div></div><div class="proof-links"><a href="'+safe(pdfLink(u.page))+'" target="_blank" rel="noopener noreferrer">原始 PDF · 第 '+safe(u.page)+' 页 ↗</a>'+(u.evidenceRefs?.length?'<a href="../../?view=reader&paper='+safe(doc.paperId)+'">论文结果与证据 ↗</a>':'')+'</div></div><aside class="annotation" data-dim="'+safe(u.dimension)+'"><strong>'+safe(u.id)+' · '+safe(dimLabels[u.dimension])+'</strong><dl><dt>段落功能</dt><dd>'+safe(u.annotation.function)+'</dd><dt>论证链中的位置</dt><dd>'+safe(u.annotation.role)+'</dd><dt>值得注意的推理 / 局限</dt><dd>'+safe(u.annotation.critique)+'</dd></dl></aside></article>';
  function draw() {
    const prefs=readPrefs(); const filtered=doc.units.filter(u=>[u.id,u.englishKeywords,u.interpretation,u.annotation.role,u.annotation.critique].join(' ').toLowerCase().includes(query));
    $('#unit-count').textContent=filtered.length+' / '+doc.units.length+' 单元';
    const allowed=new Set(filtered.map(x=>x.section));
    const sections=doc.sections.filter(s=>allowed.has(s.id));
    root.innerHTML=sections.map((s,i)=>'<section class="paper-section" id="'+safe(s.id)+'"><header class="section-head"><b>'+String(s.order+1).padStart(2,'0')+'</b><div><h2>'+safe(s.title)+'</h2><small>'+safe(s.summary)+'</small></div></header>'+filtered.filter(u=>u.section===s.id).map(card).join('')+'</section>').join('')||'<p class="empty">未找到匹配阅读单元。请清空搜索。</p>';
    document.body.classList.toggle('no-notes',!showNotes); document.body.classList.toggle('zh-only',zhOnly);
    if(!query){const to=prefs[doc.paperId];if(to && document.getElementById(to) && !location.hash){/* position restoration remains opt-in through chapter links */}}
  }
  function overview() {
    const ov=doc.overview;
    $('#argument-map').innerHTML='<header><div class="kicker">ARGUMENT MAP</div><h2>论证结构总览</h2></header><div class="content"><p><strong>作者核心主张：</strong>'+safe(ov.thesis)+'</p><div class="chain">'+ov.chain.map(([title,text],i)=>'<article><span class="mini-label">0'+(i+1)+'</span><b>'+safe(title)+'</b><p>'+safe(text)+'</p></article>').join('')+'</div><div class="judgment"><article><h3>论证最强处</h3><p>'+safe(ov.strong)+'</p></article><article><h3>论证最弱处</h3><p>'+safe(ov.weak)+'</p></article></div></div>';
  }
  async function start(){
    try{const res=await fetch(docUrl,{credentials:'omit',cache:'no-cache'});if(!res.ok)throw Error('HTTP '+res.status);doc=await res.json();if(doc.schemaVersion!==1||doc.paperId!=='p148'||!Array.isArray(doc.sections)||!Array.isArray(doc.units))throw Error('Invalid reading data');}
    catch(e){root.innerHTML='<p role="alert" class="empty">精读内容暂时不可用。请刷新页面后重试。 '+safe(e.message)+'</p>';return;}
    document.title='SLA · 论文精读 · VLA-Radar';
    $('#reading-title').textContent=doc.title;$('#reading-subtitle').textContent=doc.subtitle;
    $('#reading-notice').textContent=doc.notice;
    $('#reading-meta').textContent=doc.sourceVersion+' · '+doc.updatedAt+' · '+doc.units.length+' 个分析单元';
    $('#chapter-nav').innerHTML=doc.sections.map(s=>'<a href="#'+safe(s.id)+'">'+safe(s.title)+'</a>').join('')+'<a href="#argument-map">论证总览</a>';
    const prefs=readPrefs();showNotes=prefs.notes!==false;zhOnly=prefs.zhOnly===true;$('#notes').checked=showNotes;$('#lang').value=zhOnly?'zh':'annotated';
    draw();overview();
    $('#search').addEventListener('input',e=>{query=e.target.value.trim().toLowerCase();draw()});
    $('#notes').addEventListener('change',e=>{showNotes=e.target.checked;savePrefs({notes:showNotes});draw()});
    $('#lang').addEventListener('change',e=>{zhOnly=e.target.value==='zh';savePrefs({zhOnly});draw()});
    document.querySelectorAll('[data-highlight]').forEach(btn=>btn.addEventListener('click',()=>{const dim=btn.dataset.highlight,off=document.body.classList.toggle('hide-'+dim);btn.setAttribute('aria-pressed',String(!off))}));
    $('#print-page').addEventListener('click',()=>window.print());
    const progress=$('#read-progress');
    const update=()=>{const h=document.documentElement;progress.style.width=(Math.max(0,Math.min(100,(h.scrollTop/(h.scrollHeight-h.clientHeight||1))*100)))+'%'};
    window.addEventListener('scroll',update,{passive:true});update();
    const nav=$('#chapter-nav');
    const obs=new IntersectionObserver(entries=>{const visible=entries.filter(x=>x.isIntersecting);if(!visible.length)return;const id=visible[0].target.id;nav.querySelectorAll('a').forEach(a=>{if(a.getAttribute('href')==='#'+id)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current')})},{rootMargin:'-150px 0px -68% 0px',threshold:0});
    document.querySelectorAll('.paper-section').forEach(s=>obs.observe(s));
  }
  start();
})();
