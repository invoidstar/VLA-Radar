import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import json,subprocess,time,socket
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
PUBLIC_ROOT=Path('/tmp/vla-radar-public')
subprocess.run(['python',str(root/'scripts/build/stage_site.py'),'--output',str(PUBLIC_ROOT)],check=True)
import os,shutil
out=Path(os.environ.get('RADAR_SMOKE_OUTPUT','/tmp/radar-browser'));out.mkdir(parents=True,exist_ok=True)
s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close()
server=subprocess.Popen(['python','-m','http.server',str(port),'--bind','127.0.0.1'],cwd=PUBLIC_ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),headless=True,args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];requests=[];console=[];failed=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
  page.on('console',lambda m:console.append({'type':m.type,'text':m.text}))
  page.on('requestfailed',lambda r:failed.append({'url':r.url,'failure':r.failure}))
  page.goto(f'http://127.0.0.1:{port}/',wait_until='networkidle')
  # Network idleness alone is not a guarantee that async app initialization finished.
  # Keep the exact first-page and lazy-loading assertions; fail with useful evidence.
  try:
   page.wait_for_function('Boolean(window.RadarTest)',timeout=15000)
   assert page.locator('.paper-card').count()==12
  except Exception:
   diagnostic={'status':'failure','stage':'initial-render','cards':page.locator('.paper-card').count(),'errors':errors,'console':console,'failedRequests':failed,'requests':requests,'body':page.locator('body').inner_text()[:12000]}
   (out/'initial-failure.json').write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2));print(json.dumps(diagnostic,ensure_ascii=False),flush=True)
   page.screenshot(path=str(out/'initial-failure.png'),full_page=True)
   raise
  # Native MathML must render in the real browser without external CDN/font requests.
  math_source=r'inline $a_t = \\frac{\\Delta x}{\\Delta t}$ and display \\[L=\\sum_{t=1}^{T}\\lVert a_t-\\hat{a}_t\\rVert^2\\]'
  math_audit=page.evaluate("""(source) => {
    const host=document.createElement('div');
    host.id='math-smoke';
    host.style.width='320px';
    host.innerHTML=window.RadarMath.renderText(source);
    document.body.appendChild(host);
    const inline=host.querySelector('.math-inline math'),display=host.querySelector('.math-display math');
    const displayWrap=host.querySelector('.math-display');
    return {
      mathCount:host.querySelectorAll('math').length,
      inlineWidth:inline?.getBoundingClientRect().width||0,
      displayWidth:display?.getBoundingClientRect().width||0,
      displayOverflow:getComputedStyle(displayWrap).overflowX,
      rawDollar:host.textContent.includes('$a_t'),
      rawDelimiter:host.textContent.includes('\\\\['),
      pageOverflow:document.documentElement.scrollWidth>innerWidth+1
    };
  }""",math_source)
  assert math_audit['mathCount']==2,math_audit
  assert math_audit['inlineWidth']>0 and math_audit['displayWidth']>0,math_audit
  assert math_audit['displayOverflow']=='auto',math_audit
  assert not math_audit['rawDollar'] and not math_audit['rawDelimiter'],math_audit
  assert not math_audit['pageOverflow'],math_audit
  page.locator('#math-smoke').evaluate('(el)=>el.remove()')
  assert not any('search-index.' in u or 'board-index.' in u or '/details/' in u or '/reproducibility/' in u for u in requests), requests
  # Official resources are separate from evidence: render only when verified and never add placeholders.
  page.locator('#search').fill('OpenVLA');page.wait_for_timeout(900)
  openvla=page.locator('[data-paper="p064"]').first;assert openvla.count()==1
  card=openvla.locator('xpath=ancestor::article[contains(@class,"paper-card")]')
  assert card.locator('.paper-resource.project').count()==1 and card.locator('.paper-resource.code').count()==1
  assert 'openvla.github.io' in card.locator('.paper-resource.project').get_attribute('href')
  assert 'github.com/openvla/openvla' in card.locator('.paper-resource.code').get_attribute('href')
  card.locator('.detail-btn').click();page.wait_for_selector('.note-section')
  assert page.locator('#paper-detail .paper-resources .paper-resource').count()==2
  # Verified paper lineage/series is rendered from catalog/relations.json, not inferred in-browser.
  assert page.locator('#paper-detail .relation-section').count()==1
  assert 'Follow-up' in page.locator('#paper-detail .relation-section').inner_text()
  assert 'Same Series · OpenVLA' in page.locator('#paper-detail .relation-section').inner_text()
  assert page.locator('#paper-detail .relation-section [data-paper="p069"]').count()>=1
  # Reproducibility Card distinguishes an official link from audited release completeness.
  assert page.locator('#paper-detail .reproducibility-card').count()==1
  assert any('/data/reproducibility/p064.json' in u for u in requests),requests
  assert '可用' in page.locator('#paper-detail [data-repro-dim="weights"]').inner_text()
  assert '部分开放' in page.locator('#paper-detail [data-repro-dim="license"]').inner_text()
  assert page.locator('#paper-detail [data-repro-dim="weights"] a').count()>=1
  for link in page.locator('#paper-detail .paper-resources .paper-resource').all():
   assert link.get_attribute('target')=='_blank' and 'noopener' in (link.get_attribute('rel') or '')
  page.locator('#paper-detail [data-focus="p064"]').click();page.wait_for_selector('.reader-title-tools')
  assert page.locator('.reader-title-tools a',has_text='项目主页').count()==1
  assert page.locator('.reader-title-tools a',has_text='开源代码').count()==1
  page.locator('.reader-toolbar [data-view="papers"]').click();page.wait_for_selector('#search');page.wait_for_timeout(250)
  page.locator('#search').fill('Qwen-RobotManip');page.wait_for_timeout(900)
  qwen=page.locator('[data-paper="p114"]').first;assert qwen.count()==1
  qwen.locator('xpath=ancestor::article[contains(@class,"paper-card")]').locator('.detail-btn').click();page.wait_for_selector('.note-section')
  assert '未开放' in page.locator('#paper-detail [data-repro-dim="weights"]').inner_text()
  assert '部分开放' in page.locator('#paper-detail [data-repro-dim="code"]').inner_text()
  assert page.locator('#paper-detail [data-repro-dim="weights"] .repro-evidence').count()==1
  assert page.locator('#paper-detail [data-repro-dim="weights"] a:not(.repro-evidence)').count()==0
  page.keyboard.press('Escape');page.wait_for_timeout(150)
  page.locator('#search').fill('In-Context VLA');page.wait_for_timeout(900)
  nores=page.locator('[data-paper="p006"]').first;assert nores.count()==1
  assert nores.locator('xpath=ancestor::article[contains(@class,"paper-card")]').locator('.paper-resources').count()==0
  page.locator('#search').fill('LIBERO');page.wait_for_timeout(900)
  assert any('search-index.' in u for u in requests)
  assert page.locator('.paper-card').count()>0
  page.locator('[data-paper="p001"]').first.click() if page.locator('[data-paper="p001"]').count() else page.locator('.detail-btn').first.click()
  page.wait_for_selector('.note-section')
  assert page.locator('.note-section').count()>=8
  page.locator('[data-note-tab="life"]').click();assert page.locator('#paper-detail #panel-life .life-grid').is_visible()
  page.locator('[data-note-tab="results"]').click();page.wait_for_timeout(300)
  page.keyboard.press('Escape');page.locator('.nav-link[data-view="leaderboards"]').click()
  try:
   page.wait_for_selector('#setting-select',timeout=12000)
  except Exception:
   diagnostic={'status':'failure','stage':'benchmark-setting-render','url':page.url,'errors':errors,'console':console[-30:],'failedRequests':failed[-30:],'body':page.locator('body').inner_text()[:12000]}
   (out/'benchmark-setting-failure.json').write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2));print(json.dumps(diagnostic,ensure_ascii=False),flush=True)
   page.screenshot(path=str(out/'benchmark-setting-failure.png'),full_page=True)
   raise
  assert page.locator('.setting-table').count()==1
  page.locator('[data-setting-dataset="CALVIN"]').click();page.wait_for_selector('#setting-select')
  page.wait_for_function('new URLSearchParams(location.search).get("dataset")==="CALVIN"')
  assert page.locator('.setting-summary').is_visible() and page.locator('.setting-table').is_visible()
  page.screenshot(path=str(out/'desktop.png'),full_page=False)
  # Exact track analysis remains available as the advanced compatibility path.
  page.locator('.setting-advanced-link').click();page.wait_for_selector('#lb-track')
  assert 'CALVIN' in page.locator('.protocol-card').inner_text()
  assert not any('/data/leaderboards.json' in u for u in requests),requests
  page.locator('.nav-link[data-view="papers"]').click();page.wait_for_timeout(200)
  # Clear and test saved state persistence across a real HTTP reload.
  page.locator('#search').fill('');page.wait_for_timeout(300)
  page.locator('.paper-card [data-save]').first.click();saved=page.evaluate('localStorage.getItem("vla-radar.reading.v1")');assert saved and 'true' in saved
  page.reload(wait_until='networkidle');assert page.evaluate('localStorage.getItem("vla-radar.reading.v1")')==saved
  page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(450);page.evaluate('window.scrollTo(0,0)')
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
  page.screenshot(path=str(out/'mobile.png'),full_page=False)
  assert not errors, errors
  (out/'audit.json').write_text(json.dumps({'status':'pass','tests':['HTTP initial lazy-load boundary','native MathML formula rendering','search worker index loading','official project/code resources and absent-placeholder behavior','verified paper lineage and same-series rendering','lazy reproducibility shard loading and explicit unavailable weights','8-section notes','lifecycle tab','paper results tab','Setting-first CALVIN switching','advanced track compatibility','no full-board download','localStorage reload persistence','mobile overflow','no uncaught JS errors'],'errors':errors,'requestCount':len(requests),'environment':'local Chromium 1440x1000 and 390x844; not production or real mobile hardware'},indent=2))
  print('PASS browser HTTP integration, persistence, lazy-loading, worker search and mobile overflow')
  browser.close()
finally:server.terminate();server.wait()
