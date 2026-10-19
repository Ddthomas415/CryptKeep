import json
from pathlib import Path

import pytest

from scripts.research import run_cmc_bounded_workflow as workflow
from scripts.research import cmc_snapshot_inventory as inventory
from tests.test_cmc_bounded_adapter import sources, NOW


@pytest.fixture
def sealed(sources):
    root = Path(sources[0]['file']).parent
    snapshots = root/'snapshots'
    snapshots.mkdir()
    for source in sources:
        path = Path(source['file'])
        path.rename(snapshots/path.name)
    seal = root/'seal.json'
    seal.write_text(json.dumps(inventory.seal(snapshots, now_ms=NOW)))
    return seal, inventory.digest(seal)


def test_complete_real_stack(sealed):
    result = workflow.run(*sealed, now_ms=NOW, evaluate=True)
    assert result['market_outcomes_evaluated'] is True
    assert result['result']['eligible_events'] == 1
    assert result['result']['clipped_events'] == 1
    assert result['scoring_authorized'] is False
    assert result['qualification_verified'] is False


def test_readiness_never_reads_outcomes(sealed, monkeypatch):
    monkeypatch.setattr(workflow.adapter, 'build', lambda *a, **k: pytest.fail('outcome access'))
    assert workflow.run(*sealed, now_ms=NOW)['market_outcomes_evaluated'] is False


def test_early_evaluation_and_bad_anchor_refuse(sealed, monkeypatch):
    monkeypatch.setattr(workflow, 'verified_manifest', lambda *a, **k: [])
    monkeypatch.setattr(workflow.adapter, 'build', lambda *a, **k: pytest.fail('outcome access'))
    with pytest.raises(ValueError, match='not mature'):
        workflow.run(*sealed, now_ms=0, evaluate=True)
    with pytest.raises(ValueError, match='anchor'):
        workflow.run(sealed[0], 'b'*64, now_ms=NOW)


def test_postseal_additions_and_modified_sources_refuse(sealed):
    seal, sha = sealed
    saved = json.loads(seal.read_bytes())
    root = Path(saved['directory'])
    path = root/'0.json'
    path.write_text('{}')
    with pytest.raises(ValueError):
        workflow.run(seal, sha, now_ms=NOW, evaluate=True)


def test_cli_no_overwrite(sealed, monkeypatch, tmp_path):
    seal, sha = sealed
    out = tmp_path/'report.json'
    monkeypatch.setattr('sys.argv', ['workflow', '--seal', str(seal), '--seal-sha256', sha,
                                   '--evaluate', '--output', str(out)])
    monkeypatch.setattr(workflow.time, 'time', lambda: NOW/1000)
    assert workflow.main() == 0
    before = out.read_bytes()
    assert workflow.main() == 2
    assert out.read_bytes() == before
