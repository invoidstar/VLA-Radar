'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const C=require('../../site/js/features/experience/experience-core.js'),R=require('../../site/js/features/research/research.js');
const fixture=JSON.parse(fs.readFileSync('catalog/papers/p001.json','utf8'));
let cases=0;const check=(a,b)=>{assert.deepEqual(a,b);cases++;};
check(C.uniqueIds(['p001','x','p001','p002','p003','p004','p005'],new Set(['p001','p002','p003','p004','p005'])),['p001','p002','p003','p004']);
check(C.url('javascript:alert(1)'),'#');check(C.url('https://u:secret@example.org'),'#');check(C.esc('<img onerror="x">'),'&lt;img onerror=&quot;x&quot;&gt;');
check(C.isNew({observedAt:null},'2026-09-17T12:00:00Z'),false);check(C.isNew({observedAt:'2026-09-18'},'2026-09-18T12:00:00Z'),true);check(C.isNew({observedAt:'2026-09-17T11:00:00Z'},'2026-09-17T12:00:00Z'),false);
check(C.sectionsFor(fixture,'nonsense'),[]);assert(C.sectionsFor(fixture,'training').length>0);cases++;
const bib=C.bibtex(fixture);assert(bib.includes('2608.27550'));assert(!bib.includes('author ='));assert(bib.includes('reading version'));cases+=3;
const markdown=C.markdown(fixture);assert(markdown.includes(fixture.note.version));assert(markdown.includes(fixture.note.sections[0].body));assert(!markdown.includes('localStorage'));cases+=3;
check(C.csvCell('=SUM(A1)'), '"\'=SUM(A1)"');check(C.csvCell('a"b'),'"a""b"');
const tr={id:'t',columns:['SR'],unit:'percent'},rows=[{method:'a',values:{SR:0}},{method:'b',values:{SR:50}},{method:'c',values:{SR:null}}];
const d=C.chartData(tr,rows,'SR');check(d.missing,1);check(d.rows.length,2);check(d.rows[0].width,0);check(d.max,100);check(d.rows[1].width,50);
check(C.chartData({columns:['x'],unit:'score'},[{values:{x:-1}},{values:{x:2}}],'x').min,-1);
const data={results:[{id:'old',trackId:'t',evidence:'checked',supersedes:''},{id:'new',trackId:'t',evidence:'checked',supersedes:'old'},{id:'candidate',trackId:'t',evidence:'candidate',supersedes:''}]};check(R.visibleResults(data,'t').map(x=>x.id),['new']);
const lib=JSON.parse(fs.readFileSync('data/library.json','utf8'));assert(lib.experienceUrl);const ix=JSON.parse(fs.readFileSync(lib.experienceUrl));const events=JSON.parse(fs.readFileSync(ix.updatesUrl));assert(!('results' in ix));cases+=2;
for(const stream of Object.values(events.streams))for(const part of stream){const obj=JSON.parse(fs.readFileSync(part.url));assert(obj.events.length<=50);assert(fs.statSync(part.url).size<512000,'Feed shard byte budget');cases++;}
const cov=JSON.parse(fs.readFileSync(ix.coverageUrl));for(const cell of cov.cells){check(cell.paperIds.length,new Set(cell.paperIds).size);assert(cell.resultCount>=cell.paperIds.length);cases++;}
assert(fs.statSync('site/js/features/experience/experience-loader.js').size<4000,'Eager loader budget');assert(fs.statSync('site/js/features/experience/experience.js').size<60000,'Optional feature JS budget');assert(fs.statSync('site/styles/features/experience.css').size<32000,'CSS budget');cases+=3;
console.log('PASS: '+cases+' workspace assertions: URL/HTML safety, IDs, citations, snapshots, null/zero, protocol results, sharded feeds, byte budgets and coverage deduplication.');
