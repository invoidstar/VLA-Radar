"""Real HTTP regression for sortable columns and source-scoped time/score charts.
Test fixtures and browser preferences are never written to the public catalog.
"""
import csv
import io
import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('RADAR_LEADERBOARD_OUTPUT', '/tmp/radar-leaderboard'))
OUT.mkdir(parents=True, exist_ok=True)
with socket.socket() as s:
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
server = subprocess.Popen(['python', '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(.3)
base = f'http://127.0.0.1:{port}/'
checks, errors, requests = [], [], []
boards = json.loads((ROOT/'data/leaderboards.json').read_text())
lib = json.loads((ROOT/'data/library.json').read_text())
papers = {p['id']: p for p in lib['papers']}
tracks = {t['id']: t for t in boards['tracks']}

def yes(name, value):
    assert value, name
    checks.append(name)

def open_track(page, track, **params):
    page.goto(base+'?'+urlencode({'view':'leaderboards', 'dataset':tracks[track]['dataset'], 'track':track, **params}), wait_until='networkidle')
    page.wait_for_selector('#lb-track')
    page.wait_for_function('(id)=>document.querySelector("#lb-track")?.value===id', arg=track)

def wait_sort(page, metric, order=None):
    page.wait_for_function('([m,o])=>document.querySelector("#lb-metric")?.value===m && (!o || document.querySelector("#lb-order")?.value===o)', arg=[metric,order])
    page.wait_for_function('(m)=>Boolean(document.querySelector("th[aria-sort] button")?.dataset.sortColumn===m)',arg=metric)

def methods(page):
    return page.locator('.board-table tbody tr > td:nth-child(2) > strong').all_text_contents()

def click_point(page, locator):
    # Actual pointer input at the source coordinate; dense SVG circles can overlap.
    locator.scroll_into_view_if_needed()
    xy=locator.evaluate('(g)=>{const c=g.querySelector(".scatter-dot"),p=new DOMPoint(c.cx.baseVal.value,c.cy.baseVal.value).matrixTransform(g.getScreenCTM());return [p.x,p.y];}')
    page.mouse.click(*xy)

try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),headless=True,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1440,'height':1100},accept_downloads=True)
        page=context.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:requests.append(r.url))
        page.goto(base,wait_until='networkidle');page.wait_for_selector('.paper-card')
        yes('home still has twelve cards',page.locator('.paper-card').count()==12)
        yes('chart data and optional code not loaded on home',not any('experience.js?' in u or 'board-index.' in u or '/data/boards/' in u for u in requests))
        page.evaluate('localStorage.setItem("vla-radar.reading.v1", JSON.stringify({p001:{status:"reading",saved:true}}))')
        reading=page.evaluate('localStorage.getItem("vla-radar.reading.v1")')

        t='libero-openvla-v3-singleview-cleaned'
        open_track(page,t,lbMetric='Object',lbOrder='desc')
        yes('paper-table metric is enabled',page.locator('#lb-metric').is_enabled())
        yes('selected column affects initial order',methods(page)[0]=='Diffusion Policy (from scratch)')
        yes('paper-table still has no fair rank column',page.locator('.board-table thead th').first.inner_text()=='记录')
        page.locator('[data-sort-column="Object"]').click();wait_sort(page,'Object','asc')
        yes('header toggles ascending',methods(page)[0]=='Octo (fine-tuned)')
        yes('aria-sort on only active header',page.locator('th[aria-sort]').count()==1 and page.locator('th[aria-sort]').get_attribute('aria-sort')=='ascending')
        yes('header retains keyboard focus',page.locator('[data-sort-column="Object"]').evaluate('(el)=>el===document.activeElement'))
        page.locator('[data-sort-column="Goal"]').focus();page.keyboard.press('Enter');wait_sort(page,'Goal','auto')
        yes('keyboard sorts another column',methods(page)[0]=='Octo (fine-tuned)')
        page.locator('#lb-metric').select_option('Long');wait_sort(page,'Long')
        yes('dropdown and header synchronized',page.locator('th[aria-sort] button').get_attribute('data-sort-column')=='Long')
        page.locator('#lb-order').select_option('source')
        page.wait_for_function('document.querySelector("#lb-order").value==="source" && !document.querySelector("th[aria-sort]")')
        source_methods=[r['method'] for r in boards['results'] if r['trackId']==t and r['evidence']=='checked']
        yes('original record order can be restored',methods(page)==source_methods)
        page.locator('#lb-order').select_option('asc');wait_sort(page,'Long','asc')
        with page.expect_download() as event:page.locator('#export-protocol-csv').click()
        download=event.value;download.save_as(str(OUT/'protocol.csv'))
        parsed=list(csv.reader(io.StringIO((OUT/'protocol.csv').read_text(encoding='utf-8-sig'))))
        yes('CSV follows displayed order',parsed[1][0]==methods(page)[0])

        page.locator('#show-time-scatter').click();page.wait_for_selector('.score-scatter')
        yes('scatter takes currently selected metric',page.locator('#chart-metric').input_value()=='Long')
        yes('source-date semantics explicit','不一定是被引用基线的方法首发' in page.locator('.scatter-time-note').inner_text())
        yes('all values remain separate points',page.locator('[data-scatter-point]').count()==3)
        page.locator('[data-scatter-point]').first.focus()
        yes('keyboard point focus shows source','p064' in page.locator('#scatter-detail').inner_text())
        yes('source first date displayed',papers['p064']['firstPublished'] in page.locator('#scatter-detail').inner_text())
        yes('no lines pretend to show trend',page.locator('.score-scatter path,.score-scatter polyline').count()==0)
        yes('single-date data disclosed','当前只有一个日期' in page.locator('#protocol-plot').inner_text())
        page.locator('#chart-metric').select_option('Object');wait_sort(page,'Object','asc');page.wait_for_selector('.score-scatter')
        yes('chart metric also sorts table',methods(page)[0]=='Octo (fine-tuned)' and page.locator('#lb-metric').input_value()=='Object')
        page.locator('#chart-time').select_option('verifiedAt');page.wait_for_function('document.querySelector("#chart-time")?.value==="verifiedAt"');page.wait_for_selector('.score-scatter')
        click_point(page,page.locator('[data-scatter-point]').first)
        yes('verification date separately labelled','本站结果核验日期' in page.locator('#scatter-detail').inner_text())
        with page.expect_download() as event:page.locator('#export-scatter-csv').click()
        event.value.save_as(str(OUT/'scatter.csv'))
        parsed=list(csv.reader(io.StringIO((OUT/'scatter.csv').read_text(encoding='utf-8-sig'))))
        yes('scatter CSV preserves date basis and all rows',len(parsed)==4 and parsed[1][6]=='VLA-Radar verification date')
        page.reload(wait_until='networkidle');page.wait_for_selector('.score-scatter')
        yes('refresh preserves sorting and plot choices',page.locator('#lb-metric').input_value()=='Object' and page.locator('#lb-order').input_value()=='asc' and page.locator('#chart-time').input_value()=='verifiedAt')
        page.locator('#chart-type').select_option('bar');page.wait_for_selector('.chart-row')
        yes('bar plot still works and shares selected metric',page.locator('#chart-metric').input_value()=='Object')
        page.locator('#show-protocol-chart').click();page.wait_for_function('document.querySelector("#protocol-chart").hidden')
        yes('chart can be collapsed',page.locator('#protocol-chart').is_hidden())
        page.locator('#show-time-scatter').click();page.wait_for_selector('.score-scatter')
        page.locator('#chart-time').select_option('firstPublished');page.wait_for_function('document.querySelector("#chart-time")?.value==="firstPublished"')
        page.locator('#protocol-chart').scroll_into_view_if_needed();page.screenshot(path=str(OUT/'scatter-desktop.png'))

        open_track(page,'rlbench-rvt2-v1-table1',lbMetric='Close Jar',lbOrder='asc',lbChart='scatter')
        page.wait_for_selector('.score-scatter')
        yes('missing selected value stays at end in ascending order',methods(page)[-1]=='Act3D（原文引用）')
        yes('missing selected value is omitted not plotted as zero','成绩缺失 1 条' in page.locator('.scatter-summary').inner_text())
        page.locator('#lb-order').select_option('desc');wait_sort(page,'Close Jar','desc')
        yes('missing stays last in descending order',methods(page)[-1]=='Act3D（原文引用）')

        open_track(page,'robocasa24-cosmos-table',lbChart='scatter')
        page.wait_for_selector('.score-scatter')
        overlap=page.locator('[data-scatter-point][aria-label^="2条重合记录"]')
        yes('identical time and score grouped without shifting dates',overlap.count()>=1)
        click_point(page,overlap.first)
        yes('overlap reveals both original records',page.locator('#scatter-detail .scatter-record').count()==2)

        open_track(page,'rlbench-chained-corl2023-standard10',lbChart='scatter')
        page.wait_for_selector('#export-scatter-csv')
        yes('unknown first date is not filled from publication date',page.locator('.score-scatter').count()==0 and '缺少精确日期' in page.locator('.scatter-summary').inner_text())
        page.locator('#chart-time').select_option('verifiedAt');page.wait_for_selector('.score-scatter')
        yes('undated source can still use separately labelled verification date',page.locator('[data-scatter-point]').count()>0)

        open_track(page,'libero-original-neurips23-nbt',lbChart='scatter')
        page.wait_for_selector('.score-scatter')
        yes('lower is better auto order',float(page.locator('td.selected-metric').first.inner_text())==.07)
        yes('score ticks not mislabeled percent','%' not in ''.join(page.locator('.scatter-tick').all_text_contents()))
        page.locator('#lb-order').select_option('desc');wait_sort(page,'Spatial','desc')
        yes('explicit descending still available for lower metric',float(page.locator('td.selected-metric').first.inner_text())==.81)
        yes('metric direction remains visible','越低越好' in page.locator('.board-sort-status').inner_text())
        for width in [740,390,320]:
            page.set_viewport_size({'width':width,'height':1000});page.wait_for_timeout(100)
            yes(f'{width}px viewport avoids page-wide overflow',page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'))
        page.locator('#protocol-chart').scroll_into_view_if_needed();page.screenshot(path=str(OUT/'scatter-mobile.png'))
        page.set_viewport_size({'width':1440,'height':1100})

        open_track(page,t,lbMetric='<invalid>',lbOrder='bad',lbChart='bad',lbTime='bad')
        yes('invalid URL values normalized',page.locator('#lb-metric').input_value()=='Average' and page.locator('#lb-order').input_value()=='auto' and page.locator('#protocol-chart').is_hidden())
        yes('original reading storage unchanged',page.evaluate('localStorage.getItem("vla-radar.reading.v1")')==reading)
        yes('no uncaught JavaScript errors',not errors)
        yes('plot uses local public shards only',all(u.startswith(base) or u.startswith('data:') for u in requests))
        (OUT/'audit.json').write_text(json.dumps({'status':'pass','count':len(checks),'checks':checks,'pageErrors':errors,'mode':'Real HTTP Chromium; mobile viewport simulation, not physical hardware or production network'},ensure_ascii=False,indent=2))
        print(f'PASS leaderboard HTTP integration: {len(checks)} checks')
        browser.close()
except Exception as exc:
    (OUT/'failure.json').write_text(json.dumps({'error':str(exc),'checks':checks,'pageErrors':errors},ensure_ascii=False,indent=2))
    try:page.screenshot(path=str(OUT/'failure.png'),full_page=True)
    except Exception:pass
    raise
finally:
    server.terminate();server.wait()
