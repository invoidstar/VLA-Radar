import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def j(p): return json.loads((R/p).read_text())
ALL=['p067','p032','p031','p045','p043','p022','p018','p075','p008','p071','p077','p030','p005','p038','p006','p019','p033','p007','p010','p046','p034','p016','p037','p097']
def test_final24_counts_and_zero_deferred():
    r=j('maintenance/state/benchmark-review.json')['papers']
    assert all(r[x]['status']=='extracted' for x in ALL)
    assert sum(x['status']=='extracted' for x in r.values())>=96
    assert sum(x['status']=='not-applicable' for x in r.values())>=2
    assert len(j('catalog/benchmarks.json')['tracks'])>=286
    assert len(list((R/'catalog/results').glob('r-*.json')))>=1063
    assert j('maintenance/state/work-queue.json')['remainingNotes']==0
def test_efficiency_is_not_robot_success():
    t={x['id']:x for x in j('catalog/benchmarks.json')['tracks']}
    assert t['fast-v1-training-speedup']['unit']=='score'
    assert t['deltoris-v1-hardware-speedup']['metric'].startswith('Maximum reported')
    assert j('catalog/results/r-fast-v1-train-speed.json')['values']['Speedup factor']==5.0
def test_former_limited_sources_promoted_only_after_fulltext():
    r=j('maintenance/state/benchmark-review.json')['papers']
    for pid in ['p043','p046']:
        assert r[pid]['status']=='extracted' and r[pid]['trackIds'] and r[pid]['resultIds']
        p=j('catalog/papers/'+pid+'.json')
        assert p['note']['status']=='expanded' and p['note']['coverage']['level']=='deep'
    assert not (R/'catalog/results/r-dmsvla-abstract-range.json').exists()
    assert not (R/'catalog/results/r-vlabot-trial-bound.json').exists()
def test_negative_results_preserved():
    assert j('catalog/results/r-meco-v1-real-fast.json')['values']['Stack blocks']==60
    assert j('catalog/results/r-meco-v1-real-meco.json')['values']['Stack blocks']==60
    assert j('catalog/results/r-baton-v1-tsr-baton.json')['values']['Transferring TSR']==39.4
    assert j('catalog/results/r-lingbot-v2-async-fdm.json')['values']['Easy horizon=3']==85.6
    assert j('catalog/results/r-lingbot-v2-async-sync.json')['values']['Easy horizon=3']==93.2
def test_latest_version_reviews():
    for pid,mark in [('p018','v2'),('p075','v2'),('p030','v2'),('p038','v2'),('p034','v3'),('p037','v2')]:
        p=j('catalog/papers/'+pid+'.json')
        assert p['note']['status']=='expanded' and mark in p['note']['version']
    q=j('maintenance/state/work-queue.json')['notes']
    assert not any(x['paperId'] in {'p034','p075'} for x in q)
def test_counts_not_faked_as_sr():
    m=j('catalog/results/r-mvp-v1-pixmc-count.json')
    assert m['values']=={'Outperform supervised count':7,'Near state-oracle count':5}
    t={x['id']:x for x in j('catalog/benchmarks.json')['tracks']}
    assert t['mvp-v1-pixmc-textual-count']['unit']=='score'
def test_robodojo_score_sr_separated():
    t={x['id']:x for x in j('catalog/benchmarks.json')['tracks']}
    assert t['robodojo-v3-sim-score']['unit']=='score'
    assert t['robodojo-v3-sim-sr']['unit']=='percent'
    assert j('catalog/results/r-robodojo-v3-rand-hy.json')['values']=={'Standard':21.98,'Random':1.57}
