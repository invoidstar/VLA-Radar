"""Execute current top-level function-style regressions with no third-party test runner.

unittest discovery remains responsible for unittest.TestCase suites. This runner closes
the gap for plain test_* functions that previously looked like tests but were skipped.
"""
from __future__ import annotations
import importlib.util, inspect, sys, traceback
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TEST_ROOT=ROOT/'tests'
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

count=0
failures=[]
for path in sorted(TEST_ROOT.glob('test_*.py')):
    name='radar_'+path.stem
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    for test_name,obj in sorted(vars(module).items()):
        if not test_name.startswith('test_') or not inspect.isfunction(obj) or obj.__module__!=name:
            continue
        required=[p for p in inspect.signature(obj).parameters.values() if p.default is inspect._empty and p.kind in (p.POSITIONAL_ONLY,p.POSITIONAL_OR_KEYWORD,p.KEYWORD_ONLY)]
        if required:
            continue
        count+=1
        try:
            obj()
            print(f'PASS {path.name}::{test_name}')
        except Exception as exc:
            failures.append((path.name,test_name,exc,traceback.format_exc()))
            print(f'FAIL {path.name}::{test_name}: {exc}',file=sys.stderr)

if failures:
    for path,name,exc,tb in failures:
        print(f'\n--- {path}::{name} ---\n{tb}',file=sys.stderr)
    raise SystemExit(f'{len(failures)} / {count} function-style tests failed')
print(f'PASS: {count} function-style Python regression tests completed.')
