"""Offline editorial checks. Source presence and length do not certify scientific truth."""
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
from pathlib import Path
from catalog_core import load, read_catalog, require

FULL_SCOPES={'primary-methods-experiments','primary-theory','official-technical-report'}
PARTIAL_SCOPES={'official-abstract-only','author-materials-partial'}


def check(records,policy,ledger,results):
    baseline=policy['baselinePaperIds'];require(len(baseline)==len(set(baseline)),'Duplicate baseline ID')
    limited=policy['limitedLegacyIds'];by_id={r['id']:r for r in results}
    require(set(ledger['papers'])=={r['paper']['id'] for r in records},'Benchmark disposition must cover every paper')
    for record in records:
        pid=record['paper']['id'];note=record['note'];cov=note.get('coverage',{})
        is_limited=cov.get('level')=='limited';scope=cov.get('scope')
        require(cov.get('level') in {'deep','limited'},pid+': missing source-scoped reading coverage')
        require(note['status'] in {'expanded','needs_review'},pid+': legacy summary is not a completed deep note')
        require(note['verifiedAt'] and note['version'],pid+': actual read date and version required')
        require(len(note['sections'])>=policy['minimumSections'],pid+': eight substantive sections required')
        require(all(len(s['body'])>=90 and s['sources'] for s in note['sections']),pid+': short or uncited section')
        body=sum(len(s['body']) for s in note['sections'])
        if is_limited:
            require(pid in limited and pid in baseline,pid+': new blocked papers belong in candidates, not published full-paper records')
            require(scope==limited[pid] and scope in PARTIAL_SCOPES,pid+': unexpected source limitation')
            require(note['status']=='needs_review',pid+': a limited guide must remain visibly incomplete')
            require(body>=1200,pid+': limited guide lacks useful evidence-scoped explanation')
        else:
            require(scope in FULL_SCOPES,pid+': abstract/partial materials cannot certify full-source reading')
            require(body>=(1500 if pid in baseline else policy['newPaperMinimumCharacters']),pid+': insufficient substantive reading depth')
        br=note.get('benchmarkReview',{})
        require(br.get('status') in {'extracted','not-applicable','protocol-unresolved'} and br.get('checkedAt') and br.get('note'),pid+': complete or explicitly defer the benchmark review')
        entry=ledger['papers'][pid]
        wanted='deferred' if br['status']=='protocol-unresolved' else br['status']
        require(entry.get('status')==wanted and entry.get('note'),pid+': inconsistent benchmark disposition')
        rids=entry.get('resultIds',[]);tids=entry.get('trackIds',[])
        require(len(rids)==len(set(rids)) and len(tids)==len(set(tids)),pid+': duplicate evidence references')
        if wanted=='extracted':
            require(rids,pid+': extracted needs actual result IDs')
            for rid in rids:
                require(rid in by_id and by_id[rid]['paperId']==pid and by_id[rid]['evidence']=='checked',pid+': wrong or unverified result reference')
            require(set(tids)=={by_id[rid]['trackId'] for rid in rids},pid+': track/result reference mismatch')
        else:require(not rids and not tids,pid+': deferred/non-applicable record cannot pretend to contain checked rows')
        if is_limited:require(wanted=='deferred',pid+': partial sources cannot be automatically promoted into the leaderboard')
    return True


if __name__=='__main__':
    root=Path(__file__).resolve().parents[2]
    _,records,_,results=read_catalog(root)
    check(records,load(root/'maintenance/policies/editorial-policy.json'),load(root/'maintenance/state/benchmark-review.json'),results)
    print('PASS: all papers have substantive source-scoped notes and traceable benchmark dispositions; new entries require full-source deep reading. This is not independent scientific certification.')
