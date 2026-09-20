from __future__ import annotations
import argparse, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PUBLIC_FILES={
    'site/index.html':'index.html',
    'site/favicon.svg':'favicon.svg',
    'site/styles/base.css':'styles.css',
    'site/styles/components/sidebar.css':'sidebar.css',
    'site/styles/features/research.css':'research.css',
    'site/styles/features/experience.css':'experience.css',
    'site/styles/features/news.css':'news.css',
    'site/styles/features/tools.css':'tools.css',
    'site/js/features/library/app.js':'app.js',
    'site/js/features/research/research.js':'research.js',
    'site/js/features/research/benchmark-settings.js':'benchmark-settings.js',
    'site/js/core/dates.js':'dates.js',
    'site/js/core/runtime.js':'runtime.js',
    'site/js/core/search-core.js':'search-core.js',
    'site/js/core/search-client.js':'search-client.js',
    'site/js/core/search-worker.js':'search-worker.js',
    'site/js/components/sidebar.js':'sidebar.js',
    'site/js/features/experience/experience-loader.js':'experience-loader.js',
    'site/js/features/experience/experience-core.js':'experience-core.js',
    'site/js/features/experience/experience.js':'experience.js',
    'site/js/features/news/news-core.js':'news-core.js',
    'site/js/features/news/news.js':'news.js',
    'site/js/features/tools/tools-loader.js':'tools-loader.js',
    'site/js/features/tools/tools-core.js':'tools-core.js',
    'site/js/features/tools/tools.js':'tools.js',
}

def stage(output:Path)->Path:
    output=output if output.is_absolute() else ROOT/output
    source=ROOT/'site'
    if output.resolve() in {source.resolve(),(ROOT/'data').resolve()}:raise ValueError('refusing destructive output path')
    if output.exists():shutil.rmtree(output)
    output.mkdir(parents=True)
    for src,dst in PUBLIC_FILES.items():
        source_file=ROOT/src
        if not source_file.is_file():raise FileNotFoundError(source_file)
        shutil.copy2(source_file,output/dst)
    shutil.copytree(ROOT/'data',output/'data')
    (output/'.nojekyll').touch()
    return output

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=Path('_site'));a=ap.parse_args()
    print(stage(a.output))
