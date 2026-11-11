/* VLA Radar public close-reading list. No full article payload on the landing page. */
'use strict';
(function (g) {
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function show(host,entries,library) {
    const list=Array.isArray(entries)?entries:[];
    const byId=new Map((library?.papers||[]).map(x=>[x.id,x]));
    function card(x){
      const p=byId.get(x.paperId)||{};
      const name=p.name||x.title.split(':')[0];
      return '<article class="close-card">'+
        '<div class="close-card-top"><span class="close-tag">SOURCE-LINKED / PDF</span><span class="close-verified">已核验来源 · '+esc(x.curatedAt)+'</span></div>'+
        '<h2>'+esc(name)+'</h2><p class="close-full-title">'+esc(x.title)+'</p>'+
        '<p class="close-description">'+esc(p.contribution||'以原始论文、图表和来源页码为依据，逐段梳理论证与批判性分析。')+'</p>'+
        '<div class="close-stats"><span><strong>'+x.units+'</strong> 个论证单元</span>'+
        '<span><strong>'+x.sections+'</strong> 个研究章节</span><span>'+esc(x.sourceVersion)+'</span></div>'+
        '<a class="close-open" href="'+esc(x.href)+'" aria-label="打开 '+esc(name)+' 论文精读">进入完整论证精读 ↗</a>'+
        '</article>';
    }
    host.innerHTML='<div class="close-head"><span class="eyebrow">PAPER DEEP READING</span><h1>沿着原文，<em>理解论证。</em></h1>'+
      '<p>从论文观点到实验归因：逐段批注、英文技术关键词、中文逻辑导读，以及原稿 PDF 页码与 Benchmark 证据链接。</p></div>'+
      '<div class="close-board"><div class="close-stat"><strong>'+list.length+'</strong><span>精选论文</span></div>'+
      '<div class="close-stat"><strong>'+list.reduce((n,x)=>n+x.units,0)+'</strong><span>来源定位单元</span></div>'+
      '<p>本专区采用可复用的精读结构；未经授权的论文原文和原图不镜像托管。已有的详细笔记仍在每篇论文详情页查看。</p></div>'+
      '<label class="close-search">⌕ <input id="close-filter" type="search" placeholder="检索论文名称、作者和关键研究方向…" aria-label="筛选论文精读"></label>'+
      '<div class="close-list" id="close-list"></div>'+
      '<p class="close-note">文献库现有 149 篇论文的深度笔记与这里的逐段论证精读相互补充；本栏目不自动将所有论文标为“全文译注”。精读材料持续核对原稿版本、图表和评价条件。</p>';
    const output=host.querySelector('#close-list'),input=host.querySelector('#close-filter');
    function render(){
      const text=input.value.trim().normalize('NFKC').toLowerCase();
      const subset=list.filter(x=>[x.title,x.sourceVersion,byId.get(x.paperId)?.name,byId.get(x.paperId)?.contribution].join(' ').normalize('NFKC').toLowerCase().includes(text));
      output.innerHTML=subset.length?subset.map(card).join(''):'<p class="close-empty">当前没有匹配的精读内容。可以减少关键词后重试。</p>';
    }
    input.addEventListener('input',render);
    render();
  }
  g.RadarCloseReading={show};
})(window);
