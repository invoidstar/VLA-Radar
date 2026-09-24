import json
from pathlib import Path

R=Path(__file__).resolve().parents[1]
NEW={'p111','p112','p113','p114','p115','p116'}

def j(path):
    return json.loads((R/path).read_text())

def test_robot_series_inventory_and_depth():
    manifest=j('catalog/manifest.json')
    assert NEW <= set(manifest['paperOrder'])
    assert len(manifest['paperOrder']) >= 116
    for pid in NEW:
        p=j(f'catalog/papers/{pid}.json')
        assert p['note']['status']=='expanded'
        assert p['note']['coverage']['level']=='deep'
        assert p['note']['verifiedAt']=='2026-09-25'
        assert len(p['note']['sections']) >= 8
        assert sum(len(s['body']) for s in p['note']['sections']) >= 2000
        assert all(s['sources'] for s in p['note']['sections'])

def test_robot_series_benchmark_dispositions():
    review=j('maintenance/state/benchmark-review.json')['papers']
    assert all(review[pid]['status']=='extracted' for pid in ['p111','p112','p113','p114'])
    assert all(review[pid]['status']=='deferred' for pid in ['p115','p116'])
    assert all(not review[pid]['trackIds'] and not review[pid]['resultIds'] for pid in ['p115','p116'])
    result_ids={p.stem for p in (R/'catalog/results').glob('r-*.json')}
    for pid in ['p111','p112','p113','p114']:
        assert review[pid]['resultIds']
        assert set(review[pid]['resultIds']) <= result_ids

def test_robot_series_resources_and_queue():
    resources=j('catalog/resources.json')['papers']
    assert resources['p004']['project']=='https://robotics.xiaomi.com/xiaomi-robotics-1.html'
    assert resources['p111']['code']=='https://github.com/RLinf/LaWAM'
    assert resources['p112']['code']=='https://github.com/XiaomiRobotics/Xiaomi-Robotics-0'
    assert resources['p113']['code']=='https://github.com/QwenLM/Qwen-VLA'
    assert resources['p114']['code']=='https://github.com/QwenLM/Qwen-RobotManip'
    assert resources['p115']['code']=='https://github.com/QwenLM/Qwen-RobotNav'
    assert resources['p116']=={'project':'https://qwen.ai/blog?id=qwen-robotworld'}
    queue=j('maintenance/state/work-queue.json')
    assert queue['remainingNotes']==0 and queue['notes']==[]
