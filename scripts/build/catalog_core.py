"""Public catalog v2: one editable record per paper; no network or private inputs."""
from __future__ import annotations
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import copy, hashlib, ipaddress, json, math, re, unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlparse

LEGACY_KEYS = set('id name title team venue publicationType publicationStatus firstPublished dateNote collectionMonth versionNote topics tags priority contribution findings limitations insight readingFocus evidence evidenceNote hasCautionaryResult sources paperUrl arxiv doi'.split())
PUBLICATION_KEYS = set('firstArxivAt firstArxivSource latestArxivVersion latestArxivAt status venue doi acceptedAt publishedAt lastCheckedAt history alerts'.split())
EVENT_KEYS = set('kind date observedAt venue source note'.split())
NOTE_KEYS = set('status updatedAt verifiedAt version sections'.split())
SECTION_KEYS = set('id title body sources'.split())
RESULT_KEYS = set('id paperId method trackId values evidence verifiedAt source sourceVersion locator attribution trainingData evaluationNotes supersedes'.split())
TRACK_KEYS = set('id dataset name version tasks split metric unit direction protocol trainingRegime comparisonScope columns source'.split())

def dumps(x): return json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path, data):
    p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_text(dumps(data), encoding='utf-8'); tmp.replace(p)
def today(at=None):
    now=at if at is not None else datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError('Editorial clock must be timezone-aware')
    return now.astimezone(ZoneInfo('Asia/Singapore')).date().isoformat()
def require(ok, message):
    if not ok: raise ValueError(message)
def keys(obj, expected, context):
    require(isinstance(obj,dict) and set(obj)==expected, f'{context}: unexpected/missing public fields')
def day(value, optional=True, partial=False):
    if value is None and optional: return
    require(isinstance(value,str), 'date must be text or null')
    require(bool(re.fullmatch(r'\d{4}(?:-\d{2}){0,2}' if partial else r'\d{4}-\d{2}-\d{2}',value)),f'invalid date {value}')
    date.fromisoformat(value+('-01-01' if len(value)==4 else '-01' if len(value)==7 else ''))
def public_url(value):
    require(isinstance(value,str),'URL must be text')
    u=urlparse(value)
    require(u.scheme in {'http','https'} and u.hostname and not u.username and not u.password, 'only credential-free HTTP(S) URLs')
    host=u.hostname.lower().rstrip('.')
    require(host not in {'localhost','metadata.google.internal'} and not host.endswith(('.local','.internal','.localhost')), 'non-public host')
    require(u.port in {None,80,443}, 'non-standard network port')
    try: ip=ipaddress.ip_address(host)
    except ValueError: require('.' in host,'non-public hostname')
    else: require(ip.is_global,'non-public address')
    return value

def normal_title(s): return re.sub(r'[\W_]+','',unicodedata.normalize('NFKC',s).casefold())
def canonical_doi(s): return re.sub(r'^https?://(?:dx\.)?doi.org/','',s.strip().lower())
def add_event(pub, kind, event_date, source, venue='', note='', observed=None):
    event={'kind':kind,'date':event_date,'observedAt':observed or today(),'venue':venue,'source':source,'note':note}
    sig=lambda e:tuple(e[k] for k in ('kind','date','venue','source','note'))
    if sig(event) not in {sig(e) for e in pub['history']}: pub['history'].append(event)

def migrate_paper(p, when):
    explicit=bool(p['arxiv'] and p['firstPublished'] and len(p['firstPublished'])==10 and 'arXiv v1' in p['dateNote'])
    pub={'firstArxivAt':p['firstPublished'] if explicit else None,
         'firstArxivSource':f'https://arxiv.org/abs/{p["arxiv"]}v1' if explicit else '',
         'latestArxivVersion':None,'latestArxivAt':None,
         'status':'legacy','venue':p['venue'],'doi':p['doi'],'acceptedAt':None,'publishedAt':None,
         'lastCheckedAt':None,'history':[],'alerts':[]}
    # A migration preserves assertions, but does not certify old acceptance or version claims.
    add_event(pub,'imported',None,p['paperUrl'],p['venue'],'既有文献记录；本次结构迁移不重新认证发表状态。',when)
    sections=[]
    for sid,title,field in [('contribution','核心贡献与方法概览','contribution'),('results','结果与实验结论','findings'),('limits','适用范围与限制','limitations'),('insight','阅读启示','insight'),('focus','方法、创新与消融的阅读重点','readingFocus')]:
        sections.append({'id':sid,'title':title,'body':p[field],'sources':copy.deepcopy(p['sources'])})
    return {'schemaVersion':2,'paper':copy.deepcopy(p),'publication':pub,
        'note':{'status':'legacy','updatedAt':when,'verifiedAt':None,'version':p['versionNote'],'sections':sections}}

def validate_record(rec, topic_ids=None):
    keys(rec,{'schemaVersion','paper','publication','note'},'record'); require(rec['schemaVersion']==2,'record schema version')
    p=rec['paper']; keys(p,LEGACY_KEYS,'paper')
    require(bool(re.fullmatch(r'p\d{3,}',p['id'])),'paper ID')
    for field in LEGACY_KEYS-{'firstPublished','topics','tags','sources','hasCautionaryResult'}: require(isinstance(p[field],str),f'{p["id"]}.{field}: text required')
    require(all(p[k] for k in ('name','title','contribution','findings')),'empty essential paper field')
    day(p['firstPublished'],partial=True); day(p['collectionMonth'],False,True)
    require(re.fullmatch(r'\d{4}-\d{2}',p['collectionMonth']),'collection month')
    require(p['firstPublished'] is not None or bool(p['dateNote']),'unknown date needs explanation')
    require(p['priority'] in {'deep','selective','overview'},'priority')
    require(p['evidence'] in {'notes','metadata','checked'},'evidence')
    require(p['publicationType'] in {'preprint','conference','journal','report'},'publicationType')
    require(type(p['hasCautionaryResult']) is bool,'boolean caution marker')
    require(isinstance(p['tags'],list) and all(isinstance(t,str) for t in p['tags']),'tags')
    require(isinstance(p['topics'],list) and p['topics'] and all(isinstance(t,str) for t in p['topics']),'topics')
    if topic_ids is not None: require(set(p['topics'])<=topic_ids,'unknown topic')
    require(not p['arxiv'] or re.fullmatch(r'\d{2}(?:0[1-9]|1[0-2])\.\d{4,5}',p['arxiv']),'arxiv ID')
    public_url(p['paperUrl']); require(isinstance(p['sources'],list) and p['sources'],'sources required')
    for s in p['sources']: keys(s,{'label','url'},'source'); require(isinstance(s['label'],str),'source label'); public_url(s['url'])
    pub=rec['publication']; keys(pub,PUBLICATION_KEYS,'publication')
    for k in ('firstArxivAt','latestArxivAt','lastCheckedAt'): day(pub[k])
    for k in ('acceptedAt','publishedAt'): day(pub[k],partial=True)
    require(pub['status'] in {'legacy','preprint','accepted','published','report','withdrawn'},'publication status')
    require(pub['latestArxivVersion'] is None or (isinstance(pub['latestArxivVersion'],str) and re.fullmatch(r'v[1-9]\d*',pub['latestArxivVersion'])),'arxiv version')
    for k in ('firstArxivSource','venue','doi'): require(isinstance(pub[k],str),'publication text')
    if pub['firstArxivAt']: require(p['arxiv'] and pub['firstArxivSource'],'first arxiv requires exact source'); public_url(pub['firstArxivSource'])
    require(isinstance(pub['alerts'],list) and all(isinstance(x,str) for x in pub['alerts']),'alerts')
    require(isinstance(pub['history'],list),'history')
    for e in pub['history']:
        keys(e,EVENT_KEYS,'event'); day(e['date'],partial=True); day(e['observedAt'],False); public_url(e['source'])
        for k in ('kind','venue','note'): require(isinstance(e[k],str),'event text')
    if pub['status'] in {'accepted','published','withdrawn'}: require(any(e['kind']==pub['status'] for e in pub['history']),'verified lifecycle status requires a source event')
    note=rec['note']; keys(note,NOTE_KEYS | (set(note) & {'coverage','figures','tables','benchmarkReview'}),'note'); require(note['status'] in {'legacy','expanded','needs_review'},'note status')
    day(note['updatedAt'],False); day(note['verifiedAt']); require(isinstance(note['version'],str),'note version')
    require(isinstance(note['sections'],list) and note['sections'],'note sections')
    seen=set()
    for s in note['sections']:
        keys(s,SECTION_KEYS,'note section'); require(re.fullmatch(r'[a-z][a-z0-9-]*',s['id']) and s['id'] not in seen,'section id'); seen.add(s['id'])
        require(isinstance(s['title'],str) and isinstance(s['body'],str),'section text'); require(isinstance(s['sources'],list),'section sources')
        for src in s['sources']: keys(src,{'label','url'},'note source'); public_url(src['url'])
        if note['status']=='expanded': require(s['body'] and s['sources'],'expanded notes require content and citations')
    if note['status']=='expanded': require(note['verifiedAt'] and note['version'] and len(note['sections'])>=6,'expanded note coverage')

    # source-scoped deep-note extensions
    from note_quality import validate_note_extras
    validate_note_extras(note, public_url, require)

def validate_track(t):
    keys(t,TRACK_KEYS,'track'); require(re.fullmatch(r'[a-z0-9-]+',t['id']),'track id')
    require(isinstance(t['dataset'],str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._+()-]{0,59}',t['dataset']),'public benchmark family name')
    require(t['comparisonScope'] in {'protocol','paper-table'},'comparison scope')
    require(t['direction'] in {'higher','lower'},'metric direction')
    require(t['unit'] in {'percent','score','seconds'},'unit')
    require(isinstance(t['columns'],list) and t['columns'] and len(set(t['columns']))==len(t['columns']),'track columns')
    require(all(isinstance(t[k],str) and t[k] for k in TRACK_KEYS-{'columns'}),'track description required'); public_url(t['source'])

def validate_result(r, ids, tracks):
    keys(r,RESULT_KEYS,'result'); require(re.fullmatch(r'r-[a-z0-9-]+',r['id']),'result id')
    require(r['paperId'] in ids,'reporting paper missing'); require(r['trackId'] in tracks,'unknown protocol')
    t=tracks[r['trackId']]; require(isinstance(r['values'],dict) and set(r['values'])==set(t['columns']),'result columns mismatch')
    for val in r['values'].values():
        require(val is None or (type(val) in {int,float} and math.isfinite(val)),'numeric result or null')
        if val is not None and t['unit']=='percent': require(0<=val<=100,'percent outside [0,100]')
    require(r['evidence'] in {'checked','candidate','superseded'},'result evidence')
    require(r['attribution'] in {'author-reported','reported-baseline','independent-reproduction'},'result attribution')
    day(r['verifiedAt']); public_url(r['source'])
    for k in RESULT_KEYS-{'values','verifiedAt'}: require(isinstance(r[k],str),'result text field')
    if r['evidence']=='checked': require(r['verifiedAt'] and all(r[k] for k in ('locator','sourceVersion','trainingData','evaluationNotes')),'ranked result lacks evidence or protocol')
    require(not r['supersedes'] or r['supersedes']!=r['id'],'self supersession')

def read_catalog(root):
    root=Path(root); m=load(root/'catalog/manifest.json')
    require(m.get('schemaVersion')==2,'manifest schema'); order=m['paperOrder']; require(len(order)==len(set(order)),'duplicate order')
    files=list((root/'catalog/papers').glob('p*.json')); require({p.stem for p in files}==set(order),'manifest/file mismatch')
    records=[load(root/f'catalog/papers/{pid}.json') for pid in order]; topic_ids={t['id'] for t in m['topics']}; seen={k:{} for k in ('arxiv','doi','title')}
    locked=load(root/'catalog/first-public.json')
    for pid,rec in zip(order,records):
        validate_record(rec,topic_ids); p=rec['paper']; require(p['id']==pid,'invalid file record ID')
        if p['id'] in locked: require(p['firstPublished']==locked[p['id']],'immutable firstPublished was changed')
        for k,val in [('arxiv',p['arxiv'].lower()),('doi',canonical_doi(p['doi'])),('title',normal_title(p['title']))]:
            if val: require(val not in seen[k],f'duplicate {k}: {p["id"]} / {seen[k].get(val)}'); seen[k][val]=p['id']
    raw=load(root/'catalog/benchmarks.json'); require(raw['schemaVersion']==1,'benchmark schema'); tracks={}
    for t in raw['tracks']: validate_track(t); require(t['id'] not in tracks,'duplicate track'); tracks[t['id']]=t
    results=[]; rids=set()
    for f in sorted((root/'catalog/results').glob('*.json')):
        r=load(f); validate_result(r,set(order),tracks); require(r['id']==f.stem and r['id'] not in rids,'result id/file mismatch'); rids.add(r['id']); results.append(r)
    for r in results:
        if r['supersedes']:
            require(r['supersedes'] in rids,'missing superseded record')
            old=next(x for x in results if x['id']==r['supersedes'])
            require(old['trackId']==r['trackId'] and old['method']==r['method'],'supersession cannot cross method/protocol')
    return m,records,list(tracks.values()),results
