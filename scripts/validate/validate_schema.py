"""Validate public source records and deterministic exports, not scientific truth."""
import sys as _sys
from pathlib import Path as _Path
_SCRIPT_ROOT=_Path(__file__).resolve().parents[1]
for _name in ('build','validate','browser','maintenance','discovery','migrations'):
    _candidate=str(_SCRIPT_ROOT/_name)
    if _candidate not in _sys.path:_sys.path.insert(0,_candidate)
import sys
from pathlib import Path
from catalog_core import read_catalog
from build_catalog import build
if __name__=='__main__':
    try:
        root=Path(__file__).resolve().parents[2]
        m,records,tracks,results=read_catalog(root);build(root,check=True)
        print(f'PASS: {len(records)} papers, {len(tracks)} protocol tracks, {len(results)} source-located results.')
        print('Schema checks do not certify publication status, research facts, links or exhaustive coverage.')
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print('FAIL:',exc,file=sys.stderr);sys.exit(1)
