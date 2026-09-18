'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),C=require('../news-core.js');let n=0;function check(ok,msg){assert.ok(ok,msg);n++;}
check(C.isoWeek('2026-09-18')==='2026-W38','ISO current week');check(C.isoWeek('2026-01-01')==='2026-W01','year rollover');check(C.isoWeek('2021-01-01')==='2020-W53','previous ISO year');check(C.isoWeek('2026-02-31')==='','reject invalid dates');
check(C.safeUrl('javascript:alert(1)')==='#','script URL rejected');check(C.safeUrl('https://a:b@example.com')==='#','credential URL rejected');check(!C.esc('<img src=x onerror=alert(1)>').includes('<'),'text escaped');
const lib=JSON.parse(fs.readFileSync('data/library.json')),idx=JSON.parse(fs.readFileSync(lib.newsUrl));
check(idx.total>=6,'verified initial news');check(idx.trend.length===12,'12 weekly bins');check(idx.trend.every(x=>x.status!=='not_run'||x.count===null),'unscanned weeks unknown');
const items=idx.weeks.flatMap(w=>w.pages.flatMap(p=>JSON.parse(fs.readFileSync(p.url)).items));
check(items.length===idx.total,'shards complete');check(new Set(items.map(x=>x.id)).size===items.length,'no duplicate stories');check(C.filtered(items,{query:'Digit'}).some(x=>x.id==='news-20260915-digit-5'),'keyword filter');check(C.filtered(items,{category:'opensource'}).length>=2,'category filter');check(C.filtered(items,{evidence:'reported'}).every(x=>x.evidence==='reported'),'source filter');check(C.filtered(items,{paper:'p050'}).some(x=>x.eventKey.includes('xplanner')),'background relations explicit');
check(C.selectWeek(idx,new URLSearchParams('nw=2026-W37'),'2026-W38')==='2026-W37','archive route');check(C.selectWeek(idx,new URLSearchParams('nw=bad'),'2026-W38')==='2026-W38','bad week falls back');check(C.selectWeek(idx,new URLSearchParams('paper=p070'),'2026-W38')===idx.paperWeeks.p070[0],'related paper locates newest linked archive');
const first=items.find(x=>x.eventDate),u=new URL(C.permalink('https://x.test/?private=secret#local',first.id,C.isoWeek(first.eventDate)));check(!u.search.includes('private')&&!u.hash,'share excludes unrelated local state');check(u.searchParams.get('story')===first.id,'story permalink');
for(const w of idx.weeks){check(w.featuredIds.length<=5,'bounded featured');for(const p of w.pages)check(p.count<=20,'bounded chunks');}
const app=fs.readFileSync('app.js','utf8');check(app.includes("news:'具身智能周报'"),'registered view');check(!fs.readFileSync('index.html','utf8').includes('src="news.js'),'optional script not eager');
console.log('PASS news:',n,'date, source, query, shard and safety assertions');
