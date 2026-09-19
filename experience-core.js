/* Pure reading-workspace helpers. No network, analytics or private-state export. */
'use strict';
(function(g){
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const url=v=>{try{const u=new URL(v);return /^https?:$/.test(u.protocol)&&!u.username&&!u.password?u.href:'#';}catch{return '#';}};
 const uniqueIds=(ids,allowed,max=4)=>[...new Set(Array.isArray(ids)?ids.filter(x=>allowed.has(x)):[])].slice(0,max);
 const dimensions=[
  ['problem','研究问题',/problem|motivation|研究问题|背景|瓶颈/i],
  ['novelty','创新与前作差异',/novelty|contribution|创新|贡献|新颖/i],
  ['mechanism','输入、输出与模块',/mechanism|architecture|representation|信息流|架构|输入|模块|表示/i],
  ['training','监督与训练',/training|supervision|训练|监督/i],
  ['deployment','部署与执行',/deployment|inference|推理|部署|执行/i],
  ['protocol','评测与数据预算',/protocol|experiment|evaluation|评测|实验设置|关键实验/i],
  ['ablation','消融与归因',/ablation|消融|归因/i],
  ['limits','局限与证据边界',/limit|caution|局限|适用|边界/i]
 ];
 function sectionsFor(record,dimension){const d=dimensions.find(x=>x[0]===dimension);return d?(record.note?.sections||[]).filter(s=>d[2].test(s.id+' '+s.title)).slice(0,2):[];}
 function signature(r,key){return sectionsFor(r,key).map(s=>s.body.replace(/\s+/g,' ').trim()).join('\n');}
 function tex(s){return String(s??'').replace(/[\u0000-\u001f]/g,' ').replace(/\\/g,'\\textbackslash{}').replace(/[{}]/g,'').replace(/[%&#_$]/g,x=>'\\'+x).replace(/~/g,'\\textasciitilde ').replace(/\^/g,'\\textasciicircum ');}
 function bibtex(r){const p=r.paper,n=r.note,year=(p.firstPublished||p.collectionMonth||'').slice(0,4);const f=[['title',p.title],['year',year],['url',url(p.paperUrl)]];
  if(p.arxiv)f.push(['eprint',p.arxiv],['archivePrefix','arXiv']);if(p.doi)f.push(['doi',p.doi]);
  f.push(['note',`VLA-Radar reading version: ${n?.version||'not verified'}; verified: ${n?.verifiedAt||'unknown'}. Basic metadata only; verify authors and final venue at the primary source.`]);
  return `@misc{vlaradar_${p.id}_${year},\n${f.filter(([,v])=>v).map(([k,v])=>'  '+k+' = {'+tex(v)+'}').join(',\n')}\n`;
 }
 const md=v=>String(v??'').replace(/([\\`*_\[\]<>#])/g,'\\$1');
 function markdown(r){const p=r.paper,n=r.note;let s=`# ${md(p.name)}\n\n${md(p.title)}\n\n首发：${md(p.firstPublished||'未知')} · 阅读版本：${md(n.version)} · 核验：${md(n.verifiedAt||'未知')}\n\n原文：${url(p.paperUrl)}\n\n来源范围：${md(n.coverage?.scope||'未记录')}；状态：${md(n.status)}。作者报告与编辑解读，不代表独立复现。\n\n## KEY RESULT\n\n${p.findings}\n`;
  for(const t of n.sections)s+=`\n## ${md(t.title)}\n\n${t.body}\n\n`+t.sources.map(x=>`来源：${md(x.label)} — ${url(x.url)}`).join('\n')+'\n';
  for(const t of n.tables||[])s+=`\n## ${md(t.title)}\n\n| ${t.columns.map(md).map(x=>x.replace(/\|/g,'\\|')).join(' | ')} |\n| ${t.columns.map(()=> '---').join(' | ')} |\n`+t.rows.map(row=>'| '+row.map(v=>md(v).replace(/\|/g,'\\|').replace(/\n/g,' ')).join(' | ')+' |').join('\n')+`\n\n${md(t.locator)} · ${md(t.caption)}\n`;
  for(const f of n.figures||[])s+=`\n### ${md(f.title)}\n\n${md(f.caption)}\n\n原图：${url(f.url)}\n`;
  return s+'\n---\n导出仅含公开论文内容，不包含收藏、私人阅读进度或比较清单。\n';
 }
 function csvCell(v){let s=String(v??'');if(/^[\s]*[=+@\-]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';}
 function csv(track,rows){return '\uFEFF'+[['Method',...track.columns,'Unit','Protocol','Source','Version','Locator','Training data','Evaluation notes'],...rows.map(r=>[r.method,...track.columns.map(k=>r.values[k]??''),track.unit,track.id,url(r.source),r.sourceVersion,r.locator,r.trainingData,r.evaluationNotes])].map(row=>row.map(csvCell).join(',')).join('\r\n');}
 function chartData(track,rows,metric){const chosen=track.columns.includes(metric)?metric:track.columns[0];const valid=rows.filter(r=>Number.isFinite(r.values[chosen]));const vals=valid.map(r=>r.values[chosen]);const lo=Math.min(0,...vals),hi=track.unit==='percent'?Math.max(100,...vals):Math.max(0,...vals,1);return {metric:chosen,min:lo,max:hi,missing:rows.length-valid.length,rows:valid.map(r=>({...r,width:Math.abs(r.values[chosen])/(hi-lo)*100,offset:(Math.min(0,r.values[chosen])-lo)/(hi-lo)*100}))};}
 // Exact public day only: never use an inferred month/day or fall back to today's date.
 function exactDay(value){
  if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value))return null;
  const n=Date.parse(value+'T00:00:00Z');
  return Number.isFinite(n)&&new Date(n).toISOString().slice(0,10)===value?n:null;
 }
 function scatterData(track,rows,metric,papers,basis='firstPublished',limit=500){
  const chosen=track.columns.includes(metric)?metric:track.columns[0];basis=basis==='verifiedAt'?'verifiedAt':'firstPublished';
  const lookup=id=>papers instanceof Map?papers.get(id):papers?.[id];
  const valid=[],eligible=rows.filter(r=>r.trackId===track.id&&r.evidence==='checked');let missingScore=0,missingDate=0;
  for(const row of eligible){
   const value=row.values?.[chosen];if(!Number.isFinite(value)){missingScore++;continue;}
   const paper=lookup(row.paperId),date=basis==='verifiedAt'?row.verifiedAt:paper?.firstPublished,time=exactDay(date);
   if(time===null){missingDate++;continue;}
   valid.push({row,value,date,time,paperName:paper?.name||row.paperId});
  }
  valid.sort((a,b)=>a.time-b.time||a.value-b.value||String(a.row.id).localeCompare(String(b.row.id)));
  const groups=new Map();let minTime=Infinity,maxTime=-Infinity,min=0,max=track.unit==='percent'?100:1;
  for(const point of valid){
   minTime=Math.min(minTime,point.time);maxTime=Math.max(maxTime,point.time);min=Math.min(min,point.value);max=Math.max(max,point.value);
   const key=point.date+'|'+point.value;if(!groups.has(key))groups.set(key,{date:point.date,time:point.time,value:point.value,points:[]});groups.get(key).points.push(point);
  }
  const oneDate=valid.length>0&&minTime===maxTime,pad=oneDate?86400000:Math.max(86400000,(maxTime-minTime)*0.05);
  if(!valid.length){minTime=0;maxTime=86400000;}
  const all=[...groups.values()],safeLimit=Number.isInteger(limit)&&limit>0?Math.min(limit,500):500,shown=all.slice(0,safeLimit);
  return {metric:chosen,basis,eligible:eligible.length,missingScore,missingDate,oneDate,min,max,
   start:minTime-pad,end:maxTime+pad,groups:shown,totalGroups:all.length,validCount:valid.length,
   plottedCount:shown.reduce((n,g)=>n+g.points.length,0),limit:safeLimit};
 }
 function scatterCSV(track,rows,metric,papers,basis='firstPublished'){
  const chosen=track.columns.includes(metric)?metric:track.columns[0];basis=basis==='verifiedAt'?'verifiedAt':'firstPublished';
  const header=['Result ID','Method','Reporting paper ID','Metric','Value','Unit','Date basis','Recorded date','Plottable','Reason','Protocol','Source','Source version','Locator'];
  const body=rows.filter(r=>r.trackId===track.id&&r.evidence==='checked').map(r=>{
   const p=papers instanceof Map?papers.get(r.paperId):papers?.[r.paperId];
   const d=basis==='verifiedAt'?r.verifiedAt:p?.firstPublished,v=r.values?.[chosen];
   const reason=!Number.isFinite(v)?'missing numeric score':exactDay(d)===null?'missing exact day':'';
   return [r.id,r.method,r.paperId,chosen,Number.isFinite(v)?v:'',track.unit,basis==='verifiedAt'?'VLA-Radar verification date':'Reporting paper first public date (not necessarily method release date)',d||'',reason?'no':'yes',reason,track.id,url(r.source),r.sourceVersion,r.locator];
  });
  return '\uFEFF'+[header,...body].map(row=>row.map(csvCell).join(',')).join('\r\n');
 }
 function isNew(e,since){if(!since||!e.observedAt)return false;const d=e.observedAt;return d.length===10?d>=String(since).slice(0,10):Date.parse(d)>Date.parse(since);}
 function localJSON(key,fallback){try{const s=localStorage.getItem(key);return s?JSON.parse(s):fallback;}catch{return fallback;}}
 function store(key,value){try{localStorage.setItem(key,JSON.stringify(value));return true;}catch{return false;}}
 const api={esc,url,uniqueIds,dimensions,sectionsFor,signature,tex,bibtex,markdown,csv,csvCell,chartData,exactDay,scatterData,scatterCSV,isNew,localJSON,store};g.RadarExperienceCore=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window==='undefined'?globalThis:window);
