"""One offline entry point used by local development and both PR/publish CI."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
commands=[[sys.executable,'validate.py'],[sys.executable,'scripts/check_editorial.py'],[sys.executable,'scripts/check_catalog.py'],[sys.executable,'-m','unittest','discover','-s','tests','-v'],['node','--check','app.js'],['node','--check','research.js'],['node','--check','dates.js'],['node','scripts/test_dates.cjs'],['node','scripts/test_urls.cjs'],['node','scripts/test_research.cjs'],['node','scripts/test_content.cjs']]
for command in commands:
    if command[0]=='node' and not (root/command[-1]).exists():raise SystemExit('Missing test: '+command[-1])
    subprocess.run(command,cwd=root,check=True)
print('PASS: all offline validation commands completed.')
