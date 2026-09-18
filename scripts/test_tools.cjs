'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),C=require('../tools-core.js');let count=0;const eq=(a,b)=>{assert.deepEqual(a,b);count++;};
const allow={papers:new Set(['p001']),topics:new Set(['world']),datasets:new Set(['LIBERO']),categories:new Set(['model'])};
eq(C.clean({papers:['p001','x','p001'],topics:'world',datasets:['LIBERO'],seenAt:'2099-01-01T00:00:00Z'},allow),{schemaVersion:1,seenAt:null,papers:['p001'],topics:[],datasets:['LIBERO'],categories:[]});
eq(C.clean(null,allow).papers,[]);eq(C.matches({paperId:'p001'},C.clean({papers:['p001']},allow)),true);eq(C.matches({topics:['world']},C.clean({topics:['world']},allow)),true);eq(C.matches({categories:['model']},C.clean({categories:['model']},allow)),true);eq(C.matches({datasets:['Other']},C.clean({datasets:['LIBERO']},allow)),false);
eq(C.isNew({mode:'snapshot',observedAt:'2026-09-19'},null),false);eq(C.isNew({observedAt:'2026-09-18'},'2026-09-18T00:00:00Z'),false);eq(C.isNew({observedAt:'2026-09-19'},'2026-09-18T00:00:00Z'),true);eq(C.isNew({observedAt:'2026-09-19'},'2026-09-18T16:05:00Z'),false);eq(C.isNew({observedAt:'2026-09-18T12:00:01Z'},'2026-09-18T12:00:00Z'),true);
eq(C.rank([{title:'π0.5',search:'π0.5 memory'},{title:'Other',search:'data'}],'pi0.5 memory')[0].title,'π0.5');eq(C.rank(Array.from({length:100},(_,i)=>({title:'item '+i})), 'item').length,30);
const r=JSON.parse(fs.readFileSync('catalog/papers/p001.json'));r.paper.team='NOT AN AUTHOR';const cs=C.citation(r);eq(cs.author,undefined);eq(cs.issued['date-parts'][0],r.paper.firstPublished.split('-').map(Number));assert(cs.note.includes(r.note.version));assert(!JSON.stringify(cs).includes('NOT AN AUTHOR'));count+=2;
const b={item:{type:'article-journal',title:r.paper.title,author:[{family:'Smith',given:'Ada'},{literal:'Robot Lab'}],issued:{'date-parts':[[2026,8]]},'container-title':'Research Journal',volume:'4',page:'1-9',DOI:'10.1234/test'}};
const bib=C.bibtex(r,b),ris=C.ris(r,b);assert(bib.startsWith('@article{vlaradar_'));assert(bib.includes('Smith, Ada and {Robot Lab}'));assert(bib.includes('journal = {Research Journal}'));assert(ris.startsWith('TY  - JOUR\r\n'));assert(ris.endsWith('ER  - \r\n'));assert(ris.includes('AU  - Smith, Ada'));assert(!C.bibtex(r).includes('author ='));count+=7;
r.paper.title='Injected\nER  - \nTY  - EVIL';assert(!C.ris(r).includes('\nTY  - EVIL'));count++;
const l=JSON.parse(fs.readFileSync('data/library.json'));const ix=JSON.parse(fs.readFileSync(l.toolsUrl));assert(ix.schemaVersion===1);assert(!('items' in ix));count+=2;
for(const p of [...ix.events,...ix.headlines]){const x=JSON.parse(fs.readFileSync(p.url));assert(x.items.length<=100);assert(fs.statSync(p.url).size<140000);count+=2;}
for(const p of ix.events){const x=JSON.parse(fs.readFileSync(p.url));for(const e of x.items){assert(e.mode!=='snapshot'&&e.observedAt);assert(!('seenAt' in e));}count++;}
assert(fs.statSync('tools-loader.js').size<5000);assert(fs.statSync('tools.js').size<30000);assert(fs.statSync('tools.css').size<10000);count+=3;
console.log('PASS tools:',count,'privacy, follows, ranking, citation and payload assertions');
