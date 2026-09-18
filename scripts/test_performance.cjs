'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict'),{performance}=require('node:perf_hooks');
globalThis.RadarDates=require('../dates.js');
const C=require('../search-core.js'),R=require('../runtime.js');
const lib=JSON.parse(fs.readFileSync('data/library.json','utf8')),source=JSON.parse(fs.readFileSync(lib.searchUrl,'utf8'));
const cache=new R.LRU(3);for(let i=0;i<10;i++)cache.set(i,i);assert.equal(cache.map.size,3);assert.equal(cache.get(7),7);cache.set(10,10);assert.equal(cache.get(8),undefined);
for(const p of ['https://attacker.example/data.json','data/../private.json','//host/data.json','file:///etc/passwd'])assert.equal(R.safePath(p),false);
const original=C.buildIndex(source);assert(C.search(original,'LIBERO').length>0);assert(C.search(original,'记忆').length>0);assert(C.search(original,'no_such_term_123456').length===0);
const reports=[];
for(const n of [1000,5000,10000]){
 const data={topics:source.topics,papers:Array.from({length:n},(_,i)=>({...source.papers[i%source.papers.length],id:'fixture'+i}))};
 const start=performance.now(),idx=C.buildIndex(data),build=performance.now()-start;
 const queries=['LIBERO','memory','扩散','openvla','vidio'];const times=[];
 for(const q of queries){const t=performance.now();const result=C.search(idx,q);times.push(performance.now()-t);assert(result.length<=n);}
 reports.push({syntheticPapers:n,indexMs:+build.toFixed(2),queryMaxMs:+Math.max(...times).toFixed(2),queryMeanMs:+(times.reduce((a,b)=>a+b,0)/times.length).toFixed(2)});
}
console.log('PASS: bounded LRU, safe paths, source-based queries, synthetic scalability; not a real-device browser/network benchmark.');
console.log(JSON.stringify(reports,null,2));
