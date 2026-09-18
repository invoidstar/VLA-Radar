"""Real HTTP integration for the public reading workspace, not physical-device benchmarking."""
import json,os,shutil,socket,subprocess,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('RADAR_WORKSPACE_OUTPUT','/tmp/radar-workspace'));OUT.mkdir(parents=True,exist_ok=True)
s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close()
server=subprocess.Popen(['python','-m','http.server',str(port),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.3)
base=f'http://127.0.0.1:{port}/';checks=[];errors=[];requests=[]
def yes(name,value):
 assert value,name
 checks.append(name)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),headless=True,args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
  page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
  page.goto(base,wait_until='networkidle');page.wait_for_selector('.paper-card')
  yes('startup has 12 cards',page.locator('.paper-card').count()==12)
  yes('optional modules remain lazy',not any('experience.js?' in u or '/data/experience/' in u for u in requests))
  page.screenshot(path=str(OUT/'library.png'))
  page.goto(base+'?view=reader&paper=p001',wait_until='networkidle');page.wait_for_selector('.reader-chapter')
  yes('reader direct route has full chapters',page.locator('.reader-chapter').count()>=9)
  page.locator('#reader-font').select_option('20');page.locator('#reader-line').select_option('2.15');page.locator('#reader-theme').select_option('night')
  yes('reader font setting applied',page.locator('#reader-content').evaluate('(el)=>el.style.getPropertyValue("--reader-font")')=='20px')
  page.locator('#reader-theme').select_option('paper');page.locator('[data-reader-jump="read-training"]').click();page.wait_for_timeout(600)
  saved=page.evaluate('JSON.parse(localStorage.getItem("vla-radar.reader.v1"))');yes('per-paper position saved',saved and 'p001' in saved)
  page.reload(wait_until='networkidle');page.wait_for_selector('.reader-chapter');yes('reader preferences persist',page.locator('#reader-font').input_value()=='20')
  page.locator('#reader-status').select_option('reading');yes('existing local reading key preserved','reading' in page.evaluate('localStorage.getItem("vla-radar.reading.v1")'))
  page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(300);page.screenshot(path=str(OUT/'reader-desktop.png'))
  page.locator('[data-reader-export]').first.click();page.wait_for_selector('#workspace-export[open]')
  yes('export dialog has accessible name',page.locator('#workspace-export').get_attribute('aria-labelledby')=='export-title')
  with page.expect_download() as dl:page.locator('#export-md').click()
  download=dl.value;target=OUT/download.suggested_filename;download.save_as(str(target));content=target.read_text()
  yes('markdown retains reading version and body','arXiv 2608.27550' in content and '研究问题' in content)
  yes('markdown does not include private state','vla-radar.reading.v1' not in content)
  page.keyboard.press('Escape');yes('export Escape closes dialog',not page.locator('#workspace-export').evaluate('(d)=>d.open'))
  page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(300);yes('reader mobile no document overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(OUT/'reader-mobile.png'))
  page.set_viewport_size({'width':1440,'height':1000})
  page.goto(base+'?view=compare&compare=p001,p069,p051',wait_until='networkidle');page.wait_for_selector('.comparison-table')
  yes('comparison direct link 3 papers',page.locator('.compare-chip').count()==3)
  page.locator('.compare-excerpt').first.locator('summary').click();yes('comparison expandable sourced excerpt',page.locator('.compare-excerpt[open]').count()==1)
  page.screenshot(path=str(OUT/'compare-desktop.png'));page.locator('#compare-differences').check();yes('comparison differences filter remains functional',page.locator('.comparison-table').count()==1)
  page.locator('[data-remove-paper="p051"]').click();page.wait_for_timeout(200);yes('comparison removal persists','p051' not in page.evaluate('localStorage.getItem("vla-radar.compare.v1")'))
  page.locator('#compare-search').fill('PerAct');page.locator('[data-add-paper="p051"]').click();page.wait_for_timeout(200);yes('comparison search add works',page.locator('.compare-chip').count()==3)
  page.set_viewport_size({'width':390,'height':844});yes('comparison overflow remains inside table',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(OUT/'compare-mobile.png'));page.set_viewport_size({'width':1440,'height':1000})
  page.goto(base+'?view=coverage',wait_until='networkidle');page.wait_for_selector('.heat-cell');yes('coverage has topic dataset matrix',page.locator('.heat-cell').count()>=100)
  page.locator('.heat-cell:not(.heat-0)').first.click();yes('heatmap drilldown contains sourced papers',page.locator('.coverage-paper').count()>0);page.screenshot(path=str(OUT/'coverage-desktop.png'))
  page.locator('#coverage-measure').select_option('results');yes('heatmap metric toggles',page.locator('.heat-cell').count()>=100)
  page.set_viewport_size({'width':390,'height':844});yes('heatmap scroll contained on mobile',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(OUT/'coverage-mobile.png'));page.set_viewport_size({'width':1440,'height':1000})
  page.goto(base+'?view=updates',wait_until='networkidle');page.wait_for_selector('.update-event');yes('updates list has real records',page.locator('.update-event').count()>0)
  page.locator('#updates-kind').select_option('site');page.wait_for_selector('.update-marker.site');yes('updates type filtering',page.locator('.update-marker.site').count()>=1);page.locator('.update-diff summary').first.click();yes('actual feature changes can be expanded',page.locator('.update-diff[open]').count()>0);page.screenshot(path=str(OUT/'updates-desktop.png'))
  page.locator('#updates-mark').click();yes('mark seen stays local',bool(page.evaluate('localStorage.getItem("vla-radar.updates-seen.v1")')))
  page.goto(base+'?view=leaderboards&dataset=CALVIN',wait_until='networkidle');page.wait_for_selector('#show-protocol-chart');page.locator('#show-protocol-chart').click();page.wait_for_selector('.chart-row')
  yes('CALVIN chart uses no percentage suffix','%' not in ''.join(page.locator('.chart-value').all_text_contents()));page.screenshot(path=str(OUT/'chart-desktop.png'))
  with page.expect_download() as dl:page.locator('#export-protocol-csv').click()
  yes('protocol CSV download',dl.value.suggested_filename.endswith('.csv'))
  page.locator('#show-protocol-chart').click();yes('chart can collapse',page.locator('#protocol-chart').get_attribute('hidden') is not None)
  page.goto(base,wait_until='networkidle');page.wait_for_selector('.paper-card');page.locator('.detail-btn').first.click();page.wait_for_selector('.note-section');page.locator('#paper-detail [data-focus]').click();page.wait_for_selector('.reader-chapter');yes('modal to dedicated reader closes modal',not page.locator('#paper-dialog').evaluate('(d)=>d.open'))
  yes('no uncaught JS errors',not errors)
  (OUT/'audit.json').write_text(json.dumps({'status':'pass','checks':checks,'count':len(checks),'errors':errors,'mode':'real HTTP Chromium on CI; not production CDN or physical mobile hardware','requests':len(requests)},ensure_ascii=False,indent=2))
  print('PASS workspace integration:',len(checks),'checks; real HTTP');browser.close()
except Exception as exc:
 (OUT/'failure.json').write_text(json.dumps({'error':str(exc),'checksPassed':checks,'pageErrors':errors},ensure_ascii=False,indent=2));raise
finally:
 server.terminate();server.wait()
