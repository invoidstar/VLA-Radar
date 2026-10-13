"""Audited presentation projection for the public Benchmark explorer.

Never rewrite canonical catalog/results or turn a cited baseline into an independent
measurement. Registry classification and overrides are narrow, reviewable assertions.
"""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import copy
import json
import re
import unicodedata

from benchmark_settings import evaluation_key


def _norm(value):
    return unicodedata.normalize('NFKC', str(value or '')).casefold().strip()


def method_identity(value):
    norm = _norm(value).replace('π', 'pi').replace('δ', 'delta')
    return re.sub(r'[^a-z0-9]+', '', norm) or 'unknown'


def canonical_column(dataset, name):
    """Only merge verified lexical aliases, never similarly scored metrics."""
    name = str(name)
    if dataset == 'RLBench':
        if _norm(name) == 'sweep':
            return 'Sweep to Dustpan'
        if _norm(name) == 'sweep to dustpan':
            return 'Sweep to Dustpan'
        standard = {
            'open drawer', 'slide block', 'meat off grill', 'turn tap',
            'put in drawer', 'close jar', 'drag stick', 'stack blocks',
            'screw bulb', 'put in safe', 'place wine', 'put in cupboard',
            'sort shape', 'push buttons', 'insert peg', 'stack cups',
            'place cups',
        }
        if _norm(name) in standard:
            return ' '.join(part.capitalize() if part.lower() not in {'in', 'off'} else part.lower()
                            for part in name.lower().split())
    if dataset == 'RoboMimic' and re.sub(r'\s+', '', _norm(name)) == 'toolhang':
        return 'Tool Hang'
    if dataset == 'SimplerEnv' and re.sub(r'\s+', '', _norm(name)) == 'open/closedrawer':
        return 'Open/Close Drawer'
    return name


def column_spec(track, column):
    default = {'unit': track['unit'], 'direction': track['direction']}
    if track['dataset'] == 'CALVIN' and re.fullmatch(r'Task [1-5]', column):
        return {'unit': 'percent', 'direction': 'higher'}
    if track['id'] == 'safeloop-v1-libero-safety':
        if column in {'Haz-B', 'Haz-O'}:
            return {'unit': 'percent', 'direction': 'lower'}
        if column == 'Success':
            return {'unit': 'percent', 'direction': 'higher'}
    return default


def load_quality(root):
    path = Path(root) / 'catalog/benchmark-quality.json'
    registry = json.loads(path.read_text(encoding='utf-8'))
    expected = {'schemaVersion','description','benchmarks','datasetAliases',
                'scopeOverrides','trackTiers','resultTiers','legacySettingTracks'}
    if registry.get('schemaVersion') != 1 or set(registry) != expected:
        raise ValueError('Benchmark quality registry schema mismatch')
    for name, item in registry['benchmarks'].items():
        if item.get('kind') not in {'benchmark', 'case-study'}:
            raise ValueError('Unclassified Benchmark: '+name)
        url = item.get('officialUrl')
        if url is not None and not str(url).startswith('https://'):
            raise ValueError('Invalid official URL for '+name)
    for tier in list(registry['trackTiers'].values())+list(registry['resultTiers'].values()):
        if tier not in {'primary', 'paper', 'sweep', 'case-study'}:
            raise ValueError('Unknown presentation tier: '+tier)
    return registry


def apply_quality(root, tracks, results):
    """Project aliases, per-column meaning and display roles, preserving IDs/rows."""
    registry = load_quality(root)
    ids = {t['id'] for t in tracks}
    result_ids = {r['id'] for r in results}
    for key in ('datasetAliases', 'scopeOverrides', 'trackTiers'):
        unknown = set(registry[key]) - ids
        if unknown:
            raise ValueError('Quality '+key+' refers to absent track: '+str(sorted(unknown)))
    if set(registry['resultTiers']) - result_ids:
        raise ValueError('Quality result tiers refer to absent rows')
    projected_tracks = []
    for original in tracks:
        t = copy.deepcopy(original)
        t['dataset'] = registry['datasetAliases'].get(t['id'], t['dataset'])
        if t['dataset'] not in registry['benchmarks']:
            raise ValueError('Review new Benchmark classification before publishing: '+t['dataset'])
        t['qualityKind'] = registry['benchmarks'][t['dataset']]['kind']
        if t['id'] in registry['scopeOverrides']:
            t['evaluationScope'] = registry['scopeOverrides'][t['id']]
        t['columns'] = list(dict.fromkeys(canonical_column(t['dataset'], c) for c in t['columns']))
        t['columnSpecs'] = {c: column_spec(t, c) for c in t['columns']}
        # Advanced raw-track charts and ranking must honour metric-level direction.
        t['columnDirections'] = {c: item['direction'] for c, item in t['columnSpecs'].items()}
        t['columnUnits'] = {c: item['unit'] for c, item in t['columnSpecs'].items()}
        projected_tracks.append(t)
    track_by_id = {t['id']:t for t in projected_tracks}
    source_by_id = {t['id']:t for t in tracks}
    projected_results = []
    for original in results:
        row = copy.deepcopy(original)
        t = track_by_id[row['trackId']]
        old_t = source_by_id[row['trackId']]
        vals = {}
        for old_col, v in row['values'].items():
            col = canonical_column(t['dataset'], old_col)
            if col in vals and vals[col] != v:
                raise ValueError('Conflicting values for canonical task column: '+row['id']+': '+col)
            vals[col] = v
        if any(c not in t['columns'] for c in vals):
            raise ValueError('Unrecognized task column in '+row['id'])
        row['values'] = vals
        row['methodId'] = method_identity(row['method'])
        tier = ('case-study' if t['qualityKind']=='case-study' else 'primary')
        tier = registry['trackTiers'].get(t['id'], tier)
        tier = registry['resultTiers'].get(row['id'], tier)
        row['displayTier'] = tier
        row['sourceClass'] = ('official-snapshot' if t['id'].startswith('robodojo-official-')
                              else ('cited-baseline' if row.get('attribution')=='reported-baseline'
                                    else ('independent' if row.get('attribution')=='independent-reproduction'
                                          else 'paper-reported')))
        projected_results.append(row)
    # Repeated citations are not independent evaluations. Suppress only on the
    # default *presentation*; leave every original report, training note and URL.
    groups = defaultdict(list)
    for row in projected_results:
        if row.get('evidence') != 'checked':
            continue
        signature = (evaluation_key(track_by_id[row['trackId']]), row['methodId'],
                     tuple(sorted((k, v) for k, v in row['values'].items())))
        groups[signature].append(row)
    for same in groups.values():
        if len(same) < 2:
            continue
        ordered = sorted(same, key=lambda row: (
            0 if row.get('attribution')=='independent-reproduction' else
            1 if row.get('attribution')=='author-reported' else 2,
            row['paperId'], row['id']))
        anchor = ordered[0]
        for row in ordered[1:]:
            if row['displayTier'] != 'primary':
                continue
            if row['paperId'] == anchor['paperId'] or row.get('attribution')=='reported-baseline':
                row['displayTier'] = 'reference'
                row['repeatedOf'] = anchor['id']
    primary = sum(row['displayTier']=='primary' and row.get('evidence')=='checked'
                  for row in projected_results)
    meta = {
      'schemaVersion':1,
      'benchmarks':registry['benchmarks'],
      'legacySettingTracks':registry['legacySettingTracks'],
      'primaryResultCount':primary,
      'archivedResultCount':sum(row.get('evidence')=='checked' and row['displayTier']!='primary'
                                for row in projected_results),
    }
    return projected_tracks, projected_results, meta
