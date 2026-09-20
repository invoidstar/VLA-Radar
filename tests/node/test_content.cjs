const assert=require('node:assert/strict');const r=require('../../site/js/features/research/research.js');
assert.equal(r.formatScore(4.21,'score'),'4.21');assert.equal(r.formatScore(85.4,'percent'),'85.4%');assert.equal(r.formatScore(null,'score'),'—');
assert.deepEqual(r.datasetNames({tracks:[{dataset:'CALVIN'},{dataset:'RLBench'},{dataset:'CALVIN'}]}),['CALVIN','RLBench']);
const html=r.noteBlocks('| Method | SR |\n|---|---|\n| <script>alert(1)</script> | 60 |');assert(html.includes('<table'));assert(!html.includes('<script>'));assert(html.includes('&lt;script&gt;'));
assert(!r.noteBlocks('| A | B |\n|---|---|\n| broken |').includes('<table'));
console.log('PASS: dynamic datasets, score units, escaped note tables and malformed-table fallback');
