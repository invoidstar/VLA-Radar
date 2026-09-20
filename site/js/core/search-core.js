'use strict';
(function(global){
  const norm = s => String(s||'').normalize('NFKC').toLowerCase().replace(/[‐‑–—]/g,'-').replace(/π/g,'pi').replace(/τ/g,'tau').trim();
  function safeUrl(url){try{const u=new URL(url);return /^https?:$/.test(u.protocol)?u.href:'#';}catch{return '#';}}
  const aliases = [
    ['memory','记忆','历史','history'],['pretrain','pretraining','pre-training','预训练'],
    ['world','世界'],['action','动作'],['future','未来'],['freezing','frozen','freeze','冻结','先验保护'],
    ['spatial','空间','几何','geometry','geometric'],['acceleration','accelerate','efficient','efficiency','加速','高效'],
    ['tactile','触觉'],['language','语言'],['video','视频'],['cache','caching','缓存'],
    ['long-horizon','longhorizon','长程','长时程'],['benchmark','evaluation','评测','基准'],
    ['negative','负面','负迁移'],['distill','distillation','蒸馏'],['reinforcement','rl','强化学习'],
    ['landmark','landmarks','foundational','关键文献','奠基工作'],['robot','机器人'],['pointmap','点图'],['asynchronous','async','异步']
  ];
  function distance(a,b,max){
    if(Math.abs(a.length-b.length)>max)return max+1;
    const m=Array.from({length:a.length+1},()=>Array(b.length+1).fill(0));
    for(let i=0;i<=a.length;i++)m[i][0]=i;for(let j=0;j<=b.length;j++)m[0][j]=j;
    for(let i=1;i<=a.length;i++){let rowMin=Infinity;for(let j=1;j<=b.length;j++){
      m[i][j]=Math.min(m[i-1][j]+1,m[i][j-1]+1,m[i-1][j-1]+(a[i-1]===b[j-1]?0:1));
      if(i>1&&j>1&&a[i-1]===b[j-2]&&a[i-2]===b[j-1])m[i][j]=Math.min(m[i][j],m[i-2][j-2]+1);
      rowMin=Math.min(rowMin,m[i][j]);
    }if(rowMin>max)return max+1;}return m[a.length][b.length];
  }
  function score(entry,tokens){
    let total=0;
    for(const token of tokens){
      let best=0;const variants=aliases.find(a=>a.includes(token))||[token];
      for(const [field,weight]of entry.fields){if(field.includes(token))best=Math.max(best,weight+1);else if(variants.some(v=>field.includes(v)))best=Math.max(best,weight*.8);}
      if(!best&&/^[a-z]{4,30}$/.test(token)){
        const max=token.length>7?2:1;
        if(entry.words.some(w=>distance(token,w,max)<=max))best=1.4;
      }
      if(!best)return 0;total+=best;
    }return total;
  }

  function buildIndex(data){
    const topics=Object.fromEntries(data.topics.map(t=>[t.id,t]));
    return data.papers.map(p=>({id:p.id,fields:[[p.name,9],[p.title,6],[p.team,4],[p.tags.join(' ')+' '+p.topics.map(t=>topics[t].name+' '+topics[t].en).join(' '),5],[p.contribution,2],[p.findings,2],[p.insight,2],[p.limitations,1],[p.venue+' '+p.publicationStatus+' '+p.arxiv,3],[p.firstPublished+' '+(global.RadarDates?.isoWeek(p.firstPublished)?.key||'日期未精确到日'),4]].map(([v,w])=>[norm(v),w]),words:norm(p.name+' '+p.title+' '+p.tags.join(' ')).match(/[a-z][a-z0-9+-]{2,}/g)||[]}));
  }
  function search(index,query){const tokens=norm(query).split(/\s+/).filter(Boolean).slice(0,12);return index.map(e=>[e.id,tokens.length?score(e,tokens):1]).filter(x=>x[1]>0);}
  global.RadarSearchCore={norm,score,buildIndex,search};
  if(typeof module!=='undefined')module.exports=global.RadarSearchCore;
})(typeof window!=='undefined'?window:globalThis);
