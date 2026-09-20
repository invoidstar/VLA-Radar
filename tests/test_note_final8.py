import json
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
