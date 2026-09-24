import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def j(p): return json.loads((R/p).read_text())
def test_final_counts_zero_deferred_and_notes():
    review=j('maintenance/state/benchmark-review.json')['papers']
    assert all(review[pid]['status']=='extracted' for pid in ['p043','p046'])
    assert sum(x['status']=='extracted' for x in review.values())>=96
    assert sum(x['status']=='not-applicable' for x in review.values())>=2
    assert len(j('catalog/benchmarks.json')['tracks'])>=286
    assert len(list((R/'catalog/results').glob('r-*.json')))>=1063
    assert j('maintenance/state/work-queue.json')['remainingNotes']==0
    assert j('maintenance/state/work-queue.json')['notes']==[]
    cat=[j('catalog/papers/p043.json'),j('catalog/papers/p046.json')]
    assert all(x['note']['status']=='expanded' and x['note']['coverage']['level']=='deep' for x in cat)
def test_limited_policy_cleared():
    limited=j('maintenance/policies/editorial-policy.json')['limitedLegacyIds']
    assert 'p043' not in limited and 'p046' not in limited
def test_dms_negative_cells_and_speedup_distinction():
    base=j('catalog/results/r-dms-ieee-libero-openvla.json')['values']
    dms=j('catalog/results/r-dms-ieee-libero-openvla-dms.json')['values']
    assert base['Object']==88.4 and dms['Object']==88.1
    assert base['Goal']==79.2 and dms['Goal']==78.9
    assert j('catalog/results/r-dms-ieee-eff-speed-dms-int4.json')['values']=={'Jetson Orin':2.96,'H100':2.64}
    assert j('catalog/results/r-dms-ieee-fig6-libero-openvla.json')['values']=={'Jetson Orin':1.56,'RTX4090':1.5,'H100':1.41}
def test_dms_template_tradeoff():
    q12=j('catalog/results/r-dms-ieee-template-quality-12.json')['values']
    q2=j('catalog/results/r-dms-ieee-template-quality-2.json')['values']
    s12=j('catalog/results/r-dms-ieee-template-speed-12.json')['values']
    s2=j('catalog/results/r-dms-ieee-template-speed-2.json')['values']
    assert q12=={'LIBERO Average':76.5,'SIMPLER Average':33.0}
    assert q2=={'LIBERO Average':72.9,'SIMPLER Average':30.3}
    assert s12['Jetson Orin']==1.56 and s2['Jetson Orin']==1.85
def test_vlabot_learning_and_nonmonotonic_interaction():
    assert j('catalog/results/r-vlabot-trial-success-1.json')['values']=={'Gear assembly':2,'Beam assembly':1}
    assert j('catalog/results/r-vlabot-trial-success-3.json')['values']=={'Gear assembly':3,'Beam assembly':3}
    assert j('catalog/results/r-vlabot-trial-int-1.json')['values']['Beam assembly']==37.3
    assert j('catalog/results/r-vlabot-trial-int-2.json')['values']['Beam assembly']==56
def test_vlabot_missing_is_null_not_zero():
    no=j('catalog/results/r-vlabot-exec-no-updates.json')['values']
    ramp=j('catalog/results/r-vlabot-exec-ramp.json')['values']
    assert no['Gear3'] is None and no['Peg2'] is None and no['Beam'] is None
    assert ramp['Gear1'] is None and ramp['Beam'] is None
def test_vlabot_table_times_authoritative():
    assert j('catalog/results/r-vlabot-trial-time-1.json')['values']=={'Gear assembly':1360.11,'Beam assembly':1177.24}
    assert j('catalog/results/r-vlabot-trial-time-5.json')['values']=={'Gear assembly':500.86,'Beam assembly':498.06}
    p=j('catalog/papers/p046.json')
    assert any('1360.11' in x and '500.86' in x for x in p['publication']['alerts'])
