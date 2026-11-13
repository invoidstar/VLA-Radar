/* Source-aligned reader. External arXiv HTML is linked; the user's complete annotated HTML
   can be rendered locally, unit-by-unit, without uploading or republishing copyrighted text. */
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
  let inlineOriginal = new Map();
  let q = '';
  let raf = 0;
  let lastVisibleCount = 0;
  const allUnits = d => d.sections.reduce((n,s)=>n+s.units.length,0);
  const validUrl = u => {try{const x = new URL(u);return x.protocol==='https:'?x.href:'#'}catch{return '#'}};
  const sectionAnchors = {
    abstract:'abstract',intro:'S1',related:'S2',motivation:'S3.SS1',architecture:'S3.SS2.SSS1',
    supervision:'S3.SS2.SSS2',adaptive:'S3.SS2.SSS3',dropout:'S3.SS2.SSS4',
    data:'S3.SS3.SSS1',preprocess:'S3.SS3.SSS2',setup:'S4.SS1',baselines:'S4.SS3',
    scaling:'S4.SS4.SSS1',ablations:'S4.SS4',real:'S4.SS5',conclusion:'S5',
    appendix:'A1',memory:'A2'
  };
  const htmlSource = () => doc ? validUrl(doc.pdfUrl.replace('/pdf/', '/html/').split('#')[0]) : '#';
  function setSourceOpen(open) {
    document.body.classList.toggle('source-open', Boolean(open));
    const button=$('#source-toggle');
    button.setAttribute('aria-pressed',String(Boolean(open)));
    button.setAttribute('aria-expanded',String(Boolean(open)));
    button.textContent=open?'收起官方 HTML 面板':'官方原文 HTML';
  }
  function jumpHtml(unit) {
    if(!doc || !unit)return;
    const url=htmlSource();
    if(url==='#')return;
    const section=doc.sections.find(s=>s.units.some(x=>x.id===unit.id));
    // arXiv section anchors are approximate when the user has not loaded exact P-ID source.
    const anchor=sectionAnchors[section?.id]||'';
    const target=url+(anchor?'#'+anchor:'');
    const frame=$('#original-html');
    $('#source-page').textContent=section ? section.englishTitle : '原文网页';
    $('#source-external').href=target;
    if(frame.dataset.anchor!==target){frame.dataset.anchor=target;frame.src=target;}
    for(const item of $('#reading-units').querySelectorAll('.source-jump'))
      item.setAttribute('aria-pressed',String(item.dataset.unitId===unit.id));
  }

  function allowedInline(node) {
    if(node.nodeType===3)return esc(node.textContent);
    if(node.nodeType!==1)return '';
    const tag=node.tagName.toLowerCase();
    const inside=[...node.childNodes].map(allowedInline).join('');
    if(tag==='mark'){
      const dim=node.getAttribute('data-dim')||node.className;
      return '<mark class="'+(named[dim]?esc(dim):'')+'">'+inside+'</mark>';
    }
    if(['em','strong','i','b','sub','sup','code'].includes(tag))
      return '<'+tag+'>'+inside+'</'+tag+'>';
    if(tag==='br')return ' ';
    return inside;
  }
  function originalBlock(unit) {
    const orig=inlineOriginal.get(unit.id);
    if(!orig)return '';
    const english=orig.en ? '<div class="source-label">EN · 原论文对应段落</div><p class="original-english" lang="en">'+orig.en+'</p>' : '';
    const translation=orig.zh ? '<div class="source-label">中文 · 对应学术意译</div><div class="original-translation" lang="zh-CN">'+orig.zh.map(x=>'<p>'+esc(x)+'</p>').join('')+'</div>' : '';
    const graphic=orig.image ? '<figure class="original-local-figure"><img loading="lazy" alt="'+esc(unit.id)+' · 个人提供的原稿图表" src="'+orig.image+'"><figcaption>仅在本机显示的原始图表，未上传到本站</figcaption></figure>' : '';
    return '<div class="original-block" data-source-unit="'+esc(unit.id)+'">'+english+graphic+translation+'</div>';
  }
  async function importOriginal(file) {
    if(!doc)throw new Error('精读索引尚未就绪。');
    if(!file || !/\.html?$/i.test(file.name) || file.size>20*1024*1024)
      throw new Error('请选择不超过 20MB 的原始双语精读 HTML。');
    const parsed=new DOMParser().parseFromString(await file.text(),'text/html');
    const expected=new Set(doc.sections.flatMap(s=>s.units.map(u=>u.id)));
    const rows=[...parsed.querySelectorAll('article.reading-row[data-unit]')];
    if(!parsed.title.includes('SLA') || rows.length!==expected.size)
      throw new Error('文件不是完整的 SLA 双语精读版，或段落数量不一致。');
    const loaded=new Map();
    for(const row of rows){
      const id=row.dataset.unit;
      if(!expected.has(id)||loaded.has(id))throw new Error('原稿编号与精读批注不匹配：'+id);
      const main=row.querySelector('.reading-main');
      if(!main)throw new Error('原稿缺少阅读内容：'+id);
      const en=main.querySelector('p.en, div.en');
      const zh=[...main.querySelectorAll('.translation .zh-block p[lang], .translation .zh-block p')]
        .map(x=>x.textContent.trim()).filter(Boolean);
      if(id.startsWith('P') && (!en || !zh.length))throw new Error(id+' 缺失英文原文或中文意译。');
      const figure=main.querySelector('.asset-figure img, figure img');
      const src=figure?.getAttribute('src')||'';
      const image=/^data:image\/(?:png|jpeg|gif|webp);base64,[a-z0-9+/=]+$/i.test(src) && src.length<=5*1024*1024 ? src : '';
      loaded.set(id,{
        en:en?[...en.childNodes].map(allowedInline).join(''):'',
        zh,image,
        search:(en?.textContent||'')+' '+zh.join(' ')
      });
    }
    if(loaded.size!==expected.size)throw new Error('原文段落没有全部匹配，请使用完整原版文件。');
    inlineOriginal=loaded;
    setSourceOpen(false);
    $('#clear-source').hidden=false;
    $('#inline-source-status').textContent='已在本机载入 '+loaded.size+' 个逐段对照单元；英文、中文意译与右栏批注一一对应。';
    renderUnits();
  }

  function textIndex(unit) {
    return [unit.id,unit.title,unit.function,unit.argumentRole,unit.criticalNote,unit.sourcePageLabel,
      ...unit.englishKeywords.map(x=>x.text),...unit.evidenceTracks,inlineOriginal.get(unit.id)?.search||''].join(' ').normalize('NFKC').toLowerCase();
  }
  function keywords(unit) {
    const terms=unit.englishKeywords||[];
    if(!terms.length)return '<span class="empty">请导入个人双语 HTML 或使用官方 HTML 查看对应原文。</span>';
    return terms.map(t=>'<mark class="'+esc(t.dimension)+'">'+esc(t.text)+'</mark>').join('');
  }
  function unitHtml(unit) {
    const isAsset=unit.kind!=='paragraph';
    const sourceLink=validUrl(unit.sourceUrl);
    const evidence=(unit.evidenceTracks||[]).map(t=>'<a href="'+prefix+'index.html?view=leaderboards&track='+encodeURIComponent(t)+'" title="打开相关 Benchmark 赛道">核对评测 · '+esc(t)+'</a>').join('');
    return '<article class="reading-row'+(inlineOriginal.has(unit.id)?' has-inline-original':'')+'" id="'+esc(unit.id)+'" data-unit="'+esc(unit.id)+'">'+
      '<div class="reading-main">'+
        '<div class="unit-meta"><a href="#'+esc(unit.id)+'" class="unit-id">'+esc(unit.id)+'</a>'+
        '<span>'+esc(unit.sourcePageLabel)+'</span><span>'+ (isAsset?'原始'+(unit.kind==='table'?'表格':'图像')+'定位':'段落级论证批注')+'</span>'+
        '<a class="source-link" target="_blank" rel="noopener noreferrer" href="'+sourceLink+'">PDF 原稿 ↗</a></div>'+
        '<h3>'+esc(unit.title)+'</h3>'+originalBlock(unit)+
        '<div class="kicker enlabel">ENGLISH FOCUS · TECHNICAL TERMS (NOT FULL TEXT)</div>'+
        '<div class="keywords" lang="en">'+keywords(unit)+'</div>'+
        '<div class="cn"><div class="kicker">中文 · 论证导读</div>'+
          '<div class="cn-box"><p>'+esc(unit.argumentRole)+'</p></div></div>'+
        (isAsset&&!inlineOriginal.has(unit.id)?'<div class="figure-note">原稿'+(unit.kind==='table'?'表格':'图片')+'未在本站镜像，可从个人双语 HTML 读取或通过原论文链接查看。</div>':'')+
        '<div class="source-button-row"><button type="button" class="source-jump" data-unit-id="'+esc(unit.id)+'" aria-pressed="false" aria-label="打开 '+esc(unit.id)+' 对应原文">'+(inlineOriginal.has(unit.id)?'定位本地原文 · '+esc(unit.id):'查看官方 HTML 对应章节')+'</button><a href="'+sourceLink+'" target="_blank" rel="noopener noreferrer">PDF 原稿 p.'+Number(unit.pdfPage)+' ↗</a>'+evidence+'</div>'+
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
      '<p>原稿 HTML 来自 arXiv；如导入此前的个人双语精读 HTML，完整英文与意译在对应批注左侧逐行显示，不上传原稿。</p></section>';
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
    $('#source-toggle').addEventListener('click',()=>{
      const open=!document.body.classList.contains('source-open');
      setSourceOpen(open);
      if(open)jumpHtml(doc?.sections[0]?.units[0]);
    });
    $('#original-html-file').addEventListener('change',async e=>{
      try{if(e.target.files?.[0])await importOriginal(e.target.files[0]);}
      catch(error){$('#inline-source-status').textContent='导入失败：'+error.message;}
      finally{e.target.value='';}
    });
    $('#clear-source').addEventListener('click',()=>{
      inlineOriginal.clear();$('#clear-source').hidden=true;
      $('#inline-source-status').textContent='已退出本地原文模式；可重新导入此前的双语 HTML。';
      renderUnits();setSourceOpen(true);jumpHtml(doc?.sections[0]?.units[0]);
    });
    $('#reading-units').addEventListener('click',e=>{
      const jump=e.target.closest('.source-jump');
      if(!jump)return;
      const id=jump.dataset.unitId;
      const unit=doc?.sections.flatMap(s=>s.units).find(x=>x.id===id);
      if(inlineOriginal.has(id)){
        setSourceOpen(false);
        document.querySelector('#'+id+' .original-block')?.scrollIntoView({block:'center',behavior:'smooth'});
      }else{
        setSourceOpen(true);jumpHtml(unit);
      }
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
      renderOutline(data);renderUnits();setSourceOpen(true);jumpHtml(data.sections[0]?.units[0]);requestProgress();
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
