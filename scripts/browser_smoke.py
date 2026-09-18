import json,subprocess,time,socket
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
import os,shutil
out=Path(os.environ.get('RADAR_SMOKE_OUTPUT','/tmp/radar-browser'));out.mkdir(parents=True,exist_ok=True)
s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close()
server=subprocess.Popen(['python','-m','http.server',str(port),'--bind','127.0.0.1'],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),headless=True,args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];requests=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
  page.goto(f'http://127.0.0.1:{port}/',wait_until='networkidle')
  assert page.locator('.paper-card').count()==12
  assert not any('search-index.' in u or 'board-index.' in u or '/details/' in u for u in requests), requests
  page.locator('#search').fill('LIBERO');page.wait_for_timeout(900)
  assert any('search-index.' in u for u in requests)
  assert page.locator('.paper-card').count()>0
  page.locator('[data-paper="p001"]').first.click() if page.locator('[data-paper="p001"]').count() else page.locator('.detail-btn').first.click()
  page.wait_for_selector('.note-section')
  assert page.locator('.note-section').count()>=8
  page.locator('[data-note-tab="life"]').click();assert page.locator('.life-grid').is_visible()
  page.locator('[data-note-tab="results"]').click();page.wait_for_timeout(300)
  page.keyboard.press('Escape');page.locator('.nav-link[data-view="leaderboards"]').click();page.wait_for_selector('#lb-track')
  page.locator('[data-dataset="CALVIN"]').click();page.wait_for_timeout(350);assert 'CALVIN' in page.locator('.protocol-card').inner_text()
  assert not any('/data/leaderboards.json' in u for u in requests),requests
  page.screenshot(path=str(out/'desktop.png'),full_page=False)
  page.locator('.nav-link[data-view="papers"]').click();page.wait_for_timeout(200)
  # Clear and test saved state persistence across a real HTTP reload.
  page.locator('#search').fill('');page.wait_for_timeout(300)
  page.locator('.paper-card [data-save]').first.click();saved=page.evaluate('localStorage.getItem("vla-radar.reading.v1")');assert saved and 'true' in saved
  page.reload(wait_until='networkidle');assert page.evaluate('localStorage.getItem("vla-radar.reading.v1")')==saved
  page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(450);page.evaluate('window.scrollTo(0,0)')
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
  page.screenshot(path=str(out/'mobile.png'),full_page=False)
  assert not errors, errors
  (out/'audit.json').write_text(json.dumps({'status':'pass','tests':['HTTP initial lazy-load boundary','search worker index loading','8-section notes','lifecycle tab','paper results tab','CALVIN switching','no full-board download','localStorage reload persistence','mobile overflow','no uncaught JS errors'],'errors':errors,'requestCount':len(requests),'environment':'local Chromium 1440x1000 and 390x844; not production or real mobile hardware'},indent=2))
  print('PASS browser HTTP integration, persistence, lazy-loading, worker search and mobile overflow')
  browser.close()
finally:server.terminate();server.wait()
