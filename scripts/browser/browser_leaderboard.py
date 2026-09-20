"""Real HTTP regression for sortable columns and source-scoped time/score charts.
Test fixtures and browser preferences are never written to the public catalog.
"""
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
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

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_ROOT = Path('/tmp/vla-radar-public')
subprocess.run(['python', str(ROOT/'scripts/build/stage_site.py'), '--output', str(PUBLIC_ROOT)], check=True)
OUT = Path(os.environ.get('RADAR_LEADERBOARD_OUTPUT', '/tmp/radar-leaderboard'))
OUT.mkdir(parents=True, exist_ok=True)
with socket.socket() as s:
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
server = subprocess.Popen(['python', '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=PUBLIC_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        # Default Benchmark path is Evaluation-Setting-first; search works across all datasets/settings.
        all_settings=boards.get('settings',[])
        page.goto(base+'?view=leaderboards',wait_until='networkidle');page.wait_for_selector('#benchmark-search-input')
        yes('Benchmark search is visible on default view',page.locator('#benchmark-search-form').count()==1)
        page.locator('#benchmark-search-input').fill('RoboTwin 50 tasks clean random');page.locator('#benchmark-search-form').press('Enter')
        page.wait_for_function('new URLSearchParams(location.search).get("lbSearch")==="RoboTwin 50 tasks clean random"')
        page.wait_for_selector('.setting-table')
        yes('global search narrows Benchmark tabs',page.locator('[data-setting-dataset]').count()==1 and page.locator('[data-setting-dataset]').inner_text()=='RoboTwin')
        yes('global search narrows Settings',page.locator('#setting-select option').count()==1 and 'Clean + Random' in page.locator('#setting-select option').inner_text())
        page.reload(wait_until='networkidle');page.wait_for_selector('#benchmark-search-input')
        yes('Benchmark search persists across refresh',page.locator('#benchmark-search-input').input_value()=='RoboTwin 50 tasks clean random' and page.locator('[data-setting-dataset]').count()==1)
        page.locator('#benchmark-search-clear').click();page.wait_for_function('!new URLSearchParams(location.search).has("lbSearch")');page.wait_for_selector('#benchmark-search-input')
        yes('clearing search restores all Benchmark tabs',page.locator('[data-setting-dataset]').count()>10)
        rt=next(s for s in all_settings if s['dataset']=='RoboTwin' and s['evalId']=='auto:50-clean-random')
        yes('RoboTwin evaluation settings collapse track clutter',len([s for s in all_settings if s['dataset']=='RoboTwin'])<len([t for t in boards['tracks'] if t['dataset']=='RoboTwin']))
        yes('RoboTwin main Setting is genuinely cross-paper and cross-training',rt['paperCount']>=10 and len(rt['trainingOptions'])>=5 and len(rt['trackIds'])>=6)
        page.goto(base+'?'+urlencode({'view':'leaderboards','dataset':'RoboTwin','setting':rt['id']}),wait_until='networkidle')
        page.wait_for_selector('.setting-summary');page.wait_for_function('(sid)=>document.querySelector("#setting-select")?.value===sid',arg=rt['id'])
        yes('default benchmark view keeps Setting adjacent to scores',page.locator('.setting-summary').count()==1 and page.locator('.setting-table').count()==1 and page.locator('#lb-track').count()==0)
        yes('Setting identity is evaluation-only','EVALUATION PROTOCOL ONLY' in page.locator('.setting-summary').inner_text())
        yes('Training Data is a row column and filter',page.locator('#setting-train option').count()>=5 and page.locator('.setting-training-cell').count()>0)
        yes('Method and Source filters are available',page.locator('#setting-method option').count()>2 and page.locator('#setting-source option').count()>=10)
        before=page.locator('.setting-table tbody tr').count()
        train_value=page.locator('#setting-train option').nth(1).get_attribute('value')
        page.locator('#setting-train').select_option(train_value);page.wait_for_function('(v)=>document.querySelector("#setting-train")?.value===v',arg=train_value)
        after=page.locator('.setting-table tbody tr').count()
        yes('Training Data filter narrows reports without changing Setting',after>0 and after<=before and page.locator('#setting-select').input_value()==rt['id'])
        page.locator('#setting-train').select_option('all')
        pi_option=page.locator('#setting-method option').filter(has_text='π0.5').first
        if pi_option.count():
            page.locator('#setting-method').select_option(pi_option.get_attribute('value'));page.wait_for_timeout(120)
            yes('same Method can keep multiple source reports',page.locator('.setting-table tbody tr').count()>=2)
            page.locator('#setting-method').select_option('all')
        source_ids=page.locator('.setting-source .board-paper-link').evaluate_all('(els)=>[...new Set(els.map(e=>e.dataset.paper))]')
        yes('same Setting preserves separate source papers',len(source_ids)>=5)
        page.locator('.setting-recipe details').first.locator('summary').click()
        yes('result row expands recipe and evidence','Training recipe' in page.locator('.setting-recipe details').first.inner_text() and page.locator('.recipe-evidence-actions a').count()>=2)
        advanced=page.locator('.setting-advanced-link').get_attribute('href')
        yes('Setting offers exact original-track advanced view','track=' in advanced)
        page.set_viewport_size({'width':390,'height':900});page.wait_for_timeout(100)
        yes('Setting view avoids mobile page overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        page.set_viewport_size({'width':1440,'height':1100})
        rm=next(s for s in all_settings if s['dataset']=='RoboMimic' and {'robomimic-corl21-lowdim-ph-best','robomimic-corl21-image-ph-best'}<=set(s['trackIds']))
        page.goto(base+'?'+urlencode({'view':'leaderboards','dataset':'RoboMimic','setting':rm['id']}),wait_until='networkidle');page.wait_for_selector('.setting-table')
        yes('same method reports are never deduplicated',page.locator('.setting-method strong').all_text_contents().count('BC-RNN')>=2)
        li=next(s for s in all_settings if s['dataset']=='LIBERO' and s['evalId']=='auto:standard40')
        page.goto(base+'?'+urlencode({'view':'leaderboards','dataset':'LIBERO','setting':li['id']}),wait_until='networkidle');page.wait_for_selector('.setting-table')
        yes('LIBERO standard Setting aggregates many papers',li['paperCount']>=10 and li['resultCount']>=50)
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
        # Source navigation organizes entries only; all scoring remains track-scoped.
        open_track(page,t,lbMetric='Object',lbOrder='desc',lbChart='scatter')
        page.wait_for_selector('.score-scatter')
        ids=page.locator('[data-result-id]').evaluate_all('(els)=>els.map(x=>x.dataset.resultId)')
        yes('source navigation shown by default',page.locator('#lb-group').is_enabled())
        yes('deep link resolves correct source group','OpenVLA' in page.locator('#lb-group option:checked').inner_text())
        yes('specific selector is scoped to source',page.locator('#lb-track option').count()<len([t for t in boards['tracks'] if t['dataset']=='LIBERO']))
        yes('full protocol collapsed by default',not page.locator('.protocol-details').evaluate('(e)=>e.open'))
        page.locator('.protocol-details summary').click()
        yes('full protocol and budget remain accessible',page.locator('.protocol-details').evaluate('(e)=>e.open') and bool(page.locator('.protocol-facts').inner_text()))
        page.locator('#lb-all').click();page.wait_for_function('document.querySelector("#lb-all")?.getAttribute("aria-pressed")==="true"')
        yes('all-settings mode keeps entire dataset list',page.locator('#lb-track option').count()==len([t for t in boards['tracks'] if t['dataset']=='LIBERO']))
        yes('switching navigation does not aggregate results',page.locator('[data-result-id]').evaluate_all('(els)=>els.map(x=>x.dataset.resultId)')==ids)
        yes('sort and scatter survive navigation toggle',page.locator('#lb-metric').input_value()=='Object' and page.locator('#lb-order').input_value()=='desc' and page.locator('.score-scatter').count()==1)
        page.reload(wait_until='networkidle');page.wait_for_selector('.score-scatter')
        yes('all-settings view persists on refresh',page.locator('#lb-group').is_disabled() and page.locator('#lb-track').input_value()==t)
        page.locator('#lb-all').click();page.wait_for_function('!document.querySelector("#lb-group").disabled')
        yes('return to group preserves exact track',page.locator('#lb-track').input_value()==t)
        open_track(page,'robotwin2-selfwam-27500')
        page.wait_for_selector('.protocol-family-panel')
        yes('RoboTwin uses six protocol families',page.locator('#lb-group option').count()==6)
        yes('standard family hides nineteen-track clutter',page.locator('#lb-track option').count()==6)
        yes('family view is method-first','先选评测协议族' in page.locator('.board-browse-heading').inner_text() and page.locator('.family-method').count()>0)
        pi=page.locator('.family-method').filter(has_text='pi0.5').first
        yes('same method exposes multiple reported recipes','reported recipes' in pi.inner_text())
        pi.locator('.family-recipes summary').click()
        yes('recipe expansion preserves evidence',pi.locator('.recipe-item').count()>=3 and pi.locator('.recipe-actions').count()>=3)
        partial=page.locator('#lb-group option').evaluate_all('(ops)=>String(ops.findIndex(o=>o.textContent.includes("Partial / Subset")))')
        page.locator('#lb-group').select_option(partial);page.wait_for_selector('.protocol-family-panel')
        yes('subset series refuses representative score aggregation','不合并成绩' in page.locator('.protocol-family-panel').inner_text() and page.locator('.family-method-values').count()==0)
        page.locator('#lb-all').click();page.wait_for_function('document.querySelector("#lb-track")?.options.length===19')
        yes('advanced mode still exposes all original RoboTwin tracks',page.locator('#lb-track option').count()==19)
        page.locator('#lb-all').click();page.wait_for_function('!document.querySelector("#lb-group").disabled')
        page.screenshot(path=str(OUT/'robotwin-protocol-family.png'))

        open_track(page,'robocasa365-paper-v1-target-50')
        yes('related budgets share navigation entry',page.locator('#lb-track option[value="robocasa365-paper-v1-target-500"]').count()==1)
        page.locator('#lb-track').select_option('robocasa365-paper-v1-target-500')
        page.wait_for_function('document.querySelector("#lb-track").value==="robocasa365-paper-v1-target-500"')
        yes('budget selection loads only its separate result scope',all(x.startswith('r-robocasa365-paper-v1-target-500') for x in page.locator('[data-result-id]').evaluate_all('(els)=>els.map(x=>x.dataset.resultId)')))
        group_total=page.locator('#lb-group option').count()
        next_group=(int(page.locator('#lb-group').input_value())+1)%group_total
        page.locator('#lb-group').select_option(str(next_group));page.wait_for_function('(n)=>document.querySelector("#lb-group").value===n',arg=str(next_group))
        yes('changing source chooses a valid exact track',page.locator('#lb-track').input_value() in tracks)
        page.screenshot(path=str(OUT/'source-groups-desktop.png'))
        for width in [740,390,320]:
            page.set_viewport_size({'width':width,'height':1000});page.wait_for_timeout(100)
            yes(f'group navigation at {width}px avoids document overflow',page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'))
        page.screenshot(path=str(OUT/'source-groups-mobile.png'))
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
