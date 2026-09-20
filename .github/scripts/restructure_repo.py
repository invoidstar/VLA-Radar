from pathlib import Path
import json, re, shutil

R=Path('.')

def move(src,dst):
    src=R/src; dst=R/dst
    if not src.exists(): return
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists(): raise RuntimeError(f'destination exists: {dst}')
    src.rename(dst)

# Public website source: source hierarchy only; public URLs remain staged at Pages root.
frontend={
  'index.html':'site/index.html',
  'favicon.svg':'site/favicon.svg',
  'styles.css':'site/styles/base.css',
  'sidebar.css':'site/styles/components/sidebar.css',
  'research.css':'site/styles/features/research.css',
  'experience.css':'site/styles/features/experience.css',
  'news.css':'site/styles/features/news.css',
  'tools.css':'site/styles/features/tools.css',
  'runtime.js':'site/js/core/runtime.js',
  'dates.js':'site/js/core/dates.js',
  'search-core.js':'site/js/core/search-core.js',
  'search-client.js':'site/js/core/search-client.js',
  'search-worker.js':'site/js/core/search-worker.js',
  'sidebar.js':'site/js/components/sidebar.js',
  'app.js':'site/js/features/library/app.js',
  'research.js':'site/js/features/research/research.js',
  'experience-core.js':'site/js/features/experience/experience-core.js',
  'experience-loader.js':'site/js/features/experience/experience-loader.js',
  'experience.js':'site/js/features/experience/experience.js',
  'news-core.js':'site/js/features/news/news-core.js',
  'news.js':'site/js/features/news/news.js',
  'tools-core.js':'site/js/features/tools/tools-core.js',
  'tools-loader.js':'site/js/features/tools/tools-loader.js',
  'tools.js':'site/js/features/tools/tools.js',
}
for a,b in frontend.items(): move(a,b)
if (R/'.nojekyll').exists(): (R/'.nojekyll').unlink()

# Tooling by responsibility.
groups={
  'build':['build_catalog.py','catalog_core.py','experience_build.py','news_core.py','tools_build.py'],
  'validate':['check_catalog.py','check_editorial.py','check_performance.py','validate_all.py'],
  'browser':['browser_leaderboard.py','browser_news.py','browser_sidebar.py','browser_smoke.py','browser_tools.py','browser_workspace.py'],
  'maintenance':['capture_activity.py','check_sources.py','configure_main_protection.py','maintenance_queue.py','repo_housekeeping.py','sync_publications.py'],
  'discovery':['arxiv_metadata.py','discover_results.py','extract_results.py','http_public.py','note_quality.py'],
  'migrations':['apply_content_batch.py','apply_library_completion.py','import_legacy.py','install_editorial_policy.py','migrate_v2.py','recover_library.py','upgrade_batch_ui.py'],
}
script_map={}
for group,names in groups.items():
    for name in names:
        old=f'scripts/{name}'; new=f'scripts/{group}/{name}'
        script_map[old]=new; move(old,new)
move('validate.py','scripts/validate/validate_schema.py')
script_map['validate.py']='scripts/validate/validate_schema.py'

# JS/Node tests belong with tests, not operational scripts.
node_tests=['test_content.cjs','test_dates.cjs','test_experience.cjs','test_leaderboard_controls.cjs','test_news.cjs','test_performance.cjs','test_research.cjs','test_tools.cjs','test_urls.cjs']
for name in node_tests:
    old=f'scripts/{name}';new=f'tests/node/{name}';script_map[old]=new;move(old,new)

# Maintenance taxonomy.
policies=['benchmark-content-policy.md','branch-policy.json','content-standard.md','editorial-policy.json','main-protection.json','news-policy.md','publishing-policy-applied.json','publishing-policy.md']
states=['applied-batches.json','benchmark-review.json','news-candidates.json','news-source-hashes.json','news-state.json','publication-candidates.json','publication-check.json','source-health.json','state.json','work-queue.json']
docs=['daily-tools.md','github-delivery.md','landmarks-2026-09.md','leaderboard-analysis.md','operations.md','sidebar-resize.md','week-search.md','workspace.md']
migration_audits=['library-completion.json','library-recovery.json','migration.json','runtime-upgrade.json','v2-migration.json','v2-online-attempt.json','workspace-install.json','v2-github-validation.md','v2-validation.md']
release_audits=['final-branch-cleanup-20260920.json','final-consistency-audit-20260920.json','news-release-validation.json','runtime-validation.json']
editorial_audits=['final-two-source-audit-20260920.json','note-review-audit-20260920-final8.json']
discovery_audits=['news-search-2026-09-18.json']
maint_map={}
def mmove(name,dst_dir):
    old=f'maintenance/{name}';new=f'maintenance/{dst_dir}/{name}'
    maint_map[old]=new;move(old,new)
for n in policies:mmove(n,'policies')
for n in states:mmove(n,'state')
for n in docs:mmove(n,'docs')
for n in migration_audits:mmove(n,'audits/migrations')
for n in release_audits:mmove(n,'audits/release')
for n in editorial_audits:mmove(n,'audits/editorial')
for n in discovery_audits:mmove(n,'audits/discovery')
for p in sorted((R/'maintenance').glob('benchmark-source-audit*.json')):
    mmove(p.name,'audits/benchmark')
if (R/'maintenance/benchmark-audit-invariance.json').exists():mmove('benchmark-audit-invariance.json','audits/benchmark')
if (R/'maintenance/batches').exists():
    maint_map['maintenance/batches/']='maintenance/audits/batches/'
    move('maintenance/batches','maintenance/audits/batches')
if (R/'maintenance/deep-reading').exists():
    maint_map['maintenance/deep-reading/']='maintenance/audits/deep-reading/'
    move('maintenance/deep-reading','maintenance/audits/deep-reading')

# Three completed one-shot workflows are historical machinery, not current operations.
for p in ['.github/workflows/complete-library.yml','.github/workflows/import-site.yml','.github/workflows/recover-library.yml']:
    q=R/p
    if q.exists():q.unlink()

# Update path references everywhere except canonical and generated data, which must be byte-identical.
replacements={}
replacements.update(script_map);replacements.update(maint_map)
text_ext={'.py','.cjs','.js','.css','.html','.md','.json','.yml','.yaml','.txt'}
for p in R.rglob('*'):
    if not p.is_file() or p.suffix not in text_ext: continue
    rel=p.as_posix()
    if rel.startswith('catalog/') or rel.startswith('data/'): continue
    s=p.read_text(encoding='utf-8')
    old=s
    for a,b in sorted(replacements.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
    if s!=old:p.write_text(s,encoding='utf-8')

# Site paths are relative to the staged public root.
index=R/'site/index.html';s=index.read_text()
for a,b in {
  'styles.css':'styles/base.css',
  'sidebar.css':'styles/components/sidebar.css',
  'sidebar.js':'js/components/sidebar.js',
  'tools-loader.js':'js/features/tools/tools-loader.js',
  'runtime.js':'js/core/runtime.js',
  'search-core.js':'js/core/search-core.js',
  'search-client.js':'js/core/search-client.js',
  'dates.js':'js/core/dates.js',
  'research.css':'styles/features/research.css',
  'experience.css':'styles/features/experience.css',
  'experience-loader.js':'js/features/experience/experience-loader.js',
  'research.js':'js/features/research/research.js',
  'app.js':'js/features/library/app.js',
}.items():s=s.replace(a,b)
index.write_text(s)

p=R/'site/js/features/experience/experience-loader.js';s=p.read_text()
for a,b in {
  "'experience-core.js":"'js/features/experience/experience-core.js",
  "'experience.js":"'js/features/experience/experience.js",
  "'news.css":"'styles/features/news.css",
  "'news-core.js":"'js/features/news/news-core.js",
  "'news.js":"'js/features/news/news.js",
}.items():s=s.replace(a,b)
p.write_text(s)

p=R/'site/js/features/tools/tools-loader.js';s=p.read_text()
for a,b in {
  "'tools.css":"'styles/features/tools.css",
  "'tools-core.js":"'js/features/tools/tools-core.js",
  "'tools.js":"'js/features/tools/tools.js",
}.items():s=s.replace(a,b)
p.write_text(s)

p=R/'site/js/features/tools/tools.js';s=p.read_text().replace("'experience-core.js","'js/features/experience/experience-core.js");p.write_text(s)
p=R/'site/js/core/search-client.js';s=p.read_text().replace("new Worker('search-worker.js","new Worker('js/core/search-worker.js");p.write_text(s)
p=R/'site/js/features/research/research.js';s=p.read_text().replace("require('./runtime.js')","require('../../core/runtime.js')");p.write_text(s)
p=R/'site/js/features/library/app.js';s=p.read_text().replace('本地打开请运行 python -m http.server，或使用离线预览文件。','本地预览请先运行 python scripts/build/stage_site.py --output _site，再从 _site 启动 HTTP server。');p.write_text(s)

# Python subdirectories still share a small internal module namespace; inject sibling tool dirs.
bootstrap="""import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
"""
def insert_bootstrap(s):
    if '_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]' in s:return s
    lines=s.splitlines(True);i=0
    if lines and lines[0].startswith('#!'):i=1
    if i<len(lines) and lines[i].lstrip().startswith(('"""',"'''")):
        quote='"""' if '"""' in lines[i] else "'''"
        if lines[i].count(quote)>=2:i+=1
        else:
            i+=1
            while i<len(lines):
                if quote in lines[i]:i+=1;break
                i+=1
    while i<len(lines) and lines[i].startswith('from __future__ import '):i+=1
    lines.insert(i,bootstrap)
    return ''.join(lines)
for p in R.glob('scripts/*/*.py'):
    if p.name=='stage_site.py':continue
    s=p.read_text()
    s=s.replace('Path(__file__).resolve().parents[1]','Path(__file__).resolve().parents[2]')
    s=s.replace("sys.path.insert(0,str(Path(__file__).parent/'scripts'))\n",'')
    if p.name=='validate_schema.py':
        s=s.replace('root=Path(__file__).parent','root=Path(__file__).resolve().parents[2]')
    p.write_text(insert_bootstrap(s))

# Node tests now live under tests/node.
node_refs={
  "../dates.js":"../../site/js/core/dates.js",
  "../runtime.js":"../../site/js/core/runtime.js",
  "../search-core.js":"../../site/js/core/search-core.js",
  "../research.js":"../../site/js/features/research/research.js",
  "../experience-core.js":"../../site/js/features/experience/experience-core.js",
  "../news-core.js":"../../site/js/features/news/news-core.js",
  "../tools-core.js":"../../site/js/features/tools/tools-core.js",
  "../app.js":"../../site/js/features/library/app.js",
  "'app.js'":"'site/js/features/library/app.js'",
  "'index.html'":"'site/index.html'",
  "'tools-loader.js'":"'site/js/features/tools/tools-loader.js'",
  "'tools.js'":"'site/js/features/tools/tools.js'",
  "'tools.css'":"'site/styles/features/tools.css'",
  "'experience-loader.js'":"'site/js/features/experience/experience-loader.js'",
  "'experience.js'":"'site/js/features/experience/experience.js'",
  "'experience.css'":"'site/styles/features/experience.css'",
}
for p in (R/'tests/node').glob('*.cjs'):
    s=p.read_text()
    for a,b in node_refs.items():s=s.replace(a,b)
    p.write_text(s)

# validate_all references the new JS and test locations.
p=R/'scripts/validate/validate_all.py';s=p.read_text()
asset_map={
  "'tools-loader.js'":"'site/js/features/tools/tools-loader.js'",
  "'tools-core.js'":"'site/js/features/tools/tools-core.js'",
  "'tools.js'":"'site/js/features/tools/tools.js'",
  "'sidebar.js'":"'site/js/components/sidebar.js'",
  "'news.js'":"'site/js/features/news/news.js'",
  "'news-core.js'":"'site/js/features/news/news-core.js'",
  "'app.js'":"'site/js/features/library/app.js'",
  "'research.js'":"'site/js/features/research/research.js'",
  "'dates.js'":"'site/js/core/dates.js'",
  "'runtime.js'":"'site/js/core/runtime.js'",
  "'search-core.js'":"'site/js/core/search-core.js'",
  "'search-client.js'":"'site/js/core/search-client.js'",
  "'search-worker.js'":"'site/js/core/search-worker.js'",
  "'experience-loader.js'":"'site/js/features/experience/experience-loader.js'",
  "'experience-core.js'":"'site/js/features/experience/experience-core.js'",
  "'experience.js'":"'site/js/features/experience/experience.js'",
}
for a,b in asset_map.items():s=s.replace(a,b)
p.write_text(s)

# Browser tests serve an assembled public root instead of the repository root.
for p in (R/'scripts/browser').glob('browser_*.py'):
    s=p.read_text()
    if 'PUBLIC_ROOT=Path(' not in s:
        marker='ROOT=Path(__file__).resolve().parents[2]'
        marker2='ROOT = Path(__file__).resolve().parents[2]'
        low='root=Path(__file__).resolve().parents[2]'
        if marker in s:
            s=s.replace(marker,marker+"\nPUBLIC_ROOT=Path('/tmp/vla-radar-public')\nsubprocess.run(['python',str(ROOT/'scripts/build/stage_site.py'),'--output',str(PUBLIC_ROOT)],check=True)",1)
        elif marker2 in s:
            s=s.replace(marker2,marker2+"\nPUBLIC_ROOT = Path('/tmp/vla-radar-public')\nsubprocess.run(['python', str(ROOT/'scripts/build/stage_site.py'), '--output', str(PUBLIC_ROOT)], check=True)",1)
        elif low in s:
            s=s.replace(low,low+"\nPUBLIC_ROOT=Path('/tmp/vla-radar-public')\nsubprocess.run(['python',str(root/'scripts/build/stage_site.py'),'--output',str(PUBLIC_ROOT)],check=True)",1)
        else: raise RuntimeError(f'No ROOT marker in {p}')
    s=s.replace('cwd=ROOT','cwd=PUBLIC_ROOT').replace('cwd = ROOT','cwd = PUBLIC_ROOT').replace('cwd=root','cwd=PUBLIC_ROOT')
    p.write_text(s)

# Deterministic site staging shared by browser tests and Pages.
stage=R/'scripts/build/stage_site.py'
stage.write_text("""from __future__ import annotations
import argparse, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def stage(output:Path)->Path:
    output=output if output.is_absolute() else ROOT/output
    source=ROOT/'site'
    if output.resolve() in {source.resolve(),(ROOT/'data').resolve()}:raise ValueError('refusing destructive output path')
    if output.exists():shutil.rmtree(output)
    shutil.copytree(source,output)
    shutil.copytree(ROOT/'data',output/'data')
    (output/'.nojekyll').touch()
    return output

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=Path('_site'));a=ap.parse_args()
    print(stage(a.output))
""")

# Current operational workflows.
p=R/'.github/workflows/site.yml';s=p.read_text()
pattern=r"      - name: Stage public website only\n        if: github\.event_name != 'pull_request'\n        run: \|\n.*?(?=      - uses: actions/upload-pages-artifact@v3)"
new="""      - name: Stage public website only
        if: github.event_name != 'pull_request'
        run: python scripts/build/stage_site.py --output _site
"""
s,count=re.subn(pattern,new,s,count=1,flags=re.S)
if count!=1:raise RuntimeError('site staging block changed unexpectedly')
p.write_text(s)

# Human-facing structure documentation.
(R/'site/README.md').write_text("""# Site source

This directory contains the human-authored static website source. GitHub Pages does not publish this directory directly: `scripts/build/stage_site.py` combines `site/` with generated `data/` into a disposable public root. Public routes therefore remain unchanged.
""")
(R/'scripts/README.md').write_text("""# Tooling layout

- `build/`: deterministic catalog/data generation and public-site staging
- `validate/`: schema, editorial, catalog and performance validation
- `browser/`: Playwright HTTP regressions against a staged public root
- `maintenance/`: recurring publication, source-health and repository maintenance
- `discovery/`: bounded public-source/result discovery helpers
- `migrations/`: historical/import/batch migration utilities

Run commands from the repository root.
""")
(R/'maintenance/README.md').write_text("""# Maintenance layout

- `policies/`: durable editorial, publication and repository rules
- `state/`: current operational queues/checkpoints
- `audits/`: immutable historical evidence grouped by purpose
- `docs/`: maintainer-facing operating notes

Canonical research content remains in `catalog/`; generated public payloads remain in `data/`.
""")

# Docs: repo-root HTTP serving is no longer the preview contract.
for name in ['README.md','MAINTENANCE.md']:
    p=R/name;s=p.read_text()
    s=s.replace('python -m http.server 8080','python scripts/build/stage_site.py --output _site\npython -m http.server 8080 -d _site')
    p.write_text(s)

# Permanent regression for the architecture boundary.
(R/'tests/test_repository_structure.py').write_text("""from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_repository_layers_are_explicit():
    assert (ROOT/'site/index.html').is_file()
    assert (ROOT/'site/js/core').is_dir()
    assert (ROOT/'site/js/features').is_dir()
    assert (ROOT/'site/styles/features').is_dir()
    assert (ROOT/'scripts/build').is_dir()
    assert (ROOT/'scripts/validate').is_dir()
    assert (ROOT/'scripts/browser').is_dir()
    assert (ROOT/'scripts/maintenance').is_dir()
    assert (ROOT/'scripts/discovery').is_dir()
    assert (ROOT/'scripts/migrations').is_dir()
    assert (ROOT/'maintenance/policies').is_dir()
    assert (ROOT/'maintenance/state').is_dir()
    assert (ROOT/'maintenance/audits').is_dir()
    assert (ROOT/'maintenance/docs').is_dir()

def test_root_is_not_a_frontend_source_dump():
    forbidden=['index.html','app.js','styles.css','research.js','research.css','experience.js','experience.css','news.js','news.css','tools.js','tools.css','sidebar.js','sidebar.css','runtime.js','dates.js','search-core.js','search-client.js','search-worker.js','validate.py']
    assert not [name for name in forbidden if (ROOT/name).exists()]

def test_operational_directories_are_not_flat_dumps():
    assert not list((ROOT/'scripts').glob('*.py'))
    assert not list((ROOT/'scripts').glob('*.cjs'))
    top_files={p.name for p in (ROOT/'maintenance').iterdir() if p.is_file()}
    assert top_files=={'README.md'}
""")

# Changelog entry.
p=R/'CHANGELOG.md';s=p.read_text()
entry="""## 2026-09-20 · 仓库信息架构重构

- 前端源码归入 `site/`，按 core/components/features 与 styles 分层；Pages 仍发布到原站点根路径，公开 URL 与 localStorage key 不变。
- `scripts/` 按 build/validate/browser/maintenance/discovery/migrations 分责；Node 回归归入 `tests/node/`，本地与 CI 共用确定性 site staging。
- `maintenance/` 分为 policies/state/audits/docs，历史审计保留且不与当前运行状态混放。
- `catalog/` 与 `data/` 在迁移中逐字节锁定；论文、结果、协议及榜单语义不参与本次重构。
- 移除已完成使命的三套历史一次性 workflow，保留并更新当前 Pages、内容批处理和 housekeeping 流程。

"""
p.write_text(entry+s)

# Record the refactor itself under the new release-audit hierarchy.
audit=R/'maintenance/audits/release/repository-structure-refactor-20260920.json'
audit.parent.mkdir(parents=True,exist_ok=True)
audit.write_text(json.dumps({
  'schemaVersion':1,
  'baseMainSha':'60b442c10d25591e3aa74308d599b98e258f83ac',
  'scope':'repository information architecture only; canonical research semantics excluded',
  'layers':['site','catalog','data','scripts','tests','maintenance'],
  'guarantees':{
    'catalogByteIdentical':None,'dataByteIdentical':None,
    'publicRoutesUnchanged':True,'localStorageKeysUnchanged':True,
    'paperResultTrackSemanticsUnchanged':True
  },
  'removedHistoricalOneShotWorkflows':['complete-library.yml','import-site.yml','recover-library.yml']
},ensure_ascii=False,indent=2)+'\n')

# The one-shot refactor workflow removes itself from the final tree.
q=R/'.github/workflows/restructure-repository.yml'
if q.exists():q.unlink()

# No stale known paths may remain outside immutable catalog/data.
stale=list(script_map)+[k for k in maint_map if not k.endswith('/')]
found=[]
for p in R.rglob('*'):
    if not p.is_file() or p.suffix not in text_ext:continue
    rel=p.as_posix()
    if rel.startswith(('catalog/','data/')):continue
    s=p.read_text(errors='ignore')
    for old in stale:
        if old in s:found.append((rel,old))
if found:raise RuntimeError('stale paths: '+repr(found[:30]))
print('structure migration complete')