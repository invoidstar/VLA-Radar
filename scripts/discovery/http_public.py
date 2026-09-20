"""Bounded public-only HTTP client. Network failures are evidence gaps, not deletions."""
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import ipaddress, socket, time
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from catalog_core import public_url
AGENT='VLA-Radar/2.0 (public literature maintenance; https://github.com/invoidstar/VLA-Radar)'
def check_host(url):
    public_url(url)
    from urllib.parse import urlparse
    host=urlparse(url).hostname
    addresses=socket.getaddrinfo(host,None,type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):raise ValueError('DNS resolved to a non-public address')
class PublicRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        check_host(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)
def fetch(url,timeout=18,max_bytes=6000000,method='GET',attempts=2,accept=None):
    check_host(url);last=None
    for attempt in range(attempts):
        try:
            req=Request(url,headers={'User-Agent':AGENT,'Accept':accept or 'text/html,application/json;q=0.9,*/*;q=0.8'},method=method)
            with build_opener(PublicRedirect()).open(req,timeout=timeout) as r:
                body=r.read(max_bytes+1)
                if len(body)>max_bytes:raise ValueError('response exceeds size limit')
                return body.decode('utf-8',errors='replace'),r.status,r.url
        except HTTPError as e:
            last=e
            if e.code not in {429,500,502,503,504} or attempt+1==attempts:raise
        except (URLError,TimeoutError,OSError) as e:
            last=e
            if attempt+1==attempts:raise
        delay=3*(attempt+1)
        if isinstance(last,HTTPError) and last.headers:
            retry=last.headers.get('Retry-After','')
            if retry.isdigit():
                if int(retry)>60: raise last
                delay=max(delay,int(retry))
        time.sleep(delay)
    raise last
