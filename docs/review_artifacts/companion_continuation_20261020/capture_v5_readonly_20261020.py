"""Dated, read-only capture recipe; creates public evidence, never an approval."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import time
import uuid

from scripts.research import collect_companion_recreation_metadata as capture
from scripts.research import companion_existing_controller as core
from scripts.research import companion_installer as install
from scripts.research import companion_install_docker as native
from scripts.research import companion_network_configuration as network
from scripts.research import companion_runtime_adapter as adapter

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'docs/review_artifacts/companion_install_candidate_20261018/configured_v3/reviewed_configured_plan.json'
SOURCE_HASH = 'f5b044858c3d40881239b77745d0b404c4ac05d2f35a6d043fed8f6ba934bf5f'
OUTPUT = Path(__file__).resolve().parent / 'fresh_v5_capture_20261020'


def main():
    source_raw = SOURCE.read_bytes()
    if hashlib.sha256(source_raw).hexdigest() != SOURCE_HASH:
        raise ValueError('recipe_changed_no_commands_run')
    if hashlib.sha256(capture.CLI.read_bytes()).hexdigest() != capture.CLI_SHA256:
        raise ValueError('cli_changed_no_commands_run')
    source = json.loads(source_raw)
    OUTPUT.mkdir(exist_ok=False)
    report = {'schema': 'companion-running-preparation-capture-v1', 'state': 'INCOMPLETE',
        'observed_utc': datetime.now(timezone.utc).isoformat(), 'commands': [],
        'source_recipe_sha256': SOURCE_HASH, 'cli_sha256': capture.CLI_SHA256,
        'operations_authorized': False, 'credentials_exported': False}
    deadline = time.monotonic() + 60
    with tempfile.TemporaryDirectory(prefix='cki-v5-capture-') as config:
        def read(args, label):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ValueError('capture_deadline')
            report['commands'].append(label)
            return capture.readonly_run((str(capture.CLI), '--config', config, '--host', capture.ENDPOINT, *args),
                timeout=min(10, remaining), input_bytes=None, limit=1_048_576, env={'PATH': '/usr/bin:/bin'})

        try:
            report['engine'] = json.loads(read(('version', '--format', native.ENGINE_FORMAT), 'public engine version/commit'))
            report['engine_matches_existing_pin'] = report['engine'] == native.REVIEWED_ENGINE
            entries = read(('container', 'ls', '--all', '--no-trunc', '--format', '{{.ID}} {{.Names}}'),
                           'container identities/names only').decode('ascii').splitlines()
            inventory = dict(line.split(maxsplit=1)[::-1] for line in entries)
            if (len(inventory) != len(entries) or not 1 <= len(inventory) <= 128
                    or any(not install.ID.fullmatch(identity) for identity in inventory.values())
                    or not set(core.TARGETS).issubset(inventory)):
                raise ValueError('inventory_shape')
            report['inventory'] = inventory
            identities = [inventory[name] for name in core.TARGETS]
            # The existing formatter returns booleans for secret presence and
            # unknown command recognition. No raw environment/labels are exported.
            fmt = capture.capture_format()
            def inspect():
                raw = read(('container', 'inspect', '--format', fmt, *identities), 'sanitized seven-target metadata')
                rows = [json.loads(line) for line in raw.splitlines()]
                if (len(rows) != 7 or [row.get('id') for row in rows] != identities
                        or [row.get('name', '').removeprefix('/') for row in rows] != list(core.TARGETS)):
                    raise ValueError('selected_identity_mismatch')
                return rows
            rows = inspect()
            report['observations'] = rows
            if any('flags' not in row for row in rows):
                raise ValueError('unrecognized_startup_metadata')
            label_format = '{"id":{{json .Id}},"has_attempt":{{not (not (index .Config.Labels "cryptkeep.install-attempt"))}}}'
            raw = read(('container', 'inspect', '--format', label_format, *identities), 'attempt label presence only')
            labels = [json.loads(line) for line in raw.splitlines()]
            report['attempt_labels_absent'] = ([row.get('id') for row in labels] == identities
                and all(row.get('has_attempt') is False for row in labels))
            if not report['attempt_labels_absent']:
                raise ValueError('original_attempt_label_present_or_unknown')
            network_ids = sorted({value['NetworkID'] for row in rows for value in row['networks'].values()})
            if not 1 <= len(network_ids) <= 7 or any(not install.ID.fullmatch(value) for value in network_ids):
                raise ValueError('original_network_identity')
            raw = read(('network', 'inspect', '--format', native.NETWORK_FORMAT, *network_ids), 'network names/IDs only')
            records = [json.loads(line) for line in raw.splitlines()]
            bindings = {row['name']: row['id'] for row in records}
            network.validate_bindings(bindings)
            if len(records) != len(bindings) or sorted(bindings.values()) != network_ids:
                raise ValueError('network_binding_mismatch')
            report['network_bindings'] = bindings
            snapshots = []
            for row in rows:
                configured, configured_ids, evidence = network.project(row, bindings)
                snapshots.append(asdict(install.Snapshot(row['name'].removeprefix('/'), row['id'], row['image'],
                    row['state'], row['started'], row['restarts'], row['restart_policy'], adapter.preservation_digest(row),
                    adapter.preservation_digest({**row, 'networks': {}}),
                    tuple(sorted(value['NetworkID'] for value in row['networks'].values())),
                    configured_metadata=configured, configured_networks=configured_ids, network_evidence=evidence)))
            report['snapshots'] = snapshots
            report['final_observations_match'] = inspect() == rows
            report['running_originals'] = all(row['state'] == 'running' and row['restart_policy'] == 'no' for row in rows)
            report['source_checks'] = []
            for app in source['applications']:
                mismatches = [entry['local'] for entry in app['sources']
                    if hashlib.sha256((ROOT / entry['local']).read_bytes()).hexdigest() != entry['sha256']]
                report['source_checks'].append({'name': app['name'], 'entries': len(app['sources']), 'mismatches': mismatches})
            report['recipe_identity_matches'] = all(inventory[row['name']] == row['id'] for row in source['baseline'])
            report['effective_flags'] = {row['name'].removeprefix('/'): adapter.PinnedRuntimeAdapter._flags(row) for row in rows}
            draft = {**source, 'schema': 'companion-staged-update-v5', 'decision': 'INCOMPLETE', 'reviewer': '',
                'attempt': uuid.uuid4().hex, 'cli_sha256': capture.CLI_SHA256, 'baseline': snapshots,
                'network_contract': {'schema': network.CONTRACT, 'bindings': bindings, 'connectivity_verified': False}}
            # Existing recipe hashes are carried forward, not newly certified.
            # An INCOMPLETE draft cannot pass Plan.load or authorize operations.
            raw = install.canonical(draft)
            (OUTPUT / 'candidate_manifest.json').write_bytes(raw)
            report['candidate_sha256'] = hashlib.sha256(raw).hexdigest()
            report['replacement_expectations'] = 'Carried forward from recipe; actual replacement metadata UNVERIFIED'
            report['state'] = 'READY_FOR_INDEPENDENT_REVIEW' if (
                report['final_observations_match'] and report['running_originals'] and report['engine_matches_existing_pin']
                and not any(row['mismatches'] for row in report['source_checks'])) else 'INCOMPLETE'
        except Exception as error:
            report['failure_category'] = type(error).__name__
            if isinstance(error, capture.CaptureFailure):
                report['sanitized_detail'] = error.category
    (OUTPUT / 'capture.json').write_bytes(install.canonical(report))
    print(json.dumps({key: report.get(key) for key in ('state', 'engine', 'engine_matches_existing_pin',
        'running_originals', 'final_observations_match', 'candidate_sha256', 'failure_category', 'sanitized_detail')}))


if __name__ == '__main__':
    main()
