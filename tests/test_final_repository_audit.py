import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def j(p): return json.loads((R/p).read_text())
def test_content_queues_are_closed():
    r=j('maintenance/state/benchmark-review.json')['papers']
    counts={}
    for x in r.values(): counts[x['status']]=counts.get(x['status'],0)+1
    assert counts.get('extracted',0)>=102 and counts.get('not-applicable',0)>=3 and counts.get('deferred',0)>=5
    baseline_deferred={'p102','p103','p105','p107','p110'}
    assert baseline_deferred <= {pid for pid,x in r.items() if x['status']=='deferred'}
    assert all(r[pid]['note'] and not r[pid]['trackIds'] and not r[pid]['resultIds'] for pid in baseline_deferred)
    w=j('maintenance/state/work-queue.json')
    assert w['remainingNotes']==0 and w['notes']==[]
def test_final_counts_and_referential_closure():
    a=j('maintenance/audits/release/final-consistency-audit-20260920.json')
    assert a['canonical']['papers']==98
    assert a['canonical']['results']==1063
    assert a['canonical']['tracks']==286
    assert a['canonical']['orphanResults']==0
    assert a['canonical']['orphanTracks']==0
def test_cleanup_audit_is_exact_and_conservative():
    a=j('maintenance/audits/release/final-branch-cleanup-20260920.json')
    assert {x['branch'] for x in a['deleted']}=={
      'pre-update-safety-2026-09-17',
      'feature/vla-radar-v2-2026-09-17',
      'weekly-update-2026-09-18-benchmark-batch4'}
    preserved={x['branch']:x['reason'] for x in a['preserved']}
    assert 'release/deep-notes-2026-09-17' in preserved
    assert 'unique historical content commits' in preserved['release/deep-notes-2026-09-17']
def test_governance_warning_is_not_hidden():
    g=j('maintenance/audits/release/final-consistency-audit-20260920.json')['governance']
    assert g['branchProtectionReadHttpStatus']==403
    assert g['branchProtectionReadAccessible'] is False
