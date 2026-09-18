"""HTTP news integration. CI viewport tests are not mobile-hardware measurements."""
import json,os,shutil,socket,subprocess,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ.get('RADAR_NEWS_OUTPUT','/tmp/radar-news-browser'));OUT.mkdir(parents=True,exist_ok=True)
s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close()
server=subprocess.Popen(['python','-m','http.server',str(port),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.4)
base=f'http://127.0.0.1:{port}/';checks=[];errors=[];requests=[]
def yes(name,value):
 assert value,name
 checks.append(name)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),headless=True,args=['--no-sandbox']);context=browser.new_context(viewport={'width':1440,'height':1050},accept_downloads=True)
  page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url));page.goto(base,wait_until='networkidle');page.wait_for_selector('.paper-card')
  yes('homepage still has twelve cards',page.locator('.paper-card').count()==12)
  yes('news module data styles remain lazy',not any('/news.js' in u or '/news.css' in u or '/data/news/' in u for u in requests))
  page.goto(base+'?view=news&nw=2026-W38',wait_until='networkidle');page.wait_for_selector('.news-story');yes('three real first-issue stories',page.locator('.news-story').count()>=3);yes('curated lead cards visible',page.locator('.news-feature').count()>=3)
  yes('optional script loaded only on route',any('/news.js' in u for u in requests));yes('partial scan visibly labelled','部分检索' in page.locator('#news-issue-status').inner_text());yes('unknown weeks not shown as zero',page.locator('.news-week-bar.unknown').count()>0)
  yes('no main document horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(OUT/'news-desktop.png'))
  page.locator('[data-news-jump="news-20260916-xplanner"]').click();yes('featured opens explanation',page.locator('#news-20260916-xplanner details').first.evaluate('(d)=>d.open'));yes('background link is not presented as same paper','非本次发布论文' in page.locator('#news-20260916-xplanner').inner_text())
  page.locator('#news-evidence').select_option('reported');yes('source filter isolates media',page.locator('.news-story').count()==1 and 'HERON' in page.locator('.news-story').inner_text());page.locator('#news-evidence').select_option('')
  page.locator('#news-query').fill('不存在的新闻关键词');page.wait_for_timeout(250);yes('empty state honest and usable',page.locator('.news-empty').count()==1);page.locator('#news-reset').click();yes('reset restores current issue',page.locator('.news-story').count()>=3)
  page.locator('#news-week').select_option('2026-W37');page.wait_for_selector('#news-20260911-unitree-er');yes('archive replaces not appends',page.locator('#news-20260916-xplanner').count()==0);yes('older issue explicitly marked','归档' in page.locator('#news-stale').inner_text());yes('partial release shown','部分开放' in page.locator('#news-20260911-unitree-er').inner_text())
  page.locator('#news-category').select_option('model');yes('category filter',page.locator('.news-story').count()==1 and 'GE-Act' in page.locator('.news-story').inner_text())
  page.goto(base+'?view=news&story=news-20260916-xplanner',wait_until='networkidle');page.wait_for_selector('#news-20260916-xplanner details[open]');yes('permalink chooses correct issue and opens story',page.locator('#news-week').input_value()=='2026-W38')
  page.locator('#news-20260916-xplanner [data-focus="p050"]').click();page.wait_for_selector('.reader-chapter');yes('news links to existing reader','view=reader' in page.url and 'paper=p050' in page.url)
  page.locator('.reader-title-tools a[href*="view=news"]').click();page.wait_for_selector('.news-story');yes('reader reverse association works','SayCan' in page.locator('#news-paper-filter').inner_text());page.locator('#news-clear-paper').click();yes('association can be cleared',page.locator('.news-story').count()>=3)
  page.set_viewport_size({'width':390,'height':844});page.evaluate('scrollTo(0,0)');page.wait_for_timeout(200);yes('mobile page contains overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(OUT/'news-mobile.png'))
  page.locator('#news-20260915-digit-5 details').first.locator('summary').click();yes('sources accessible on mobile',page.locator('#news-20260915-digit-5 .news-source').count()==2);page.screenshot(path=str(OUT/'news-mobile-detail.png'))
  page.goto(base+'?view=news&nw=bad&nc=%3Cscript%3E&story=unknown',wait_until='networkidle');page.wait_for_selector('.news-story');yes('invalid routes recover','bad' not in page.locator('#news-issue-number').inner_text())
  # Failed requests must be retryable, not an empty successful edition.
  page.route('**/data/news/**',lambda route:route.abort());page.reload(wait_until='networkidle');page.wait_for_selector('#news-content [role="alert"]');yes('network failure visible',page.locator('#news-content [role="alert"]').count()>0);page.unroute('**/data/news/**');page.locator('#news-content [data-view="news"]').click();page.wait_for_selector('.news-story');yes('retry evicts failed JSON cache',page.locator('.news-story').count()>0)
  yes('no uncaught script errors',not errors)
  (OUT/'audit.json').write_text(json.dumps({'status':'pass','count':len(checks),'checks':checks,'errors':errors,'mode':'real HTTP Chromium; viewport emulation, not physical phone or production network'},ensure_ascii=False,indent=2));print('PASS news browser:',len(checks),'checks');browser.close()
except Exception as e:
 (OUT/'failure.json').write_text(json.dumps({'error':str(e),'checksPassed':checks,'pageErrors':errors},ensure_ascii=False,indent=2));raise
finally:server.terminate();server.wait()
