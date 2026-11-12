"""Read-only public-source reconciliation; no imports of application modules."""
import ast
from datetime import datetime, timezone
import hashlib
from functools import lru_cache
import json
from pathlib import Path, PurePosixPath
import sys
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = ROOT / 'docs/review_artifacts/group_a_release_candidate_20261104'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def archive(path, expected):
    if digest(path.read_bytes()) != expected:
        raise ValueError('archive_hash_changed')
    files = {}
    total = 0
    with tarfile.open(path, 'r:gz') as source:
        for member in source:
            name = PurePosixPath(member.name)
            total += member.size
            if (not member.isfile() or name.is_absolute() or '..' in name.parts
                    or member.name in files or member.size > 1048576
                    or len(files) >= 100 or total > 4194304):
                raise ValueError('unsafe_archive_member')
            files[member.name] = source.extractfile(member).read()
    return files


@lru_cache(maxsize=512)
def local(name):
    path = ROOT / name
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT) or not path.is_file():
        raise ValueError('unsafe_or_missing_local_source')
    if path.stat().st_size > 1048576:
        raise ValueError('oversized_local_source')
    return path.read_bytes()


def module_path(module):
    name = module.replace('.', '/')
    for candidate in (name + '.py', name + '/__init__.py'):
        if (ROOT / candidate).is_file():
            return candidate
    return None


def static_closure(roots):
    pending = list(roots)
    found = {}
    external = set()
    while pending:
        name = pending.pop()
        if name in found:
            continue
        if len(found) >= 200:
            raise ValueError('closure_budget')
        raw = local(name)
        found[name] = digest(raw)
        package = name.removesuffix('.py').replace('/', '.')
        package = package.removesuffix('.__init__') if name.endswith('/__init__.py') else package.rsplit('.', 1)[0]
        modules = set()
        for node in ast.walk(ast.parse(raw)):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ''
                if node.level:
                    parts = package.split('.')
                    prefix = parts[:len(parts)-node.level+1]
                    base = '.'.join(prefix + ([base] if base else []))
                if base:
                    modules.add(base)
                    modules.update(base + '.' + alias.name for alias in node.names if alias.name != '*')
        for module in sorted(modules):
            path = module_path(module)
            if path:
                pending.append(path)
                parts = module.split('.')
                for end in range(1, len(parts)):
                    init = '/'.join(parts[:end]) + '/__init__.py'
                    if (ROOT / init).is_file():
                        pending.append(init)
            elif module.split('.')[0] not in sys.stdlib_module_names | {'services', 'storage', 'scripts'}:
                external.add(module.split('.')[0])
    return dict(sorted(found.items())), sorted(external)


def base_sources(names, base):
    names = sorted(names)
    probe = subprocess.run(['/usr/bin/git', 'cat-file', '--batch'], cwd=ROOT,
        input=''.join(base+':'+name+'\n' for name in names).encode(),
        capture_output=True, timeout=10, check=True,
        env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'GIT_OPTIONAL_LOCKS': '0'})
    if len(probe.stdout) > 8388608:
        raise ValueError('base_source_budget')
    at = 0
    result = {}
    for name in names:
        end = probe.stdout.index(b'\n', at)
        header = probe.stdout[at:end]
        at = end+1
        if header.endswith(b' missing'):
            result[name] = {'present': False}
        else:
            _, kind, size = header.split()
            size = int(size)
            if kind != b'blob' or not 0 <= size <= 1048576:
                raise ValueError('unexpected_base_object')
            raw = probe.stdout[at:at+size]
            at += size+1
            result[name] = {'present': True, 'sha256': digest(raw),
                            'matches_current': raw == local(name)}
    if at != len(probe.stdout):
        raise ValueError('unexpected_batch_trailer')
    return result


def audit():
    overlay_sha = 'c9853e61189727721d84aee43277324a26c5a082a15ffea3a17a333395cb27e9'
    probe_sha = '9027d7ddcdca0b45c639c64156af15c32418cf221fdde890049a34434d84f95c'
    overlay = archive(ARTIFACTS / 'review-candidate-overlay.tar.gz', overlay_sha)
    manifest = dict((line.split(None, 1)[1].strip(), line.split(None, 1)[0])
                    for line in (ARTIFACTS / 'SHA256SUMS').read_text().splitlines())
    if set(manifest) != set(overlay) or any(digest(overlay[name]) != expected for name, expected in manifest.items()):
        raise ValueError('overlay_manifest_mismatch')
    probe = archive(ARTIFACTS / 'r3_native_probe_20261105/group_a_linux_probe.tar.gz', probe_sha)
    probe_manifest = json.loads(probe.pop('MANIFEST.json'))['files']
    if set(probe) != set(probe_manifest) or any(digest(raw) != probe_manifest[name]['sha256'] for name, raw in probe.items()):
        raise ValueError('probe_manifest_mismatch')
    rows = [{"path": name, "reviewed_sha256": expected, "current_sha256": digest(local(name)),
             "matches": expected == digest(local(name))} for name, expected in sorted(manifest.items())]
    closure, external = static_closure(('scripts/run_group_a_alert.py',
        'scripts/run_group_a_quote_publisher.py', 'services/control/group_a_account_units.py',
        'services/control/group_a_quote_routing.py',
        'services/logging/app_logger.py'))
    covered = set(overlay) | set(probe)
    base = base_sources(set(manifest) | set(probe) | set(closure),
                        '580ca31ea983af6452a1e02ab8d4b51645e9b43c')
    receipt_raw = (ARTIFACTS / 'r3_native_probe_20261105/instrumented_attempt_20261111T112512Z.json').read_bytes()
    receipt_sha = 'd6afffc54c319a767019b3654f5f00dae984638482003072131b45cee70901a6'
    if digest(receipt_raw) != receipt_sha:
        raise ValueError('host_receipt_changed')
    sample = json.loads(receipt_raw)['inventory_summary']
    host_matches = {name: (not base[name]['present'] if entry.get('status') == 'missing'
                          else base[name].get('sha256') == entry.get('sha256'))
                    for name, entry in sample['sources'].items()}
    return {'schema': 1, 'checked_utc': datetime.now(timezone.utc).isoformat(),
            'scope': 'local_reconciliation_only_not_a_release_manifest',
            'auditor_sha256': digest(Path(__file__).read_bytes()),
            'host_receipt_sha256': receipt_sha, 'host_sample_utc': sample['utc'],
            'remote_source_paths_match_base': host_matches,
            'base': '580ca31ea983af6452a1e02ab8d4b51645e9b43c',
            'overlay_sha256': overlay_sha, 'probe_sha256': probe_sha,
            'overlay_files': rows,
            'probe_files': [{'path': name, 'reviewed_sha256': digest(raw),
                             'current_sha256': digest(local(name)),
                             'matches': raw == local(name)} for name, raw in sorted(probe.items())],
            'static_runtime_roots': ['scripts/run_group_a_alert.py', 'scripts/run_group_a_quote_publisher.py',
                                    'services/control/group_a_account_units.py',
                                    'services/control/group_a_quote_routing.py', 'services/logging/app_logger.py'],
            'static_closure': closure, 'third_party_or_unresolved_roots': external,
            'base_sources': base,
            'static_paths_outside_both_archives': sorted(set(closure)-covered),
            'limits': 'AST discovery includes optional/function imports, not runtime proof or a dependency lock. No application code executed. No candidate built or deployed.'}


if __name__ == '__main__':
    print(json.dumps(audit(), sort_keys=True, indent=2))
