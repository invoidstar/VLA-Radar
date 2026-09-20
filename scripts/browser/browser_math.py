"""Small cross-browser MathML smoke using the same public note renderer."""
from __future__ import annotations
import json,os,shutil,socket,subprocess,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=Path('/tmp/vla-radar-math-public')
OUT=Path(os.environ.get('RADAR_MATH_OUTPUT','/tmp/radar-math-browser'));OUT.mkdir(parents=True,exist_ok=True)
subprocess.run(['python',str(ROOT/'scripts/build/stage_site.py'),'--output',str(PUBLIC)],check=True)
sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
server=subprocess.Popen(['python','-m','http.server',str(port),'--bind','127.0.0.1'],cwd=PUBLIC,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
base=f'http://127.0.0.1:{port}/'
fixture=r"""真实笔记段落
\[
L = \sum_{t=1}^{T}\lVert a_t-\hat{a}_t\rVert^2
\]
行内 $a_t=\frac{\Delta x}{\Delta t}$ 继续正文。"""
checks={}
try:
    time.sleep(.2)
    with sync_playwright() as p:
        for name,browser_type in [('chromium',p.chromium),('firefox',p.firefox),('webkit',p.webkit)]:
            browser=browser_type.launch(headless=True,executable_path=(shutil.which('google-chrome') or shutil.which('chromium')) if name=='chromium' else None)
            page=browser.new_page(viewport={'width':390,'height':844})
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base+'?view=reader&paper=p001',wait_until='networkidle')
            page.wait_for_selector('.reader-chapter')
            page.wait_for_function('Boolean(window.RadarMath && window.RadarResearch && window.RadarResearch.richText)')
            audit=page.evaluate("""source=>{
              const host=document.createElement('section');host.id='cross-browser-math';
              host.innerHTML=window.RadarResearch.noteBlocks(source);document.querySelector('main').appendChild(host);
              const maths=[...host.querySelectorAll('math')],display=host.querySelector('.math-display');
              return {
                count:maths.length,
                visible:maths.every(x=>x.getBoundingClientRect().width>0&&x.getBoundingClientRect().height>0),
                rawDisplay:host.textContent.includes('\\\\[')||host.textContent.includes('\\\\]'),
                rawInline:host.textContent.includes('$a_t'),
                overflow:getComputedStyle(display).overflowX,
                pageOverflow:document.documentElement.scrollWidth>innerWidth+1
              };
            }""",fixture)
            assert audit['count']==2,(name,audit)
            assert audit['visible'],(name,audit)
            assert not audit['rawDisplay'] and not audit['rawInline'],(name,audit)
            assert audit['overflow']=='auto',(name,audit)
            assert not audit['pageOverflow'],(name,audit)
            assert not errors,(name,errors)
            checks[name]=audit
            browser.close()
    (OUT/'audit.json').write_text(json.dumps({'status':'pass','engines':checks,'scope':'native MathML through the real Reader route and RadarResearch.noteBlocks; local staged HTTP'},ensure_ascii=False,indent=2))
    print('PASS cross-browser MathML:',', '.join(checks))
finally:
    server.terminate();server.wait()
