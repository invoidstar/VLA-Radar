'use strict';
const a=require('node:assert/strict'), R=require('../research.js');
for(const total of [1,2,10,100,10000])for(const current of [1,Math.ceil(total/2),total]){const w=R.pageWindow(current,total);a(w.length<=9);a(w.includes(current));a(w.includes(1));a(w.includes(total));}
const row=(id,n,evidence='checked',supersedes='')=>({id,method:id,values:{Average:n},trackId:'one',evidence,supersedes});
let r=R.rankRows([row('a',90),row('b',null),row('c',90),row('d',0)],'Average');a.deepEqual(r.map(x=>x.rank),[1,1,3,null]);a.equal(r.at(-1).values.Average,null);
r=R.rankRows([row('a',10),row('b',20)],'Average','lower');a.equal(r[0].method,'a');
a.deepEqual(R.visibleResults({results:[row('old',89),row('new',90,'checked','old'),row('draft',100,'candidate'),{...row('other',100),trackId:'two'}]},'one').map(x=>x.id),['new']);
a.deepEqual(R.visibleResults({results:[row('old',89),row('draft',100,'candidate','old')]},'one').map(x=>x.id),['old']);
console.log('PASS: bounded pagination at 10,000 pages; ties, nulls, zero, protocol isolation, candidate exclusion and supersession.');
