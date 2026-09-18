"""Real HTTP pointer/keyboard regression; viewports are not physical phones."""
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('RADAR_SIDEBAR_OUTPUT', '/tmp/radar-sidebar'))
OUT.mkdir(parents=True, exist_ok=True)
KEY = 'vla-radar.sidebar-width.v1'
checks, errors, requests = [], [], []

def yes(name, value):
    assert value, name
    checks.append(name)

def width(page):
    return round(page.locator('#sidebar').bounding_box()['width'])

def stored(page):
    return page.evaluate('(key) => localStorage.getItem(key)', KEY)

def drag(page, target):
    box = page.locator('#sidebar-resizer').bounding_box()
    page.mouse.move(box['x'] + box['width']/2, 90)
    page.mouse.down()
    page.mouse.move(target, 90, steps=8)
    page.mouse.up()
    page.wait_for_timeout(60)

def label_fits(page):
    return page.locator('.nav-link[data-view="news"]').evaluate('''el => {
      const text = Array.from(el.childNodes).find(n => n.nodeType === 3 && n.textContent.includes('具身智能周报'));
      if (!text) return false;
      const range = document.createRange(); range.selectNodeContents(text);
      const rects = Array.from(range.getClientRects());
      return rects.length === 1 && el.scrollWidth <= el.clientWidth + 1;
    }''')

sock = socket.socket(); sock.bind(('127.0.0.1', 0))
port = sock.getsockname()[1]; sock.close()
server = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'],
                          cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    time.sleep(.3)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),
                                   headless=True, args=['--no-sandbox'])
        context = browser.new_context(viewport={'width':1100, 'height':900})
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: requests.append(request.url))
        base = f'http://127.0.0.1:{port}/'
        page.goto(base, wait_until='networkidle'); page.wait_for_selector('.paper-card')
        yes('default width 260px', width(page) == 260)
        yes('six-character news label and badge fit one line', label_fits(page))
        yes('startup remains lazy', not any('/data/news/' in u or '/details/' in u or 'search-index.' in u for u in requests))
        yes('accessible separator', page.locator('#sidebar-resizer').get_attribute('role') == 'separator')
        reading = page.evaluate('localStorage.getItem("vla-radar.reading.v1")')
        drag(page, 328)
        yes('actual mouse drag resizes sidebar and main', width(page) == 328 and round(page.locator('.app-shell').bounding_box()['x']) == 328)
        yes('preference saved', stored(page) == '328')
        yes('pointer capture and cursor cleaned up', not page.evaluate('document.documentElement.classList.contains("sidebar-resizing")'))
        page.reload(wait_until='networkidle')
        yes('width survives reload', width(page) == 328)
        page.locator('.nav-link[data-view="news"]').click(); page.wait_for_selector('.news-story')
        yes('news route preserves width', width(page) == 328 and label_fits(page))
        drag(page, 50); yes('lower bound', width(page) == 244 and label_fits(page))
        drag(page, 850); yes('upper bound', width(page) == 380)
        page.set_viewport_size({'width':740, 'height':900}); page.wait_for_timeout(100)
        yes('narrow desktop leaves 400px main area', width(page) == 340 and round(page.locator('.app-shell').bounding_box()['width']) == 400)
        yes('responsive clamp preserves preference', stored(page) == '380')
        yes('740px page has no horizontal overflow', page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'))
        page.set_viewport_size({'width':701, 'height':900}); page.wait_for_timeout(100)
        yes('smallest desktop label fits', width(page) == 301 and label_fits(page))
        page.screenshot(path=str(OUT/'small-desktop.png'))
        page.set_viewport_size({'width':1100, 'height':900}); page.wait_for_timeout(100)
        yes('wide preference restored after viewport expansion', width(page) == 380)
        handle = page.locator('#sidebar-resizer')
        handle.focus(); page.keyboard.press('Home')
        yes('keyboard minimum', width(page) == 244)
        page.keyboard.press('ArrowRight'); page.keyboard.press('Shift+ArrowRight')
        yes('keyboard regular and coarse adjustment', width(page) == 276)
        page.keyboard.press('ArrowLeft'); page.keyboard.press('End')
        yes('keyboard maximum and aria value', width(page) == 380 and handle.get_attribute('aria-valuenow') == '380')
        page.keyboard.press('Enter')
        yes('keyboard reset clears preference', width(page) == 260 and stored(page) is None)
        drag(page, 320); handle.dblclick(position={'x':5, 'y':90})
        yes('double-click reset', width(page) == 260 and stored(page) is None)
        # Escape and lost capture restore pre-drag preference, not an intermediate preview.
        page.mouse.move(260, 90); page.mouse.down(); page.mouse.move(320, 90, steps=5)
        page.keyboard.press('Escape'); page.mouse.up()
        yes('Escape cancels and restores width', width(page) == 260 and stored(page) is None)
        page.mouse.move(260,90); page.mouse.down(); page.mouse.move(310,90,steps=5)
        handle.dispatch_event('pointercancel', {'pointerId':1}); page.mouse.up()
        yes('cancelled pointer leaves no stuck drag', width(page) == 260 and not page.evaluate('document.documentElement.classList.contains("sidebar-resizing")'))
        page.mouse.move(260,90); page.mouse.down(); page.mouse.move(312,90,steps=5)
        handle.evaluate('el => el.releasePointerCapture(1)'); page.mouse.up()
        yes('lost capture cancels safely', width(page) == 260 and stored(page) is None)
        drag(page, 310)
        page.screenshot(path=str(OUT/'desktop.png'))
        for viewport in [700, 390, 320]:
            page.set_viewport_size({'width':viewport, 'height':844}); page.wait_for_timeout(100)
            yes(f'{viewport}px mobile hides resizer without main offset', not handle.is_visible() and round(page.locator('.app-shell').bounding_box()['x']) == 0)
            page.locator('#mobile-menu').click(); page.wait_for_timeout(250)
            yes(f'{viewport}px drawer label fits without overflow', label_fits(page) and page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'))
            if viewport == 390: page.screenshot(path=str(OUT/'mobile.png'))
            page.locator('#mobile-menu').click(); page.wait_for_timeout(250)
        yes('mobile never overwrites desktop preference', stored(page) == '310')
        page.set_viewport_size({'width':1100, 'height':900}); page.wait_for_timeout(100)
        yes('desktop width restored after mobile', width(page) == 310)
        page.emulate_media(media='print')
        yes('print hides resize handle', not handle.is_visible())
        page.emulate_media(media='screen')
        yes('reading state never modified by resizing', page.evaluate('localStorage.getItem("vla-radar.reading.v1")') == reading)
        page.evaluate('(key) => localStorage.setItem(key, "not-a-number")', KEY)
        page.reload(wait_until='networkidle')
        yes('invalid stored value falls back to default', width(page) == 260)
        # A disabled Storage implementation must not stop app or drag interaction.
        blocked = browser.new_context(viewport={'width':1100, 'height':900})
        blocked.add_init_script('''for (const name of ['getItem','setItem','removeItem']) {
          Storage.prototype[name] = function () { throw new DOMException('Disabled', 'SecurityError'); };
        }''')
        blocked_page = blocked.new_page()
        blocked_page.on('pageerror', lambda error: errors.append(str(error)))
        blocked_page.goto(base, wait_until='networkidle'); blocked_page.wait_for_selector('.paper-card')
        drag(blocked_page, 310)
        yes('storage denial still permits rendering and dragging', width(blocked_page) == 310)
        blocked.close()
        yes('no uncaught JavaScript errors', not errors)
        (OUT/'audit.json').write_text(json.dumps({'status':'pass','count':len(checks),'checks':checks,'errors':errors,
             'scope':'Actual HTTP Chromium pointer/keyboard tests; viewport simulation, not a physical phone'}, ensure_ascii=False,indent=2))
        print('PASS sidebar browser:', len(checks), 'checks')
        browser.close()
except Exception as error:
    (OUT/'failure.json').write_text(json.dumps({'error':str(error),'passed':checks,'errors':errors}, ensure_ascii=False,indent=2))
    raise
finally:
    server.terminate(); server.wait()
