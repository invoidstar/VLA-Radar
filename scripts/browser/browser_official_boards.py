"""Real-browser verification of the three source-pinned official benchmark snapshots."""
from pathlib import Path
from urllib.parse import urlencode
import os
import shutil
import socket
import subprocess
import time

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = Path('/tmp/vla-radar-official-test-site')
OUT = Path('/tmp/radar-official-boards')
OUT.mkdir(parents=True, exist_ok=True)
subprocess.run(['python',str(ROOT/'scripts/build/stage_site.py'),'--output',str(PUBLIC)],check=True)
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0))
    port=sock.getsockname()[1]
server=subprocess.Popen(['python','-m','http.server',str(port),'--bind','127.0.0.1'],
    cwd=PUBLIC,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(.3)
base=f'http://127.0.0.1:{port}/'
errors=[]
count=0
def check(label,result):
    global count
    assert result,label
    count+=1
def show(page,dataset,cases=False):
    q={'view':'leaderboards','dataset':dataset}
    if cases:q['lbType']='cases'
    page.goto(base+'?'+urlencode(q),wait_until='networkidle')
    page.wait_for_selector('.setting-table')
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),
            headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.on('pageerror',lambda err:errors.append(str(err)))
        show(page,'LIBERO')
        check('LIBERO audit summary exists',page.locator('.benchmark-audit-note').count()==1)
        check('LIBERO has no fabricated source-complete official leaderboard',
            page.locator('.benchmark-official').count()==0)
        show(page,'RoboTwin')
        page.wait_for_selector('.benchmark-official summary')
        check('RoboTwin snapshot is dated and pinned',
            '2026-10-11' in page.locator('.benchmark-official summary').inner_text())
        page.locator('.benchmark-official summary').click()
        page.wait_for_selector('[data-official-model="PatchWAM"]')
        check('RoboTwin top score keeps percent semantics',
            '79.14%' in page.locator('[data-official-model="PatchWAM"] .official-score').inner_text())
        page.locator('[data-official-dimension]').select_option('Random')
        check('RoboTwin random evaluation remains distinct',
            '66.72%' in page.locator('[data-official-model="PatchWAM"] .official-score').inner_text())
        page.locator('[data-official-all]').click()
        check('All 25 official RoboTwin submissions remain available',
            page.locator('.official-table tbody tr').count()==25)
        check('Research paper comparison remains a separate table',
            page.locator('.setting-table').count()==1)
        show(page,'RoboDojo')
        page.locator('.benchmark-official summary').click()
        page.wait_for_selector('[data-official-model="VPP2"]')
        check('VPP2 has previously verified paper linkage',
            'p125' in page.locator('[data-official-model="VPP2"] .official-paper-id').inner_text())
        check('Official model without verified paper stays visible',
            page.locator('[data-official-model="PhysicalRSI"]').count()==1)
        page.locator('[data-official-measure]').select_option('sr')
        check('RoboDojo SR is percent, never partial-progress Score',
            '32.26%' in page.locator('[data-official-model="VPP2"] .official-score').inner_text())
        page.locator('[data-official-all]').click()
        check('All 57 official RoboDojo simulation submissions remain visible',
            page.locator('.official-table tbody tr').count()==57)
        show(page,'RoboDojo real')
        check('RoboDojo Real is a public standardized Benchmark, not a paper case study',
            page.locator('[data-board-kind="benchmark"]').get_attribute('aria-pressed')=='true')
        page.locator('.benchmark-official summary').click()
        page.wait_for_selector('[data-official-model="OpenWAM-α"]')
        page.locator('[data-official-all]').click()
        page.locator('[data-official-measure]').select_option('sr')
        check('All 11 official real robot entries are retained',
            page.locator('.official-table tbody tr').count()==11)
        check('Genuine zero success is displayed as zero, not missing',
            '0.00%' in page.locator('[data-official-model="DM0"] .official-score').inner_text())
        page.set_viewport_size({'width':390,'height':850})
        check('Official view avoids mobile page overflow',
            page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        page.screenshot(path=str(OUT/'robodojo-real-mobile.png'))
        check('No browser JavaScript errors',not errors)
        browser.close()
finally:
    server.terminate()
    server.wait(timeout=10)
print(f'PASS: {count} official benchmark HTTP/browser assertions.')
