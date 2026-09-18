"""One-time public editorial recovery. Canonical records stay authoritative afterwards."""
from __future__ import annotations
import copy, hashlib, json, re
from pathlib import Path
from collections import Counter
from catalog_core import load, write, require, validate_record, validate_track, validate_result

ROOT=Path(__file__).resolve().parents[1]
STAMP='2026-09-18'
LIMITED={'p043':'author-materials-partial','p046':'official-abstract-only'}


def install_scope_support(root):
    p=root/'scripts/note_quality.py';s=p.read_text(encoding='utf-8')
    s=s.replace("'official-technical-report', 'official-abstract-only'", "'official-technical-report', 'official-abstract-only', 'author-materials-partial'")
    s=s.replace("(cov['scope']=='official-abstract-only')", "(cov['scope'] in {'official-abstract-only','author-materials-partial'})")
    p.write_text(s,encoding='utf-8')
    # Existing module imports must see the newly supported partial-author-material scope.
    import importlib, note_quality
    importlib.reload(note_quality)
    p=root/'research.js';s=p.read_text(encoding='utf-8')
    s=s.replace("'official-abstract-only':'仅依据官方摘要：全文方法、实验细节仍待核验'", "'official-abstract-only':'仅依据官方摘要：全文方法、实验细节仍待核验','author-materials-partial':'作者供稿与正式摘要导读：未取得完整期刊正文'")
    s=s.replace("c.scope==='official-abstract-only'?'limited':''", "c.level==='limited'?'limited':''")
    s=s.replace("note.coverage?.scope==='official-abstract-only'?'摘要解读 · 全文待核验'", "note.coverage?.level==='limited'?'受限材料导读 · 正文待核验'")
    s=s.replace("note.coverage?.scope==='official-abstract-only'?'已核读可访问的官方摘要；正文、实验表格和消融仍待取得。以下为有限证据导读，不作为全文结论或榜单数值依据。'", "note.coverage?.level==='limited'?'可核读材料及其边界已在各节说明；未取得完整正文，不将机制说明、分析或摘要扩写冒充全文实验核验。'")
    p.write_text(s,encoding='utf-8')
    p=root/'scripts/validate_all.py';s=p.read_text(encoding='utf-8')
    if "'scripts/check_editorial.py'" not in s:
        s=s.replace("commands=[[sys.executable,'validate.py'],", "commands=[[sys.executable,'validate.py'],[sys.executable,'scripts/check_editorial.py'],")
    p.write_text(s,encoding='utf-8')


def apply(root=ROOT):
    marker=root/'maintenance/library-completion.json'
    if marker.exists():
        print('Already applied; do not overwrite subsequent canonical edits.');return
    inputs=sorted((root/'maintenance/deep-reading').glob('completion-*.json'))
    require(len(inputs)==7,'All seven explicit reading batches must be present')
    records={p.stem:load(p) for p in (root/'catalog/papers').glob('p*.json')}
    old_meta={pid:copy.deepcopy(r['paper']) for pid,r in records.items()}
    old_pub={pid:copy.deepcopy(r['publication']) for pid,r in records.items()}
    old_results={p.name:p.read_bytes() for p in (root/'catalog/results').glob('*.json')}
    old_locks=(root/'catalog/first-public.json').read_bytes()
    install_scope_support(root)
    changed=[]
    for path in inputs:
        for draft in load(path):
            pid=draft['id'];require(pid in records and pid not in changed,'Unknown or repeated note ID')
            note=records[pid]['note'];was_stale=note['status']=='needs_review'
            level=draft.get('level','deep');scope=draft['scope']
            require((level=='limited')==(pid in LIMITED),'Only explicit legacy access exceptions may be limited')
            if pid in LIMITED:require(scope==LIMITED[pid],'Wrong source limitation')
            sections=[]
            for sid,title,body,label in draft['sections']:
                sources=[{'label':label,'url':draft['source']}]
                if pid=='p043':sources.append({'label':'IEEE正式摘要；非全文','url':'https://xplorestaging.ieee.org/document/11479850/'})
                if pid=='p046':sources.append({'label':'Elsevier摘要与出版信息；非全文','url':'https://www.sciencedirect.com/science/article/pii/S0736584526000475'})
                sections.append({'id':sid,'title':title,'body':body,'sources':sources})
            note.update(status='needs_review' if was_stale or level=='limited' else 'expanded',updatedAt=STAMP,verifiedAt=STAMP,version=draft['version'],sections=sections,coverage={'level':level,'scope':scope,'source':draft['source']},figures=draft.get('figures',[]),tables=draft.get('tables',[]))
            validate_record(records[pid]);write(root/f'catalog/papers/{pid}.json',records[pid]);changed.append(pid)
    require(len(changed)==30,'Expected 28 substantive retained notes and two limited guides')
    bench=load(root/'catalog/benchmarks.json');tracks={t['id']:t for t in bench['tracks']};added=[]
    result_source=root/'maintenance/deep-reading/retained-results.json'
    for group in load(result_source):
        track=group['track'];validate_track(track)
        if track['id'] in tracks:require(tracks[track['id']]==track,'Do not replace an existing protocol')
        else:tracks[track['id']]=track;bench['tracks'].append(track)
        for row in group['rows']:
            result={**group['defaults'],**row};validate_result(result,set(records),tracks)
            path=root/f'catalog/results/{result["id"]}.json'
            if path.exists():require(load(path)==result,'Do not overwrite an existing result')
            else:write(path,result);added.append(result['id'])
    write(root/'catalog/benchmarks.json',bench)
    results=[load(p) for p in sorted((root/'catalog/results').glob('*.json'))]
    ledger={'schemaVersion':1,'reviewedAt':STAMP,'scope':'Per-paper editorial disposition; existing checked rows preserved. Unextracted tables remain deferred, not automatically ranked.','papers':{}}
    for pid,r in records.items():
        rows=[x for x in results if x['paperId']==pid and x['evidence']=='checked']
        note=r['note'];cov=note.get('coverage',{})
        require(cov.get('level') in {'deep','limited'},pid+': no source-scoped note')
        if rows:
            state='extracted';message=f'保留{len(rows)}条具有来源版本及原表定位的核验记录；只代表这些行，不声称已穷尽全文结果。'
        elif cov.get('scope')=='primary-theory':
            state='not-applicable';message='本页为理论与证明范围解读；不从理论命题推导或补造机器人成功率。'
        else:
            state='protocol-unresolved'
            if pid in LIMITED:message='完整正文及原表尚不可读；不得从摘要或作者宣传稿推导精确分数与可比协议。'
            elif pid=='p067':message='FAST策略结果主要在图中；未获得完整精确值与协议，不从柱高猜分。token数不冒充任务成功率。'
            else:
                locators='；'.join(t['locator'] for t in note.get('tables',[]))
                message='笔记有分节来源与解释，但尚未完成相应结果的标准赛道映射；'+(locators+'。' if locators else '')+'保留原报告指标与训练条件，待逐表确认后入榜；缺失不按零分。'
        note['benchmarkReview']={'status':state,'checkedAt':STAMP,'note':message}
        write(root/f'catalog/papers/{pid}.json',r)
        ledger['papers'][pid]={'status':'deferred' if state=='protocol-unresolved' else state,'trackIds':sorted({x['trackId'] for x in rows}),'resultIds':sorted(x['id'] for x in rows),'note':message}
    write(root/'maintenance/benchmark-review.json',ledger)
    manifest=load(root/'catalog/manifest.json');manifest['updatedAt']=STAMP;write(root/'catalog/manifest.json',manifest)
    require((root/'catalog/first-public.json').read_bytes()==old_locks,'First-public lock changed')
    for pid in records:
        require(records[pid]['paper']==old_meta[pid],pid+': legacy paper field changed')
        require(records[pid]['publication']==old_pub[pid],pid+': lifecycle state changed during note recovery')
    for name,raw in old_results.items():require((root/'catalog/results'/name).read_bytes()==raw,'Existing result changed: '+name)
    full=[pid for pid,r in records.items() if r['note']['coverage']['level']=='deep']
    limited=[pid for pid in records if pid not in full]
    require(len(full)==76 and set(limited)==set(LIMITED),'Unexpected coverage totals')
    write(root/'maintenance/editorial-policy.json',{'schemaVersion':1,'effectiveAt':STAMP,'baselinePaperIds':sorted(records),'limitedLegacyIds':LIMITED,'newPaperMinimumCharacters':2000,'minimumSections':8,'weeklyMergeMode':'self-review-ci-then-merge','scope':'Counts are structural checks, not independent scientific certification.'})
    report={'schemaVersion':1,'preparedAt':STAMP,'totalPapers':len(records),'fullSourceNotes':len(full),'limitedSourceIds':limited,'changedNoteIds':changed,'noteSections':sum(len(r['note']['sections']) for r in records.values()),'figureLinks':sum(len(r['note'].get('figures',[])) for r in records.values()),'explanatoryTables':sum(len(r['note'].get('tables',[])) for r in records.values()),'benchmarkFamilies':len({t['dataset'] for t in tracks.values()}),'benchmarkTracks':len(tracks),'resultRecords':len(results),'addedResultIds':added,'existingResultsPreserved':len(old_results),'staleReadVersions':[pid for pid in full if records[pid]['note']['status']=='needs_review'],'inputSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs+[result_source]},'statement':'All records have substantive source-scoped guides; 76 full-method/theory/report notes, two explicit partial-source guides. This recovery is not a new literature search, latest-version certification or proof of deployment.'}
    write(marker,report)
    p=root/'CHANGELOG.md';p.write_text('## 2026-09-18 — 全库深入笔记与自检发布规则\n\n合入其余28篇正文／报告笔记；两篇资料受限论文扩展为8节导读并明确限制（DMS作者供稿、VLAbot官方摘要），不认证为完整期刊正文。全库78条均有分节笔记，76条为正文／理论／报告范围。保留全部最早公开日期、KEY RESULT、发表状态与原66条结果；恢复39条原表结果，共14系列、29赛道、105条。新增全库笔记和逐篇榜单处理检查，周更改为来源自检、CI通过后正常合并并核实Pages，不绕过保护。\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':apply()
