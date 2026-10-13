"""Regression checks for audited Benchmark identities and read-only evidence projections."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts/build'))
from catalog_core import read_catalog
from build_catalog import curated_benchmark
from benchmark_quality import apply_quality, canonical_column, load_quality
from benchmark_settings import build_settings

def _data():
    _,_,tracks,results=read_catalog(ROOT)
    before={r['id']:(r['trackId'],dict(r['values'])) for r in results}
    dt,dr=curated_benchmark(ROOT,tracks,results)
    qt,qr,registry=apply_quality(ROOT,dt,dr)
    settings=build_settings(qt,qr)
    return before,dt,dr,qt,qr,registry,settings

def test_registry_tracks_all_exposed_datasets_and_does_not_modify_canonical():
    before,_,_,tracks,rows,registry,settings=_data()
    assert {t['dataset'] for t in tracks} <= set(registry['benchmarks'])
    assert len({x['id'] for x in rows})==len(rows)
    assert all(x['id'] in before for x in rows)
    assert all(s['columnMeta'] for s in settings)
    danger = next(t for t in tracks if t['id']=='safeloop-v1-libero-safety')
    assert danger['columnDirections']['Haz-B']=='lower' and danger['columnUnits']['Haz-B']=='percent'
    chain = next(t for t in tracks if t['id']=='foreact3d-v1-calvin-abc-no-pretrain')
    assert chain['columnUnits']['Task 1']=='percent' and chain['columnUnits']['Average length']=='score'
    assert all(s.get('latestReportVerifiedAt') for s in settings)
    assert registry['benchmarks']['RoboCasa365']['officialUrl']=='https://robocasa.ai/leaderboard.html'
    assert all(s['primaryResultCount']<=s['resultCount'] for s in settings)
    assert any(x['qualityKind']=='case-study' for x in settings)

def test_robocasa_atomic_and_composite_never_merge():
    *_,settings=_data()
    atom=next(s for s in settings if s['dataset']=='RoboCasa' and s['evalId']=='auto:24-main')
    comp=next(s for s in settings if s['dataset']=='RoboCasa' and s['evalId']=='auto:5-composite')
    assert 'robocasa-original-5composite-v1' not in atom['trackIds']
    assert 'robocasa-original-5composite-v1' in comp['trackIds']
    assert 'Arrange vegetables' not in atom['columns']

def test_libero_source_experiments_not_merged_into_standard40():
    *_,settings=_data()
    standard=next(s for s in settings if s['dataset']=='LIBERO' and s['evalId']=='auto:standard40')
    for forbidden in ('safeloop-v1-libero-safety','toast-v1-libero-data-scale','libero-plus-rldx-v2'):
        assert forbidden not in standard['trackIds']
    assert not any(x in standard['columns'] for x in ('Haz-B','Haz-O','1/1','1/16'))
    safety=next(s for s in settings if s['dataset']=='LIBERO' and s['evalId']=='auto:safety-24')
    assert safety['columnMeta']['Haz-B']['direction']=='lower'

def test_libero_plus_identity_alias_preserves_original_result_ids():
    *_,tracks,rows,registry,settings=_data()
    assert next(t for t in tracks if t['id']=='libero-plus-rldx-v2')['dataset']=='LIBERO-Plus'
    assert all(x['id'] for x in rows)
    assert registry['legacySettingTracks']['setting-libero-plus-d7a11d009077']=='libero-plus-rldx-v2'

def test_rlbench_column_aliases_are_really_one_task():
    *_,settings=_data()
    main=next(s for s in settings if s['dataset']=='RLBench' and s['evalId']=='auto:18-main')
    assert 'Open Drawer' in main['columns']
    assert 'Open drawer' not in main['columns']
    assert 'Sweep' not in main['columns']
    assert 'Sweep to Dustpan' in main['columns']

def test_calvin_mixed_units_not_mislabeled():
    *_,settings=_data()
    composite=next(s for s in settings if s['dataset']=='CALVIN' and 'Task 1' in s['columns'])
    assert composite['columnMeta']['Task 1']['unit']=='percent'
    assert composite['columnMeta']['Average length']['unit']=='score'

def test_budget_sweeps_and_repeated_reports_remain_in_archives():
    *_,rows,registry,settings=_data()
    sweep=[x for x in rows if x['id']=='r-libero-infoentropy-v1-budget60-ours']
    assert len(sweep)==1 and sweep[0]['displayTier']=='sweep'
    assert sum(s['primaryResultCount'] for s in settings)==registry['primaryResultCount']
    assert sum(s['resultCount'] for s in settings)==len([x for x in rows if x['evidence']=='checked' and not x.get('superseded')])

def test_robodojo_coap_and_physevo_are_paper_reports_not_official_ranks():
    _,_,_,tracks,rows,_,settings=_data()
    canonical={"robodojo-coap-v1-sim-sr","robodojo-coap-v1-sim-score",
               "robodojo-physevo-v1-sim-sr","robodojo-physevo-v1-sim-score"}
    present={t['id'] for t in tracks}
    assert canonical<=present
    selected=[r for r in rows if r['trackId'] in canonical]
    assert len(selected)==4
    assert all(r['displayTier']=='paper' for r in selected)
    assert sum(s['primaryResultCount'] for s in settings if set(s['trackIds'])&canonical)==0
    assert all(s['dataset']=='RoboDojo' for s in settings if set(s['trackIds'])&canonical)
