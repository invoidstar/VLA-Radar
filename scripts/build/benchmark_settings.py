"""Build Benchmark Settings from evaluation protocol only.

A Setting answers one question: are these reports evaluating the same benchmark task
set / split / metric? Training data, optimization recipe, base model, checkpoint and
source paper are properties of result reports, never Setting identity.

Cross-paper grouping uses benchmark-aware evaluation fingerprints with conservative
guards for conditions that genuinely change evaluation (task subsets, VM/VA, camera
perturbation, deployment delay, physical scene, etc.). Canonical track/result records
remain untouched.
"""
from __future__ import annotations
import hashlib,re,unicodedata
from collections import Counter

UNKNOWN_MARKERS=(
    '未披露','未完整给出','不明确','unknown','not disclosed','not reported',
    '各方法原配置','same paper setting','paper setup','官网训练设置；个别行预算未披露',
    'reported configuration'
)
DATA_CUES=re.compile(
    r'(?:\bdemo(?:s|nstrations?)?\b|demo_clean|示范|演示|轨迹|trajectory|human300|'
    r'\brlds\b|droid|bridge(?:data)?|open.?x|oxe|robocasa|robotwin|libero|calvin|'
    r'每任务\s*\d+|\d+[,.]?\d*\s*(?:k|万)?\s*(?:条)?(?:示范|演示|demos?))',re.I)
RECIPE_CUES=re.compile(
    r'(?:batch|steps?|epochs?|warmup|\blr\b|learning rate|vit-|qwen|bert|h\d+|'
    r'action horizon|gradient|gpu|h100|h200|rtx|denois|执行\d|检查点|checkpoint|'
    r'归一化|optimizer|cosine)',re.I)

def norm(value):
    return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',str(value or '')).strip().lower())

def slug(value):
    s=re.sub(r'[^a-z0-9]+','-',norm(value)).strip('-')
    return (s or 'setting')[:72]

def metric_class(value):
    n=norm(value)
    if re.search(r'\bfwt\b|forward transfer',n):return 'fwt'
    if re.search(r'\bnbt\b|backward transfer',n):return 'nbt'
    if re.search(r'\bauc\b|area under',n):return 'auc'
    if 'latency' in n or 'inference time' in n:return 'latency'
    if 'plan correctness' in n:return 'plan-correctness'
    if 'success' in n:return 'success'
    if 'score' in n:return 'score'
    return re.sub(r'[^a-z0-9]+','-',n).strip('-') or 'metric'

def metric_label(value):
    kind=metric_class(value)
    return {
        'success':'Success Rate','latency':'Latency','score':'Score','fwt':'FWT',
        'nbt':'NBT','auc':'AUC','plan-correctness':'Plan Correctness'
    }.get(kind,str(value))

def canon_col(value):
    n=norm(value).replace('avg.','average').replace('avg','average')
    return re.sub(r'[^a-z0-9]+','',n)

def canon_columns(columns):
    return tuple(canon_col(c) for c in columns)

def task_count(track):
    fields=(str(track.get('tasks','')),str(track.get('name','')))
    for text in fields:
        m=re.search(r'(?<!\d)(\d{1,3})\s*(?:tasks?|任务|skills?|skill types?|atomic tasks?)(?!\d)',text,re.I)
        if m:return int(m.group(1))
    raw=str(track.get('tasks','')).strip()
    return int(raw) if re.fullmatch(r'\d{1,3}',raw) else None

def text_of(track):
    return ' '.join(norm(track.get(k,'')) for k in ('id','name','tasks','split','protocol'))

def eval_context(track):
    text=text_of(track);dataset=track['dataset'];kind=metric_class(track['metric']);tags=[]
    # Explicit evaluation perturbations / environments. Training-only differences are intentionally absent.
    rules=[
      ('camera-shift',r'camera perturb|viewshift|view shift|camera shift|相机扰动'),
      ('delay-d0',r'\bd\s*=\s*0\b'),('delay-d1',r'\bd\s*=\s*1\b'),('delay-d4',r'\bd\s*=\s*4\b'),
      ('subset-short',r'short[- ]?duration|短时长'),('subset-medium',r'medium[- ]?duration|中时长'),('subset-long',r'long[- ]?duration|长时长'),
      ('mock-kitchen',r'mock kitchen|mock物理厨房'),('office-kitchen',r'office kitchen|office物理厨房'),
      ('camera-1d',r'1 distractor|1个干扰'),('camera-4to5d',r'4\s*[-–]?\s*5 distractor|4to5 distractor|4.?5个干扰'),
      ('enriched-language',r'gpt-?4 alternatives|扩写指令|enriched instruction'),
    ]
    for tag,pat in rules:
        if re.search(pat,text,re.I):tags.append(tag)
    if dataset=='SimplerEnv':
        split=norm(track.get('split',''))
        if re.search(r'visual matching|(?:^|[ /_-])vm(?:$|[ /_-])',split,re.I):tags.append('vm')
        if re.search(r'variant aggregation|(?:^|[ /_-])va(?:$|[ /_-])',split,re.I):tags.append('va')
    if dataset=='RoboCasa365':
        if re.search(r'target kitchens?|目标厨房',text,re.I):tags.append('target-kitchens')
        elif re.search(r'pretraining kitchens?|human300|预训练厨房',text,re.I):tags.append('pretraining-kitchens')
    if dataset=='Meta-World':
        for tag,pat in [('mt10',r'\bmt10\b'),('mt50',r'\bmt50\b'),('ml10-train',r'\bml10\b.*meta[- ]?train'),('ml10-test',r'\bml10\b.*meta[- ]?test'),('ml45-train',r'\bml45\b.*meta[- ]?train'),('ml45-test',r'\bml45\b.*meta[- ]?test')]:
            if re.search(pat,text,re.I):tags.append(tag)
        if 'r3m' in text:tags.append('r3m-five')
    if dataset=='ActionCache (real)':
        for task in ('button','close','sausage'):
            if task in norm(track['id']):tags.append('task-'+task)
    if kind=='latency':
        for tag,pat in [('jetson',r'jetson|orin'),('4090',r'4090'),('h100',r'h100'),('a100',r'a100')]:
            if re.search(pat,text,re.I):tags.append('hw-'+tag)
    return tuple(sorted(set(tags)))

def dataset_scope(track):
    ds=track['dataset'];cols=canon_columns(track['columns']);kind=metric_class(track['metric']);text=text_of(track);ctx=eval_context(track);count=task_count(track)
    # Major benchmarks: normalize paper-specific wording into stable evaluation questions.
    if ds=='RoboTwin':
        if {'clean','random'}<=set(cols):
            scope='50-clean-random'
            subset=[x for x in ctx if x.startswith('subset-') or x.startswith('delay-')]
            if subset:scope+='-'+'-'.join(subset)
            elif count==12:scope='12-clean-random'
            return scope
        if {'easy','hard'}<=set(cols):return '50-easy-hard'
        if cols==('average',):
            if 'clean' in text:return '50-clean-only'
            delays=[x for x in ctx if x.startswith('delay-')]
            return 'average-'+('-'.join(delays) if delays else str(count or 'reported'))
    if ds=='LIBERO':
        if kind in {'fwt','nbt','auc'}:return 'lifelong-'+kind
        if 'camera' in cols and 'robot' in cols and 'language' in cols:return 'plus'
        if 'semantic' in cols and 'position' in cols:return 'pro'
        if kind=='latency':return 'latency-'+'-'.join(ctx or ('reported',))
        if kind=='success':
            delays=[x for x in ctx if x.startswith('delay-')]
            if delays:return 'standard40-'+'-'.join(delays)
            scope_text=' '.join(norm(track.get(k,'')) for k in ('id','name','tasks','split'))
            if count==10 and re.search(r'long(?:-horizon)?|long horizon',scope_text,re.I):return 'long10'
            if re.search(r'3 suites|three suites|excluding long',scope_text,re.I):return 'three-suites'
            return 'standard40'
    if ds=='RoboCasa' and kind=='success':
        if count==24 or '24' in text:return '24-main'
    if ds=='RoboCasa365' and kind=='success':
        context=[x for x in ctx if x in {'target-kitchens','pretraining-kitchens'}]
        return '50-main'+(('-'+context[0]) if context else '')
    if ds=='RLBench' and kind=='success':
        if count==18:return '18-main'
        if count==74:return '74-single'
        if count==10:return '10-'+hashlib.sha256('|'.join(cols).encode()).hexdigest()[:8]+('-camera-shift' if 'camera-shift' in ctx else '')
    if ds=='SimplerEnv':
        mode='vm' if 'vm' in ctx else 'va' if 'va' in ctx else 'reported'
        return kind+'-'+mode+'-'+hashlib.sha256('|'.join(cols).encode()).hexdigest()[:8]
    if ds=='CALVIN':
        m=norm(track['metric'])
        if ('five-task chain' in m or 'five-instruction chain' in m or 'consecutive tasks completed' in m) and len(cols)==1:
            return 'chain-average-length'+('-enriched' if 'enriched-language' in ctx else '')
        return kind+'-'+hashlib.sha256('|'.join(cols).encode()).hexdigest()[:8]+('-enriched' if 'enriched-language' in ctx else '')
    if ds=='RoboDojo':
        return kind+'-'+hashlib.sha256('|'.join(cols).encode()).hexdigest()[:8]
    if ds=='Google Robot (real)':
        env=[x for x in ctx if x in {'mock-kitchen','office-kitchen','camera-1d','camera-4to5d'}]
        return kind+'-'+hashlib.sha256('|'.join(cols).encode()).hexdigest()[:8]+(('-'+'-'.join(env)) if env else '')
    if ds=='RoboMimic':
        if re.search(r'\bph\b|proficient-human',text,re.I):return 'ph-'+str(count or 5)
        if re.search(r'\bmh\b|multi-human',text,re.I):return 'mh-'+str(count or 4)
    if ds=='Meta-World':
        tags=[x for x in ctx if x.startswith(('mt','ml','r3m'))]
        return (tags[0] if tags else 'tasks-'+str(count or 'reported'))+'-'+kind
    if ds=='VLABench':
        n=count
        if not n:
            m=re.search(r'(?<!\d)(10|3)\s*(?:原子任务|任务)',str(track.get('name','')))
            n=int(m.group(1)) if m else None
        return kind+'-'+str(n or 'reported')
    if ds=='ActionCache (real)':
        task=next((x for x in ctx if x.startswith('task-')),'task-reported')
        return kind+'-'+task
    # Generic fallback: column schema + reliable task count + true evaluation-context guards.
    return kind+'-'+hashlib.sha256('|'.join(cols).encode()).hexdigest()[:10]+'-'+str(count or 'na')+(('-'+'-'.join(ctx)) if ctx else '')

PROFILE_SCHEMA_VERSION=1

def protocol_profile(track):
    """Return the structured evaluation-only identity used to control Setting growth.

    Hard identity fields answer the evaluation question. Training data, optimization
    recipe, base model, checkpoint choice, paper/source and author-specific reporting
    prose are deliberately excluded so they cannot create duplicate Settings.
    """
    scope=dataset_scope(track)
    metric='chain-average-length' if track['dataset']=='CALVIN' and scope.startswith('chain-average-length') else metric_class(track['metric'])
    return {
      'schemaVersion':PROFILE_SCHEMA_VERSION,
      'benchmark':track['dataset'],
      'taskScope':scope,
      'taskCount':task_count(track),
      'metric':metric,
      'unit':track['unit'],
      'direction':track['direction'],
      'columns':list(canon_columns(track)),
      'conditions':list(eval_context(track)),
    }

def profile_identity(profile):
    """Stable hard dimensions. Adding report metadata must not change this tuple."""
    return (
      profile['benchmark'],profile['taskScope'],profile['metric'],
      profile['unit'],profile['direction']
    )

def protocol_fingerprint(track):
    """Short stable fingerprint for the normalized evaluation question."""
    profile=protocol_profile(track)
    raw='|'.join(map(str,profile_identity(profile)))
    return 'ep1-'+hashlib.sha256(raw.encode()).hexdigest()[:12]

def protocol_compatibility(left,right):
    """Classify two tracks without turning every reporting difference into a Setting.

    incompatible: different hard evaluation identity;
    partial: same question but different known task/column coverage;
    exact: same normalized structured profile;
    compatible: same hard identity with only soft/reporting differences.
    """
    a,b=protocol_profile(left),protocol_profile(right)
    if profile_identity(a)!=profile_identity(b):return 'incompatible'
    if a['columns']!=b['columns']:return 'partial'
    if a['taskCount'] is not None and b['taskCount'] is not None and a['taskCount']!=b['taskCount']:return 'partial'
    if a==b:return 'exact'
    return 'compatible'

def evaluation_key(track):
    return profile_identity(protocol_profile(track))

def scope_label(track,scope):
    ds=track['dataset'];kind=metric_label(track['metric'])
    special={
      ('RoboTwin','50-clean-random'):'50 Tasks · Clean + Random',
      ('RoboTwin','50-clean-only'):'50 Tasks · Clean-only',
      ('RoboTwin','50-easy-hard'):'50 Tasks · Easy / Hard',
      ('LIBERO','standard40'):'Standard 40 Tasks · Four Suites',
      ('LIBERO','plus'):'LIBERO-Plus',
      ('LIBERO','pro'):'LIBERO-PRO',
      ('RoboCasa','24-main'):'24 Tasks',
      ('RoboCasa365','50-main-pretraining-kitchens'):'50 Tasks · Pretraining Kitchens',
      ('RoboCasa365','50-main-target-kitchens'):'50 Tasks · Target Kitchens',
      ('LIBERO','long10'):'Long-Horizon 10 Tasks',
      ('LIBERO','three-suites'):'Three Suites',
      ('CALVIN','chain-average-length'):'Five-task Chain · Average Length',
      ('CALVIN','chain-average-length-enriched'):'Five-task Chain · Enriched Instructions',
      ('RLBench','18-main'):'18 Tasks',
      ('RLBench','74-single'):'74 Tasks',
    }
    base=special.get((ds,scope))
    if base:
        if ds=='CALVIN' and scope.startswith('chain-average-length'):return f'{ds} · {base}'
        return f'{ds} · {base} · {kind}'
    count=task_count(track)
    if count:return f'{ds} · {count} Tasks · {kind}'
    cols=[str(c) for c in track['columns'] if canon_col(c) not in {'average','total','overall'}]
    detail=' / '.join(cols[:3])+((' / …') if len(cols)>3 else '')
    return f'{ds} · {detail or kind} · {kind}'

def training_identity(value):
    raw=str(value or '').strip();n=norm(raw)
    if not n or any(marker in n for marker in UNKNOWN_MARKERS):return None
    segments=[seg.strip(' ,，:：') for seg in re.split(r'[;；。]\s*',raw) if seg.strip()]
    kept=[]
    for seg in segments:
        if not DATA_CUES.search(seg):continue
        parts=[p.strip() for p in re.split(r'(?<!\d)[,，]|[,，](?!\d)|、',seg) if p.strip()];data_parts=[]
        for part in parts:
            if RECIPE_CUES.search(part) and data_parts:break
            if DATA_CUES.search(part) or not data_parts:data_parts.append(part)
        candidate='，'.join(data_parts).strip()
        if candidate and candidate not in kept:kept.append(candidate)
    return '；'.join(kept) if kept else None

def training_option(row):
    identity=training_identity(row.get('trainingData'))
    if identity:
        key='data-'+hashlib.sha256(norm(identity).encode()).hexdigest()[:12]
        return key,identity,True
    key='unknown-'+row['paperId']
    return key,'训练数据未完整披露 · '+row['paperId'],False

def build_settings(tracks,results):
    trackmap={t['id']:t for t in tracks}
    superseded={r['supersedes'] for r in results if r.get('evidence')=='checked' and r.get('supersedes')}
    accepted=[r for r in results if r.get('evidence')=='checked' and r['id'] not in superseded]
    groups={};track_order={t['id']:i for i,t in enumerate(tracks)};result_order={r['id']:i for i,r in enumerate(results)}
    for row in accepted:
        track=trackmap[row['trackId']];key=evaluation_key(track)
        groups.setdefault(key,[]).append(row)
    settings=[]
    for key,rows in groups.items():
        dataset,scope,metric,unit,direction=key
        rows=sorted(rows,key=lambda r:result_order[r['id']])
        member_tracks=sorted({r['trackId'] for r in rows},key=lambda tid:track_order[tid])
        candidates=[trackmap[tid] for tid in member_tracks];primary=candidates[0]
        columns=[]
        for t in candidates:
            for col in t['columns']:
                if col not in columns:columns.append(col)
        option_counts=Counter();option_meta={};training_by_result={}
        for row in rows:
            oid,label,known=training_option(row);training_by_result[row['id']]=oid;option_counts[oid]+=1;option_meta[oid]=(label,known)
        training_options=[{'id':oid,'label':option_meta[oid][0],'known':option_meta[oid][1],'count':option_counts[oid]} for oid in option_counts]
        split_values={norm(t['split']) for t in candidates};protocol_values={norm(t['protocol']) for t in candidates}
        digest=hashlib.sha256('|'.join(map(str,key)).encode()).hexdigest()[:12]
        settings.append({
          'id':'setting-'+slug(dataset)+'-'+slug(scope)+'-'+digest,
          'dataset':dataset,'evalId':'auto:'+scope,'name':scope_label(primary,scope),
          'tasks':primary['tasks'],
          'split':primary['split'] if len(split_values)==1 else '多来源评测描述；详见各行 Evidence',
          'metric':primary['metric'],'unit':unit,'direction':direction,'columns':columns,
          'protocol':primary['protocol'] if len(protocol_values)==1 else '同一 Evaluation Setting；来源论文的回合数、种子或报告细节可能不同，详见各行 Evidence。',
          'trackIds':member_tracks,'resultIds':[r['id'] for r in rows],
          'resultCount':len(rows),'paperCount':len({r['paperId'] for r in rows}),
          'paperIds':list(dict.fromkeys(r['paperId'] for r in rows)),
          'methodCount':len({norm(r['method']) for r in rows}),'primaryTrackId':primary['id'],
          'trainingOptions':training_options,'trainingByResult':training_by_result
        })
    settings.sort(key=lambda s:(track_order[s['primaryTrackId']],s['id']))
    return settings

# materialize evaluation-only settings

# refresh evaluation-only settings

# final evaluation-only setting refresh
