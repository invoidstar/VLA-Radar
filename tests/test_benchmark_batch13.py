import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def j(p): return json.loads((R/p).read_text())
def test_batch13_counts():
    r=j('maintenance/benchmark-review.json')['papers']
    assert all(r[x]['status']=='extracted' for x in ['p017','p035','p036','p023','p039'])
    assert sum(x['status']=='extracted' for x in r.values())==62
    assert sum(x['status']=='deferred' for x in r.values())==34
    assert len(j('catalog/benchmarks.json')['tracks'])==194
    assert len(list((R/'catalog/results').glob('r-*.json')))==720
def test_tau0_ttc():
    assert j('catalog/results/r-tau0-v1-ttc-ttc.json')['values']=={'Make Milk Tea':70,'Book Organization':90,'Clean Room':70}
def test_cotrain_no_reverse():
    x=j('catalog/results/r-cotrain-v1-sim-unseen-final.json'); assert x['values']['Average']==72.6 and '不由36.4' in x['evaluationNotes']
def test_halo_negative_boundary():
    assert j('catalog/results/r-halo-rss26-sim-hand.json')['values']['Retrieve Object']==68
    assert j('catalog/results/r-halo-rss26-sim-halo.json')['values']['Retrieve Object']==64
def test_dswam_units():
    t={x['id']:x for x in j('catalog/benchmarks.json')['tracks']}
    assert t['dswam-v1-real-folding-time']['unit']=='seconds' and t['dswam-v1-sorting-errors']['direction']=='lower'
    assert j('catalog/results/r-dswam-v1-fold-time-dswam.json')['values']['Average']==104
def test_veritas_small_n():
    x=j('catalog/results/r-veritas-v1-carrot50-auto.json'); assert x['values']['Success']==70 and '20' in x['evaluationNotes']
