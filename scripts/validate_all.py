"""One offline entry point used by local development and both PR/publish CI."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
commands=[['node','--check','news.js'],['node','--check','news-core.js'],['node','scripts/test_news.cjs'],[sys.executable,'validate.py'],[sys.executable,'scripts/check_editorial.py'],[sys.executable,'scripts/check_performance.py'],[sys.executable,'scripts/check_catalog.py'],[sys.executable,'-m','unittest','discover','-s','tests','-v'],['node','--check','app.js'],['node','--check','research.js'],['node','--check','dates.js'],*([ 'node','--check',p] for p in ['runtime.js','search-core.js','search-client.js','search-worker.js']),['node','scripts/test_dates.cjs'],['node','scripts/test_urls.cjs'],['node','scripts/test_research.cjs'],['node','scripts/test_content.cjs'],['node','scripts/test_performance.cjs'],['node','scripts/test_experience.cjs'],*(['node','--check',p] for p in ['experience-loader.js','experience-core.js','experience.js'])]
for command in commands:
    if command[0]=='node' and not (root/command[-1]).exists():raise SystemExit('Missing test: '+command[-1])
    subprocess.run(command,cwd=root,check=True)
print('PASS: all offline validation commands completed.')
