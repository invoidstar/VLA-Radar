"""One-time transport of the locally tested public V2 implementation.

This script cannot write workflow files or update Git refs. The calling workflow
is restricted to the named feature branch. The payload is UTF-8 source text,
not executable pickles; only allowlisted paths are materialized.
"""
import base64
import hashlib
import json
import lzma
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BRANCH = 'feature/lifecycle-notes-leaderboards-2026-09-17'
PAYLOAD_SHA = '7b24213ce726b696e3a1be0e3fefce00381994e595abfdb887afffa76410420c'
BASELINE_SHA = '937c08ee9ad429fcc8b247e3c66c44fbc6267edd108a5951406860946a9ab531'
ALLOWED = {
    'research.css', 'README.md', 'MAINTENANCE.md', 'AGENTS.md', '.gitignore',
    'validate.py', '.gitattributes', 'research.js',
    'maintenance/work-queue.json', 'maintenance/v2-migration.json',
    'maintenance/v2-validation.md', 'tests/test_catalog.py',
    'scripts/catalog_core.py', 'scripts/maintenance_queue.py',
    'scripts/http_public.py', 'scripts/build_catalog.py',
    'scripts/sync_publications.py', 'scripts/test_urls.cjs',
    'scripts/discover_results.py', 'scripts/extract_results.py',
    'scripts/test_dates.cjs', 'scripts/validate_all.py',
    'scripts/check_catalog.py', 'scripts/check_sources.py',
    'scripts/test_research.cjs', 'scripts/migrate_v2.py',
    '.v2-site.patch', '.v2-changelog.md',
}

def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)

def main():
    if os.environ.get('GITHUB_REPOSITORY') != 'invoidstar/VLA-Radar':
        raise SystemExit('This one-time bootstrap is restricted to the public VLA-Radar repository.')
    if os.environ.get('GITHUB_REF') != 'refs/heads/' + BRANCH:
        raise SystemExit('Refusing to run outside the authorized feature branch.')
    if (ROOT / 'catalog/manifest.json').exists():
        raise SystemExit('Canonical catalog already exists; migration must not run twice.')
    original = (ROOT / 'data/papers.json').read_bytes()
    if hashlib.sha256(original).hexdigest() != BASELINE_SHA:
        raise SystemExit('Baseline catalog changed; review and regenerate instead of overwriting.')
    payload = base64.b64decode(''.join((ROOT / f'_v2/part-{i}.txt').read_text().strip() for i in range(1, 5)), validate=True)
    if hashlib.sha256(payload).hexdigest() != PAYLOAD_SHA:
        raise SystemExit('Payload checksum mismatch; no source files written.')
    files = json.loads(lzma.decompress(payload))
    if set(files) != ALLOWED or not all(isinstance(v, str) for v in files.values()):
        raise SystemExit('Unexpected source paths or data types.')
    for path, content in files.items():
        target = ROOT / path
        if target.is_symlink() or not target.resolve().is_relative_to(ROOT):
            raise SystemExit('Unsafe source path: ' + path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
    run('git', 'apply', '--check', '.v2-site.patch')
    run('git', 'apply', '.v2-site.patch')
    changelog = ROOT / 'CHANGELOG.md'
    old = changelog.read_text(encoding='utf-8')
    section = (ROOT / '.v2-changelog.md').read_text(encoding='utf-8')
    changelog.write_text(section + '\n' + old, encoding='utf-8')
    run(sys.executable, 'scripts/migrate_v2.py')
    run(sys.executable, 'scripts/build_catalog.py')
    run(sys.executable, 'scripts/validate_all.py')
    (ROOT / '.v2-site.patch').unlink()
    (ROOT / '.v2-changelog.md').unlink()
    print('Verified V2 sources materialized; original changelog retained. No Git refs changed.')

if __name__ == '__main__':
    main()
