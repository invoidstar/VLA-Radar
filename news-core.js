/* Pure helpers shared with tests. Categories describe events, not scientific confidence. */
'use strict';
(function(g){
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function safeUrl(s){try{const u=new URL(s);return u.protocol==='https:'&&!u.username&&!u.password?u.href:'#';}catch{return '#';}}
 function isoWeek(s){if(!/^\d{4}-\d{2}-\d{2}$/.test(s||''))return '';const d=new Date(s+'T00:00:00Z');if(!Number.isFinite(+d)||d.toISOString().slice(0,10)!==s)return '';d.setUTCDate(d.getUTCDate()+4-(d.getUTCDay()||7));const year=d.getUTCFullYear(),start=new Date(Date.UTC(year,0,1));return year+'-W'+String(Math.ceil(((d-start)/86400000+1)/7)).padStart(2,'0');}
 function today(){return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Singapore',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());}
 function selectWeek(index,params,current=isoWeek(today())){if(params.get('story')&&index.storyWeeks[params.get('story')])return index.storyWeeks[params.get('story')];if(index.weeks.some(w=>w.key===params.get('nw')))return params.get('nw');if(params.get('paper')&&index.paperWeeks[params.get('paper')]?.length)return index.paperWeeks[params.get('paper')][0];return index.weeks.some(w=>w.key===current)?current:index.weeks[0]?.key||current;}
 function filtered(items,{category='',evidence='',query='',paper=''}={}){const q=query.trim().normalize('NFKC').toLocaleLowerCase();return items.filter(n=>(!category||n.primaryCategory===category)&&(!evidence||n.evidence===evidence)&&(!paper||n.paperLinks.some(p=>p.paperId===paper))&&(!q||[n.title,n.whatHappened,...n.tags].join(' ').normalize('NFKC').toLocaleLowerCase().includes(q)));}
 function counts(items){const out={};for(const n of items)if(n.status!=='withdrawn')out[n.primaryCategory]=(out[n.primaryCategory]||0)+1;return out;}
 function permalink(base,id,week){const u=new URL(base);u.search='';u.hash='';u.searchParams.set('view','news');u.searchParams.set('nw',week);u.searchParams.set('story',id);return u.href;}
 g.RadarNewsCore={esc,safeUrl,isoWeek,today,selectWeek,filtered,counts,permalink};if(typeof module!=='undefined')module.exports=g.RadarNewsCore;
})(typeof window!=='undefined'?window:globalThis);
