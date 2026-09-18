'use strict';
const a=require('node:assert/strict'), R=require('../research.js');
for(const total of [1,2,10,100,10000])for(const current of [1,Math.ceil(total/2),total]){const w=R.pageWindow(current,total);a(w.length<=9);a(w.includes(current));a(w.includes(1));a(w.includes(total));}
const row=(id,n,evidence='checked',supersedes='')=>({id,method:id,values:{Average:n},trackId:'one',evidence,supersedes});
let r=R.rankRows([row('a',90),row('b',null),row('c',90),row('d',0)],'Average');a.deepEqual(r.map(x=>x.rank),[1,1,3,null]);a.equal(r.at(-1).values.Average,null);
r=R.rankRows([row('a',10),row('b',20)],'Average','lower');a.equal(r[0].method,'a');
a.deepEqual(R.visibleResults({results:[row('old',89),row('new',90,'checked','old'),row('draft',100,'candidate'),{...row('other',100),trackId:'two'}]},'one').map(x=>x.id),['new']);
a.deepEqual(R.visibleResults({results:[row('old',89),row('draft',100,'candidate','old')]},'one').map(x=>x.id),['old']);
console.log('PASS: bounded pagination at 10,000 pages; ties, nulls, zero, protocol isolation, candidate exclusion and supersession.');

a.equal(R.metricValue(4.42,'score'),'4.42');
a.equal(R.metricValue(0,'percent'),'0%');
a.equal(R.metricValue(null,'seconds'),'—');
a.equal(R.metricValue(0.5,'seconds'),'0.5 s');
a.deepEqual(R.benchmarkFamilies({tracks:[{dataset:'CALVIN'},{dataset:'LIBERO'},{dataset:'CALVIN'}]}),['CALVIN','LIBERO']);
const html=R.richEvidence({sections:[{sources:[{url:'https://example.com/paper'}]}],tables:[{title:'<script>',columns:['a','b'],rows:[['<img onerror=x>','2']],locator:'Table 1',caption:'Test'}]});
a(!html.includes('<script>'));a(!html.includes('<img onerror'));a(html.includes('&lt;script&gt;'));
console.log('PASS: deep-note escaping, dynamic benchmark families, score/seconds/percent units.');
