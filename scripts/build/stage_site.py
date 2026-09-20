from __future__ import annotations
import argparse, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def stage(output:Path)->Path:
    output=output if output.is_absolute() else ROOT/output
    source=ROOT/'site'
    if output.resolve() in {source.resolve(),(ROOT/'data').resolve()}:raise ValueError('refusing destructive output path')
    if output.exists():shutil.rmtree(output)
    shutil.copytree(source,output)
    shutil.copytree(ROOT/'data',output/'data')
    (output/'.nojekyll').touch()
    return output

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=Path('_site'));a=ap.parse_args()
    print(stage(a.output))
