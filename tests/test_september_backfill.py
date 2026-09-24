import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def j(p): return json.loads((R/p).read_text())

NEW={
 'p099':('2609.05588','2026-09-04'),'p100':('2609.11561','2026-09-10'),
 'p101':('2609.16074','2026-09-13'),'p102':('2609.18197','2026-09-16'),
 'p103':('2609.19666','2026-09-17'),'p104':('2609.23863','2026-09-20'),
 'p105':('2609.24350','2026-09-21'),'p106':('2609.24682','2026-09-21'),
 'p107':('2609.25562','2026-09-22'),'p108':('2609.25636','2026-09-22'),
 'p109':('2609.26292','2026-09-22'),'p110':('2609.28431','2026-09-23')
}

def test_september_backfill_inventory_and_depth():
    manifest=j('catalog/manifest.json')
    assert len(manifest['paperOrder'])==110 and set(NEW)<=set(manifest['paperOrder'])
    for pid,(arxiv,date) in NEW.items():
        p=j(f'catalog/papers/{pid}.json')
        assert p['paper']['arxiv']==arxiv and p['paper']['firstPublished']==date
        assert p['paper']['collectionMonth']=='2026-09'
        assert p['note']['status']=='expanded' and p['note']['coverage']['level']=='deep'
        assert p['note']['verifiedAt']=='2026-09-24' and len(p['note']['sections'])>=8
        assert sum(len(s['body']) for s in p['note']['sections'])>=2000
        assert all(s['sources'] for s in p['note']['sections'])

def test_september_discovery_window_is_complete_but_deferred_stays_explicit():
    a=j('maintenance/audits/discovery-2026-09-01-2026-09-24.json')
    assert a['window']['from']=='2026-09-01' and a['window']['to']=='2026-09-24' and a['window']['completedAt']=='2026-09-24'
    assert a['counts']=={'total':276,'selected':12,'deferred':244,'excluded':20,'crossIndexed':79}
    assert {x['arxiv'] for x in a['candidates'] if x['status']=='selected'}=={v[0] for v in NEW.values()}
    state=j('maintenance/state/state.json')
    assert state['lastStatus']=='success' and state['lastSuccessfulSearchAt']=='2026-09-24'
    assert j('maintenance/state/work-queue.json')['remainingNotes']==0

def test_september_benchmark_dispositions_and_canonical_counts():
    review=j('maintenance/state/benchmark-review.json')['papers']
    counts={}
    for x in review.values(): counts[x['status']]=counts.get(x['status'],0)+1
    assert counts=={'extracted':102,'not-applicable':3,'deferred':5}
    assert {pid for pid,x in review.items() if x['status']=='deferred'}=={'p102','p103','p105','p107','p110'}
    assert len(j('catalog/benchmarks.json')['tracks'])==293
    assert len(list((R/'catalog/results').glob('r-*.json')))==1091

def test_september_resources_are_verified_or_absent_not_placeholder():
    resources=j('catalog/resources.json')['papers']
    for pid in ['p099','p100','p101','p102','p104','p105','p106','p107','p108','p110']:
        assert pid in resources and resources[pid]
    assert 'p103' not in resources and 'p109' not in resources
    assert resources['p108']['code']=='https://github.com/AutoLab-SAI-SJTU/RoboFollow'

def test_latest_main_candidate_is_september_not_august():
    papers=[j(f'catalog/papers/{pid}.json')['paper'] for pid in j('catalog/manifest.json')['paperOrder']]
    exact=[p for p in papers if isinstance(p['firstPublished'],str) and len(p['firstPublished'])==10]
    latest=max(p['firstPublished'] for p in exact)
    assert latest=='2026-09-23'
    assert any(p['id']=='p110' and p['firstPublished']==latest for p in exact)
