from __future__ import annotations
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha_tree(rel: str) -> str:
    base = ROOT / rel
    h = hashlib.sha256()
    for p in sorted(x for x in base.rglob('*') if x.is_file()):
        h.update(p.relative_to(ROOT).as_posix().encode())
        h.update(b'\0')
        h.update(p.read_bytes())
        h.update(b'\0')
    return h.hexdigest()

def move(old: str, new: str) -> None:
    src, dst = ROOT / old, ROOT / new
    if not src.exists():
        raise SystemExit(f'missing source for move: {old}')
    if dst.exists():
        raise SystemExit(f'target already exists: {new}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))

before_catalog = sha_tree('catalog')
before_data = sha_tree('data')

site_moves = {
    'index.html': 'site/index.html',
    'favicon.svg': 'site/favicon.svg',
    'styles.css': 'site/styles/base.css',
    'sidebar.css': 'site/styles/components/sidebar.css',
    'research.css': 'site/styles/features/research.css',
    'experience.css': 'site/styles/features/workspace.css',
    'news.css': 'site/styles/features/news.css',
    'tools.css': 'site/styles/features/tools.css',
    'app.js': 'site/js/app.js',
    'dates.js': 'site/js/core/dates.js',
    'runtime.js': 'site/js/core/runtime.js',
    'search-core.js': 'site/js/core/search/search-core.js',
    'search-client.js': 'site/js/core/search/search-client.js',
    'search-worker.js': 'site/js/core/search/search-worker.js',
    'sidebar.js': 'site/js/components/sidebar.js',
    'research.js': 'site/js/features/research/research.js',
    'experience-loader.js': 'site/js/features/workspace/experience-loader.js',
    'experience-core.js': 'site/js/features/workspace/experience-core.js',
    'experience.js': 'site/js/features/workspace/experience.js',
    'news-core.js': 'site/js/features/news/news-core.js',
    'news.js': 'site/js/features/news/news.js',
    'tools-loader.js': 'site/js/features/tools/tools-loader.js',
    'tools-core.js': 'site/js/features/tools/tools-core.js',
    'tools.js': 'site/js/features/tools/tools.js',
}
for old, new in site_moves.items():
    move(old, new)

script_groups = {
    'build': ['build_catalog.py','catalog_core.py','capture_activity.py','experience_build.py','news_core.py','tools_build.py'],
    'validation': ['check_catalog.py','check_editorial.py','check_performance.py','note_quality.py','validate_all.py'],
    'maintenance': ['check_sources.py','configure_main_protection.py','install_editorial_policy.py','maintenance_queue.py','repo_housekeeping.py','sync_publications.py'],
    'discovery': ['arxiv_metadata.py','discover_results.py','extract_results.py','http_public.py'],
    'migration': ['apply_content_batch.py','apply_library_completion.py','import_legacy.py','migrate_v2.py','recover_library.py','upgrade_batch_ui.py'],
}
script_moves = {}
for group, names in script_groups.items():
    for name in names:
        old = f'scripts/{name}'
        new = f'scripts/{group}/{name}'
        script_moves[old] = new
        move(old, new)

browser_names = ['browser_leaderboard.py','browser_news.py','browser_sidebar.py','browser_smoke.py','browser_tools.py','browser_workspace.py']
browser_moves = {}
for name in browser_names:
    old, new = f'scripts/{name}', f'tests/browser/{name}'
    browser_moves[old] = new
    move(old, new)

node_test_names = ['test_content.cjs','test_dates.cjs','test_experience.cjs','test_leaderboard_controls.cjs','test_news.cjs','test_performance.cjs','test_research.cjs','test_tools.cjs','test_urls.cjs']
node_moves = {}
for name in node_test_names:
    old, new = f'scripts/{name}', f'tests/unit/{name}'
    node_moves[old] = new
    move(old, new)

python_test_moves = {}
for p in sorted((ROOT/'tests').glob('test_*.py')):
    old = p.relative_to(ROOT).as_posix()
    new = f'tests/unit/{p.name}'
    python_test_moves[old] = new
    move(old, new)

maintenance_map = {}
policies = ['branch-policy.json','benchmark-content-policy.md','content-standard.md','editorial-policy.json','news-policy.md','publishing-policy.md']
live_state = ['applied-batches.json','benchmark-review.json','main-protection.json','news-candidates.json','news-source-hashes.json','news-state.json','publication-candidates.json','publishing-policy-applied.json','source-health.json','state.json','work-queue.json']
release_audits = ['final-branch-cleanup-20260920.json','final-consistency-audit-20260920.json','final-two-source-audit-20260920.json','library-completion.json','news-release-validation.json','note-review-audit-20260920-final8.json','publication-check.json','runtime-validation.json']
migration_audits = ['library-recovery.json','migration.json','runtime-upgrade.json','v2-github-validation.md','v2-migration.json','v2-online-attempt.json','v2-validation.md','workspace-install.json']
docs = ['daily-tools.md','github-delivery.md','landmarks-2026-09.md','leaderboard-analysis.md','operations.md','sidebar-resize.md','week-search.md','workspace.md']
for name in policies:
    maintenance_map[f'maintenance/{name}'] = f'maintenance/policies/{name}'
for name in live_state:
    maintenance_map[f'maintenance/{name}'] = f'maintenance/state/{name}'
for name in release_audits:
    maintenance_map[f'maintenance/{name}'] = f'maintenance/audits/release/{name}'
for name in migration_audits:
    maintenance_map[f'maintenance/{name}'] = f'maintenance/audits/migration/{name}'
for name in docs:
    maintenance_map[f'maintenance/{name}'] = f'maintenance/docs/{name}'
for p in sorted((ROOT/'maintenance').glob('benchmark-*.json')):
    if p.name == 'benchmark-review.json':
        continue
    maintenance_map[f'maintenance/{p.name}'] = f'maintenance/audits/benchmark/{p.name}'
maintenance_map['maintenance/batches'] = 'maintenance/state/batches'
maintenance_map['maintenance/deep-reading'] = 'maintenance/docs/deep-reading'
for old, new in sorted(maintenance_map.items(), key=lambda x: x[0].count('/'), reverse=True):
    if (ROOT/old).exists():
        move(old, new)

for p in ['scripts/__init__.py','scripts/build/__init__.py','scripts/validation/__init__.py','scripts/maintenance/__init__.py','scripts/discovery/__init__.py','scripts/migration/__init__.py','tests/__init__.py','tests/unit/__init__.py','tests/browser/__init__.py']:
    q = ROOT/p
    q.parent.mkdir(parents=True, exist_ok=True)
    if not q.exists():
        q.write_text('', encoding='utf-8')
(ROOT/'tests/fixtures').mkdir(parents=True, exist_ok=True)
(ROOT/'tests/fixtures/README.md').write_text('# Test fixtures\n\nReusable static fixtures belong here. Prefer small synthetic fixtures over unfinished production records.\n', encoding='utf-8')

public_asset = {
    'styles.css': 'styles/base.css',
    'sidebar.css': 'styles/components/sidebar.css',
    'research.css': 'styles/features/research.css',
    'experience.css': 'styles/features/workspace.css',
    'news.css': 'styles/features/news.css',
    'tools.css': 'styles/features/tools.css',
    'app.js': 'js/app.js',
    'dates.js': 'js/core/dates.js',
    'runtime.js': 'js/core/runtime.js',
    'search-core.js': 'js/core/search/search-core.js',
    'search-client.js': 'js/core/search/search-client.js',
    'search-worker.js': 'js/core/search/search-worker.js',
    'sidebar.js': 'js/components/sidebar.js',
    'research.js': 'js/features/research/research.js',
    'experience-loader.js': 'js/features/workspace/experience-loader.js',
    'experience-core.js': 'js/features/workspace/experience-core.js',
    'experience.js': 'js/features/workspace/experience.js',
    'news-core.js': 'js/features/news/news-core.js',
    'news.js': 'js/features/news/news.js',
    'tools-loader.js': 'js/features/tools/tools-loader.js',
    'tools-core.js': 'js/features/tools/tools-core.js',
    'tools.js': 'js/features/tools/tools.js',
}
index_path = ROOT/'site/index.html'
index = index_path.read_text(encoding='utf-8')
for old, new in public_asset.items():
    index = index.replace(f'href="{old}', f'href="{new}').replace(f'src="{old}', f'src="{new}')
nav_pattern = re.compile(r'<div class="side-heading">EXPLORE</div>\s*<nav class="nav-main">.*?</nav>\s*<div class="side-heading topic-heading">RESEARCH TOPICS</div>', re.S)
nav = '''<div class="side-heading">DISCOVER</div>
  <nav class="nav-main">
    <button class="nav-link active" data-view="papers"><span data-icon="library"></span>文献总览<span class="nav-count" id="nav-total">—</span></button>
    <button class="nav-link" data-view="topics"><span data-icon="grid"></span>研究方向</button>
    <button class="nav-link" data-view="timeline"><span data-icon="clock"></span>发表时间线</button>
    <button class="nav-link" data-view="news"><span data-icon="spark"></span>具身智能周报<span class="local-indicator">WEEKLY</span></button>
    <div class="side-heading workspace-heading">EVIDENCE</div>
    <button class="nav-link" data-view="leaderboards"><span data-icon="table"></span>评测榜单<span class="local-indicator">NEW</span></button>
    <button class="nav-link" data-view="coverage"><span data-icon="grid"></span>证据地图</button>
    <div class="side-heading workspace-heading">WORKSPACE</div>
    <button class="nav-link" data-view="compare"><span data-icon="table"></span>论文对比 <small id="compare-count"></small></button>
    <button class="nav-link" data-view="updates"><span data-icon="clock"></span>更新中心</button>
    <div class="side-heading workspace-heading">PERSONAL</div>
    <button class="nav-link" data-view="radar"><span data-icon="spark"></span>My Radar<span class="local-indicator">本地</span></button>
    <button class="nav-link" data-view="reading"><span data-icon="bookmark"></span>我的阅读<span class="local-indicator">本地</span></button>
  </nav>
  <div class="side-heading topic-heading">RESEARCH TOPICS</div>'''
index, n = nav_pattern.subn(nav, index, count=1)
if n != 1:
    raise SystemExit('failed to replace sidebar information architecture')
index_path.write_text(index, encoding='utf-8')

replacements = {
    ROOT/'site/js/core/search/search-client.js': {"new Worker('search-worker.js?v=maintenance-20260918')": "new Worker('js/core/search/search-worker.js?v=maintenance-20260918')"},
    ROOT/'site/js/core/search/search-worker.js': {"importScripts('dates.js','search-core.js');": "importScripts('../dates.js','search-core.js');"},
    ROOT/'site/js/features/workspace/experience-loader.js': {
        "script('experience-core.js?v=leaderboard-20260919')": "script('js/features/workspace/experience-core.js?v=leaderboard-20260919')",
        "script('experience.js?v=leaderboard-20260919')": "script('js/features/workspace/experience.js?v=leaderboard-20260919')",
        "l.href='news.css?v=news-20260918'": "l.href='styles/features/news.css?v=news-20260918'",
        "script('news-core.js?v=news-20260918')": "script('js/features/news/news-core.js?v=news-20260918')",
        "script('news.js?v=news-20260918')": "script('js/features/news/news.js?v=news-20260918')",
    },
    ROOT/'site/js/features/tools/tools-loader.js': {
        "s.href='tools.css?v=final-20260918'": "s.href='styles/features/tools.css?v=final-20260918'",
        "js('tools-core.js?v=final-20260918')": "js('js/features/tools/tools-core.js?v=final-20260918')",
        "js('tools.js?v=final-20260918')": "js('js/features/tools/tools.js?v=final-20260918')",
    },
}
for path, reps in replacements.items():
    text = path.read_text(encoding='utf-8')
    for old, new in reps.items():
        if old not in text:
            raise SystemExit(f'missing runtime reference {old} in {path}')
        text = text.replace(old, new)
    path.write_text(text, encoding='utf-8')

tools_js = ROOT/'site/js/features/tools/tools.js'
t = tools_js.read_text(encoding='utf-8')
old_nav = "const nav=[['radar','My Radar · 我的关注'],['papers','文献总览'],['reading','我的阅读'],['compare','论文对比'],['leaderboards','评测榜单'],['news','具身智能周报'],['updates','更新中心'],['coverage','证据地图']];"
new_nav = "const nav=[['papers','文献总览'],['news','具身智能周报'],['leaderboards','评测榜单'],['coverage','证据地图'],['compare','论文对比'],['updates','更新中心'],['radar','My Radar · 我的关注'],['reading','我的阅读']];"
if old_nav in t:
    t = t.replace(old_nav, new_nav)
tools_js.write_text(t, encoding='utf-8')

module_paths = {}
for old, new in script_moves.items():
    module_paths[Path(old).stem] = '.'.join(Path(new).with_suffix('').parts)
py_files = [p for p in ROOT.rglob('*.py') if '.git' not in p.parts and '.refactor' not in p.parts]
for p in py_files:
    text = p.read_text(encoding='utf-8')
    for mod, target in sorted(module_paths.items(), key=lambda x: -len(x[0])):
        text = re.sub(rf'(?m)^from\s+{re.escape(mod)}\s+import\s+', f'from {target} import ', text)
        text = re.sub(rf'(?m)^import\s+{re.escape(mod)}(\s+as\s+\w+)?\s*$', lambda m: f'import {target}{m.group(1) or ""}', text)
    p.write_text(text, encoding='utf-8')

moved_python = [ROOT/new for new in script_moves.values()] + [ROOT/new for new in browser_moves.values()] + [ROOT/new for new in python_test_moves.values()]
for p in moved_python:
    text = p.read_text(encoding='utf-8').replace("Path(__file__).resolve().parents[1]", "Path(__file__).resolve().parents[2]")
    p.write_text(text, encoding='utf-8')

bootstrap = """# Direct-file compatibility: add repository root before importing scripts packages.
if __package__ in (None, ''):
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))

"""
for p in [ROOT/new for new in script_moves.values()]:
    text = p.read_text(encoding='utf-8')
    if 'from scripts.' in text and 'Direct-file compatibility:' not in text:
        future = list(re.finditer(r'(?m)^from __future__ import .+$', text))
        if future:
            pos = future[-1].end()
            text = text[:pos] + '\n' + bootstrap + text[pos+1:]
        else:
            text = bootstrap + text
        p.write_text(text, encoding='utf-8')

validate = ROOT/'validate.py'
v = validate.read_text(encoding='utf-8')
v = re.sub(r"(?m)^sys\.path\.insert\(0,str\(Path\(__file__\)\.parent/'scripts'\)\)\n", '', v)
v = v.replace('from catalog_core import', 'from scripts.build.catalog_core import')
v = v.replace('from build_catalog import', 'from scripts.build.build_catalog import')
validate.write_text(v, encoding='utf-8')

validate_all = ROOT/'scripts/validation/validate_all.py'
validate_all.write_text("""\"\"\"One offline entry point used by local development and both PR/publish CI.\"\"\"
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
commands=[
 ['node','tests/unit/test_leaderboard_controls.cjs'],
 ['node','--check','site/js/features/tools/tools-loader.js'],
 ['node','--check','site/js/features/tools/tools-core.js'],
 ['node','--check','site/js/features/tools/tools.js'],
 ['node','tests/unit/test_tools.cjs'],
 ['node','--check','site/js/components/sidebar.js'],
 ['node','--check','site/js/features/news/news.js'],
 ['node','--check','site/js/features/news/news-core.js'],
 ['node','tests/unit/test_news.cjs'],
 [sys.executable,'validate.py'],
 [sys.executable,'scripts/validation/check_editorial.py'],
 [sys.executable,'scripts/validation/check_performance.py'],
 [sys.executable,'scripts/validation/check_catalog.py'],
 [sys.executable,'-m','unittest','discover','-s','tests/unit','-v'],
 ['node','--check','site/js/app.js'],
 ['node','--check','site/js/features/research/research.js'],
 ['node','--check','site/js/core/dates.js'],
 *(['node','--check',p] for p in ['site/js/core/runtime.js','site/js/core/search/search-core.js','site/js/core/search/search-client.js','site/js/core/search/search-worker.js']),
 ['node','tests/unit/test_dates.cjs'],
 ['node','tests/unit/test_urls.cjs'],
 ['node','tests/unit/test_research.cjs'],
 ['node','tests/unit/test_content.cjs'],
 ['node','tests/unit/test_performance.cjs'],
 ['node','tests/unit/test_experience.cjs'],
 *(['node','--check',p] for p in ['site/js/features/workspace/experience-loader.js','site/js/features/workspace/experience-core.js','site/js/features/workspace/experience.js'])
]
for command in commands:
    if command[0]=='node' and not (root/command[-1]).exists():
        raise SystemExit('Missing test: '+command[-1])
    subprocess.run(command,cwd=root,check=True)
print('PASS: all offline validation commands completed.')
""", encoding='utf-8')

for p in (ROOT/'tests/unit').glob('*.cjs'):
    text = p.read_text(encoding='utf-8')
    text = text.replace("path.join(__dirname,'..',", "path.join(__dirname,'..','..',")
    text = text.replace('path.join(__dirname,"..",', 'path.join(__dirname,"..","..",')
    text = text.replace("require('../", "require('../../")
    text = text.replace('require("../', 'require("../../')
    for old, new in site_moves.items():
        text = text.replace(f"../../{old}", f"../../{new}")
    p.write_text(text, encoding='utf-8')

for p in (ROOT/'tests/browser').glob('browser_*.py'):
    text = p.read_text(encoding='utf-8')
    if 'import tempfile,shutil' not in text:
        text = 'import tempfile,shutil\\n' + text
    token = 'Path(__file__).resolve().parents[2]'
    pos = text.find(token)
    if pos < 0:
        raise SystemExit(f'root marker missing in {p}')
    line_start = text.rfind('\\n', 0, pos) + 1
    line_end = text.find('\\n', pos)
    if line_end < 0:
        line_end = len(text)
    line = text[line_start:line_end]
    repo_var = 'ROOT' if re.search(r'\\bROOT\\s*=', line) else ('root' if re.search(r'\\broot\\s*=', line) else None)
    if repo_var is None:
        raise SystemExit(f'repository root variable missing in {p}: {line}')
    staging = (
        "\\npublic=Path(tempfile.mkdtemp(prefix='vla-radar-public-'))"
        + "\\nshutil.copytree(" + repo_var + "/'site',public,dirs_exist_ok=True)"
        + "\\nshutil.copytree(" + repo_var + "/'data',public/'data',dirs_exist_ok=True)"
    )
    text = text[:line_end] + staging + text[line_end:]
    text = re.sub(r'cwd\\s*=\\s*(root|ROOT)', 'cwd=public', text)
    p.write_text(text, encoding='utf-8')

path_map = {}
path_map.update(script_moves)
path_map.update(browser_moves)
path_map.update(node_moves)
path_map.update(python_test_moves)
path_map.update(maintenance_map)
active_roots = [ROOT/'README.md',ROOT/'MAINTENANCE.md',ROOT/'AGENTS.md',ROOT/'validate.py',ROOT/'.github',ROOT/'scripts',ROOT/'tests',ROOT/'maintenance/policies',ROOT/'maintenance/state',ROOT/'maintenance/docs',ROOT/'site']
active_files = []
for x in active_roots:
    if x.is_file():
        active_files.append(x)
    elif x.exists():
        active_files.extend(p for p in x.rglob('*') if p.is_file())
text_suffixes = {'.md','.py','.js','.cjs','.json','.yml','.yaml','.html','.css','.txt'}
for p in active_files:
    if p.suffix.lower() not in text_suffixes and p.name != 'AGENTS.md':
        continue
    try:
        text = p.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        continue
    old_text = text
    for old, new in sorted(path_map.items(), key=lambda x: -len(x[0])):
        text = text.replace(old, new)
        old_parts, new_parts = old.split('/'), new.split('/')
        for q in ("'", '"'):
            text = text.replace('/'.join(q+x+q for x in old_parts), '/'.join(q+x+q for x in new_parts))
            text = text.replace(','.join(q+x+q for x in old_parts), ','.join(q+x+q for x in new_parts))
    if text != old_text:
        p.write_text(text, encoding='utf-8')

for p in [ROOT/'README.md',ROOT/'MAINTENANCE.md',ROOT/'AGENTS.md']:
    text = p.read_text(encoding='utf-8')
    for old, new in site_moves.items():
        text = text.replace(old, new)
    p.write_text(text, encoding='utf-8')

wf = ROOT/'.github/workflows/site.yml'
w = wf.read_text(encoding='utf-8')
w = w.replace('python scripts/validate_all.py', 'python scripts/validation/validate_all.py')
for name in browser_names:
    w = w.replace(f'python scripts/{name}', f'python tests/browser/{name}')
w = re.sub(r"mkdir -p _site/data\n\s+cp .*?_site/\n\s+cp -R data/\. _site/data/", "mkdir -p _site/data\n          cp -R site/. _site/\n          cp -R data/. _site/data/", w, count=1)
if 'cp -R site/. _site/' not in w:
    raise SystemExit('failed to update Pages staging')
wf.write_text(w, encoding='utf-8')

readme = ROOT/'README.md'
r = readme.read_text(encoding='utf-8')
anchor = '## Maintain\n'
architecture = '''## Repository architecture

The repository is organized by responsibility rather than by feature files at the root:

- site/ — static website source, split into core, components and feature modules.
- catalog/ — canonical public research records; this remains the only hand-edited content source.
- data/ — deterministic generated public artifacts; do not edit by hand.
- scripts/ — build, validation, discovery, maintenance and migration tooling.
- tests/ — unit and browser regression suites plus reusable fixtures.
- maintenance/ — live state, policies, documentation and immutable historical audits.

This layout is structural only: paper IDs, result IDs, benchmark protocols, page routes and local-reading semantics are unchanged.

'''
if architecture not in r:
    r = r.replace(anchor, architecture + anchor, 1)
readme.write_text(r, encoding='utf-8')

maint = ROOT/'MAINTENANCE.md'
m = maint.read_text(encoding='utf-8')
if '## Repository layout' not in m:
    m += '\n\n## Repository layout\n\nRuntime source lives in site/; canonical research content stays in catalog/; generated exports stay in data/. Tooling is grouped under scripts/{build,validation,discovery,maintenance,migration} and tests under tests/{unit,browser,fixtures}. Maintenance records are separated into maintenance/{state,policies,docs,audits}. Historical audit bodies are preserved as snapshots even when their recorded paths predate this layout.\n'
maint.write_text(m, encoding='utf-8')

changelog = ROOT/'CHANGELOG.md'
c = changelog.read_text(encoding='utf-8')
entry = '\n## 2026-09-20 — Repository architecture cleanup\n\n- Grouped static website source under site/ with core, component and feature boundaries; public page routes and query parameters are unchanged.\n- Grouped Python tooling by build, validation, discovery, maintenance and migration responsibility; moved browser and unit checks under tests/.\n- Split maintenance material into live state, policies, docs and historical audits without changing canonical catalog/data semantics.\n- Reorganized sidebar information architecture into Discover, Evidence, Workspace and Personal groups while preserving every existing view.\n\n'
if entry not in c:
    first_nl = c.find('\n')
    c = c[:first_nl+1] + entry + c[first_nl+1:]
changelog.write_text(c, encoding='utf-8')

audit = {
    'schemaVersion': 1,
    'date': '2026-09-20',
    'baseMainSha': '60b442c10d25591e3aa74308d599b98e258f83ac',
    'scope': 'repository architecture cleanup; no canonical research-data or route semantic changes',
    'moves': {'siteFiles':len(site_moves),'scriptFiles':len(script_moves),'browserTests':len(browser_moves),'nodeUnitTests':len(node_moves),'pythonUnitTests':len(python_test_moves),'maintenanceEntries':len(maintenance_map)},
    'invariants': {'catalogSha256Before':before_catalog,'catalogSha256After':sha_tree('catalog'),'dataSha256Before':before_data,'dataSha256After':sha_tree('data'),'publicRoutesChanged':False,'benchmarkProtocolSemanticsChanged':False},
    'informationArchitecture': ['DISCOVER','EVIDENCE','WORKSPACE','PERSONAL'],
}
audit_path = ROOT/'maintenance/audits/release/repository-architecture-20260920.json'
audit_path.parent.mkdir(parents=True, exist_ok=True)
audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
if audit['invariants']['catalogSha256Before'] != audit['invariants']['catalogSha256After']:
    raise SystemExit('catalog changed during structural refactor')
if audit['invariants']['dataSha256Before'] != audit['invariants']['dataSha256After']:
    raise SystemExit('generated data changed during structural refactor')
for old in list(site_moves)+list(script_moves)+list(browser_moves)+list(node_moves):
    if (ROOT/old).exists():
        raise SystemExit(f'flat file remains: {old}')
print('PASS structural refactor staged')
print(json.dumps(audit, ensure_ascii=False, indent=2))
