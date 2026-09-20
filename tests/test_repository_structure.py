from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_repository_layers_are_explicit():
    assert (ROOT/'site/index.html').is_file()
    assert (ROOT/'site/js/core').is_dir()
    assert (ROOT/'site/js/features').is_dir()
    assert (ROOT/'site/styles/features').is_dir()
    assert (ROOT/'scripts/build').is_dir()
    assert (ROOT/'scripts/validate').is_dir()
    assert (ROOT/'scripts/browser').is_dir()
    assert (ROOT/'scripts/maintenance').is_dir()
    assert (ROOT/'scripts/discovery').is_dir()
    assert (ROOT/'scripts/migrations').is_dir()
    assert (ROOT/'maintenance/policies').is_dir()
    assert (ROOT/'maintenance/state').is_dir()
    assert (ROOT/'maintenance/audits').is_dir()
    assert (ROOT/'maintenance/docs').is_dir()

def test_root_is_not_a_frontend_source_dump():
    forbidden=['index.html','app.js','styles.css','research.js','research.css','experience.js','experience.css','news.js','news.css','tools.js','tools.css','sidebar.js','sidebar.css','runtime.js','dates.js','search-core.js','search-client.js','search-worker.js','validate.py']
    assert not [name for name in forbidden if (ROOT/name).exists()]

def test_operational_directories_are_not_flat_dumps():
    assert not list((ROOT/'scripts').glob('*.py'))
    assert not list((ROOT/'scripts').glob('*.cjs'))
    top_files={p.name for p in (ROOT/'maintenance').iterdir() if p.is_file()}
    assert top_files=={'README.md'}
