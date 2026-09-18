"""Refresh all tracked arXiv records, preserving first-public dates and reading versions.
Safe metadata changes stay on the working branch. Acceptance mentions become candidates;
only an explicitly linked DOI with matching publisher metadata can confirm publication.
"""
from __future__ import annotations
import argparse, copy, json, re, time, xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote, urlencode
from catalog_core import add_event, canonical_doi, day, load, normal_title, read_catalog, today, write
from http_public import fetch
from arxiv_metadata import parse_abstract
from datetime import date
from urllib.error import HTTPError
NS={'a':'http://www.w3.org/2005/Atom','x':'http://arxiv.org/schemas/atom'}

def parse_feed(text):
    root=ET.fromstring(text);out={}
    for e in root.findall('a:entry',NS):
        ident=e.findtext('a:id','',NS); m=re.search(r'(\d{4}\.\d{4,5})(v\d+)?$',ident)
        if not m:continue
        pub=e.findtext('a:published','',NS)[:10]; upd=e.findtext('a:updated','',NS)[:10]
        day(pub,False);day(upd,False)
        out[m[1]]={'arxiv':m[1],'version':m[2] or None,'firstArxivAt':pub,'latestArxivAt':upd,
            'title':' '.join(e.findtext('a:title','',NS).split()),'doi':e.findtext('x:doi','',NS).strip(),
            'journalRef':e.findtext('x:journal_ref','',NS).strip(),'comment':e.findtext('x:comment','',NS).strip()}
    return out

def publisher_date(msg):
    for field in ('published-online','published-print','published','issued'):
        parts=msg.get(field,{}).get('date-parts',[])
        if parts and parts[0] and 1<=len(parts[0])<=3:
            result='-'.join(f'{int(x):04d}' if i==0 else f'{int(x):02d}' for i,x in enumerate(parts[0]))
            day(result,False,True)
            return result
    return None

def apply_arxiv(rec, meta, checked_at):
    p=rec['paper'];pub=rec['publication']; candidates=[];url=f'https://arxiv.org/abs/{p["arxiv"]}'
    if meta['arxiv']!=p['arxiv']:raise ValueError('arXiv identity mismatch')
    if pub['firstArxivAt'] and pub['firstArxivAt']!=meta['firstArxivAt']:
        candidates.append({'paperId':p['id'],'kind':'first-arxiv-conflict','source':url,'value':meta['firstArxivAt'],'note':'既有首发日期与 API 不一致；需核对 v1，不静默覆盖。'})
    else:
        pub['firstArxivAt']=meta['firstArxivAt'];pub['firstArxivSource']=url+'v1'
        add_event(pub,'arxiv_first',meta['firstArxivAt'],url+'v1',note=('arXiv Submission history v1（UTC）' if meta.get('provider')=='arxiv-abstract' else 'arXiv Atom published（UTC）')+'；不替代既有首次公开日期。',observed=checked_at)
    version=meta['version']; old=pub['latestArxivVersion']
    if version and (old is None or int(version[1:])>=int(old[1:])):
        pub['latestArxivVersion']=version;pub['latestArxivAt']=meta['latestArxivAt']
        add_event(pub,'arxiv_version',meta['latestArxivAt'],url+version,note=f'元数据版本 {version}；并不表示已重读该版本。',observed=checked_at)
        read_versions=re.findall(r'(?<![A-Za-z])v(\d+)\b',re.split(r'[;；]',rec['note']['version'],maxsplit=1)[0])
        if rec['note']['status']=='expanded' and ((read_versions and int(version[1:])>max(map(int,read_versions))) or (not read_versions and int(version[1:])>1)): rec['note']['status']='needs_review'
    if pub['status']=='legacy' and p['publicationType']=='preprint':pub['status']='preprint'
    if re.search(r'withdraw|retract',meta['comment'],re.I):
        candidates.append({'paperId':p['id'],'kind':'withdrawal-mention','source':url,'value':meta['comment'],'note':'作者注释提示撤稿；需核对，不直接删除记录。'})
    if meta['journalRef'] or re.search(r'accept|appear|conference|journal',meta['comment'],re.I):
        candidates.append({'paperId':p['id'],'kind':'venue-mention','source':url,'value':(meta['journalRef']+' '+meta['comment']).strip(),'note':'arXiv 注释或 journal-ref 为发现线索；需会议/期刊一手页面确认。'})
    return candidates

def apply_crossref(rec,msg,linked_doi,checked_at):
    doi=canonical_doi(linked_doi);pub=rec['publication'];p=rec['paper']
    if pub['status']=='withdrawn':return False,'Withdrawn status requires manual resolution'
    if canonical_doi(msg.get('DOI',''))!=doi: return False,'DOI identity mismatch'
    if doi.startswith('10.48550/arxiv'):return False,'arXiv DOI is not journal/conference publication'
    titles=msg.get('title',[])
    if not titles or SequenceMatcher(None,normal_title(titles[0]),normal_title(p['title'])).ratio()<.93:return False,'publisher title mismatch; manual identity resolution needed'
    ptype=msg.get('type'); venue=(msg.get('container-title') or [''])[0]
    if ptype not in {'journal-article','proceedings-article'} or not venue:return False,'not a named journal/conference article'
    published=publisher_date(msg)
    if not published or published>checked_at:return False,'missing or future publication date'
    pub.update({'status':'published','venue':venue,'doi':doi,'publishedAt':published})
    # Never invent an acceptance date from publication/deposit/indexing timestamps.
    url='https://doi.org/'+doi
    add_event(pub,'published',published,url,venue,'由 arXiv/既有记录直接关联 DOI，且出版元数据标题匹配。日期精度遵循出版方。',checked_at)
    p['venue']=venue;p['doi']=doi;p['publicationType']='journal' if ptype=='journal-article' else 'conference'
    p['publicationStatus']=f'正式发表于 {venue}；出版日期 {published}；DOI:{doi}'
    if not any(s['url']==url for s in p['sources']):p['sources'].append({'label':'出版方 DOI','url':url})
    return True,''

def sync(root,limit=100,apply=False,pause=3.1,due_days=7):
    if limit is not None and limit<1:raise ValueError('limit must be positive')
    root=Path(root);m,records,_,_=read_catalog(root)
    eligible=[r for r in records if r['paper']['arxiv']]
    when=today()
    due=[r for r in sorted(eligible,key=lambda r:(r['publication']['lastCheckedAt'] or '',r['paper']['id']))
         if not r['publication']['lastCheckedAt'] or (date.fromisoformat(when)-date.fromisoformat(r['publication']['lastCheckedAt'])).days>=due_days]
    selected=due[:limit] if limit else due
    errors=[]; warnings=[]; candidates=[]; changed=[]; checked=[]; network={}; providers={}; blocked=False
    for start in range(0,len(selected),40):
        batch=selected[start:start+40]
        if start:time.sleep(pause)
        url='https://export.arxiv.org/api/query?'+urlencode({'id_list':','.join(r['paper']['arxiv'] for r in batch),'max_results':len(batch)})
        try:
            found=parse_feed(fetch(url,accept='application/atom+xml',attempts=1)[0])
            for ident,meta in found.items(): network[ident]=meta;providers[ident]='arxiv-api'
        except Exception as e:
            warnings.append({'provider':'arxiv-api','paperIds':[r['paper']['id'] for r in batch],'error':str(e)[:300]})
            # Do not switch endpoints to evade authorization failures or throttling.
            if isinstance(e,HTTPError) and e.code in {401,403,429}:blocked=True;break
    failures=0
    for r in selected:
        ident=r['paper']['arxiv']
        if ident in network:continue
        if blocked or failures>=3:
            errors.append({'paperIds':[r['paper']['id']],'provider':'arxiv-abstract','error':'Fallback circuit open; retained for next run'})
            continue
        try:
            time.sleep(pause)
            html,_,final=fetch('https://arxiv.org/abs/'+ident,accept='text/html',attempts=1)
            from urllib.parse import urlparse
            if urlparse(final).hostname!='arxiv.org':raise ValueError('Unexpected abstract redirect host')
            network[ident]=parse_abstract(html,ident);providers[ident]='arxiv-abstract';failures=0
        except Exception as e:
            failures+=1
            if isinstance(e,HTTPError) and e.code in {401,403,429}:blocked=True
            errors.append({'paperIds':[r['paper']['id']],'provider':'arxiv-abstract','error':str(e)[:300]})
    for original in selected:
        rec=copy.deepcopy(original); p=rec['paper']; pid=p['id']; meta=network.get(p['arxiv'])
        if not meta:
            errors.append({'paperIds':[pid],'provider':'arxiv','error':'No usable exact-ID metadata returned'});continue
        if SequenceMatcher(None,normal_title(meta['title']),normal_title(p['title'])).ratio()<.85:
            candidates.append({'paperId':pid,'kind':'title-identity-review','source':'https://arxiv.org/abs/'+p['arxiv'],'value':meta['title'],'note':'精确ID对应标题差异明显；可能改名或旧记录错误，待人工源核验。'})
            errors.append({'paperIds':[pid],'provider':providers.get(p['arxiv']),'error':'Title identity requires review'});continue
        if meta['firstArxivAt']>when or meta['latestArxivAt']>when:
            errors.append({'paperIds':[pid],'provider':providers.get(p['arxiv']),'error':'Future submission timestamp rejected'});continue
        candidates.extend(apply_arxiv(rec,meta,when));complete=True
        doi=canonical_doi(meta['doi'] or rec['publication']['doi'])
        if doi and not doi.startswith('10.48550/arxiv'):
            try:
                time.sleep(.15);msg=json.loads(fetch('https://api.crossref.org/works/'+quote(doi,safe=''))[0])['message']
                ok,why=apply_crossref(rec,msg,doi,when)
                if not ok:candidates.append({'paperId':pid,'kind':'doi-review','source':'https://doi.org/'+doi,'value':doi,'note':why})
            except Exception as e:
                complete=False;errors.append({'paperIds':[pid],'provider':'crossref','error':str(e)[:400]})
        if complete:rec['publication']['lastCheckedAt']=when;checked.append(pid)
        if rec!=original:
            old_content=copy.deepcopy(original);new_content=copy.deepcopy(rec)
            old_content['publication']['lastCheckedAt']=None;new_content['publication']['lastCheckedAt']=None
            if old_content!=new_content:changed.append(pid)
            if apply:write(root/f'catalog/papers/{pid}.json',rec)
    no_arxiv=[r['paper']['id'] for r in records if not r['paper']['arxiv']]
    report={'schemaVersion':1,'checkedAt':when,'mode':'apply-safe' if apply else 'dry-run','selected':len(selected),'metadataChecked':checked,'changed':changed,
        'status':'success' if not errors and len(selected)==len(due) else 'partial','errors':errors,
        'warnings':warnings,'providers':providers,'totalTracked':len(eligible),'dueCount':len(due),'dueRemaining':len(due)-len(checked),
        'dueDays':due_days,'checkedScope':'due subset, not discovery or acceptance certification',
        'manualSourceReview':no_arxiv,'scope':'arXiv IDs and directly linked Crossref DOIs only; acceptance pages and missing DOIs need source review. Not a complete publication-status certification.'}
    if apply:
        # No changes to maintenance/state.json: a metadata scan is not a literature-discovery sweep.
        write(root/'maintenance/publication-check.json',report)
        prev=load(root/'maintenance/publication-candidates.json') if (root/'maintenance/publication-candidates.json').exists() else {'candidates':[]}
        keyed={(x['paperId'],x['kind'],x['value']):x for x in prev['candidates']}
        for c in candidates:keyed[(c['paperId'],c['kind'],c['value'])]=c
        write(root/'maintenance/publication-candidates.json',{'schemaVersion':1,'updatedAt':when,'candidates':list(keyed.values())})
        if changed:m['updatedAt']=when;write(root/'catalog/manifest.json',m)
    return report
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--limit',type=int,default=100);ap.add_argument('--due-days',type=int,default=7);ap.add_argument('--apply-safe',action='store_true');a=ap.parse_args()
    print(json.dumps(sync(a.root,a.limit,a.apply_safe,due_days=a.due_days),ensure_ascii=False,indent=2))
