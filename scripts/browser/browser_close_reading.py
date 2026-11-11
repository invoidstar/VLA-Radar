"""Real HTTP/browser regression for copyright-safe, modular SLA close reading."""
from __future__ import annotations
import os,sys,shutil,socket,subprocess,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(os.environ.get('RADAR_CLOSE_READING_OUTPUT','/tmp/radar-close-reading'))
OUT.mkdir(parents=True,exist_ok=True)
PUBLIC_ROOT=Path('/tmp/vla-radar-close-reading-stage')
subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_site.py'),'--output',str(PUBLIC_ROOT)],check=True)
ss=socket.socket();ss.bind(('127.0.0.1',0));port=ss.getsockname()[1];ss.close()
server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],cwd=PUBLIC_ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
checks=[]
def yes(name,condition):
    assert condition,name
    checks.append(name)
try:
    time.sleep(.3)
    with sync_playwright() as p:
        for name in ('chromium','firefox','webkit'):
            browser_type=getattr(p,name)
            opts={'headless':True}
            if name=='chromium':
                binary=shutil.which('chromium') or shutil.which('google-chrome')
                if binary:opts['executable_path']=binary
                opts['args']=['--no-sandbox']
            browser=browser_type.launch(**opts)
            context=browser.new_context(viewport={'width':1200,'height':850})
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            base=f'http://127.0.0.1:{port}/'
            page.goto(base,wait_until='domcontentloaded')
            yes(name+' primary nav link',page.locator('a[href="close-reading/"]').count()==1)
            page.goto(base+'close-reading/',wait_until='domcontentloaded')
            page.wait_for_selector('.list-card',timeout=10000)
            yes(name+' listing links SLA',page.locator('.list-card[href="p148/"]').count()==1)
            page.locator('.list-card').click()
            page.wait_for_selector('#P001',timeout=10000)
            yes(name+' stable deep link and 24 units',page.locator('.unit').count()==24)
            yes(name+' 18 source section navigation entries',page.locator('#chapter-nav a').count()==19)
            yes(name+' no hosted original figure',page.locator('img').count()==0)
            yes(name+' source anchor',page.locator('#P001 .proof-links a[href*="arxiv.org/pdf/2611.08373v1#page=1"]').count()==1)
            yes(name+' English indexed keywords clearly not full quoted paragraph','非原文全文' in page.locator('#P001 .english').inner_text())
            page.locator('#search').fill('OmniVGGT')
            yes(name+' keyword search filters',page.locator('.unit').count()==1)
            page.locator('#search').fill('')
            page.locator('#notes').uncheck()
            yes(name+' notes toggle',page.locator('body.no-notes').count()==1)
            page.locator('#notes').check()
            page.locator('#lang').select_option('zh')
            yes(name+' Chinese-only toggle',page.locator('body.zh-only').count()==1)
            page.locator('#lang').select_option('annotated')
            page.locator('[data-highlight="thesis"]').click()
            yes(name+' highlighter toggles',page.locator('[data-highlight="thesis"]').get_attribute('aria-pressed')=='false')
            yes(name+' isolated reading key only',page.evaluate("""() => localStorage.getItem('vla-radar.close-reading.v1') !== null && localStorage.getItem('vla-radar.reading.v1') === null"""))
            if name=='chromium':
                page.set_viewport_size({'width':390,'height':844})
                yes('mobile content does not overflow horizontally',page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+2'))
                page.screenshot(path=str(OUT/'sla-mobile.png'),full_page=False)
                page.set_viewport_size({'width':1200,'height':850})
                page.screenshot(path=str(OUT/'sla-desktop.png'),full_page=False)
            yes(name+' no JS errors',not errors)
            context.close();browser.close()
finally:
    server.terminate()
    try:server.wait(timeout=4)
    except subprocess.TimeoutExpired:server.kill()
print('PASS close-reading live-HTTP regression: '+str(len(checks))+' checks, chromium/firefox/webkit')
