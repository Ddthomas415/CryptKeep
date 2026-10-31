"""Public saved inputs and synthetic policy records, never native approvals."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import socket
import subprocess
from types import SimpleNamespace

import pytest

from scripts.research import companion_cutover as entry
from scripts.research import companion_installer as install
from scripts.research import companion_runtime_adapter as adapter
from tests.test_companion_runtime_adapter import FakeDocker, make_pins, seal_fixture_reviews

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/review_artifacts/companion_continuation_20261021'
OLD = ROOT / 'docs/review_artifacts/companion_continuation_20261020'


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('input validation attempted native/network access')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket.socket, 'connect_ex', forbidden)
    monkeypatch.setattr(socket, 'getaddrinfo', forbidden)


def write_pins(state, pins):
    args = state.args
    args.runtime_review.write_bytes(pins.review_manifest)
    args.reviewed_runtime_review_sha256 = pins.review_record_sha256
    args.topical_approvals.write_bytes(adapter._canonical(pins.topical_approvals))
    args.dependency_review = []
    for index, raw in enumerate(pins.dependency_review_records):
        path = state.directory / f'dependency-{index}.json'
        path.write_bytes(raw)
        args.dependency_review.append(path)


@pytest.fixture
def inputs(tmp_path):
    manifest = BASE / 'preparation_reconciled_manifest.json'
    manifest_raw = manifest.read_bytes()
    trusted = hashlib.sha256(manifest_raw).hexdigest()
    plan = install.Plan.load(manifest_raw, trusted)
    metadata = json.loads((BASE / 'staged_metadata_diagnostic.json').read_bytes())
    original = json.loads((OLD / 'fresh_v5_capture_20261020/capture.json').read_bytes())
    docker = FakeDocker()
    docker.rows = {row['name'].removeprefix('/'): deepcopy(row) for row in original['observations'][:3]}
    for app, saved in zip(plan.applications, metadata['rows']):
        row = deepcopy(saved)
        row['name'] = '/' + app['name']
        for net in row['networks'].values():
            net['Aliases'] = app['network_options'][1::2]
        docker.rows[app['name']] = row
    synthetic = make_pins(docker)
    targets = []
    for pin in synthetic.targets:
        sources = dict(pin.source_sha256)
        app = next((a for a in plan.applications if a['name'] == pin.name), None)
        if app:
            sources.update({s['destination']: s['sha256'] for s in app['sources']})
        targets.append(replace(pin, source_sha256=tuple(sorted(sources.items()))))
    synthetic = seal_fixture_reviews(replace(synthetic, targets=tuple(targets)))
    args = SimpleNamespace(manifest=manifest, reviewed_manifest_sha256=trusted,
        preparation_evidence=BASE / 'preparation_reconciled_evidence.json',
        preparation_review=BASE / 'preparation_reconciled_id_review.json',
        reviewed_preparation_review_sha256='80532a1e65c447cc9e9e5fcdbeb63fc1ae321f3842ba0dd714867fb67bcce514',
        staged_metadata=tmp_path / 'metadata.json', runtime_review=tmp_path / 'runtime.json',
        topical_approvals=tmp_path / 'topical.json')
    args.staged_metadata.write_bytes(install.canonical(metadata))
    state = SimpleNamespace(args=args, plan=plan, pins=synthetic, directory=tmp_path, metadata=metadata)
    write_pins(state, synthetic)
    return state


def test_loader_cross_binds_existing_records_without_operations(inputs):
    plan, prepared, pins = entry.load_inputs(inputs.args)
    assert plan == inputs.plan and len(prepared.replacements) == 4
    assert pins == inputs.pins


@pytest.mark.parametrize('key', ['reviewed_manifest_sha256', 'reviewed_preparation_review_sha256',
                                'reviewed_runtime_review_sha256'])
def test_wrong_external_hash_refused(inputs, key):
    setattr(inputs.args, key, '0' * 64)
    with pytest.raises(install.core.Refused):
        entry.load_inputs(inputs.args)


@pytest.mark.parametrize('change', ['id', 'image', 'metadata', 'application_source', 'storage_metadata'])
def test_self_consistent_synthetic_approval_cannot_override_prepared_contract(inputs, change):
    pins = inputs.pins
    index = 0 if change == 'storage_metadata' else 3
    pin = pins.targets[index]
    if change == 'id':
        pin = replace(pin, container_id='f' * 64)
    elif change == 'image':
        pin = replace(pin, image_id='sha256:' + 'f' * 64)
    elif change in {'metadata', 'storage_metadata'}:
        pin = replace(pin, preservation_sha256='f' * 64)
    else:
        sources = dict(pin.source_sha256)
        sources[next(iter(sources))] = 'f' * 64
        pin = replace(pin, source_sha256=tuple(sorted(sources.items())))
    changed = replace(pins, targets=pins.targets[:index] + (pin,) + pins.targets[index + 1:])
    write_pins(inputs, seal_fixture_reviews(changed))
    with pytest.raises(install.core.Refused):
        entry.load_inputs(inputs.args)


@pytest.mark.parametrize('change', ['id', 'started', 'dns', 'flag', 'extra_row', 'reorder'])
def test_saved_metadata_must_reproduce_exact_reviewed_snapshots(inputs, change):
    metadata = deepcopy(inputs.metadata)
    row = metadata['rows'][0]
    if change == 'id':
        row['id'] = 'f' * 64
    elif change == 'started':
        row['started'] = '2026-10-21T00:00:00Z'
    elif change == 'dns':
        row['dns'] = ['203.0.113.1']
    elif change == 'flag':
        row['flags'] = []
    elif change == 'extra_row':
        metadata['rows'].append(deepcopy(row))
    else:
        metadata['rows'].reverse()
    inputs.args.staged_metadata.write_bytes(install.canonical(metadata))
    with pytest.raises(install.core.Refused):
        entry.load_inputs(inputs.args)


@pytest.mark.parametrize('change', ['topical', 'dependency', 'missing_sdk', 'missing_policy', 'unsafe_path'])
def test_incomplete_or_unbound_reviews_are_not_runtime_proof(inputs, change):
    if change == 'topical':
        inputs.args.topical_approvals.write_bytes(b'[]')
    elif change == 'dependency':
        inputs.args.dependency_review[0].write_bytes(b'{}')
    elif change == 'missing_policy':
        inputs.args.dependency_review = inputs.args.dependency_review[:-1]
    else:
        pins = inputs.pins
        pin = pins.targets[5]
        if change == 'missing_sdk':
            sources = tuple((p, h) for p, h in pin.source_sha256 if '/httpx/' not in p)
        else:
            sources = pin.source_sha256 + (('/etc/private_token', 'f' * 64),)
        pin = replace(pin, source_sha256=sources)
        write_pins(inputs, seal_fixture_reviews(replace(pins, targets=pins.targets[:5] + (pin,) + pins.targets[6:])))
    with pytest.raises(install.core.Refused):
        entry.load_inputs(inputs.args)


def test_old_preparation_evidence_not_rebound_implicitly(inputs):
    inputs.args.preparation_evidence = BASE / 'prepared_evidence_public_copy.json'
    with pytest.raises(install.core.Refused):
        entry.load_inputs(inputs.args)
