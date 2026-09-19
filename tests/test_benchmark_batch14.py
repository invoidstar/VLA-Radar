import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def j(p): return json.loads((R/p).read_text())
def test_batch14_counts():
    r=j('maintenance/benchmark-review.json')['papers']
    assert all(r[x]['status']=='extracted' for x in ['p012','p014','p025','p002','p015'])
    assert sum(x['status']=='extracted' for x in r.values())==67
    assert sum(x['status']=='deferred' for x in r.values())==29
    assert len(j('catalog/benchmarks.json')['tracks'])==207
    assert len(list((R/'catalog/results').glob('r-*.json')))==775
def test_ocvla_fixed_negative_preserved():
    a=j('catalog/results/r-ocvlapp-v1-qwen-ocvla.json')['values']
    b=j('catalog/results/r-ocvlapp-v1-qwen-plus.json')['values']
    assert a['Fixed view']==60.0 and b['Fixed view']==59.2
    assert b['Largest displacement']==43.3
def test_temporalflow_subset_boundary():
    x=j('catalog/results/r-temporalflow-v1-rt12-full.json')
    assert x['values']=={'Clean':85.5,'Random':84.2}
    t={z['id']:z for z in j('catalog/benchmarks.json')['tracks']}
    assert t['temporalflow-v1-robotwin12-ablation']['tasks']=='12 tasks'
def test_vtwam_negative_ablation_and_mixed_metric():
    assert j('catalog/results/r-vtwam-v1-ablation-m2.json')['values']['Wipe Vase score']==40
    assert j('catalog/results/r-vtwam-v1-ablation-m0.json')['values']['Wipe Vase score']==55
    t={z['id']:z for z in j('catalog/benchmarks.json')['tracks']}
    assert 'mixed' in t['vtwam-v1-real-main']['metric'].lower()
def test_vlaflow_negative_transfer():
    a=j('catalog/results/r-vlaflow-v2-rt1-pi-nopt.json')['values']
    b=j('catalog/results/r-vlaflow-v2-rt1-pi-full.json')['values']
    assert a['RT-1 VM']==75.7 and b['RT-1 VM']==68.2
def test_onevomemory_real_zero_not_missing():
    x=j('catalog/results/r-onevomemory-v1-rmbench-base.json')
    assert x['values']=={'SwapBlocks':0,'SwapT':0}
