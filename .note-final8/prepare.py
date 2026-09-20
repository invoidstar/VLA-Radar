import json, subprocess
from pathlib import Path

ROOT=Path('.')
BASE='60e16cc2a1edf34cc8bfd5b767bc5a80376f4f87'
DAY='2026-09-20'
assert subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()==BASE, 'main moved'

def load(p): return json.loads((ROOT/p).read_text())
def dump(p,o):
    q=ROOT/p
    q.parent.mkdir(parents=True,exist_ok=True)
    q.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')

def replace_url(record, old, new):
    if record['note'].get('coverage',{}).get('source')==old:
        record['note']['coverage']['source']=new
    for sec in record['note'].get('sections',[]):
        for src in sec.get('sources',[]):
            if src.get('url')==old: src['url']=new
    for fig in record['note'].get('figures',[]):
        if fig.get('url')==old: fig['url']=new
    for src in record['paper'].get('sources',[]):
        if src.get('url')==old: src['url']=new

def ensure_source(record,label,url):
    if not any(s.get('url')==url for s in record['paper'].get('sources',[])):
        record['paper'].setdefault('sources',[]).append({'label':label,'url':url})

def ensure_section(record,section):
    ids={s.get('id') for s in record['note'].get('sections',[])}
    if section['id'] not in ids:
        record['note'].setdefault('sections',[]).append(section)

def ensure_table(record,table):
    titles={t.get('title') for t in record['note'].get('tables',[])}
    if table['title'] not in titles:
        record['note'].setdefault('tables',[]).append(table)

completed={
'p004':{
 'version':'arXiv 2607.15330v2（2026-07-22），§2–3、Tables 2–5、Appendix；2026-09-20复核',
 'old':'https://arxiv.org/html/2607.15330v1','new':'https://arxiv.org/html/2607.15330v2',
 'label':'当前复核版本 · v2',
 'section':{
  'id':'version-review',
  'title':'v2版本复核：主表口径稳定，但57.4/57.6内部冲突必须保留',
  'body':'2026-09-20重新核读arXiv v2。RoboCasa365的摘要与Table 3都给出57.4%平均成功率，而Introduction仍出现57.6%；因此本站继续以原表57.4%作为结构化成绩，并把57.6%保留为作者版本内部冲突，而不是自行平均或择高。其余两阶段训练、Choice Policies、100K小时UMI预训练与10K小时跨本体后训练的主线没有改变。',
  'sources':[{'label':'arXiv v2 · Abstract / Introduction / Table 3','url':'https://arxiv.org/html/2607.15330v2'}]
 },
 'table':{
  'title':'v2版本复核：RoboCasa365数字冲突',
  'columns':['位置','报告值','本站处理'],
  'rows':[['Abstract','57.4%','采用原表一致口径'],['Table 3','57.4%','结构化结果采用'],['Introduction','57.6%','保留为版本内部冲突']],
  'locator':'arXiv v2 Abstract、§1、Table 3',
  'caption':'同一v2内部存在57.4/57.6冲突；本站不自行修正作者文本。'
 }
},
'p024':{
 'version':'arXiv 2607.00678v2（2026-07-06），§2–5、Tables 2–8；2026-09-20复核',
 'old':'https://arxiv.org/html/2607.00678v1','new':'https://arxiv.org/html/2607.00678v2',
 'label':'当前复核版本 · v2',
 'section':{
  'id':'version-review',
  'title':'v2版本复核：RoboCasa365主表与训练阶段边界保持一致',
  'body':'2026-09-20重新核读v2。RoboCasa365预训练表仍报告ABot-M0.5为40.4%，加入Condensed Memory为46.6%；Target 100%与Target 10%适配分别为54.2%和30.1%。这些数字与现有笔记一致，因此本次只把阅读版本升级到v2，不把不同训练阶段合并成一个协议。v2仍明确将Condensed Memory视为额外增强路径，不能倒灌成基础ABot-M0.5的默认成绩。',
  'sources':[{'label':'arXiv v2 · Tables 2–3','url':'https://arxiv.org/html/2607.00678v2'}]
 }
},
'p045':{
 'version':'arXiv 2508.05342v2（2026-02-06）/ Information Fusion 131 (2026) 104193；§3–7、Tables 1–3；2026-09-20复核',
 'old':'https://arxiv.org/html/2508.05342v1','new':'https://arxiv.org/html/2508.05342v2',
 'label':'当前复核版本 · v2',
 'section':{
  'id':'version-review',
  'title':'v2与正式期刊版复核：操作成功率和总体TSR口径未改变',
  'body':'2026-09-20按arXiv v2并对照Information Fusion正式出版信息复核。基础操作表仍给出总体抓取94%、放置89%，组合迁移Table 3总体TSR为90%；这些指标的分母与含义仍不同，因此本站继续分轨保存，不把图表示准确率、阶段分割和任务TSR合成单一总分。期刊身份的确认也不改变实验数字的证据层级。',
  'sources':[{'label':'arXiv v2 · Tables 1–3','url':'https://arxiv.org/html/2508.05342v2'},{'label':'Information Fusion · DOI','url':'https://doi.org/10.1016/j.inffus.2026.104193'}]
 }
},
'p051':{
 'version':'arXiv 2209.05451v2（2022-11-11）/ CoRL 2022 final；§3–4、Appendix、Table 1；2026-09-20复核',
 'old':None,'new':'https://arxiv.org/html/2209.05451v2',
 'label':'当前复核版本 · v2',
 'section':{
  'id':'version-review',
  'title':'v2 / CoRL最终版复核：18个RLBench任务与7个真实任务的范围不外推',
  'body':'2026-09-20重新核对arXiv v2与作者公开CoRL版本。论文仍以18个RLBench任务（249个variation）和7个真实任务（18个variation）验证PerAct；现有笔记中关于体素化3D输入、离散6-DoF动作、少量示范和多任务行为克隆的描述与最终版一致。本轮不把后续第三方PerAct复现设置或RLBench其他任务重新绑定到原论文。',
  'sources':[{'label':'arXiv v2 · final text','url':'https://arxiv.org/html/2209.05451v2'},{'label':'CoRL 2022 official paper','url':'https://proceedings.mlr.press/v205/shridhar23a.html'}]
 }
},
'p055':{
 'version':'arXiv 2303.04137v5（2024-03-14）扩展版；§1–7、Appendix；RSS 2023 Table I–IV榜单快照单独保留；2026-09-20复核',
 'old':None,'new':'https://arxiv.org/html/2303.04137v5',
 'label':'当前复核版本 · v5',
 'section':{
  'id':'version-review',
  'title':'v5扩展版复核：最新论文覆盖15个任务，既有榜单仍保留RSS表格快照',
  'body':'2026-09-20重新阅读arXiv v5。扩展版明确写为在4类机器人操作benchmark的15个任务上评测，并继续报告46.9%的平均提升；这比本站原先用于结构化成绩的RSS 2023会议版实验范围更广。为避免版本混算，本轮把深读版本升级到v5，但已入库的RoboMimic等结果仍标注为RSS 2023可定位Table I–IV快照，除非逐表重新建立v5协议，否则不悄悄替换来源版本。',
  'sources':[{'label':'arXiv v5 · extended journal version','url':'https://arxiv.org/html/2303.04137v5'},{'label':'arXiv submission history','url':'https://arxiv.org/abs/2303.04137'}]
 },
 'table':{
  'title':'版本复核：v5扩展版与RSS 2023榜单快照',
  'columns':['证据层','范围','本站处理'],
  'rows':[['arXiv v5扩展版','4类benchmark、15个任务','作为当前深读版本'],['RSS 2023 Table I–IV','既有可精确定位实验表','现有结构化结果继续保留来源版本'],['46.9%平均提升','作者跨任务汇总','不拆成缺失的逐任务新成绩']],
  'locator':'arXiv v5 Abstract；RSS 2023 Tables I–IV',
  'caption':'最新阅读版本与既有结构化实验快照明确分离，避免版本混算。'
 }
},
'p074':{
 'version':'arXiv 2509.09372v2（2025-09-22），§1–6、Appendix、Tables 2–8；2026-09-20复核',
 'old':'https://arxiv.org/html/2509.09372v1','new':'https://arxiv.org/html/2509.09372v2',
 'label':'当前复核版本 · v2',
 'section':{
  'id':'version-review',
  'title':'v2版本复核：新增VLA-Adapter-Pro，基础VLA-Adapter结果保持独立',
  'body':'2026-09-20重新核读v2。最新版本新增VLA-Adapter-Pro：LIBERO四套件平均98.5%，CALVIN连续任务平均链长4.50；基础VLA-Adapter仍为LIBERO 97.3%与CALVIN 4.42。本站把Pro视为新的方法变体，而不是用更高数字覆盖原VLA-Adapter；现有Bridge Attention、Raw/ActionQuery与门控消融的结论仍由基础版本对应表格支持。',
  'sources':[{'label':'arXiv v2 · Tables 2–8','url':'https://arxiv.org/html/2509.09372v2'}]
 },
 'table':{
  'title':'v2新增VLA-Adapter-Pro结果',
  'columns':['方法','LIBERO Avg.','CALVIN Avg. chain'],
  'rows':[['VLA-Adapter','97.3%','4.42'],['VLA-Adapter-Pro','98.5%','4.50']],
  'locator':'arXiv v2 Tables 2、6',
  'caption':'Pro是v2新增变体；不覆盖基础VLA-Adapter的既有成绩。'
 }
}
}

for pid,cfg in completed.items():
    p=load(f'catalog/papers/{pid}.json')
    p['note']['status']='expanded'
    p['note']['verifiedAt']=DAY
    p['note']['updatedAt']=DAY
    p['note']['version']=cfg['version']
    p['publication']['lastCheckedAt']=DAY
    if cfg.get('old'):
        replace_url(p,cfg['old'],cfg['new'])
    else:
        p['note']['coverage']['source']=cfg['new']
    ensure_source(p,cfg['label'],cfg['new'])
    p['paper']['evidence']='checked'
    p['paper']['evidenceNote']=f'2026-09-20按{cfg["version"]}完成当前公开版本方法、实验协议与版本差异复核；非独立实验复现。'
    ensure_section(p,cfg['section'])
    if cfg.get('table'): ensure_table(p,cfg['table'])
    p['note']['benchmarkReview']['note']=p['note']['benchmarkReview']['note'].rstrip()+' 2026-09-20完成当前版本深读复核；已有结构化结果仅在原sourceVersion/locator边界内继续有效，不因笔记升级而自动改绑。'
    dump(f'catalog/papers/{pid}.json',p)

# Limited-source papers: re-check access, but remain visibly incomplete.
limited={
 'p043':{
  'version':'IEEE RA-L正式摘要＋既有作者材料；2026-09-20再次检索全文，仍未取得可稳定阅读全文的一手版本',
  'note':'2026-09-20再次检索IEEE/作者/学术索引渠道；仍只有正式摘要与部分作者材料可稳定读取。按author-materials-partial编辑政策继续needs_review，不能把摘要加速字符串或二手页面当完整实验复核。'
 },
 'p046':{
  'version':'RCIM 100 (2026) 103268；PolyU/ScienceDirect正式摘要；2026-09-20再次尝试全文，ScienceDirect抓取仍403',
  'note':'2026-09-20确认论文Open Access身份及正式摘要，但当前自动化全文入口仍返回403，PolyU页面仅提供摘要。按official-abstract-only编辑政策继续needs_review，不把within five trials升级成未读全文的完整实验结论。'
 }
}
for pid,cfg in limited.items():
    p=load(f'catalog/papers/{pid}.json')
    p['note']['verifiedAt']=DAY
    p['note']['updatedAt']=DAY
    p['note']['version']=cfg['version']
    p['publication']['lastCheckedAt']=DAY
    p['paper']['evidenceNote']=cfg['note']
    p['note']['benchmarkReview']['checkedAt']=DAY
    p['note']['benchmarkReview']['note']=cfg['note']
    dump(f'catalog/papers/{pid}.json',p)

# Work queue: only two genuinely unresolved limited-source notes remain.
wq=load('maintenance/work-queue.json')
wq['notes']=[x for x in wq['notes'] if x['paperId'] in ('p043','p046')]
for x in wq['notes']:
    if x['paperId']=='p043':
        x['readVersion']=limited['p043']['version']
    if x['paperId']=='p046':
        x['readVersion']=limited['p046']['version']
wq['remainingNotes']=2
dump('maintenance/work-queue.json',wq)

audit={
 'schemaVersion':1,
 'reviewedAt':DAY,
 'batch':'note-final8',
 'baseCommit':BASE,
 'requestedRemaining':11,
 'actualAtStart':8,
 'completedLatestVersionReviews':list(completed),
 'limitedSourceRemaining':['p043','p046'],
 'countsBefore':{'remainingNotes':8},
 'countsAfterExpected':{'remainingNotes':2},
 'versionFindings':{
  'p004':'v2 Abstract/Table 3 report RoboCasa365 57.4 while Introduction still says 57.6; table value retained.',
  'p024':'v2 preserves 40.4/46.6 pretraining and 54.2/30.1 target-adaptation settings; stages remain separate.',
  'p045':'v2/published version preserves 94 grasp, 89 placement and 90 overall task success as distinct metrics.',
  'p051':'v2/CoRL final confirms 18 RLBench tasks with 249 variations and 7 real tasks with 18 variations.',
  'p055':'v5 expands evaluation to 15 tasks across four benchmarks; existing structured rows remain RSS 2023 snapshots.',
  'p074':'v2 adds VLA-Adapter-Pro (LIBERO 98.5, CALVIN chain 4.50); base VLA-Adapter remains 97.3/4.42.'
 },
 'qualityRules':[
  'Changing note status never silently changes benchmark sourceVersion or protocol.',
  'Internal numerical conflicts are retained rather than normalized by the site.',
  'Limited-source records remain needs_review until full primary methods/experiments are readable.',
  'No private project context is used in public VLA-Radar notes.'
 ]
}
dump('maintenance/note-review-audit-20260920-final8.json',audit)

ch=Path('CHANGELOG.md').read_text()
entry='## 2026-09-20 · 剩余笔记版本复核收口（8→2）\n\n- 基于当前main实际状态完成6篇latest-version全文复核：Xiaomi-Robotics-1 v2、ABot-M0.5 v2、GF-VLA v2/Information Fusion、PerAct v2/CoRL 2022、Diffusion Policy v5、VLA-Adapter v2。\n- remainingNotes 8→2；DMS-VLA 与 VLAbot 因仓库limited-source政策继续needs_review，2026-09-20已再次检索全文但仍无法稳定取得完整方法/实验正文。\n- 保留Xiaomi v2中57.4/57.6内部冲突；Diffusion Policy明确区分v5扩展版与RSS 2023榜单快照；VLA-Adapter v2新增Pro变体而不覆盖基础模型。\n- 本轮不改变任何Leaderboard结果、协议或排名，仅更新深读版本、来源、证据状态与work queue。\n\n'
if '剩余笔记版本复核收口（8→2）' not in ch:
    Path('CHANGELOG.md').write_text(entry+ch)

Path('tests/test_note_final8.py').write_text("""import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def j(p): return json.loads((R/p).read_text())
DONE={'p004':'v2','p024':'v2','p045':'v2','p051':'v2','p055':'v5','p074':'v2'}
def test_six_latest_reviews_completed():
    for pid,mark in DONE.items():
        p=j('catalog/papers/'+pid+'.json')
        assert p['note']['status']=='expanded'
        assert mark in p['note']['version']
        assert p['note']['verifiedAt']=='2026-09-20'
        assert p['paper']['evidence']=='checked'
def test_two_limited_sources_remain_visible():
    for pid in ['p043','p046']:
        p=j('catalog/papers/'+pid+'.json')
        assert p['note']['status']=='needs_review'
        assert p['note']['coverage']['level']=='limited'
        assert p['note']['verifiedAt']=='2026-09-20'
    w=j('maintenance/work-queue.json')
    assert w['remainingNotes']==2
    assert {x['paperId'] for x in w['notes']}=={'p043','p046'}
def test_xiaomi_conflict_preserved():
    p=j('catalog/papers/p004.json')
    assert any('57.4/57.6' in x for x in p['publication']['alerts'])
    t=next(x for x in p['note']['tables'] if x['title']=='v2版本复核：RoboCasa365数字冲突')
    assert t['rows'][0][1]=='57.4%' and t['rows'][2][1]=='57.6%'
def test_diffusion_v5_scope_does_not_rebind_results():
    p=j('catalog/papers/p055.json')
    assert '15个任务' in next(x for x in p['note']['sections'] if x['id']=='version-review')['body']
    assert 'RSS 2023' in p['note']['version']
def test_vla_adapter_pro_kept_separate():
    p=j('catalog/papers/p074.json')
    t=next(x for x in p['note']['tables'] if x['title']=='v2新增VLA-Adapter-Pro结果')
    assert t['rows']==[['VLA-Adapter','97.3%','4.42'],['VLA-Adapter-Pro','98.5%','4.50']]
def test_benchmark_counts_unchanged():
    review=j('maintenance/benchmark-review.json')['papers']
    assert sum(x['status']=='extracted' for x in review.values())==94
    assert sum(x['status']=='deferred' for x in review.values())==2
    assert sum(x['status']=='not-applicable' for x in review.values())==2
    assert len(j('catalog/benchmarks.json')['tracks'])==267
    assert len(list((R/'catalog/results').glob('r-*.json')))==962
""")

# Capture actual note changes and rebuild generated data.
subprocess.run(['python','scripts/capture_activity.py','--base',BASE,'--at','2026-09-20T01:50:00Z'],check=True)
subprocess.run(['python','scripts/build_catalog.py'],check=True)
print('completed six current-version reviews; two limited-source notes remain')
