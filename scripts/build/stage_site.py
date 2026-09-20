from __future__ import annotations
import argparse, hashlib, re, shutil
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
    'site/js/core/math.js':'math.js',
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

LAZY_REFERENCES={
    'experience-loader.js':['experience-core.js','experience.js','news.css','news-core.js','news.js'],
    'tools-loader.js':['tools.css','tools-core.js','tools.js'],
}

def _digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]

def _stamp(text:str,name:str,digest:str)->str:
    pattern=re.compile(r'(?P<q>["\\\'])'+re.escape(name)+r'(?:\\?v=[^"\\\']*)?(?P=q)')
    return pattern.sub(lambda m:f'{m.group("q")}{name}?v={digest}{m.group("q")}',text)

def _stamp_lazy_assets(output:Path)->None:
    for loader,names in LAZY_REFERENCES.items():
        path=output/loader;text=path.read_text()
        for name in names:text=_stamp(text,name,_digest(output/name))
        path.write_text(text)

def _stamp_index_assets(output:Path)->None:
    path=output/'index.html';text=path.read_text()
    for name in sorted({dst for dst in PUBLIC_FILES.values() if dst.endswith(('.js','.css'))}):
        text=_stamp(text,name,_digest(output/name))
    path.write_text(text)

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
    _stamp_lazy_assets(output)
    _stamp_index_assets(output)
    (output/'.nojekyll').touch()
    return output

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=Path('_site'));a=ap.parse_args()
    print(stage(a.output))
