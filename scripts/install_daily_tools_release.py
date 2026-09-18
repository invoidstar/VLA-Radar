"""One-use integration on the authorized release branch; removed before publication."""
from pathlib import Path
import base64, gzip, hashlib, json, os

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
if os.environ.get('GITHUB_REPOSITORY') != 'invoidstar/VLA-Radar' or os.environ.get('GITHUB_REF_NAME') != 'release/batch-2026-09-18-final-daily-tools':
    raise SystemExit('Wrong repository or release branch')
parts = []
part_hashes = ['d2f38c80d8441569409aa30b792277c1f3a27a8e1b1695e69c91f9d17b6f591d', '3a9b2fbb4353a97983915272dce413ecbc76eb523acbb0e97c555ed55e105a6a', '7fe6a743c9fd10c1d97fdc53486e9c9206a847773c77bfbaa4952b6112316fa7']
# Exact transport transcription repair, independently compared to the retained local payload.
# The complete compressed payload and every resulting source file are verified below.
repairs = [(802,804,'ky',''),(873,874,'C',''),(4597,4598,'q','n'),(4622,4623,'B',''),(4624,4624,'','T'),(4674,4675,'I','9O'),(4676,4678,'9u','')]
for i in range(3):
    text = Path(f'maintenance/daily-tools.part{i}').read_text(encoding='utf-8')
    assert hashlib.sha256(text.encode()).hexdigest() == part_hashes[i], f'Unexpected transport {i}'
    if i == 1:
        for start,end,old,new in reversed(repairs):
            assert text[start:end] == old
            text = text[:start] + new + text[end:]
    parts.append(text)
blob = base64.b64decode(''.join(parts), validate=True)
assert hashlib.sha256(blob).hexdigest() == 'ae82377c03400adb0bddb20f203e60f9922f07ef7d81e44d204959ae0483fa5e', 'Transport checksum mismatch'
payload = json.loads(gzip.decompress(blob))
assert payload['schemaVersion'] == 1
assert payload['baseCommit'] == '5d737f28d202ec0296c8b8984300b6823292c9a9'
new_allowed = {'tools-core.js','tools-loader.js','tools.js','tools.css','scripts/tools_build.py','scripts/test_tools.cjs','scripts/browser_tools.py','tests/test_tools.py','catalog/bibliography.json','maintenance/daily-tools.md'}
patch_allowed = {'index.html','app.js','experience-loader.js','experience.js','scripts/build_catalog.py','scripts/validate_all.py','styles.css','AGENTS.md','MAINTENANCE.md'}
assert set(payload['newFiles']) == new_allowed
assert {p['path'] for p in payload['patches']} == patch_allowed
outputs = {}
for path,content in payload['newFiles'].items():
    assert not Path(path).exists(), f'New path already exists: {path}'
    outputs[path] = content
for patch in payload['patches']:
    path = patch['path']
    text = Path(path).read_text(encoding='utf-8')
    assert hashlib.sha256(text.encode()).hexdigest() == patch['beforeSha256'], f'Changed base: {path}'
    for edit in sorted(patch['edits'], key=lambda e: e['start'], reverse=True):
        assert 0 <= edit['start'] <= edit['end'] <= len(text)
        text = text[:edit['start']] + edit['text'] + text[edit['end']:]
    assert hashlib.sha256(text.encode()).hexdigest() == patch['afterSha256'], f'Bad postimage: {path}'
    outputs[path] = text
# LIBERO is both a paper title and a benchmark; exercise the benchmark option,
# without assuming it must outrank the equally exact paper title.
p = 'scripts/browser_tools.py'
s = outputs[p]
assert hashlib.sha256(s.encode()).hexdigest() == 'ca52e03fc15252d4673458929f36cb5a451a04f838a9056a3690a2fd8d50c72c'
s = s.replace('  page.wait_for_function(\'document.querySelector("#command-results [role=option] small").textContent==="基准"\')', '  page.wait_for_function(\'Array.from(document.querySelectorAll("#command-results [role=option]")).some(e=>e.querySelector("small").textContent==="基准" && e.querySelector("strong").textContent==="LIBERO")\')\n  benchmark_option=page.locator(\'#command-results [role=option]\').evaluate_all(\'(els)=>els.findIndex(e=>e.querySelector("small").textContent==="基准" && e.querySelector("strong").textContent==="LIBERO")\')')
s = s.replace("  page.keyboard.press('ArrowUp');page.keyboard.press('Enter');page.wait_for_selector('#leaderboards-section:not(.hidden)')", "  page.keyboard.press('ArrowUp')\n  for _ in range(benchmark_option):page.keyboard.press('ArrowDown')\n  page.keyboard.press('Enter');page.wait_for_selector('#leaderboards-section:not(.hidden)')")
assert hashlib.sha256(s.encode()).hexdigest() == 'f95ce3be4ff5b9812b3e32897da8a0f75c3a0cd8d3d9edb6b64973ec564a8304'
outputs[p] = s
before = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('catalog').rglob('*') if p.is_file()}
audit = Path('/tmp/radar-tools-source'); audit.mkdir(parents=True, exist_ok=True)
(audit/'canonical-before.json').write_text(json.dumps(before, indent=2))
for path,text in outputs.items():
    dest = Path(path); dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(text, encoding='utf-8')
changelog = Path('CHANGELOG.md')
changelog.write_text('## 2026-09-18 — 高频工具收口与稳定维护\n\n加入本地 My Radar（论文、方向、基准、新闻分类关注）、Ctrl/Cmd+K 全局快捷搜索，以及 BibTeX/RIS/CSL-JSON/Markdown 单篇和批量导出。索引与工具按需加载，保留来源缺失提示、阅读状态和所有既有科学数据；不加入 RSS。此次功能收口后默认仅提高内容质量、覆盖率和稳定性，除非出现明确痛点或实际需求。\n\n' + changelog.read_text(encoding='utf-8'), encoding='utf-8')
(audit/'integration.json').write_text(json.dumps({'base':payload['baseCommit'],'files':{p:hashlib.sha256(t.encode()).hexdigest() for p,t in outputs.items()},'canonicalPreserved':len(before),'scope':'code integration only; no claim of browser or publication success'}, ensure_ascii=False, indent=2))
print('Integrated',len(outputs),'verified source files; original canonical files:',len(before))
