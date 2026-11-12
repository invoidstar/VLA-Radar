/* VLA-Radar V3.1 — source-linked reading with optional official original-PDF viewer.
   Embed the publisher URL without copying its PDF or article text into this repository. */
'use strict';
(() => {
  const $ = s => document.querySelector(s);
  const esc = x => String(x ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pagePath = location.pathname;
  const match = pagePath.match(/\/close-reading\/(p\d{3,})\/?(?:index\.html)?$/);
  const pid = match ? match[1] : new URLSearchParams(location.search).get('paper');
  const prefix = match ? '../../' : '../';
  const validId = /^p\d{3,}$/.test(pid || '');
  const named = {thesis:'核心论点',concept:'关键术语',evidence:'实证证据',concession:'让步/反驳',method:'方法论'};
  let doc = null;
  let q = '';
  let raf = 0;
  let lastVisibleCount = 0;
  const allUnits = d => d.sections.reduce((n,s)=>n+s.units.length,0);
  const validUrl = u => {try{const x = new URL(u);return x.protocol==='https:'?x.href:'#'}catch{return '#'}};
  function setSourceOpen(open) {
    document.body.classList.toggle('source-open', Boolean(open));
    const button=$('#source-toggle');
    button.setAttribute('aria-pressed',String(Boolean(open)));
    button.setAttribute('aria-expanded',String(Boolean(open)));
    button.textContent=open?'收起原文面板':'原文同屏 · 官方 PDF';
  }
  function jumpPdf(page) {
    if(!doc || !Number.isInteger(page) || page<1 || page>150)return;
    const source=validUrl(doc.pdfUrl);
    if(source==='#')return;
    const target=source+'#page='+page;
    const frame=$('#original-pdf');
    $('#source-page').textContent='PDF p.'+page;
    $('#source-external').href=target;
    if(frame.dataset.page!==String(page)){
      frame.dataset.page=String(page);
      frame.src=target;
    }
    for(const item of $('#reading-units').querySelectorAll('.source-jump'))
      item.setAttribute('aria-pressed',String(Number(item.dataset.pdfPage)===page));
  }

  function textIndex(unit) {
    return [unit.id,unit.title,unit.function,unit.argumentRole,unit.criticalNote,unit.sourcePageLabel,
      ...unit.englishKeywords.map(x=>x.text),...unit.evidenceTracks].join(' ').normalize('NFKC').toLowerCase();
  }
  function keywords(unit) {
    const terms=unit.englishKeywords||[];
    if(!terms.length)return '<span class="empty">本单元以中文论证分析为主。点击 PDF 来源定位查看英文原文。</span>';
    return terms.map(t=>'<mark class="'+esc(t.dimension)+'">'+esc(t.text)+'</mark>').join('');
  }
  function unitHtml(unit) {
    const isAsset=unit.kind!=='paragraph';
    const sourceLink=validUrl(unit.sourceUrl);
    const evidence=(unit.evidenceTracks||[]).map(t=>'<a href="'+prefix+'index.html?view=leaderboards&track='+encodeURIComponent(t)+'" title="打开相关 Benchmark 赛道">核对评测 · '+esc(t)+'</a>').join('');
    return '<article class="reading-row" id="'+esc(unit.id)+'" data-unit="'+esc(unit.id)+'">'+
      '<div class="reading-main">'+
        '<div class="unit-meta"><a href="#'+esc(unit.id)+'" class="unit-id">'+esc(unit.id)+'</a>'+
        '<span>'+esc(unit.sourcePageLabel)+'</span><span>'+ (isAsset?'原始'+(unit.kind==='table'?'表格':'图像')+'定位':'段落级论证批注')+'</span>'+
        '<a class="source-link" target="_blank" rel="noopener noreferrer" href="'+sourceLink+'">PDF 原稿 ↗</a></div>'+
        '<h3>'+esc(unit.title)+'</h3>'+
        '<div class="kicker enlabel">ENGLISH FOCUS · TECHNICAL TERMS (NOT FULL TEXT)</div>'+
        '<div class="keywords" lang="en">'+keywords(unit)+'</div>'+
        '<div class="cn"><div class="kicker">中文 · 论证导读</div>'+
          '<div class="cn-box"><p>'+esc(unit.argumentRole)+'</p></div></div>'+
        (isAsset?'<div class="figure-note">原稿'+(unit.kind==='table'?'表格':'图片')+'未在本站镜像；请使用原始 PDF 页码查看内容、图注与具体数值。</div>':'')+
        '<div class="source-button-row"><button type="button" class="source-jump" data-pdf-page="'+Number(unit.pdfPage)+'" aria-pressed="false" aria-label="在同屏原稿查看 PDF 第 '+Number(unit.pdfPage)+' 页">同屏查看原文 p.'+Number(unit.pdfPage)+'</button><a href="'+sourceLink+'" target="_blank" rel="noopener noreferrer">新标签打开原文 p.'+Number(unit.pdfPage)+' ↗</a>'+evidence+'</div>'+
      '</div>'+
      '<aside class="annotation '+esc(unit.dimension)+'" aria-label="'+esc(unit.id)+' 中文论证批注">'+
        '<div class="annotation-top"><strong>'+esc(unit.id)+' · 批判性阅读</strong><span>'+esc(named[unit.dimension]||'论证分析')+'</span></div>'+
        '<dl><dt>段落功能</dt><dd>'+esc(unit.function)+'</dd>'+
        '<dt>在全文中的逻辑角色</dt><dd>'+esc(unit.argumentRole)+'</dd>'+
        '<dt class="critical">论证技巧 / 潜在漏洞</dt><dd>'+esc(unit.criticalNote)+'</dd></dl>'+
      '</aside></article>';
  }
  function matches(unit) {
    return !q || q.trim().toLowerCase().split(/\s+/).every(k=>textIndex(unit).includes(k));
  }
  function renderUnits() {
    if(!doc)return;
    const container=$('#reading-units');
    let total=0;
    const pieces=[];
    doc.sections.forEach((section,si)=>{
      const found=section.units.filter(matches);
      if(!found.length)return;
      total+=found.length;
      pieces.push('<section class="paper-section" id="chapter-'+esc(section.id)+'">'+
        '<header class="section-heading"><span class="number">'+String(si+1).padStart(2,'0')+'</span>'+
        '<div><h2>'+esc(section.title)+'</h2><p lang="en">'+esc(section.englishTitle)+'</p></div></header>'+
        found.map(unitHtml).join('')+'</section>');
    });
    lastVisibleCount=total;
    container.innerHTML=pieces.join('')||'<div class="loading">没有找到匹配的论证单元。清空关键词可恢复全文。</div>';
    $('#search-status').textContent=q?('匹配 '+total+' / '+allUnits(doc)+' 单元'):allUnits(doc)+' 单元';
    requestProgress();
  }
  function renderOutline(d) {
    $('#paper-title').textContent=d.title;
    $('#paper-subtitle').textContent=d.subtitle;
    $('#paper-id').textContent=d.paperId;
    $('#version').textContent=d.sourceVersion;
    $('#reading-count').textContent=d.totals.paragraphs+' 段 / '+(d.totals.tables+d.totals.figures)+' 图表';
    $('#paper-source').href=validUrl(d.sourceUrl);
    document.title=d.title+' | VLA-Radar 论文精读';
    const sum=$('#summary');
    sum.innerHTML='<section class="summary-card"><span class="small">CENTRAL CLAIM</span>'+
      '<h2>核心研究命题</h2><p>'+esc(d.argument.claim)+'</p></section>'+
      '<section class="summary-card"><span class="small">SOURCE-ANCHORED READING</span>'+
      '<h2>原稿定位索引</h2><div class="summary-counts">'+
      '<div><strong>'+d.totals.paragraphs+'</strong><span>段落</span></div>'+
      '<div><strong>'+d.totals.tables+'</strong><span>表格</span></div>'+
      '<div><strong>'+d.totals.figures+'</strong><span>图片</span></div></div>'+
      '<p>左侧同屏加载官方原稿 PDF，可按每条批注定位页码；不复制论文全文到本站。</p></section>';
    $('#chapter-nav').innerHTML=d.sections.map((section,i)=>
      '<a href="#chapter-'+esc(section.id)+'"><span aria-hidden="true">'+String(i+1).padStart(2,'0')+' </span>'+esc(section.title)+'</a>'
    ).join('')+'<a href="#argument-map">论证总览</a>';
    $('#overview-content').innerHTML='<p class="claim">'+esc(d.argument.claim)+'</p>'+
      '<div class="chain">'+d.argument.chain.map((c,i)=>'<article><span>'+String(i+1).padStart(2,'0')+'</span>'+
        '<h3>'+esc(c.step)+'</h3><p>'+esc(c.detail)+'</p></article>').join('')+'</div>'+
      '<div class="judgments"><article><h3>论证最强处</h3><p>'+esc(d.argument.strength)+'</p></article>'+
      '<article><h3>证据最弱处 / 适用边界</h3><p>'+esc(d.argument.weakness)+'</p></article></div>';
  }
  function updateProgress() {
    raf=0;
    const max=Math.max(1,document.documentElement.scrollHeight-innerHeight);
    $('#progress-bar').style.width=Math.min(100,Math.max(0,scrollY/max*100)).toFixed(1)+'%';
    const blocks=[...document.querySelectorAll('.paper-section')];
    let current=null;
    for(const block of blocks)if(block.getBoundingClientRect().top<180)current=block.id;
    for(const a of $('#chapter-nav').querySelectorAll('a'))a.classList.toggle('current',current&&a.hash==='#'+current);
  }
  function requestProgress(){if(!raf)raf=requestAnimationFrame(updateProgress);}
  function attachControls() {
    let debounce;
    $('#unit-search').addEventListener('input',e=>{
      clearTimeout(debounce);
      debounce=setTimeout(()=>{q=e.target.value.slice(0,200);renderUnits();},140);
    });
    $('#language-mode').addEventListener('change',e=>{
      document.body.classList.toggle('only-chinese',e.target.value==='zh');
    });
    $('#notes-toggle').addEventListener('change',e=>{
      document.body.classList.toggle('no-notes',!e.target.checked);
    });
    $('#print-button').addEventListener('click',()=>window.print());
    $('#source-toggle').addEventListener('click',()=>setSourceOpen(!document.body.classList.contains('source-open')));
    $('#reading-units').addEventListener('click',e=>{
      const jump=e.target.closest('.source-jump');
      if(!jump)return;
      setSourceOpen(true);
      jumpPdf(Number(jump.dataset.pdfPage));
    });
    for(const b of document.querySelectorAll('[data-dimension]'))b.addEventListener('click',()=>{
      const type=b.dataset.dimension,enabled=b.getAttribute('aria-pressed')==='true';
      b.setAttribute('aria-pressed',String(!enabled));
      document.body.classList.toggle('hide-'+type,enabled);
    });
    addEventListener('scroll',requestProgress,{passive:true});
    addEventListener('resize',requestProgress,{passive:true});
    $('#chapter-nav').addEventListener('click',e=>{
      if(!e.target.closest('a'))return;
      if(q){q='';$('#unit-search').value='';renderUnits();}
    });
  }
  async function init() {
    attachControls();
    try {
      if(!validId)throw new Error('无效论文编号，请从 VLA-Radar 精读列表打开。');
      const response=await fetch(prefix+'data/close-readings/'+pid+'.json',{credentials:'omit',cache:'no-cache'});
      if(!response.ok)throw new Error('资源暂不可用（HTTP '+response.status+'）。');
      const data=await response.json();
      if(data.schemaVersion!==1 || data.paperId!==pid || !Array.isArray(data.sections) ||
         data.copyright?.originalFullTextRepublished!==false || data.copyright?.figuresMirrored!==false)
        throw new Error('精读内容校验未通过。');
      doc=data;
      renderOutline(data);renderUnits();setSourceOpen(true);jumpPdf(data.sections[0]?.units[0]?.pdfPage||1);requestProgress();
      if(location.hash&&/^#(?:P\d{3}|TAB\d+|FIG\d+|chapter-[a-z0-9-]+|argument-map)$/.test(location.hash)){
        document.getElementById(location.hash.slice(1))?.scrollIntoView();
      }
      window.RadarCloseReadingTest={paperId:pid,units:allUnits(doc),sections:doc.sections.length,visible:()=>lastVisibleCount};
    }catch(error){
      $('#reading-units').innerHTML='';
      $('#error').hidden=false;
      $('#error').textContent=error.message+' 可从原论文页直接阅读。';
      $('#search-status').textContent='未载入';
    }
  }
  init();
})();
