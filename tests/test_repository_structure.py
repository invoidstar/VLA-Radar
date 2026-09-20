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

def test_current_automation_uses_structured_site_paths():
    batch=(ROOT/'.github/workflows/content-batch.yml').read_text()
    assert 'site/js/features/research/research.js' in batch
    assert 'site/styles/features/research.css' in batch
    assert ' CHANGELOG.md research.js research.css ' not in batch
    upgrader=(ROOT/'scripts/migrations/upgrade_batch_ui.py').read_text()
    assert "R/'site/js/features/research/research.js'" in upgrader
    assert "R/'site/styles/features/research.css'" in upgrader
    assert "R/'research.js'" not in upgrader
    assert "R/'research.css'" not in upgrader


def test_public_asset_urls_are_stable():
    from scripts.build.stage_site import PUBLIC_FILES
    expected={
        'index.html','favicon.svg','styles.css','sidebar.css','research.css','experience.css','news.css','tools.css',
        'app.js','research.js','benchmark-settings.js','dates.js','runtime.js','search-core.js','search-client.js','search-worker.js',
        'sidebar.js','experience-loader.js','experience-core.js','experience.js','news-core.js','news.js',
        'tools-loader.js','tools-core.js','tools.js'
    }
    assert set(PUBLIC_FILES.values())==expected
    index=(ROOT/'site/index.html').read_text()
    for name in ['styles.css','sidebar.css','research.css','experience.css','app.js','research.js','benchmark-settings.js','runtime.js','search-client.js','experience-loader.js','tools-loader.js']:
        assert name in index
    assert 'src="js/' not in index
    assert 'href="styles/' not in index
