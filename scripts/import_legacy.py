"""One-time, hash-verified import. Never overwrite a populated catalog."""
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = 'b853d96b0a85462be4bea4c0b7d942cd0b15723c'
SOURCE = f'https://raw.githubusercontent.com/invoidstar/invoidstar.github.io/{COMMIT}/vla-radar/'
MANIFEST = {
    'README.md': 'a8c036f80d38d58db39ff584b1a55ab0fde31fd0',
    'app.js': '92b8cef6411dcc9ad585a36c83717586fc58853e',
    'styles.css': '0e411ff7d31f63d5c7e35ecb9a6384893c56a9cf',
    'favicon.svg': 'b373ca9ea17fa2775432bab123ab78922dbee313',
    'index.html': 'd8310e9a156b1f1f2440be919f37c584964b4424',
    'data/papers.json': 'a2fd3e7008552e31302de735ff9d6f178231fa86',
    'validate.py': 'd38db6e03a26c059307dee7f654ece9b26be13e7',
}

def blob_sha(raw):
    return hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()

existing = [name for name in MANIFEST if (ROOT / name).exists()]
if len(existing) == len(MANIFEST):
    print('Catalog already exists; one-time import skipped without overwriting any files.')
    sys.exit(0)
if existing:
    raise SystemExit(f'Refusing partial import over existing paths: {existing}')

buffers = {}
for name, expected in MANIFEST.items():
    for attempt in range(3):
        try:
            request = urllib.request.Request(SOURCE + name, headers={'User-Agent': 'VLA-Radar-Migration/1.0'})
            with urllib.request.urlopen(request, timeout=45) as response:
                raw = response.read()
            break
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    if blob_sha(raw) != expected:
        raise SystemExit(f'Source integrity mismatch: {name}')
    buffers[name] = raw

catalog = json.loads(buffers['data/papers.json'])
if len(catalog['papers']) != 46 or len({p['id'] for p in catalog['papers']}) != 46:
    raise SystemExit('Unexpected source catalog size or duplicate stable IDs')

replacements = {
    'https://invoidstar.github.io/vla-radar/': 'https://invoidstar.github.io/VLA-Radar/',
    'https://github.com/invoidstar/invoidstar.github.io/tree/main/vla-radar': 'https://github.com/invoidstar/VLA-Radar/tree/main',
    'https://github.com/invoidstar/invoidstar.github.io/blob/main/vla-radar/': 'https://github.com/invoidstar/VLA-Radar/blob/main/',
    'https://github.com/invoidstar/invoidstar.github.io/edit/main/vla-radar/': 'https://github.com/invoidstar/VLA-Radar/edit/main/',
}
for name in ('README.md', 'index.html', 'app.js'):
    text = buffers[name].decode('utf-8')
    for old, new in replacements.items():
        text = text.replace(old, new)
    if name == 'README.md':
        text = text.replace('cd vla-radar', 'cd VLA-Radar').replace('vla-radar/\n', 'VLA-Radar/\n')
        text += '\n\n## 独立仓库与持续维护\n\n本站现在由 [invoidstar/VLA-Radar](https://github.com/invoidstar/VLA-Radar) 独立维护。\n\n- 维护人员和自动化先阅读 [AGENTS.md](AGENTS.md) 与 [MAINTENANCE.md](MAINTENANCE.md)。\n- 每周日早晨的文献维护任务由 ChatGPT 定时任务发起，运行依赖有效的连接与授权；GitHub Actions 负责数据校验与静态发布，不自行生成论文结论。\n- 新建仓库需在 Settings → Pages 中将 Source 设为 GitHub Actions，再运行 Validate and deploy VLA Radar。\n- 文献唯一数据源仍为 data/papers.json，检索检查点见 maintenance/state.json，修改记录见 CHANGELOG.md。\n- 初次维护回补 2026-09-01 起的成果；迁移本身没有执行这轮检索。\n- 原个人主页仓库不再用于存放或维护本文献库。\n'
    buffers[name] = text.encode('utf-8')

for name, raw in buffers.items():
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)

subprocess.run([sys.executable, str(ROOT / 'validate.py')], cwd=ROOT, check=True)
subprocess.run([sys.executable, str(ROOT / 'scripts/check_catalog.py')], cwd=ROOT, check=True)
subprocess.run(['node', '--check', str(ROOT / 'app.js')], check=True)
report = {
    'sourceRepository': 'invoidstar/invoidstar.github.io',
    'sourceCommit': COMMIT,
    'sourceDirectory': 'vla-radar',
    'importedAt': datetime.now(timezone.utc).isoformat(),
    'paperCount': 46,
    'paperDataByteIdentical': blob_sha(buffers['data/papers.json']) == MANIFEST['data/papers.json'],
    'files': {name: {'sourceBlob': expected, 'importedBlob': blob_sha(buffers[name])} for name, expected in MANIFEST.items()},
    'note': 'Only site/repository links and README maintenance instructions were adapted. No research claim or evidence grade was changed.',
}
(ROOT / 'maintenance/migration.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Imported and validated 46 records. Catalog bytes and stable reading IDs are unchanged.')
