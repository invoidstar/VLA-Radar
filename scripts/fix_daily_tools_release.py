"""One-use exact-hash regression adjustment; removed before PR."""
from pathlib import Path
import hashlib,json,os
assert os.environ.get('GITHUB_REPOSITORY') == 'invoidstar/VLA-Radar'
assert os.environ.get('GITHUB_REF_NAME') == 'release/batch-2026-09-18-final-daily-tools'
p=Path('scripts/browser_tools.py');s=p.read_text(encoding='utf-8')
assert hashlib.sha256(s.encode()).hexdigest() == 'f95ce3be4ff5b9812b3e32897da8a0f75c3a0cd8d3d9edb6b64973ec564a8304'
assert s.count("page.locator('[data-reader-export]').click()") == 1
s=s.replace("page.locator('[data-reader-export]').click()", "page.locator('[data-reader-export]').first.click()")
assert hashlib.sha256(s.encode()).hexdigest() == '6ba4ec462ca10dfe85ac7b15ff0169051c26db067c230b818868fa2aa3949e13'
p.write_text(s,encoding='utf-8')
a=Path('/tmp/radar-tools-source/integration.json');report=json.loads(a.read_text());report['files'][str(p)]=hashlib.sha256(s.encode()).hexdigest();a.write_text(json.dumps(report,ensure_ascii=False,indent=2))
