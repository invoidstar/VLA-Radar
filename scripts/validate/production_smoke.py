"""Post-deploy Pages smoke: confirm current hashed assets and representative deep links."""
from __future__ import annotations
import argparse,hashlib,re,time
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]

def fetch(url:str)->str:
    req=Request(url,headers={'User-Agent':'VLA-Radar-production-smoke/1.0','Cache-Control':'no-cache'})
    with urlopen(req,timeout=20) as r:
        if r.status!=200: raise RuntimeError(f'{url}: HTTP {r.status}')
        return r.read().decode('utf-8')

def main(base:str):
    base=base.rstrip('/')+'/'
    expected=hashlib.sha256((ROOT/'site/js/core/math.js').read_bytes()).hexdigest()[:12]
    wanted=f'math.js?v={expected}'
    last=''
    for attempt in range(8):
        try:
            html=fetch(base);last=html
            if wanted in html: break
        except Exception as exc:
            last=str(exc)
        time.sleep(4)
    else:
        raise SystemExit(f'Pages did not expose current math asset after retries: expected {wanted}; last={last[:300]!r}')
    assert '<title>VLA-Radar · 从论文读到结论</title>' in html
    assert 'rel="canonical" href="https://invoidstar.github.io/VLA-Radar/"' in html
    refs=re.findall(r'(?:src|href)="([^"]+\.(?:js|css)\?v=[0-9a-f]{12})"',html)
    assert len(refs)>=10,refs
    math=fetch(urljoin(base,wanted))
    assert 'RadarMath' in math and 'renderParagraphs' in math
    deep=fetch(base+'?view=reader&paper=p001')
    assert wanted in deep and 'id="reader-section"' in deep
    print(f'PASS production Pages smoke: {len(refs)} hashed assets; current MathML asset; reader deep link.')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--base',required=True);args=ap.parse_args();main(args.base)
