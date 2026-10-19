import json

import pytest

from scripts.research import cmc_snapshot_inventory as inventory


def snapshot(path, *, schema=3):
    path.write_text(json.dumps({'schema_version': schema, 'artifact_type': 'research_only_forward_log_v3',
                               'places_orders': False, 'snapshot_utc': '2026-10-10T00:00:00Z',
                               'trending_hidden_boost': [], 'tracked_coinbase': [], 'majors_coinbase': {}}))


@pytest.fixture
def setup(tmp_path):
    root = tmp_path / 'snapshots'
    root.mkdir()
    snapshot(root / 'one.json')
    saved = tmp_path / 'seal.json'
    saved.write_text(json.dumps(inventory.seal(root, now_ms=1800000000000)))
    return root, saved


def test_selection_bound_to_all_sealed_sources(setup):
    root, saved = setup
    assert inventory.verified_manifest(saved, now_ms=1800000000000) == [
        {'file': str(root/'one.json'), 'sha256': inventory.digest(root/'one.json')}]
    chained = inventory.seal(root, now_ms=1800000000001, previous=saved)
    assert chained['parent_sha256'] == inventory.digest(saved)
    assert chained['past_completeness_before_baseline'] == 'UNVERIFIED'


def test_changed_or_removed_files_refuse(setup):
    root, saved = setup
    (root/'one.json').write_text('{}')
    with pytest.raises(ValueError, match='changed'):
        inventory.seal(root, now_ms=1800000000000, previous=saved)
    (root/'one.json').unlink()
    snapshot(root/'other.json')
    with pytest.raises(ValueError, match='missing'):
        inventory.seal(root, now_ms=1800000000000, previous=saved)


def test_addition_requires_new_seal_and_not_subset(setup):
    root, saved = setup
    snapshot(root/'two.json')
    with pytest.raises(ValueError, match='new published'):
        inventory.verified_manifest(saved, now_ms=1800000000000)
    assert len(inventory.seal(root, now_ms=1800000000000, previous=saved)['files']) == 2


def test_new_legacy_refuses_and_hidden_pending_ignored(setup):
    root, saved = setup
    (root/'.pending.json').write_text('unfinished')
    assert len(inventory.verified_manifest(saved, now_ms=1800000000000)) == 1
    snapshot(root/'legacy.json', schema=1)
    with pytest.raises(ValueError, match='legacy'):
        inventory.seal(root, now_ms=1800000000000, previous=saved)


def test_symlink_and_future_refuse(setup):
    root, saved = setup
    (root/'alias.json').symlink_to(root/'one.json')
    with pytest.raises(ValueError, match='non-symlink'):
        inventory.seal(root, now_ms=1800000000000)
    (root/'alias.json').unlink()
    with pytest.raises(ValueError, match='future'):
        inventory.seal(root, now_ms=0)


@pytest.mark.parametrize('nested', [False, True])
def test_cli_rejects_all_descendant_outputs(setup, monkeypatch, nested):
    root, _ = setup
    parent = root/'receipts' if nested else root
    parent.mkdir(exist_ok=True)
    output = parent/'seal.json'
    monkeypatch.setattr('sys.argv', ['inventory', '--snapshots', str(root), '--output', str(output)])
    assert inventory.main() == 2
    assert not output.exists()
