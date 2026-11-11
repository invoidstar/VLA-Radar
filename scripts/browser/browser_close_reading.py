"""Real HTTP browser regression for V3.1 annotated reading, including mobile viewport.

Runs in pinned Playwright Chromium/Firefox/WebKit; no physical phone claims.
"""
from __future__ import annotations
import json, os, shutil, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(os.getenv("RADAR_CLOSE_READING_OUTPUT","/tmp/radar-close-reading"))
OUT.mkdir(parents=True,exist_ok=True)
PUBLIC=Path("/tmp/vla-radar-close-reading-public")
subprocess.run([sys.executable,str(ROOT/"scripts/build/stage_site.py"),"--output",str(PUBLIC)],check=True)
sock=socket.socket();sock.bind(("127.0.0.1",0));port=sock.getsockname()[1];sock.close()
base=f"http://127.0.0.1:{port}/"
server=subprocess.Popen([sys.executable,"-m","http.server",str(port),"--bind","127.0.0.1"],
                        cwd=PUBLIC,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
checks=[]
errors=[]

def yes(label,value):
    assert value,label
    checks.append(label)

def page_errors(msg):
    errors.append(str(msg))

def block_fonts(page):
    page.route("https://fonts.googleapis.com/**",lambda route:route.abort())
    page.route("https://fonts.gstatic.com/**",lambda route:route.abort())

try:
    time.sleep(.35)
    with sync_playwright() as p:
        for engine in ("chromium","firefox","webkit"):
            e=getattr(p,engine)
            opts={"headless":True}
            if engine=="chromium":
                opts["executable_path"]=shutil.which("chromium") or shutil.which("google-chrome")
                opts["args"]=["--no-sandbox"]
            browser=e.launch(**opts)
            context=browser.new_context(viewport={"width":1340,"height":900})
            page=context.new_page()
            page.on("pageerror",page_errors)
            requests=[]
            page.on("request",lambda req:requests.append(req.url))
            block_fonts(page)
            page.goto(base,wait_until="domcontentloaded")
            page.wait_for_selector(".paper-card",timeout=20000)
            yes(engine+" lazy initial load",not any("/data/close-readings/p148.json" in x for x in requests))
            page.locator('[data-nav-group="discover"] [data-view="close-reading"]').click()
            page.wait_for_selector("#close-reading-section:not(.hidden) .close-card",timeout=20000)
            yes(engine+" paper list",page.locator(".close-card").count()==1)
            yes(engine+" paper list URL","view=close-reading" in page.url)
            page.locator(".close-card .close-open").click()
            page.wait_for_function("window.RadarCloseReadingTest?.units===123",timeout=20000)
            yes(engine+" source-linked route","/close-reading/p148/" in page.url)
            yes(engine+" 101 + 22 original locations",page.locator("article.reading-row").count()==123)
            yes(engine+" exact paper and section identity",page.locator("#P001").count()==1 and page.locator("#TAB3").count()==1 and page.locator("#FIG1").count()==1)
            yes(engine+" 18 chapters",page.locator(".paper-section").count()==18)
            yes(engine+" 5 highlight dimensions",page.locator("[data-dimension]").count()==5)
            yes(engine+" no inline mirrored PDF imagery",page.locator("img[src^='data:']").count()==0 and page.locator(".reading-row img").count()==0)
            yes(engine+" source citations",page.locator("#P001 .source-link").get_attribute("href").endswith("#page=1"))
            yes(engine+" canonical Benchmarks",page.locator("#TAB3 .source-button-row a[href*='view=leaderboards']").count()==1)
            if engine=="chromium":
                page.screenshot(path=str(OUT/"desktop.png"),full_page=False)
                page.locator("#unit-search").fill("RoboTwin")
                page.wait_for_function("window.RadarCloseReadingTest.visible()>0 && window.RadarCloseReadingTest.visible()<123",timeout=12000)
                yes("search filters source content",0<page.locator("article.reading-row").count()<123)
                page.locator("#unit-search").fill("")
                page.wait_for_function("window.RadarCloseReadingTest.visible()===123",timeout=12000)
                page.locator("#notes-toggle").uncheck()
                yes("notes toggle hides right side",page.locator("body").evaluate("e=>e.classList.contains('no-notes')"))
                page.locator("#notes-toggle").check()
                page.locator("#language-mode").select_option("zh")
                yes("Chinese focus mode",page.locator("body").evaluate("e=>e.classList.contains('only-chinese')"))
                page.locator("#language-mode").select_option("bilingual")
                page.locator('[data-dimension="method"]').click()
                yes("highlight toggle",page.locator("body").evaluate("e=>e.classList.contains('hide-method')"))
                mobile=browser.new_context(viewport={"width":390,"height":844},is_mobile=True,device_scale_factor=1)
                m=mobile.new_page()
                m.on("pageerror",page_errors)
                block_fonts(m)
                m.goto(base+"close-reading/p148/#TAB3",wait_until="domcontentloaded")
                m.wait_for_function("window.RadarCloseReadingTest?.units===123",timeout=20000)
                dimension=m.evaluate("({width:innerWidth,documentWidth:document.documentElement.scrollWidth})")
                yes("mobile no horizontal page overflow",dimension["documentWidth"]<=dimension["width"]+2)
                yes("mobile deep-link TAB3",m.locator("#TAB3").count()==1)
                m.screenshot(path=str(OUT/"mobile.png"),full_page=False)
                mobile.close()
            context.close()
            browser.close()
        yes("no uncaught page errors",not errors)
    (OUT/"audit.json").write_text(json.dumps({"status":"pass","checks":checks,"count":len(checks),"errors":errors,
      "scope":"Real HTTP pinned Chromium/Firefox/WebKit, mobile viewport simulation (not a physical phone)"},ensure_ascii=False,indent=2))
    print("PASS close-reading browser",len(checks),"checks")
except Exception as exc:
    (OUT/"failure.json").write_text(json.dumps({"error":str(exc),"checks":checks,"errors":errors},ensure_ascii=False,indent=2))
    raise
finally:
    server.terminate()
    server.wait()
