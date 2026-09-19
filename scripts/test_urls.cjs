'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');const vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../app.js'),'utf8');
const a=source.indexOf('  function parseUrl()'), b=source.indexOf('  function syncUrl(',a);
assert(a>=0&&b>a,'URL function extraction must match app.js');
function fixture(url){
 const u=new URL(url), state={};
 const c={URL,URLSearchParams,Dates:require('../dates.js'),TIME_UNKNOWN:'undated',views:{papers:'Papers',timeline:'Timeline',reading:'Reading',topics:'Topics',about:'About',leaderboards:'Leaderboards'},state,location:{href:u.href,search:u.search,hash:u.hash}};
 vm.createContext(c);vm.runInContext(source.slice(a,b),c);c.parseUrl();return c;
}
let c=fixture('https://example.test/VLA-Radar/?year=2025&week=2026-W35');
assert.equal(c.state.year,'2026');assert.equal(c.state.week,'2026-W35');
assert.equal(c.makeUrl().searchParams.get('week'),'2026-W35');
c=fixture('https://example.test/VLA-Radar/?week=2025-W53');assert.equal(c.state.week,'');
c=fixture('https://example.test/VLA-Radar/?month=2026-08');assert.equal(c.state.month,'2026-08');assert.equal(c.makeUrl().searchParams.get('month'),'2026-08');
c=fixture('https://example.test/VLA-Radar/?view=timeline&timeline=month');assert.equal(c.state.timeline,'month');assert.equal(c.makeUrl().searchParams.get('timeline'),'month');
c=fixture('https://example.test/VLA-Radar/?year=2026&week=undated');assert.equal(c.state.week,'undated');
c=fixture('https://example.test/VLA-Radar/?view=reading&q=RT-1&week=2022-W50#paper=p052');c.state.status='read';
assert.equal(c.makeUrl(true,true).searchParams.has('view'),false);assert.equal(c.makeUrl(true,true).searchParams.has('status'),false);
assert.equal(c.makeUrl(true,true).hash,'#paper=p052');assert.equal(c.makeUrl(false,true).hash,'');
c=fixture('https://example.test/VLA-Radar/?year=%3Cscript%3E&week=bad');assert.equal(c.state.year,'');assert.equal(c.state.week,'');
c=fixture('https://example.test/VLA-Radar/?view=leaderboards&dataset=RoboCasa&track=robocasa24-cosmos-table');assert.equal(c.makeUrl().searchParams.get('dataset'),'RoboCasa');assert.equal(c.makeUrl().searchParams.get('track'),'robocasa24-cosmos-table');
console.log('PASS: URL tests: legacy weeks/months, public sharing, invalid parameters and leaderboard tracks.');

c=fixture('https://example.test/VLA-Radar/?view=leaderboards&dataset=LIBERO&track=t&lbMetric=Long&lbOrder=asc&lbChart=scatter&lbTime=firstPublished');
for(const [key,value] of Object.entries({lbMetric:'Long',lbOrder:'asc',lbChart:'scatter',lbTime:'firstPublished'}))assert.equal(c.makeUrl(true,true).searchParams.get(key),value);
console.log('PASS: shared leaderboard URLs preserve metric, ordering and source-scoped chart choices.');
