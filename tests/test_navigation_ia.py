from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INDEX=(ROOT/'site/index.html').read_text(encoding='utf-8')

def group(name):
    marker=f'data-nav-group="{name}"'
    start=INDEX.index(marker)
    next_positions=[INDEX.find(f'data-nav-group="{x}"',start+1) for x in ['discover','evidence','workspace','personal']]
    end=min([p for p in next_positions if p>start],default=INDEX.index('</nav>',start))
    return INDEX[start:end]

def test_sidebar_has_four_primary_information_areas_in_order():
    positions=[INDEX.index(f'data-nav-group="{name}"') for name in ['discover','evidence','workspace','personal']]
    assert positions==sorted(positions)
    assert INDEX.count('data-nav-group=')==4

def test_discover_contains_browsing_and_topic_shortcuts():
    text=group('discover')
    for view in ['papers','topics','timeline','news']:
        assert f'data-view="{view}"' in text
    assert 'id="side-topics"' in text
    assert '主题快捷筛选' in text

def test_evidence_contains_benchmark_and_coverage_only():
    text=group('evidence')
    assert 'data-view="leaderboards"' in text
    assert 'data-view="coverage"' in text
    assert 'data-view="compare"' not in text

def test_workspace_contains_compare_updates_and_export():
    text=group('workspace')
    assert 'data-view="compare"' in text
    assert 'data-view="updates"' in text
    assert 'data-workspace-export="true"' in text
    assert 'data-nav-action="export"' in text

def test_personal_contains_local_views():
    text=group('personal')
    assert 'data-view="radar"' in text
    assert 'data-view="reading"' in text
    assert text.count('本地')>=2

def test_about_and_github_live_in_sidebar_footer():
    footer=INDEX[INDEX.index('<div class="side-bottom">'):INDEX.index('</aside>')]
    assert 'data-view="about"' in footer
    assert 'https://github.com/invoidstar/VLA-Radar/tree/main' in footer
    assert 'side-external' in footer
    topbar=INDEX[INDEX.index('<header class="topbar">'):INDEX.index('</header>')]
    assert 'github-link' not in topbar
