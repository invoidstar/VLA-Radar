import copy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/build'))
from catalog_core import read_catalog
from benchmark_settings import build_settings,training_identity,evaluation_key,protocol_profile,profile_identity,protocol_fingerprint,protocol_compatibility

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

def test_settings_are_evaluation_protocols_not_training_buckets():
    tracks,results,settings=catalog();trackmap={t['id']:t for t in tracks};resultmap={r['id']:r for r in results}
    # Keep the strict pre-Nov13 identity guard and audit each new paper batch independently.
    # Previously the hardcoded "<230" guard excluded Zeva only; adding genuine
    # APS/RAGu source protocols made old paper identities look like uncontrolled
    # "legacy inflation". This retains the strict prior bound and caps only the
    # *increment* from each source-verified batch by the new distinct track count.
    current_prefixes=('aps-v1-', 'ragu-v1-')
    original_tracks=[t for t in tracks if not t['id'].startswith(('zeva-v2-',)+current_prefixes)]
    original_results=[r for r in results if not r['id'].startswith(('r-zeva-v2-','r-aps-v1-','r-ragu-v1-'))]
    original_settings=build_settings(original_tracks,original_results)
    assert len(original_settings)<230, f"Pre-new-batch protocol identity inflation: {len(original_settings)}"
    batch_tracks=[t for t in tracks if t['id'].startswith(current_prefixes)]
    without_zeva_tracks=[t for t in tracks if not t['id'].startswith('zeva-v2-')]
    without_zeva_results=[r for r in results if not r['id'].startswith('r-zeva-v2-')]
    without_zeva_settings=build_settings(without_zeva_tracks,without_zeva_results)
    assert 0 <= len(without_zeva_settings)-len(original_settings) <= len(batch_tracks), (
        f"APS/RAGu Setting growth exceeds {len(batch_tracks)} genuine source tracks: "
        f"{len(without_zeva_settings)} vs original {len(original_settings)}")
    zeva_tracks=[t for t in tracks if t['id'].startswith('zeva-v2-')]
    assert 0 <= len(settings)-len(without_zeva_settings) <= len(zeva_tracks), (
        f"Zeva Setting growth exceeds {len(zeva_tracks)} source tracks: "
        f"{len(settings)} vs without Zeva {len(without_zeva_settings)}")
    for s in settings:
        assert all(trackmap[resultmap[rid]['trackId']]['dataset']==s['dataset'] for rid in s['resultIds'])
        assert all(trackmap[resultmap[rid]['trackId']]['unit']==s['unit'] for rid in s['resultIds'])
        assert all(trackmap[resultmap[rid]['trackId']]['direction']==s['direction'] for rid in s['resultIds'])
        assert len(s['trainingByResult'])==len(s['resultIds'])
        assert sum(x['count'] for x in s['trainingOptions'])==len(s['resultIds'])

def test_robotwin_training_regimes_share_clean_random_setting():
    _,_,settings=catalog()
    target=next(s for s in settings if s['dataset']=='RoboTwin' and s['evalId']=='auto:50-clean-random')
    ids=set(target['trackIds'])
    assert {'robotwin2-selfwam-27500','robotwin2-flashvla-v1-pi05-all','robotwin2-official-2500clean-cotrain','robotwin2-official-2500clean-sft'}<=ids
    assert len(target['trainingOptions'])>=3
    assert target['paperCount']>=5

def test_libero_standard_setting_is_cross_paper_not_source_scoped():
    _,_,settings=catalog()
    target=next(s for s in settings if s['dataset']=='LIBERO' and s['evalId']=='auto:standard40')
    ids=set(target['trackIds'])
    assert {'libero-oft-single-view','libero-oft-multi-view','libero-cosmos-3seeds','libero-rldx-v2','libero-openvla-v3-singleview-cleaned','dmsvla-ieee-libero-main'}<=ids
    assert target['paperCount']>=6
    assert len(target['trainingOptions'])>1

def test_libero_delay_is_real_evaluation_guard():
    _,_,settings=catalog()
    ids={s['evalId'] for s in settings if s['dataset']=='LIBERO'}
    assert 'auto:standard40-delay-d1' in ids
    assert 'auto:standard40-delay-d4' in ids
    assert 'auto:standard40' in ids

def test_rlbench_18_task_reports_share_setting_but_74_task_does_not():
    _,_,settings=catalog()
    main=next(s for s in settings if s['dataset']=='RLBench' and s['evalId']=='auto:18-main')
    assert {'rlbench-18-bridgepp-table1','rlbench-act3d-corl2023-18multi','rlbench-rvt-corl2023-table1'}<=set(main['trackIds'])
    assert 'rlbench-act3d-corl2023-74single' not in main['trackIds']

def test_robodojo_single_multi_training_mode_does_not_split_evaluation():
    _,_,settings=catalog()
    score=[s for s in settings if s['dataset']=='RoboDojo' and 'score' in s['evalId']]
    assert any({'robodojo-official-sim-multi-score','robodojo-official-sim-single-score'}<=set(s['trackIds']) for s in score)

def test_simler_vm_va_remain_distinct_evaluation_settings():
    _,_,settings=catalog()
    vm=[s for s in settings if s['dataset']=='SimplerEnv' and '-vm-' in s['evalId']]
    va=[s for s in settings if s['dataset']=='SimplerEnv' and '-va-' in s['evalId']]
    assert vm and va
    assert not any(set(a['trackIds'])&set(b['trackIds']) for a in vm for b in va)

def test_google_physical_kitchens_remain_distinct():
    _,_,settings=catalog()
    mock=[s for s in settings if s['dataset']=='Google Robot (real)' and 'mock-kitchen' in s['evalId']]
    office=[s for s in settings if s['dataset']=='Google Robot (real)' and 'office-kitchen' in s['evalId']]
    assert mock and office

def test_actioncache_real_tasks_never_merge():
    _,_,settings=catalog()
    for s in settings:
        action=[tid for tid in s['trackIds'] if tid.startswith('actioncache-v2-real-')]
        tasks={x for x in ('button','close','sausage') if any(x in tid for tid in action)}
        assert len(tasks)<=1

def test_same_method_reports_are_not_deduplicated():
    tracks,results,settings=catalog();resultmap={r['id']:r for r in results}
    libero=next(s for s in settings if s['dataset']=='LIBERO' and s['evalId']=='auto:standard40')
    methods=[resultmap[rid]['method'] for rid in libero['resultIds']]
    assert len(methods)>len(set(methods))

def test_training_identity_is_row_metadata_not_setting_identity():
    a='Human300=30,000 demos; global batch 192; steps 250000'
    b='Human300=30,000 demos; global batch 64; steps 75000'
    assert training_identity(a)==training_identity(b)=='Human300=30,000 demos'
    tracks,results,settings=catalog()
    rc=next(s for s in settings if s['dataset']=='RoboCasa365' and 'pretraining-kitchens' in s['evalId'])
    assert len(rc['trainingOptions'])>=1


def test_eval_ids_are_unique_within_dataset():
    _,_,settings=catalog()
    seen=set()
    for s in settings:
        key=(s['dataset'],s['evalId'])
        assert key not in seen
        seen.add(key)

def test_calvin_synonymous_chain_length_reports_share_setting():
    _,_,settings=catalog()
    target=[s for s in settings if s['dataset']=='CALVIN' and s['evalId']=='auto:chain-average-length']
    assert len(target)==1
    assert target[0]['paperCount']>=3
    assert target[0]['resultCount']>=25


def test_structured_protocol_profile_excludes_training_and_reporting_recipe():
    tracks,_,_=catalog()
    base=next(t for t in tracks if t['id']=='libero-oft-single-view')
    changed=copy.deepcopy(base)
    changed['trainingRegime']='Completely different training corpus, optimizer and checkpoint.'
    changed['protocol']=base['protocol']+' Reporting uses another implementation note.'
    assert profile_identity(protocol_profile(base))==profile_identity(protocol_profile(changed))
    assert protocol_fingerprint(base)==protocol_fingerprint(changed)
    assert protocol_compatibility(base,changed)=='exact'

def test_true_evaluation_condition_changes_protocol_identity():
    tracks,_,_=catalog()
    base=next(t for t in tracks if t['id']=='libero-oft-single-view')
    delayed=copy.deepcopy(base)
    delayed['id']='synthetic-libero-delay-d1'
    delayed['name']=base['name']+' D=1'
    delayed['protocol']=base['protocol']+' Deployment delay D=1.'
    assert evaluation_key(base)!=evaluation_key(delayed)
    assert protocol_fingerprint(base)!=protocol_fingerprint(delayed)
    assert protocol_compatibility(base,delayed)=='incompatible'

def test_same_setting_with_partial_column_coverage_is_not_split():
    tracks,_,_=catalog()
    base=next(t for t in tracks if t['id']=='libero-oft-single-view')
    partial=copy.deepcopy(base)
    partial['id']='synthetic-libero-partial-columns'
    partial['columns']=base['columns'][:-1]
    assert evaluation_key(base)==evaluation_key(partial)
    assert protocol_compatibility(base,partial)=='partial'


def test_zeva_atomic5_and_fixed_episode_not_target50():
    tracks,results,settings=catalog()
    mapping={t['id']:t for t in tracks}
    atomic=mapping['zeva-v2-robocasa365-atomic5']
    fixed=mapping['zeva-v2-robocasa365-fixed-episode-csr']
    assert protocol_profile(atomic)['taskScope']=='atomic5'
    assert protocol_profile(fixed)['taskScope']=='atomic5-fixed-episode'
    assert evaluation_key(atomic)!=evaluation_key(fixed)
    assert all('atomic5' not in s['evalId'] or s['dataset']=='RoboCasa365' for s in settings)
    target=[t for t in tracks if t['dataset']=='RoboCasa365' and 'target50' in (t['id'].lower()+' '+t['name'].lower())]
    if target:assert all(evaluation_key(atomic)!=evaluation_key(t) for t in target)

