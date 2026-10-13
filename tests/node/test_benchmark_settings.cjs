'use strict';
const a=require('node:assert/strict'),S=require('../../site/js/features/research/benchmark-settings.js');
let count=0;const ok=(name,f)=>{f();count++;};
const setting={direction:'higher',columns:['Average']};
const row=(id,method,v)=>({id,method,values:{Average:v}});
const rows=[row('a','Same',80),row('b','Same',90),row('c','Other',null),row('d','Zero',0)];
ok('same method reports stay separate',()=>a.deepEqual(S.sortRows(rows,setting,'Average').map(x=>x.id),['b','a','d','c']));
ok('source order does not deduplicate',()=>a.deepEqual(S.sortRows(rows,setting,'Average','source').map(x=>x.id),['a','b','c','d']));
ok('missing score stays last ascending',()=>a.deepEqual(S.sortRows(rows,setting,'Average','asc').map(x=>x.id),['d','a','b','c']));
ok('lower metric auto sorts ascending',()=>a.deepEqual(S.sortRows(rows,{...setting,direction:'lower'},'Average').map(x=>x.id),['d','a','b','c']));
ok('per-column metric directions override the shared Setting default',()=>{const mixed={direction:'higher',columnMeta:{Haz:{unit:'percent',direction:'lower'}}};const rr=[{id:'h',values:{Haz:80}},{id:'l',values:{Haz:12}}];a.deepEqual(S.sortRows(rr,mixed,'Haz').map(x=>x.id),['l','h']);});
ok('sorting is non-mutating',()=>{const before=JSON.stringify(rows);S.sortRows(rows,setting,'Average');a.equal(JSON.stringify(rows),before);});
ok('render keeps direction block-scoped',()=>{const src=require('node:fs').readFileSync('site/js/features/research/benchmark-settings.js','utf8');a(src.includes(';const dir=direction(setting,order,metric);'));a(!src.includes('),dir=direction(setting,order);'));});
ok('structured protocol facts expose stable fingerprint and hard dimensions',()=>{
  const x=S.protocolFacts({id:'setting-libero-standard40-abcdef123456',evalId:'auto:standard40',dataset:'LIBERO',tasks:'40',split:'four suites',metric:'Task success rate',unit:'percent',direction:'higher',columns:['Spatial','Average']});
  a.equal(x.fingerprint,'ep1-abcdef123456');a.equal(x.scope,'standard40');a(x.fields.some(([k,v])=>k==='Benchmark'&&v==='LIBERO'));a(x.fields.some(([k,v])=>k==='Reported columns'&&v.includes('Spatial')));
});
ok('compatibility keeps soft reporting differences inside one Setting',()=>{
  const p={id:'a',dataset:'LIBERO',tasks:'40',split:'Spatial / Object / Goal / Long',metric:'Task success rate',unit:'percent',direction:'higher',columns:['Spatial','Object','Goal','Long','Average']};
  const soft={...p,id:'b',split:'four suites; 3 seeds'};
  const partial={...p,id:'c',columns:['Spatial','Object','Goal','Long']};
  const other={...p,id:'d',metric:'Latency',unit:'seconds',direction:'lower'};
  a.equal(S.compatibilityLevel(p,p),'exact');a.equal(S.compatibilityLevel(p,soft),'compatible');a.equal(S.compatibilityLevel(p,partial),'partial');a.equal(S.compatibilityLevel(p,other),'incompatible');
  a.deepEqual(S.compatibilitySummary({primaryTrackId:'a'},[p,soft,partial]),{exact:1,compatible:1,partial:1,incompatible:0});
});
const realSettings=require('../../data/leaderboards.json').settings;
const taxonomy=require('../../catalog/benchmark-taxonomy.json');
ok('benchmark search supports multi-token AND matching',()=>{const x=S.searchSettings(realSettings,'RoboTwin 50 tasks clean random');a(x.length>=1);a(x.every(s=>s.dataset==='RoboTwin'));a(x.some(s=>s.evalId==='auto:50-clean-random'));});
ok('benchmark search covers metric and task vocabulary',()=>{const x=S.searchSettings(realSettings,'RLBench 18 success');a(x.some(s=>s.dataset==='RLBench'&&s.evalId==='auto:18-main'));});
ok('benchmark search covers setting names and normalized case',()=>{const x=S.searchSettings(realSettings,'libero LONG HORIZON 10');a(x.some(s=>s.evalId==='auto:long10'));});
ok('method search spans Benchmarks via compact method names',()=>{const x=S.searchSettings(realSettings,'VLA-InfoEntropy');a(x.some(s=>s.dataset==='LIBERO'));});
ok('benchmark search no-match is empty',()=>a.equal(S.searchSettings(realSettings,'zzzz-no-such-benchmark-987').length,0));
ok('benchmark search empty query returns copy without mutation',()=>{const before=JSON.stringify(realSettings);const x=S.searchSettings(realSettings,'  ');a.equal(x.length,realSettings.length);a.notEqual(x,realSettings);a.equal(JSON.stringify(realSettings),before);});

ok('taxonomy focus filter uses benchmark-level metadata',()=>{const x=S.filterSettingsByTaxonomy(realSettings,taxonomy,'long-horizon-memory','all',[]);a(x.length>0);a(x.every(s=>taxonomy.benchmarks[s.dataset].focus==='long-horizon-memory'));a(x.some(s=>s.dataset==='CALVIN'));});
ok('taxonomy environment filter separates real robot benchmarks',()=>{const x=S.filterSettingsByTaxonomy(realSettings,taxonomy,'all','real',[]);a(x.length>0);a(x.every(s=>taxonomy.benchmarks[s.dataset].environment==='real'));a(x.some(s=>s.dataset==='RoboDojo real'));a(!x.some(s=>s.dataset==='RoboTwin'));});
ok('taxonomy multi-tag filter uses AND semantics',()=>{const x=S.filterSettingsByTaxonomy(realSettings,taxonomy,'all','all',['tactile','contact-rich']);const ds=new Set(x.map(s=>s.dataset));a(ds.has('VLA-Touch (real)'));a(ds.has('VT-WAM real robot'));a(!ds.has('RoboTwin'));});
ok('taxonomy filters compose focus environment and tags',()=>{const x=S.filterSettingsByTaxonomy(realSettings,taxonomy,'dexterous-contact','real',['industrial-assembly']);const ds=new Set(x.map(s=>s.dataset));a(!ds.has('GF-VLA real'));a(ds.has('VLAbot real'));a([...ds].every(d=>taxonomy.benchmarks[d].focus==='dexterous-contact'&&taxonomy.benchmarks[d].environment==='real'));});
ok('taxonomy filtering is non-mutating',()=>{const before=JSON.stringify(realSettings);S.filterSettingsByTaxonomy(realSettings,taxonomy,'general-manipulation','simulation',['multi-task']);a.equal(JSON.stringify(realSettings),before);});

ok('Benchmark view separates registry and archived evidence presentation',()=>{const src=require('node:fs').readFileSync('site/js/features/research/benchmark-settings.js','utf8');a(src.includes('data-board-kind'));a(src.includes('data-rows-mode'));a(src.includes('setting-columns-toggle'));const registry=require('../../data/leaderboards.json').benchmarkRegistry;a(registry.benchmarks['LIBERO'].kind==='benchmark');a(registry.benchmarks['VLAbot real'].kind==='case-study');});
ok('official score and SR remain independent sortable metrics',()=>{
 const rows=[{model:'A',rank:1,values:{Average:{score:39,sr:22}}},{model:'B',rank:2,values:{Average:{score:35,sr:30}}}];
 a.deepEqual(S.officialSorted(rows,'Average','score').map(x=>x.model),['A','B']);
 a.deepEqual(S.officialSorted(rows,'Average','sr').map(x=>x.model),['B','A']);
 a.equal(rows[0].rank,1);
});
ok('RoboTwin official success values show percent, not RoboDojo progress score',()=>{
 const board={id:'robotwin2',benchmark:'RoboTwin',columns:['Average','Clean','Random'],metricSchema:'clean-random',
 officialUpdatedAt:'2026-10-11',capturedAt:'2026-10-13',boardUrl:'https://robotwin-platform.github.io/leaderboard',
 sourceRepoUrl:'https://github.com/RoboTwin-Platform/RoboTwin-Platform.github.io',
 entries:[{model:'PatchWAM',rank:1,track:'cotrain',contributor:'PatchWAM Team',values:{Average:79.14,Clean:91.56,Random:66.72}}]};
 a.equal(S.officialValue(board.entries[0],'Random','score'),66.72);
 a.equal(S.officialValue(board.entries[0],'Random','sr'),null);
 a(S.officialTableHtml(board).includes('79.14%'));
});
ok('RoboDojo SR is a rate, not the 39.26 progress score',()=>{
 const board={id:'robodojo-sim',benchmark:'RoboDojo',columns:['Average'],metricSchema:'score-success',
 officialUpdatedAt:'2026-10-09',capturedAt:'2026-10-13',boardUrl:'https://robodojo-benchmark.com/',
 sourceRepoUrl:'https://github.com/RoboTwin-Platform/RoboTwin-Platform.github.io',
 entries:[{model:'VPP2',rank:1,contributor:'RobotEra',values:{Average:{score:39.26,sr:32.26}}}]};
 const h=S.officialTableHtml(board,'Average','sr');
 a(h.includes('32.26%'));a(h.includes('非官网原始 Average 排名'));a(!h.includes('39.26%'));
});
ok('verified official model names appear in compact search index without full rows',()=>{
 const source=require('../../data/library.json'),index=require('../../'+source.boardIndexUrl);
 a(index.officialBoards.RoboTwin.modelNames.includes('ViGAR'));
 a(index.officialBoards.RoboDojo.modelNames.includes('PhysicalRSI'));
 a(index.officialBoards['RoboDojo real'].modelNames.includes('OpenWAM-α'));
 for(const x of Object.values(index.officialBoards))a(!Object.hasOwn(x,'entries'));
});

console.log(`PASS: ${count} Setting-table sorting / search / taxonomy assertions.`);
