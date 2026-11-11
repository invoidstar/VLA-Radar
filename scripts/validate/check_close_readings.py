"""Validate optional VLA Radar public close readings and their static integration."""
from pathlib import Path
import sys,re
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/build'))
from close_readings import validate
idx,ids=validate(ROOT)
entry=(ROOT/'site/index.html').read_text(encoding='utf-8')
app=(ROOT/'site/js/features/library/app.js').read_text(encoding='utf-8')
stage=(ROOT/'scripts/build/stage_site.py').read_text(encoding='utf-8')
if 'close-reading/' not in entry or '论文精读' not in entry:raise ValueError('missing close reading main navigation')
if 'close-reading/p148/' not in app:raise ValueError('missing paper detail reading link')
for resource in ['site/close-reading/index.html','site/close-reading/p148/index.html','site/close-reading/reader.js','site/close-reading/reading.css','site/close-reading/list.js']:
    if not (ROOT/resource).is_file():raise ValueError('missing reader asset '+resource)
for name in ['close-reading/index.html','close-reading/p148/index.html','close-reading/reader.js','close-reading/reading.css','close-reading/list.js']:
    if name not in stage:raise ValueError('reader not staged '+name)
if 'reading.v1' in (ROOT/'site/close-reading/reader.js').read_text(encoding='utf-8'):raise ValueError('do not reuse existing private reading-state key')
if 'close-reading.v1' not in (ROOT/'site/close-reading/reader.js').read_text(encoding='utf-8'):raise ValueError('reader state key missing')
if not (ROOT/'data/close-readings/p148.json').is_file():raise ValueError('generated data missing')
print('PASS close reading index, license modes, evidence links, reader assets and static Pages integration:',len(ids),'papers')
