'use strict';
const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const Dates = require('../dates.js');
let cases = 0;
function expect(actual, wanted) { assert.deepEqual(actual, wanted); cases++; }
expect(Dates.isoWeek('2021-01-01'), {year:'2020',week:53,key:'2020-W53',start:'2020-12-28',end:'2021-01-03'});
expect(Dates.isoWeek('2024-12-30'), {year:'2025',week:1,key:'2025-W01',start:'2024-12-30',end:'2025-01-05'});
expect(Dates.isoWeek('2026-08-24'), {year:'2026',week:35,key:'2026-W35',start:'2026-08-24',end:'2026-08-30'});
expect(Dates.isoWeek('2026-08-30').key, '2026-W35');
expect(Dates.isoWeek('2026-08-31').key, '2026-W36');
expect(Dates.isoWeek('2024-02-29').key, '2024-W09');
expect(Dates.yearOf('2021-01-01'), '2020');
expect(Dates.yearOf('2026-08'), '2026');
expect(Dates.yearOf(null), '');
for (const input of [null, undefined, '', '2026-08', '2026', '2026-02-29', '2026-02-30', '2026-13-01', '2026-01-00', '2026-8-1', '2026-08-01T00:00:00Z', 20260801]) { expect(Dates.isoWeek(input), null); }
expect(Dates.fromKey('2025-W53'), null);expect(Dates.fromKey('2026-W54'), null);expect(Dates.fromKey('2026-W00'), null);expect(Dates.fromKey('2026-W1'), null);
expect(Dates.fromKey('2020-W53').start, '2020-12-28');expect(Dates.weeksInYear('2026').length, 53);expect(Dates.weeksInYear('2025').length, 52);expect(Dates.weeksInYear('not-a-year'), []);expect(Dates.weeksInYear('1000').every(Boolean), true);expect(Dates.weeksInYear('9999').every(Boolean), true);
expect(Dates.label('2026-W35'), '2026-W35 · 2026-08-24—2026-08-30');expect(Dates.label('undated'), '日期未精确到日');
const python = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const code = `import datetime as d,json
x=d.date(1990,1,1); end=d.date(2041,1,1); rows=[]
while x<end:
 y,w,day=x.isocalendar(); m=x-d.timedelta(days=day-1)
 rows.append([x.isoformat(),f'{y}-W{w:02}',m.isoformat(),(m+d.timedelta(days=6)).isoformat()]); x+=d.timedelta(days=1)
print(json.dumps(rows))`;
const result = spawnSync(python, ['-c', code], {encoding:'utf8',maxBuffer:10*1024*1024});
if (result.status !== 0) throw new Error(`Python ISO-calendar cross-check failed: ${result.error || result.stderr}`);
const rows=JSON.parse(result.stdout);for(const [date,key,start,end] of rows){const actual=Dates.isoWeek(date);expect([actual.key,actual.start,actual.end],[key,start,end]);expect(Dates.fromKey(key),actual);}
console.log(`PASS: ${cases} ISO calendar assertions, including ${rows.length} dates (1990–2040); no inferred dates for month-only metadata.`);
