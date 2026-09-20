"""Real HTTP browser regression for the final daily tools; not physical-device tests."""
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import json,os,shutil,socket,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
PUBLIC_ROOT=Path('/tmp/vla-radar-public')
subprocess.run(['python',str(ROOT/'scripts/build/stage_site.py'),'--output',str(PUBLIC_ROOT)],check=True);OUT=Path(os.getenv('RADAR_TOOLS_OUTPUT','/tmp/radar-tools'));OUT.mkdir(parents=True,exist_ok=True)
lib=json.loads((ROOT/'data/library.json').read_text());sample=lib['papers'][0];pid=sample['id'];ix=json.loads((ROOT/lib['toolsUrl']).read_text());news=next(n for part in ix['headlines'] for n in json.loads((ROOT/part['url']).read_text())['items'] if n['status']!='withdrawn')
s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close();base=f'http://127.0.0.1:{port}/'
server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],cwd=PUBLIC_ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);checks=[];errors=[];requests=[]
def yes(label,value):
 assert value,label
 checks.append(label)
try:
 time.sleep(.3)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),headless=True,args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append((r.method,r.url)))
  page.goto(base,wait_until='networkidle');page.wait_for_selector('.paper-card')
  yes('tools code and indexes remain lazy',not any('tools.js' in u or 'tools-core.js' in u or '/data/tools/' in u for _,u in requests))
  original=page.evaluate('localStorage.getItem("vla-radar.reading.v1")')
  page.locator('#search').fill('');page.locator('#search').press('/')
  yes('slash does not steal typing focus',page.locator('#search').input_value()=='/' and page.locator('#radar-command[open]').count()==0)
  page.locator('#search').fill('');page.locator('h1').first.click();page.keyboard.press('Control+k');page.wait_for_selector('#radar-command[open]');page.wait_for_function('document.querySelectorAll("#command-results [role=option]").length>0')
  yes('palette accessible combobox',page.locator('#command-query').get_attribute('role')=='combobox')
  page.locator('#command-query').fill('LIBERO');expect(page.locator('#command-results [role=option]').first).to_contain_text('LIBERO')
  page.wait_for_function('Array.from(document.querySelectorAll("#command-results [role=option]")).some(e=>e.querySelector("small").textContent==="基准" && e.querySelector("strong").textContent==="LIBERO")')
  benchmark_option=page.locator('#command-results [role=option]').evaluate_all('(els)=>els.findIndex(e=>e.querySelector("small").textContent==="基准" && e.querySelector("strong").textContent==="LIBERO")')
  page.screenshot(path=str(OUT/'command-desktop.png'))
  page.keyboard.press('ArrowDown');yes('arrow tracks active descendant',page.locator('#command-query').get_attribute('aria-activedescendant')=='command-option-1')
  page.keyboard.press('ArrowUp')
  for _ in range(benchmark_option):page.keyboard.press('ArrowDown')
  page.keyboard.press('Enter');page.wait_for_selector('#leaderboards-section:not(.hidden)')
  yes('command navigates to benchmark','dataset=LIBERO' in page.url)
  page.keyboard.press('Control+k');page.wait_for_selector('#command-query');page.locator('#command-query').fill(news['title']);page.wait_for_function('(title)=>document.querySelector("#command-results strong")?.textContent===title',arg=news['title']);page.keyboard.press('Enter');page.wait_for_selector('#'+news['id'])
  yes('global news headline search opens actual news',news['id'] in page.url)
  page.keyboard.press('Control+k');page.wait_for_selector('#command-query');page.locator('#command-query').fill(sample['name']);page.wait_for_function('(n)=>document.querySelector("#command-results strong")?.textContent===n',arg=sample['name']);page.keyboard.press('Enter');page.wait_for_selector('.reader-chapter')
  yes('paper palette selection opens reader','paper='+pid in page.url)
  page.locator(f'.reader-title-tools [data-follow-paper="{pid}"]').click();expect(page.locator(f'.reader-title-tools [data-follow-paper="{pid}"]')).to_have_attribute('aria-pressed','true')
  yes('paper follow stores only follow state',pid in json.loads(page.evaluate('localStorage.getItem("vla-radar.follows.v1")'))['papers'])
  page.locator('.nav-link[data-view="radar"]').click();page.wait_for_selector('.radar-hero');expect(page.locator('#radar-paper-count')).not_to_have_text('0')
  yes('My Radar shows related followed paper',page.locator(f'#radar-paper-list a[href*="paper={pid}"]').count()==1)
  page.locator('.radar-manager summary').click();page.locator('[data-manager-tab="datasets"]').click();page.locator('#radar-manage-query').fill('LIBERO');page.locator('[data-follow-value="LIBERO"]').click();expect(page.locator('[data-follow-value="LIBERO"]')).to_have_attribute('aria-pressed','true');page.locator('#radar-manage-query').fill('')
  page.locator('[data-manager-tab="topics"]').click();topic=lib['topics'][0]['id'];page.locator(f'[data-follow-value="{topic}"]').click();page.locator('[data-manager-tab="categories"]').click();cat=news['category'];page.locator(f'[data-follow-value="{cat}"]').click()
  yes('four follow types persist',all(json.loads(page.evaluate('localStorage.getItem("vla-radar.follows.v1")'))[k] for k in ['papers','topics','datasets','categories']))
  yes('no note/result snapshots promoted to new',page.locator('#radar-feed-scope').inner_text().find('快照')>=0)
  page.locator('#radar-mark-seen').click();page.locator('#radar-only-new').check();expect(page.locator('#radar-event-count')).to_have_text('0')
  yes('same-day ambiguous records are not reannounced',page.locator('.radar-event').count()==0)
  page.locator('#radar-only-new').uncheck();page.locator('.radar-manager summary').click();page.screenshot(path=str(OUT/'my-radar-desktop.png'))
  page.reload(wait_until='networkidle');page.wait_for_selector('.radar-hero');expect(page.locator('#radar-follow-count')).to_have_text('4')
  yes('follows survive reload and reader keys unchanged',page.evaluate('localStorage.getItem("vla-radar.reading.v1")')==original)
  for size in [740,390,320]:
   page.set_viewport_size({'width':size,'height':844});page.wait_for_timeout(150);yes(f'{size}px My Radar without page overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
   if size==390:page.screenshot(path=str(OUT/'my-radar-mobile.png'))
  page.set_viewport_size({'width':1440,'height':1000});page.goto(base+f'?view=reader&paper={pid}',wait_until='networkidle');page.wait_for_selector('.reader-chapter');page.locator('[data-reader-export]').first.click();page.wait_for_selector('#workspace-export[open]')
  for kind,extension in [('bib','.bib'),('ris','.ris'),('csl','.csl.json'),('md','-notes.md')]:
   with page.expect_download() as result:page.locator('#export-'+kind).click()
   download=result.value;download.save_as(str(OUT/('sample'+extension)));content=(OUT/('sample'+extension)).read_text()
   yes(kind+' downloads with expected extension',download.suggested_filename.endswith(extension))
   yes(kind+' excludes private follow/reading keys','vla-radar.follows' not in content and 'seenAt' not in content)
   if kind=='csl':
    obj=json.loads(content);yes('CSL is importable item array with actual title',isinstance(obj,list) and obj[0]['title']==sample['title']);known=json.loads((ROOT/ix['bibliographyUrl']).read_text())['entries'].get(pid,{}).get('item',{}).get('author');yes('authors match source-verified bibliography only',obj[0].get('author')==known)
   if kind=='ris':yes('RIS boundaries and title',content.startswith('TY  - ') and content.rstrip().endswith('ER  -') and sample['title'] in content)
  yes('export explicitly reports missing authors','缺完整作者' in page.locator('#export-status').inner_text())
  page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:()=>Promise.reject(Error('blocked'))}})")
  page.locator('#export-copy').click();page.wait_for_selector('#export-fallback:not([hidden])');yes('clipboard rejection supports manual copy','@' in page.locator('#export-fallback').input_value())
  page.screenshot(path=str(OUT/'export-desktop.png'));page.locator('#export-close').click()
  page.keyboard.press('Control+k');page.wait_for_selector('#command-query');page.locator('#command-query').fill('zzzz_no_such_item');page.wait_for_function('document.querySelector("#command-status").textContent.includes("没有匹配")');yes('empty palette clears stale aria option',page.locator('#command-query').get_attribute('aria-activedescendant') is None);page.keyboard.press('Escape');yes('Escape closes palette',page.locator('#radar-command[open]').count()==0)
  # Cross-tab preferences must refresh the already-open local view.
  page.goto(base+'?view=radar',wait_until='networkidle');page.wait_for_selector('.radar-hero');other=context.new_page();other.goto(base,wait_until='networkidle');other.evaluate('localStorage.removeItem("vla-radar.follows.v1")');expect(page.locator('#radar-follow-count')).to_have_text('0');yes('cross-tab clear refreshes follows',page.locator('#radar-follow-count').inner_text()=='0');other.close()
  # Disabled storage never stops follow interactions.
  denied=browser.new_context(viewport={'width':1100,'height':900});denied.add_init_script("for(const k of ['getItem','setItem','removeItem'])Storage.prototype[k]=()=>{throw Error('Storage disabled')}");dp=denied.new_page();dp.on('pageerror',lambda e:errors.append(str(e)));dp.goto(base,wait_until='networkidle');dp.locator('[data-follow-paper]').first.click();expect(dp.locator('[data-follow-paper]').first).to_have_attribute('aria-pressed','true');yes('storage disabled follows remain usable in session',True);denied.close()
  # A missing shard must not be presented as a successful empty global search.
  fail=browser.new_context();fp=fail.new_page();fp.route('**/data/tools/**',lambda route:route.abort());fp.goto(base,wait_until='networkidle');fp.keyboard.press('Control+k');fp.wait_for_selector('#radar-command[open]');fp.wait_for_function('document.querySelector("#command-status").textContent.includes("失败")');yes('palette network failure visible',True);fp.keyboard.press('Escape');fp.unroute('**/data/tools/**');fp.keyboard.press('Control+k');fp.wait_for_function('document.querySelectorAll("#command-results [role=option]").length>0');yes('failed tool fetch is retryable',True);fail.close()
  yes('no private write requests',all(method=='GET' for method,_ in requests));yes('no uncaught JavaScript errors',not errors)
  (OUT/'audit.json').write_text(json.dumps({'status':'pass','count':len(checks),'checks':checks,'errors':errors,'scope':'Real HTTP Chromium; viewport simulation, not physical mobile or public network'},ensure_ascii=False,indent=2));print('PASS daily tools browser:',len(checks),'checks');browser.close()
except Exception as e:
 (OUT/'failure.json').write_text(json.dumps({'error':str(e),'passed':checks,'errors':errors},ensure_ascii=False,indent=2));raise
finally:server.terminate();server.wait()
