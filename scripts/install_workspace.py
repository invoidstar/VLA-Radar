"""One-time, source-guarded workspace installation. No scientific data is edited."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={'app.js':'02598fcd680d705e82ad6051fb4b5f3d840016e60a662a0b1e088d4c2639f1a5','research.js':'baf52a61b37f0a2debb2842cb5e5872412e67d071fad361384ccd77a25561126','index.html':'c5dcd143b55e0d76599a6bbbe13293900936edff1dedff0d0ccfabe8fac00eb7','scripts/build_catalog.py':'f32fc858a13abda0e119413f0cbde5931ce8c38f1de452a4e75574a8025dc9ca','scripts/validate_all.py':'57acb698c3e2f1f52d2c2dca9c7b6159becdfb5fbbbd493d0b1a3c5adf20a8c9'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def science():
 paths=[*ROOT.glob('catalog/papers/*.json'),*ROOT.glob('catalog/results/*.json'),ROOT/'catalog/first-public.json',ROOT/'catalog/benchmarks.json']
 return {p.relative_to(ROOT).as_posix():sha(p) for p in paths}
def edit(path,old,new):
 p=ROOT/path;s=p.read_text(encoding='utf-8')
 if old not in s:raise ValueError('Unexpected source: '+path+' / '+old[:70])
 p.write_text(s.replace(old,new),encoding='utf-8')
def append(path,text):
 p=ROOT/path;s=p.read_text(encoding='utf-8');p.write_text(s+'\n'+text,encoding='utf-8')
def install():
 marker=ROOT/'maintenance/workspace-install.json'
 if marker.exists():print('Workspace already installed.');return
 for name,digest in EXPECTED.items():
  if sha(ROOT/name)!=digest:raise ValueError('Source moved before installation: '+name)
 before=science()
 edit('app.js',"leaderboards:'评测榜单',about:","leaderboards:'评测榜单',reader:'专注阅读',compare:'论文对比',updates:'更新中心',coverage:'证据地图',about:")
 edit('app.js',"for(const v of ['topics','timeline','about','leaderboards'])", "for(const v of ['topics','timeline','about','leaderboards','reader','compare','updates','coverage'])")
 edit('app.js',"  function showView(){", "  function showView(){\n    if(state.view!=='leaderboards')window.RadarResearch.cancelBoards();")
 edit('app.js',"    document.title=`${views[state.view]} · VLA Research Radar`;", "    if(['reader','compare','updates','coverage'].includes(state.view))window.RadarWorkspace.show(state.view);else window.RadarWorkspace.leave();\n    document.title=`${views[state.view]} · VLA Research Radar`;")
 edit('app.js',"    if(includePaper)u.hash=location.hash;", "    if(['reader','compare'].includes(view)){const params=new URLSearchParams(location.search);for(const k of ['paper','compare']){const v=params.get(k);if(v)u.searchParams.set(k,v);}}\n    if(includePaper)u.hash=location.hash;")
 edit('app.js',"    window.RadarResearch.configure(data);", "    window.RadarResearch.configure(data);\n    window.RadarWorkspace.configure(data,{notify,closePaper,navigate:(view,params={})=>{if($('#paper-dialog').open)closePaper();const u=new URL(location.href);u.search='';u.hash='';u.searchParams.set('view',view);for(const [k,v]of Object.entries(params))if(v)u.searchParams.set(k,v);history.pushState({},'',u);parseUrl();showView();closeSidebar();window.scrollTo({top:0,behavior:'instant'});},filtered:()=>filtered,local,setStatus:(id,status)=>{if(!['unread','reading','read'].includes(status))return;reading[id]={...local(id),status};saveState();renderResults();},copy,download});")
 edit('app.js',"${saveButton(p)}</div></div></article>","<button class=\"compare-pick\" data-compare=\"${p.id}\" aria-label=\"加入对比 ${esc(p.name)}\">＋ 对比</button><button class=\"focus-pick\" data-focus=\"${p.id}\">专注阅读</button>${saveButton(p)}</div></div></article>")
 edit('app.js',"    $('#pagination').innerHTML=pages<=1", "    window.RadarExperience?.refreshPicks();\n    $('#pagination').innerHTML=pages<=1")
 edit('app.js',"    window.RadarResearch.enhance(p,$('#paper-detail'));", "    $('#paper-detail').insertAdjacentHTML('afterbegin',`<div class=\"quick-note-tools\"><button class=\"btn primary\" data-focus=\"${p.id}\">进入专注阅读 ↗</button><button class=\"btn\" data-compare=\"${p.id}\">＋ 加入对比</button><span>先看结论，再沿章节深入。</span></div>`);\n    window.RadarResearch.enhance(p,$('#paper-detail'));")
 edit('app.js',"      if(el.dataset.view)","      if(el.dataset.focus){e.preventDefault();window.RadarWorkspace.action('focus',el.dataset.focus);}\n      else if(el.dataset.compare){e.preventDefault();window.RadarWorkspace.action('compare',el.dataset.compare);}\n      else if(el.dataset.workspaceExport){window.RadarWorkspace.action('export');}\n      else if(el.dataset.view)")
 edit('app.js',"else if(el.dataset.bib)bibtex(el.dataset.bib);", "else if(el.dataset.bib)window.RadarWorkspace.action('cite',el.dataset.bib);")
 edit('research.js',"global.RadarResearch={configure,detail", "global.RadarResearch={cancelBoards:()=>{boardToken++;},loadBoards,loadTrack,loadPaperResults,lifecycle,links,scopeNotice,configure,detail")
 edit('research.js',"async function sync(){await draw();const u=", "async function sync(){await draw();if(token!==boardToken)return;const u=")
 edit('research.js','<div class="board-table-scroll"><table class="board-table"><caption>${esc(t.name)}', '<div class="board-visual-tools"><button class="btn" id="show-protocol-chart">查看当前协议图表</button><button class="btn" id="export-protocol-csv">导出当前协议 CSV</button><span>只比较所选指标，不合成跨协议总分。</span></div><div id="protocol-chart" hidden></div><div class="board-table-scroll"><table class="board-table"><caption>${esc(t.name)}')
 edit('research.js',"        host.querySelectorAll('[data-dataset]')", "        host.querySelector('#show-protocol-chart').onclick=()=>window.RadarWorkspace.action('chart',{track:t,rows,host:host.querySelector('#protocol-chart')});\n        host.querySelector('#export-protocol-csv').onclick=()=>window.RadarWorkspace.action('csv',{track:t,rows});\n        host.querySelectorAll('[data-dataset]')")
 edit('index.html','<link rel="stylesheet" href="research.css">','<link rel="stylesheet" href="research.css">\n  <link rel="stylesheet" href="experience.css">\n  <script src="experience-loader.js?v=workspace-20260918" defer></script>')
 edit('index.html','</nav>','<div class="side-heading workspace-heading">RESEARCH WORKSPACE</div><button class="nav-link" data-view="compare"><span data-icon="table"></span>论文对比 <small id="compare-count"></small></button><button class="nav-link" data-view="updates"><span data-icon="clock"></span>更新中心</button><button class="nav-link" data-view="coverage"><span data-icon="grid"></span>证据地图</button></nav>')
 edit('index.html','<button class="btn subtle" id="export-csv">','<button class="btn subtle" data-workspace-export="true">引用与笔记</button><button class="btn subtle" id="export-csv">')
 edit('index.html','    <footer class="footer">','    <section id="reader-section" class="page-section hidden"><div id="reader-content"></div></section>\n    <section id="compare-section" class="page-section hidden"><div id="compare-content"></div></section>\n    <section id="updates-section" class="page-section hidden"><div id="updates-content"></div></section>\n    <section id="coverage-section" class="page-section hidden"><div id="coverage-content"></div></section>\n    <footer class="footer">')
 edit('index.html','从公开论文提取 RoboTwin、RoboCasa 与 LIBERO 的可追溯结果。','跨数据集查看可追溯的论文结果，或打开当前协议图表。')
 edit('index.html','人工合并后发布','来源自检和 CI 通过后按授权合并发布')
 edit('index.html','app.js?v=maintenance-20260918','app.js?v=workspace-20260918');edit('index.html','research.js?v=maintenance-20260918','research.js?v=workspace-20260918')
 edit('scripts/build_catalog.py','from catalog_core import dumps,read_catalog','from catalog_core import dumps,read_catalog\nfrom experience_build import outputs as experience_outputs')
 edit('scripts/build_catalog.py',"    out['data/library.json']=compact({'schemaVersion':1,**meta,'searchUrl':searchurl,'boardIndexUrl':boardurl,'papers':light})", "    experience,indexurl=experience_outputs(root,records,tracks,results);out.update(experience)\n    out['data/library.json']=compact({'schemaVersion':1,**meta,'searchUrl':searchurl,'boardIndexUrl':boardurl,'experienceUrl':indexurl,'papers':light})")
 edit('scripts/build_catalog.py',"patterns=['data/details/p*.json'", "patterns=['data/experience/*.json','data/details/p*.json'")
 edit('scripts/validate_all.py',"['node','scripts/test_performance.cjs']]", "['node','scripts/test_performance.cjs'],['node','scripts/test_experience.cjs'],*(['node','--check',p] for p in ['experience-loader.js','experience-core.js','experience.js'])]")
 p=ROOT/'catalog/activity.json'
 if p.exists():raise ValueError('Activity log already exists; reconcile instead of overwriting')
 now=datetime.now(timezone.utc).isoformat(timespec='seconds')
 p.write_text(json.dumps({'schemaVersion':1,'events':[{'id':'site-workspace-2026-09-18','kind':'site','paperId':None,'title':'阅读工作台：从阅读到比较、追踪与引用','date':now[:10],'observedAt':now,'mode':'change','summary':'构建本批阅读与研究工具；功能随本PR成功合并部署后对外提供。未将历史笔记快照改写为新收录。','source':'https://github.com/invoidstar/VLA-Radar/blob/main/maintenance/workspace.md','changes':[{'field':'阅读体验','before':'以弹窗笔记为主','after':'独立阅读页、章节目录、本地阅读位置及字号主题设置'},{'field':'研究工具','before':'论文列表与协议表格','after':'来源摘录对比、实际变化中心、证据覆盖热力图、协议内图表与公开引用导出'}]}]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 append('AGENTS.md', '''## Reading workspace and public change capture

Read maintenance/workspace.md. Before canonical content edits, preserve the exact latest main SHA as BASE_SHA. After editing, run `python scripts/capture_activity.py --base "$BASE_SHA"`, then build_catalog.py and validate_all.py. Commit the actual public deltas and generated shards in the same PR. Never invent historical collection/change dates from firstPublished, lastCheckedAt or old note snapshots. Data/experience is generated; do not edit hashed paths. Preserve optional-module loading, zero/null separation, source limitations and original reading-state keys. Comparison uses cited note excerpts, not fabricated attributes or a global capability rank. The heatmap counts checked non-superseded evidence in this library, not field-wide research activity. Browser CI includes browser_workspace.py. Private reader preferences, comparison selections and visit history stay in the browser, never in public data.
''')
 append('MAINTENANCE.md', '''## 阅读工作台与周更变更记录

详见 maintenance/workspace.md。保存变更前最新main精确SHA后，完成论文/笔记/结果修改，再运行capture_activity.py --base该SHA、build_catalog.py、validate_all.py。只记录实际差异；旧快照不补造首次收录，元数据检查不冒充精读更新。每周继续同步榜单、全文笔记、发表状态与安全分支清理；新工具不降低来源或发布门槛。HTTP浏览器回归还包括reader、compare、updates、coverage、当前协议图表及导出。
''')
 append('README.md', '''## Research workspace

Focused reading (`?view=reader&paper=p001`), cited two-to-four-paper comparison, observed change streams, library evidence coverage, single-protocol charts, and public BibTeX/Markdown/CSV exports are available. Optional code and data load on use. See `maintenance/workspace.md` for semantic boundaries, local preferences and the weekly activity-capture command. Basic BibTeX intentionally does not guess missing authors or final venue metadata.
''')
 p=ROOT/'CHANGELOG.md';p.write_text('## 2026-09-18 — 阅读工作台与证据可视化\n\n增加独立阅读页、2–4篇来源摘录对比、真实变化中心、方向×数据集覆盖图、单协议图表、BibTeX/Markdown/CSV导出与阅读优先视觉层次。保持按需加载、现有论文/笔记/结果/首发锁不变；本机偏好不进入公开库。周更增加真实变更捕获，历史快照不伪造入库日期。\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
 after=science();assert before==after,'Scientific source unexpectedly changed'
 marker.write_text(json.dumps({'schemaVersion':1,'baseCommit':'39c4e977a8395858f684c7ad85499381c62c54c4','installedAt':now,'sourcePreimages':EXPECTED,'scientificFileCount':len(before),'scientificFileHashes':before,'scientificContentUnchanged':True,'validationStatus':'pending CI, not a deployment claim'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 # Discard an abandoned transport experiment. It is never decoded or executed.
 stage=ROOT/'maintenance/workspace-stage'
 if stage.exists():shutil.rmtree(stage)
 print('Installed workspace; scientific record invariance verified. Build and browser CI still required.')
if __name__=='__main__':install()
