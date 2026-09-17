"""Validate public source records and deterministic exports, not scientific truth."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'scripts'))
from catalog_core import read_catalog
from build_catalog import build
if __name__=='__main__':
    try:
        root=Path(__file__).parent
        m,records,tracks,results=read_catalog(root);build(root,check=True)
        print(f'PASS: {len(records)} papers, {len(tracks)} protocol tracks, {len(results)} source-located results.')
        print('Schema checks do not certify publication status, research facts, links or exhaustive coverage.')
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print('FAIL:',exc,file=sys.stderr);sys.exit(1)
