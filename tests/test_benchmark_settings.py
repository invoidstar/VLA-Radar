import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/build'))
from catalog_core import read_catalog
from benchmark_settings import build_settings,training_known

def catalog():
    _,_,tracks,results=read_catalog(ROOT)
    return tracks,results,build_settings(tracks,results)

def test_every_checked_visible_result_appears_once():
    tracks,results,settings=catalog()
    superseded={r['supersedes'] for r in results if r['evidence']=='checked' and r['supersedes']}
    expected={r['id'] for r in results if r['evidence']=='checked' and r['id'] not in superseded}
    actual=[rid for s in settings for rid in s['resultIds']]
    assert set(actual)==expected
    assert len(actual)==len(expected)

def test_every_dataset_with_checked_results_has_settings():
    tracks,results,settings=catalog();trackmap={t['id']:t for t in tracks}
    expected={trackmap[r['trackId']]['dataset'] for r in results if r['evidence']=='checked'}
    assert expected=={s['dataset'] for s in settings}

def test_setting_metric_and_training_are_consistent():
    tracks,results,settings=catalog();trackmap={t['id']:t for t in tracks};resultmap={r['id']:r for r in results}
    for s in settings:
        assert all(trackmap[resultmap[rid]['trackId']]['dataset']==s['dataset'] for rid in s['resultIds'])
        assert all(trackmap[resultmap[rid]['trackId']]['unit']==s['unit'] for rid in s['resultIds'])
        assert all(trackmap[resultmap[rid]['trackId']]['direction']==s['direction'] for rid in s['resultIds'])
        if s['trainingKnown']:
            normalized={' '.join(resultmap[rid]['trainingData'].lower().split()) for rid in s['resultIds']}
            assert len(normalized)==1
        else:
            assert s['paperCount']==1

def test_curated_cross_track_equivalence_only_where_declared():
    tracks,_,settings=catalog();trackmap={t['id']:t for t in tracks}
    for s in settings:
        if len(s['trackIds'])<=1:continue
        ts=[trackmap[x] for x in s['trackIds']]
        eval_ids={t.get('settingEvalId') or (t.get('familyId') if t.get('familyMode')=='aligned' else None) for t in ts}
        assert len(eval_ids)==1 and None not in eval_ids

def test_libero_budget_variants_are_recipe_rows_not_settings():
    _,_,settings=catalog()
    target=[s for s in settings if set(s['trackIds'])=={
        'libero-infoentropy-v1-budget60','libero-infoentropy-v1-budget80',
        'libero-infoentropy-v1-budget120','libero-infoentropy-v1-budget140'}]
    assert len(target)==1
    assert target[0]['resultCount']==4

def test_robocasa365_same_protocol_and_training_crosses_sources():
    _,_,settings=catalog()
    target=[s for s in settings if {'robocasa365-official-100','robocasa365-official-101'}<=set(s['trackIds'])]
    assert target
    assert any(s['paperCount']>=3 for s in target)

def test_robomimic_observation_recipes_share_setting_and_keep_duplicate_methods():
    tracks,results,settings=catalog();resultmap={r['id']:r for r in results}
    target=next(s for s in settings if set(s['trackIds'])=={'robomimic-corl21-lowdim-ph-best','robomimic-corl21-image-ph-best'})
    names=[resultmap[rid]['method'] for rid in target['resultIds']]
    assert names.count('BC-RNN')==2
    assert target['trainingKnown']

def test_actioncache_distinct_tasks_never_auto_merge():
    _,_,settings=catalog()
    for s in settings:
        action=[tid for tid in s['trackIds'] if tid.startswith('actioncache-v2-real-')]
        assert len(action)<=1

def test_robotwin_clean_only_training_modes_become_recipes():
    _,_,settings=catalog()
    assert any(set(s['trackIds'])=={'robotwin2-turbovla-v2-clean-per-task','robotwin2-turbovla-v2-clean-multi-task'} for s in settings)
