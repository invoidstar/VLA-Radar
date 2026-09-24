import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def j(p): return json.loads((R/p).read_text())
def test_batch15_counts():
    r=j('maintenance/state/benchmark-review.json')['papers']
    assert all(r[x]['status']=='extracted' for x in ['p011','p020','p009','p060','p003'])
    assert sum(x['status']=='extracted' for x in r.values())>=96
        assert len(j('catalog/benchmarks.json')['tracks'])>=286
    assert len(list((R/'catalog/results').glob('r-*.json')))>=1063
def test_seelike_negative_and_view_boundary():
    assert j('catalog/results/r-seelike-v1-fusion-pc-mlp.json')['values']['Average']==24.2
    assert j('catalog/results/r-seelike-v1-fusion-rgb.json')['values']['Average']==27.9
    assert j('catalog/results/r-seelike-v1-view-ee.json')['values']=={'Fixed':36.9,'Randomized':36.6}
def test_smile_units_and_chain():
    t={x['id']:x for x in j('catalog/benchmarks.json')['tracks']}
    assert t['smile-v1-calvin-chain']['unit']=='score'
    assert t['smile-v1-calvin-action-time']['unit']=='seconds'
    assert j('catalog/results/r-smile-v1-time-smile-vpp.json')['values']['Seconds per action']==0.013
def test_gwm_standard_tie_and_plus_gain():
    assert j('catalog/results/r-gwm-v1-libero-oft.json')['values']['Average']==97.1
    assert j('catalog/results/r-gwm-v1-libero-gwm.json')['values']['Average']==97.1
    assert j('catalog/results/r-gwm-v1-plus-gwm.json')['values']['Average']==76.9
def test_roboflamingo_metric_separation_and_review():
    assert j('catalog/results/r-roboflamingo-abcd-chain-rf.json')['values']['Average length']==4.09
    assert j('catalog/results/r-roboflamingo-abcd-five-rf.json')['values']['Five-task success']==66.0
    p=j('catalog/papers/p060.json')
    assert p['note']['status']=='expanded'
def test_lumo_probe_not_robot_sr():
    x=j('catalog/results/r-lumo2-v1-probe-stage2.json')
    assert x['values']['Accuracy']==95.0
    t={z['id']:z for z in j('catalog/benchmarks.json')['tracks']}
    assert 'semantic classification' in t['lumo2-v1-semantic-probe']['metric'].lower()
