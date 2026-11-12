"""Exclusive local source composition; no application imports or host actions."""
import gzip
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = '580ca31ea983af6452a1e02ab8d4b51645e9b43c'
SNAPSHOT_SHA = '1c640df20b406dc873977802452ea39aee9da2be58d6e38a22f73c14389342cd'
AUDITOR_SHA = '79ebacfcd68bbb434bd860d47f92a95c894525e861dec97222f36d0d7a22200d'
FIXTURE_PATH = 'tests/test_paper_account_snapshot.py'
FIXTURE_BEFORE = '1da55171656bd3879473e7ac8209c73be480c312a5037139e16f3029bb4f07fe'
FIXTURE_AFTER = 'e8d2a9ad1b69ecae1427af6861abc1be84dc07808ac77dfbbddb8a0fd5842f90'
ENV = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'GIT_OPTIONAL_LOCKS': '0'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_name(name):
    path = PurePosixPath(name)
    return (not path.is_absolute() and '..' not in path.parts
            and all(not part.startswith('.env') and part not in {
                '.browser-access-token', '.browser-compose-override.json', '.cbp_state'} for part in path.parts)
            and name != 'config/user.yaml')


def base_tree():
    roots = {'services', 'storage', 'scripts', 'tests', 'core', 'config', 'sample_data',
             'tools', 'dashboard', 'utils', 'shared'}
    top = {'conftest.py', 'pyproject.toml', 'pytest.ini', 'requirements.txt', 'docs/DEPLOYMENT.md'}
    listing = subprocess.run(['/usr/bin/git', 'ls-tree', '-r', '-z', '--long', BASE],
        cwd=ROOT, env=ENV, capture_output=True, check=True, timeout=10).stdout
    chosen = []
    total = 0
    for line in listing.split(b'\0'):
        if not line:
            continue
        metadata, raw_name = line.split(b'\t', 1)
        name = raw_name.decode('utf8')
        parts = PurePosixPath(name).parts
        selected = parts[0] in roots or name in top or name.startswith('packaging/systemd/')
        if (not safe_name(name) or not selected
                or (parts[0] == 'config' and not name.endswith('.py'))):
            continue
        mode, kind, oid, size = metadata.split()
        if mode not in (b'100644', b'100755') or kind != b'blob' or int(size) > 1048576:
            raise ValueError('unsafe_base_blob')
        total += int(size)
        chosen.append((name, oid, int(size), int(mode, 8) & 0o777))
    if len(chosen) > 3000 or total > 16777216:
        raise ValueError('base_budget')
    raw = subprocess.run(['/usr/bin/git', 'cat-file', '--batch'], cwd=ROOT, env=ENV,
        input=b''.join(oid+b'\n' for _, oid, _, _ in chosen), capture_output=True,
        check=True, timeout=20).stdout
    at = 0
    files = {}
    for name, oid, size, mode in chosen:
        end = raw.index(b'\n', at)
        if raw[at:end] != oid+b' blob '+str(size).encode():
            raise ValueError('base_batch_header')
        at = end+1
        body = raw[at:at+size]
        at += size+1
        files[name] = (body, mode)
    if at != len(raw):
        raise ValueError('base_batch_trailer')
    return files


def build(destination, *, fixture_correction=False):
    snapshot_raw = (HERE/'source_reconciliation_20261111.json').read_bytes()
    auditor_path = HERE/'audit_release_sources_20261111.py'
    auditor_raw = auditor_path.read_bytes()
    if sha(snapshot_raw) != SNAPSHOT_SHA or sha(auditor_raw) != AUDITOR_SHA:
        raise ValueError('reviewed_input_drift')
    snapshot = json.loads(snapshot_raw)
    scope = {'__name__': 'reviewed_readonly_auditor', '__file__': str(auditor_path)}
    exec(compile(auditor_raw, str(auditor_path), 'exec'), scope)
    inputs = scope['ARTIFACTS']
    old = scope['archive'](inputs/'review-candidate-overlay.tar.gz', snapshot['overlay_sha256'])
    probe = scope['archive'](HERE/'group_a_linux_probe.tar.gz', snapshot['probe_sha256'])
    probe.pop('MANIFEST.json')
    expected = {row['path']: row['current_sha256'] for row in snapshot['overlay_files']}
    expected.update({row['path']: row['current_sha256'] for row in snapshot['probe_files']})
    expected.update(snapshot['static_closure'])
    if fixture_correction:
        if expected[FIXTURE_PATH] != FIXTURE_BEFORE:
            raise ValueError('fixture_baseline_changed')
        expected[FIXTURE_PATH] = FIXTURE_AFTER
    current = {}
    for name, digest in expected.items():
        body = scope['local'](name)
        if sha(body) != digest:
            raise ValueError('selected_source_drift')
        current[name] = body

    delta = dict(old)
    origin = {name: 'reviewed_66_overlay' for name in delta}
    for row in snapshot['overlay_files']:
        if not row['matches']:
            delta[row['path']] = current[row['path']]
            origin[row['path']] = 'later_reviewed_R3_R5_replacement'
    if fixture_correction:
        delta[FIXTURE_PATH] = current[FIXTURE_PATH]
        origin[FIXTURE_PATH] = 'fixture_lifetime_correction_pending_independent_review'
    for name in probe:
        if name == 'scripts/research/verify_group_a_linux_processes.py':
            continue
        delta[name] = current[name]
        origin[name] = 'reviewed_R3_process_dependency'
    excluded = {'services/security/exchange_factory.py',
                'services/execution/coinbase_account_pages.py',
                'services/execution/coinbase_balance_observation.py'}
    for name in snapshot['static_closure']:
        if name in excluded:
            continue
        base = snapshot['base_sources'][name]
        if not base['present'] or not base.get('matches_current'):
            delta[name] = current[name]
            origin[name] = 'explicit_R2_R3_R5_runtime_wiring'

    tests = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/'tests').glob('test_group_a_*.py'))
    tests += ['tests/test_app_logger_component_rotation.py', 'tests/test_app_logger_redaction.py',
              'tests/test_systemd_units.py']
    tooling = ['scripts/research/build_group_a_linux_probe_packet.py',
               'scripts/research/verify_group_a_linux_processes.py']
    for name in tests+tooling:
        delta[name] = scope['local'](name)
        origin[name] = 'regression_test' if name.startswith('tests/') else 'native_review_tool_not_runtime'
    saved = json.loads(old['docs/review_artifacts/paper_simulation_r6r9_20261103/baseline_hashes.json'])
    for source_name, expected_hash in saved.items():
        name = 'docs/review_artifacts/paper_simulation_r6r9_20261103/' + source_name.replace('/', '__') + '.before'
        body = scope['local'](name)
        if sha(body) != expected_hash:
            raise ValueError('before_fixture_hash_mismatch')
        delta[name] = body
        origin[name] = 'hash_pinned_review_fixture_not_runtime'
    before = 'docs/review_artifacts/group_a_composed_20261111/r5_before_runner.py'
    delta[before] = old['services/execution/strategy_runner.py']
    origin[before] = 'review_fixture_not_runtime'
    if len(delta) > 180 or any(not safe_name(name) for name in delta):
        raise ValueError('delta_scope_invalid')

    base = base_tree()
    factory = 'services/security/exchange_factory.py'
    if sha(base[factory][0]) != snapshot['base_sources'][factory]['sha256'] or factory in delta:
        raise ValueError('base_factory_not_preserved')
    destination = Path(destination)
    destination.mkdir()  # Exclusive: never overwrite an earlier candidate.
    scratch = Path(tempfile.mkdtemp(prefix='cryptkeep-composed-20261111-', dir='/private/tmp'))
    tree = scratch/'tree'
    tree.mkdir()
    for name, (body, mode) in base.items():
        path = tree/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        path.chmod(mode)
    for name, body in delta.items():
        path = tree/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        path.chmod(0o644)
    manifest = {'schema': 1, 'status': 'READY_FOR_INDEPENDENT_REVIEW',
        'scope': 'source_and_synthetic_tests_only_not_deployment', 'base': BASE,
        'builder_sha256': sha(Path(__file__).read_bytes()),
        'fixture_lifetime_correction': {'path': FIXTURE_PATH, 'before': FIXTURE_BEFORE,
            'after': FIXTURE_AFTER} if fixture_correction else None,
        'reconciliation_sha256': SNAPSHOT_SHA, 'scratch_tree': str(tree),
        'excluded_unrelated_current_files': sorted(excluded),
        'files': {name: {'sha256': sha(body), 'bytes': len(body), 'mode': '0644',
                         'origin': origin[name]} for name, body in sorted(delta.items())},
        'preserved_host_test': 'tests/test_daily_trend_exit_translation.py',
        'preserved_base_factory_sha256': sha(base[factory][0]),
        'r5_before_fixture': before,
        'test_files': sorted({name for name in delta if name.startswith('tests/') and name.endswith('.py')}
                             | {'tests/test_daily_trend_exit_translation.py', 'tests/test_research_preflight.py',
                                'tests/test_archive_parameter_sweep.py', 'tests/test_archive_walk_forward_runner.py',
                                'tests/test_backtest_walk_forward.py'}),
        'observed_test_dependencies_not_Linux_lock': {name: importlib.metadata.version(name)
            for name in ('pytest', 'PyYAML', 'ccxt', 'numpy')},
        'linux_dependency_lock': None}
    package = destination/'source-test-overlay.tar.gz'
    with package.open('xb') as output:
        with gzip.GzipFile(filename='', mode='wb', fileobj=output, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w', format=tarfile.USTAR_FORMAT) as tar:
                for name, body in sorted(delta.items()):
                    member = tarfile.TarInfo(name)
                    member.mode, member.mtime, member.size = 0o644, 0, len(body)
                    tar.addfile(member, io.BytesIO(body))
    manifest['archive_sha256'] = sha(package.read_bytes())
    (destination/'MANIFEST.json').write_text(json.dumps(manifest, sort_keys=True, indent=2)+'\n')
    tree_manifest = {name: {'sha256': sha((tree/name).read_bytes()),
                          'mode': oct(stat.S_IMODE((tree/name).stat().st_mode))}
                     for name in sorted(set(base)|set(delta))}
    (destination/'TREE_MANIFEST.json').write_text(json.dumps(tree_manifest, sort_keys=True, indent=2)+'\n')
    (destination/'BUILD.json').write_text(json.dumps({'status': 'READY_FOR_INDEPENDENT_REVIEW',
        'scratch_tree': str(tree), 'base_files': len(base), 'delta_files': len(delta),
        'source_files_total': len(tree_manifest), 'archive_sha256': manifest['archive_sha256'],
        'tests_run': False, 'host_actions': False}, sort_keys=True, indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] != '--fixture-lifetime-correction'):
        print('one_new_candidate_directory_required', file=sys.stderr)
        sys.exit(2)
    result = build(sys.argv[1], fixture_correction=len(sys.argv) == 3)
    print(json.dumps({'scratch_tree': result['scratch_tree'], 'files': len(result['files']),
                      'tests': len(result['test_files']), 'archive_sha256': result['archive_sha256']}))
