"""One offline entry point used by local development and both PR/publish CI."""
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
commands=[['node','tests/node/test_leaderboard_controls.cjs'],['node','tests/node/test_benchmark_settings.cjs'],['node','--check','site/js/features/research/benchmark-settings.js'],['node','--check','site/js/features/tools/tools-loader.js'],['node','--check','site/js/features/tools/tools-core.js'],['node','--check','site/js/features/tools/tools.js'],['node','tests/node/test_tools.cjs'],['node','--check','site/js/components/sidebar.js'],['node','--check','site/js/features/news/news.js'],['node','--check','site/js/features/news/news-core.js'],['node','tests/node/test_news.cjs'],[sys.executable,'scripts/validate/validate_schema.py'],[sys.executable,'scripts/validate/check_editorial.py'],[sys.executable,'scripts/validate/check_performance.py'],[sys.executable,'scripts/validate/check_catalog.py'],[sys.executable,'-m','unittest','discover','-s','tests','-v'],['node','--check','site/js/features/library/app.js'],['node','--check','site/js/features/research/research.js'],['node','--check','site/js/core/dates.js'],*([ 'node','--check',p] for p in ['site/js/core/runtime.js','site/js/core/math.js','site/js/core/search-core.js','site/js/core/search-client.js','site/js/core/search-worker.js']),['node','tests/node/test_math.cjs'],['node','tests/node/test_dates.cjs'],['node','tests/node/test_urls.cjs'],['node','tests/node/test_research.cjs'],['node','tests/node/test_content.cjs'],['node','tests/node/test_performance.cjs'],['node','tests/node/test_experience.cjs'],*(['node','--check',p] for p in ['site/js/features/experience/experience-loader.js','site/js/features/experience/experience-core.js','site/js/features/experience/experience.js'])]
for command in commands:
    if command[0]=='node' and not (root/command[-1]).exists():raise SystemExit('Missing test: '+command[-1])
    subprocess.run(command,cwd=root,check=True)
print('PASS: all offline validation commands completed.')
