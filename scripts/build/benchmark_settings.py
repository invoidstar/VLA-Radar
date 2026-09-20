"""Build conservative Benchmark settings from evaluation identity + reported training data.

A Setting is a presentation/comparison unit, not a replacement for canonical track/result
records. Cross-track evaluation equivalence must be explicitly curated through
settingEvalId or an aligned protocol family. Unknown training data is source-scoped so
we never assume two papers used the same training budget.
"""
from __future__ import annotations
import hashlib,re,unicodedata

UNKNOWN_MARKERS=(
    '未披露','未完整给出','不明确','unknown','not disclosed','not reported',
    '各方法原配置','same paper setting','paper setup','官网训练设置；个别行预算未披露',
    'reported configuration'
)

def norm(value):
    return re.sub(r'\\s+',' ',unicodedata.normalize('NFKC',str(value or '')).strip().lower())

def slug(value):
    s=re.sub(r'[^a-z0-9]+','-',norm(value)).strip('-')
    return (s or 'setting')[:64]

def training_known(value):
    n=norm(value)
    return bool(n) and not any(marker in n for marker in UNKNOWN_MARKERS)

def evaluation_id(track):
    if track.get('settingEvalId'):return 'eval:'+track['settingEvalId']
    if track.get('familyId') and track.get('familyMode')=='aligned':return 'family:'+track['familyId']
    return 'track:'+track['id']

def evaluation_name(track):
    if track.get('settingEvalName'):return track['settingEvalName']
    if track.get('familyId') and track.get('familyMode')=='aligned':return track['familyName']
    return track['name']

def training_key(row):
    value=norm(row.get('trainingData'))
    return value if training_known(value) else f"source:{row['paperId']}:{value}"

def setting_key(track,row):
    return (
        track['dataset'],evaluation_id(track),norm(track['metric']),track['unit'],track['direction'],
        training_key(row)
    )

def build_settings(tracks,results):
    trackmap={t['id']:t for t in tracks}
    superseded={r['supersedes'] for r in results if r.get('evidence')=='checked' and r.get('supersedes')}
    accepted=[r for r in results if r.get('evidence')=='checked' and r['id'] not in superseded]
    groups={}
    track_order={t['id']:i for i,t in enumerate(tracks)}
    result_order={r['id']:i for i,r in enumerate(results)}
    for row in accepted:
        track=trackmap[row['trackId']]
        key=setting_key(track,row)
        if key not in groups:groups[key]=[]
        groups[key].append(row)
    settings=[]
    for key,rows in groups.items():
        dataset,eval_id,metric,unit,direction,td_key=key
        member_tracks=sorted({r['trackId'] for r in rows},key=lambda tid:track_order[tid])
        candidates=[trackmap[tid] for tid in member_tracks]
        primary=None
        for t in candidates:
            pid=t.get('familyPrimaryTrackId')
            if pid and pid in member_tracks:primary=trackmap[pid];break
        if primary is None:primary=candidates[0]
        columns=[]
        for t in candidates:
            for col in t['columns']:
                if col not in columns:columns.append(col)
        training=rows[0]['trainingData']
        known=training_known(training)
        digest=hashlib.sha256(('|'.join(map(str,key))).encode()).hexdigest()[:12]
        sid='setting-'+slug(eval_id.replace(':','-'))+'-'+digest
        settings.append({
            'id':sid,'dataset':dataset,'evalId':eval_id,'name':evaluation_name(primary),
            'tasks':primary['tasks'],'split':primary['split'],'metric':primary['metric'],
            'unit':unit,'direction':direction,'columns':columns,'trainingData':training,
            'trainingKnown':known,'protocol':primary['protocol'],'trackIds':member_tracks,
            'resultIds':[r['id'] for r in sorted(rows,key=lambda r:result_order[r['id']])],
            'resultCount':len(rows),'paperCount':len({r['paperId'] for r in rows}),
            'paperIds':list(dict.fromkeys(r['paperId'] for r in rows)),
            'methodCount':len({norm(r['method']) for r in rows}),
            'primaryTrackId':primary['id']
        })
    settings.sort(key=lambda s:(track_order[s['primaryTrackId']],s['id']))
    return settings

# materialization trigger
