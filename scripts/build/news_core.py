"""Public news schema and deterministic weekly shards. No runtime network or private data."""
from __future__ import annotations
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import hashlib, ipaddress, json, re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

CATEGORIES = {'model':'模型与世界模型','dataset':'数据与资源','benchmark':'评测基准','robot':'机器人与部署','industry':'产业动态','research':'研究进展','opensource':'开放发布','conference':'会议动态'}
STAGES = {'announced','released','partial-release','preview','planned','reported'}
LABELS = {'official','paper-backed','reported'}
SCHEMA = {'schemaVersion','id','eventKey','title','primaryCategory','tags','eventDate','publishedAt','dateNote','observedAt','updatedAt','stage','evidence','status','featured','importance','whatHappened','whyItMatters','vlaRelevance','limits','sources','paperLinks','revisionHistory'}
SOURCE_KEYS = {'id','title','publisher','url','kind','publishedAt','access','note'}

def require(ok,message):
    if not ok: raise ValueError(message)
def text(obj): return json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n'
def day(value,nullable=False):
    if value is None and nullable:return None
    require(isinstance(value,str) and bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}',value)),'ISO date required')
    return date.fromisoformat(value)
def url(value):
    require(isinstance(value,str),'URL required')
    u=urlsplit(value)
    require(u.scheme=='https' and u.hostname and not u.username and not u.password,'public HTTPS URL required')
    require(u.hostname not in {'localhost','localhost.localdomain'} and '.' in u.hostname,'public host required')
    try: addr=ipaddress.ip_address(u.hostname)
    except ValueError: addr=None
    require(addr is None or addr.is_global,'private addresses are forbidden')
    return urlunsplit((u.scheme,u.netloc.lower(),u.path.rstrip('/'),u.query,''))
def week_key(value):
    d=day(value); y,w,_=d.isocalendar();return f'{y}-W{w:02}'
def week_start(key):
    require(bool(re.fullmatch(r'\d{4}-W\d{2}',key)),'invalid week key')
    y,w=key.split('-W');return date.fromisocalendar(int(y),int(w),1)
def stamp(record): return record['eventDate'] or record['publishedAt']

def validate(records,paper_ids,state,today=None):
    today=today or date.today(); ids=set();keys=set();canonical=set()
    require(state.get('schemaVersion')==1 and state.get('status') in {'not_run','partial','complete'},'news state schema')
    asof=day(state['asOf']);require(asof<=today,'future news checkpoint')
    require(state.get('lastSuccessfulSearchAt') is None or day(state['lastSuccessfulSearchAt'])<=asof,'invalid news success checkpoint')
    if state['status']!='complete':
        require(state.get('lastSuccessfulSearchAt')!=state['asOf'],'partial scan cannot claim complete checkpoint')
    require(isinstance(state.get('coverage'),list),'coverage required')
    for c in state['coverage']:
        require(c.get('status') in {'partial','complete'},'coverage status')
        require(day(c['from'])<=day(c['to'])<=asof,'invalid coverage range')
        require(isinstance(c.get('note'),str) and c['note'],'coverage explanation required')
    for r in records:
        require(set(r)==SCHEMA,'unknown/missing news fields: '+str(set(r)^SCHEMA))
        ident=r['id'];require(re.fullmatch(r'news-\d{8}-[a-z0-9-]{3,80}',ident) is not None,'news ID')
        require(ident not in ids and r['eventKey'] not in keys,'duplicate news event');ids.add(ident);keys.add(r['eventKey'])
        require(isinstance(r['eventKey'],str) and 4<=len(r['eventKey'])<=160,'eventKey')
        require(r['schemaVersion']==1 and r['primaryCategory'] in CATEGORIES,'news category')
        require(r['stage'] in STAGES and r['evidence'] in LABELS,'news stage/evidence')
        require(r['status'] in {'verified','corrected','withdrawn'},'unreviewed candidate cannot be published')
        require(type(r['featured']) is bool,'featured boolean')
        require(r['importance'] in {'major-release','research-resource','deployment','ecosystem','conference-milestone'},'significance gate')
        require(isinstance(r['tags'],list) and len(r['tags'])<=8 and all(isinstance(t,str) and 1<=len(t)<=50 for t in r['tags']),'tags')
        event=day(r['eventDate'],True);pub=day(r['publishedAt'],True);obs=day(r['observedAt']);upd=day(r['updatedAt'])
        require(event or pub,'need event or source-publication date; no invented date from discovery')
        require((event is None or event<=asof) and (pub is None or pub<=asof) and obs<=upd<=asof,'future/misordered news dates')
        require((event is None or event<=obs) and (pub is None or pub<=obs),'observation before event/source')
        require(isinstance(r['dateNote'],str) and bool(r['dateNote']),'date basis required')
        for k,lo,hi in [('title',8,130),('whatHappened',25,900),('whyItMatters',25,900),('vlaRelevance',20,700),('limits',25,1100)]:
            require(isinstance(r[k],str) and lo<=len(r[k])<=hi,ident+': '+k+' is too short/long')
        require(isinstance(r['sources'],list) and 1<=len(r['sources'])<=8,'sources required')
        srcids=set();kinds=set()
        for s in r['sources']:
            require(set(s)==SOURCE_KEYS,'source fields');require(s['id'] not in srcids,'duplicate source ID');srcids.add(s['id'])
            u=url(s['url']); kinds.add(s['kind'])
            require(s['kind'] in {'official','paper','repository','media'},'source kind')
            require(s['access'] in {'full-page','excerpt','repository'},'actual source access must be stated')
            d=day(s['publishedAt'],True);require(d is None or d<=obs,'future source date')
            for k in ['title','publisher','note']:require(isinstance(s[k],str) and bool(s[k]),'source '+k)
        primary=url(r['sources'][0]['url']);require(primary not in canonical,'duplicate primary-source event: consolidate coverage');canonical.add(primary)
        if r['evidence']=='official':require(bool(kinds&{'official','repository'}),'official badge needs primary source')
        if r['evidence']=='paper-backed':require('paper' in kinds and any(s['kind']=='paper' and s['access']=='full-page' for s in r['sources']),'paper-backed needs read paper')
        if r['evidence']=='reported':require('media' in kinds,'reported needs attributed reporting')
        require(isinstance(r['paperLinks'],list) and len(r['paperLinks'])<=6,'paperLinks')
        links=set()
        for p in r['paperLinks']:
            require(set(p)=={'paperId','relation','note'} and p['paperId'] in paper_ids,'unknown paper link')
            require(p['paperId'] not in links,'duplicate paper link');links.add(p['paperId'])
            require(p['relation'] in {'direct','background'} and isinstance(p['note'],str) and len(p['note'])>=10,'paper relation must be explicit')
        require(isinstance(r['revisionHistory'],list),'revision history')
        if r['status'] in {'corrected','withdrawn'}:require(r['revisionHistory'],'correction/withdrawal needs history')
        for h in r['revisionHistory']:
            require(set(h)=={'date','note','source'} and day(h['date'])<=upd and len(h['note'])>=10,'invalid revision history');url(h['source'])
    weekly=Counter(week_key(stamp(r)) for r in records)
    require(all(v<=40 for v in weekly.values()),'weekly major-news cap is 40; consolidate repeated coverage')
    return True

def outputs(root,records):
    root=Path(root); state=json.loads((root/'maintenance/state/news-state.json').read_text(encoding='utf-8'))
    news=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((root/'catalog/news').glob('news-*.json'))]
    validate(news,{r['paper']['id'] for r in records},state)
    out={};groups=defaultdict(list);paperweeks=defaultdict(set);lookups={}
    def shard(name,obj):
        data=text(obj);path=f'data/news/{name}.{hashlib.sha256(data.encode()).hexdigest()[:16]}.json';out[path]=data;return path
    for n in news:
        key=week_key(stamp(n));groups[key].append(n);lookups[n['id']]=key
        for p in n['paperLinks']:paperweeks[p['paperId']].add(key)
    def coverage(key):
        start=week_start(key);end=start+timedelta(days=6)
        cs=[c for c in state['coverage'] if day(c['from'])<=min(end,day(state['asOf'])) and day(c['to'])>=start]
        if any(c['status']=='complete' and day(c['from'])<=start and day(c['to'])>=end for c in cs):return 'complete'
        return 'partial' if cs else 'not_run'
    # Retain explicitly searched empty issues too. Unscanned weeks stay unknown, not zero.
    for c in state['coverage']:
        d=week_start(week_key(c['from']))
        while d<=day(c['to']):groups.setdefault(week_key(d.isoformat()),[]);d+=timedelta(days=7)
    weeks=[]
    for key,items in sorted(groups.items(),reverse=True):
        items.sort(key=lambda n:(stamp(n),n['id']),reverse=True)
        chunks=[{'url':shard(key+'-'+str(i//20),{'schemaVersion':1,'week':key,'items':items[i:i+20]}),'count':len(items[i:i+20])} for i in range(0,len(items),20)]
        picks=sorted([n for n in items if n['featured'] and n['status']!='withdrawn'],key=lambda n:(stamp(n),n['id']),reverse=True)[:5]
        start=week_start(key);counts=Counter(n['primaryCategory'] for n in items if n['status']!='withdrawn')
        weeks.append({'key':key,'from':start.isoformat(),'to':(start+timedelta(days=6)).isoformat(),'count':len(items),'coverage':coverage(key),'counts':dict(counts),'pages':chunks,'featuredIds':[n['id'] for n in picks]})
    start=week_start(week_key(state['asOf']));trend=[];weekmap={w['key']:w for w in weeks}
    for i in range(11,-1,-1):
        key=week_key((start-timedelta(weeks=i)).isoformat());w=weekmap.get(key);cov=coverage(key)
        trend.append({'week':key,'status':cov,'count':w['count'] if w else (0 if cov=='complete' else None)})
    index={'schemaVersion':1,'asOf':state['asOf'],'status':state['status'],'searchNote':state['summary'],'categories':[{'id':k,'name':v} for k,v in CATEGORIES.items()],'total':len(news),'weeks':weeks,'trend':trend,'storyWeeks':lookups,'paperWeeks':{p:sorted(v,reverse=True) for p,v in paperweeks.items()},'scope':'本站编辑收录量，不代表领域热度；未检索周为未知，非零条新闻。'}
    path=shard('index',index)
    require(len(out[path].encode())<=max(24000,len(news)*350),'news index budget exceeded')
    require(all(len(text(n).encode())<14000 for n in news),'per-news payload budget')
    for path2,data in out.items():require(len(data.encode())<=300000,'news shard too large')
    return out,path
