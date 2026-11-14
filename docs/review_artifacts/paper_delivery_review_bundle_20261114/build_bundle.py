"""Exclusive offline review archive builder; never imports application code."""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MAX_FILE = 1048576
MAX_TOTAL = 33554432


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def name_ok(name):
    if not isinstance(name, str) or not name:
        return False
    p = PurePosixPath(name)
    return (str(p) == name and not p.is_absolute()
            and '..' not in p.parts and p.parts[0] in {'services', 'storage', 'scripts', 'tests', 'docs', 'config'}
            and not any(part.startswith('.env') or part in {
                '.cbp_state', '.venv', '__pycache__', '.git', '.browser-access-token',
                '.browser-compose-override.json'} for part in p.parts)
            and name != 'config/user.yaml'
            and not name.endswith(('.sqlite', '.sqlite-wal', '.sqlite-shm', '.db'))
            and 'group_a_backup' not in name)


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate_json_key')
        result[key] = value
    return result


def read_public(name, limit=MAX_FILE):
    if not name_ok(name):
        raise ValueError('unapproved_path')
    path = ROOT / name
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('symlink_input')
        if part == ROOT:
            break
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > limit:
            raise ValueError('unsafe_input')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    if (len(raw) > limit or (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
            != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)):
        raise ValueError('changing_input')
    return raw


def unpack(raw, *, expected_names=None):
    files = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as source:
        for member in source:
            if (not member.isfile() or not name_ok(member.name) or member.name in files
                    or member.mode != 0o644 or not 0 <= member.size <= MAX_FILE):
                raise ValueError('unsafe_archive_member')
            total += member.size
            if len(files) >= 500 or total > MAX_TOTAL:
                raise ValueError('archive_budget')
            body = source.extractfile(member).read(MAX_FILE + 1)
            if len(body) != member.size:
                raise ValueError('member_size_mismatch')
            files[member.name] = body
    if expected_names is not None and set(files) != set(expected_names):
        raise ValueError('archive_roster_mismatch')
    return files


def encode(files):
    raw = io.BytesIO()
    with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            for name, body in sorted(files.items()):
                info = tarfile.TarInfo(name)
                info.size, info.mode = len(body), 0o644
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ''
                archive.addfile(info, io.BytesIO(body))
    return raw.getvalue()


def encoded_json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def build(revision=None):
    output = HERE
    if revision is not None:
        if not re.fullmatch(r'[a-z0-9_-]{1,40}', revision):
            raise ValueError('invalid_revision_directory')
        output = HERE / revision
        output.mkdir()  # Preserve all earlier outputs; revisions are exclusive.
    # A fresh output file is mandatory. Partial failures are retained, never reset.
    for name in ('review-overlay.tar.gz', 'MANIFEST.json', 'VERIFICATION.json', 'SHA256SUMS'):
        if (output / name).exists() or (output / name).is_symlink():
            raise ValueError('existing_output_refused')
    recipe_name = str((HERE / 'RECIPE.json').relative_to(ROOT))
    recipe_raw = read_public(recipe_name)
    recipe = json.loads(recipe_raw, object_pairs_hook=pairs)
    previous = read_public(recipe['previous_archive'], MAX_TOTAL)
    old_manifest_raw = read_public(recipe['previous_manifest'])
    if (sha(previous) != recipe['previous_archive_sha256']
            or sha(old_manifest_raw) != recipe['previous_manifest_sha256']):
        raise ValueError('prior_artifact_drift')
    old_manifest = json.loads(old_manifest_raw, object_pairs_hook=pairs)
    files = unpack(previous, expected_names=old_manifest['files'])
    if len(files) != 126 or old_manifest['base'] != recipe['protected_base']:
        raise ValueError('prior_base_or_roster')
    provenance = {}
    for name, body in files.items():
        if sha(body) != old_manifest['files'][name]['sha256']:
            raise ValueError('prior_member_digest')
        provenance[name] = {'sha256': sha(body), 'bytes': len(body),
                            'origin': 'preserved_v3_overlay', 'role': old_manifest['files'][name]['origin']}
    input_hashes = {recipe_name: sha(recipe_raw), recipe['previous_archive']: sha(previous),
                    recipe['previous_manifest']: sha(old_manifest_raw)}
    replacements = []
    for name, binding in recipe['selected'].items():
        body = read_public(name)
        if sha(body) != binding['sha256']:
            raise ValueError('selected_input_drift')
        if name in files and body != files[name]:
            replacements.append({'path': name, 'previous_sha256': sha(files[name]), 'sha256': sha(body)})
        files[name] = body
        provenance[name] = {**binding, 'bytes': len(body), 'origin': 'explicit_pinned_current_selection'}
        input_hashes[name] = sha(body)
    for leaf in ('RECIPE.json', 'build_bundle.py', 'BUNDLE_SCOPE.md'):
        name = str((HERE / leaf).relative_to(ROOT))
        body = read_public(name)
        files[name] = body
        provenance[name] = {'sha256': sha(body), 'bytes': len(body),
                            'origin': 'packaging_recipe', 'role': 'review_tool_not_runtime'}
        input_hashes[name] = sha(body)
    expected_profiles = {f'docs/review_artifacts/paper_profile_candidate_20261114/profiles/{s}-{a}.yaml'
                         for s in ('breakout-default', 'ema-cross-default', 'mean-reversion-default')
                         for a in ('btc', 'eth', 'sol')}
    found_profiles = {n for n in files if '/profiles/' in n and n.endswith('.yaml')}
    if found_profiles != expected_profiles:
        raise ValueError('nine_profiles_required')
    if not set(recipe.get('required_fixture_paths', [])) <= files.keys():
        raise ValueError('required_fixture_missing')
    manifest = {'schema': 1, 'status': 'READY_FOR_INDEPENDENT_REVIEW',
        'scope': 'offline_review_overlay_only_not_installer', 'base': recipe['protected_base'],
        'previous_archive_sha256': sha(previous), 'recipe_sha256': sha(recipe_raw),
        'builder_sha256': sha(Path(__file__).read_bytes()),
        'runtime_dependency_closure_verified': False, 'deployment_status': 'INCOMPLETE',
        'runtime_configuration_checked': False, 'r10_status': 'STOPPED',
        'known_open': recipe['known_open'], 'historical_seal_supersessions': recipe['supersession_chain'],
        'v3_replacements': replacements, 'files': dict(sorted(provenance.items()))}
    manifest_raw = encoded_json(manifest)
    manifest_name = 'docs/review_artifacts/paper_delivery_review_bundle_20261114/BUNDLE_MANIFEST.json'
    files[manifest_name] = manifest_raw
    if len(files) > 500 or sum(map(len, files.values())) > MAX_TOTAL:
        raise ValueError('final_bundle_budget')
    payload = encode(files)
    if payload != encode(files):
        raise ValueError('nondeterministic_archive')
    verified = unpack(payload, expected_names=files)
    if verified != files:
        raise ValueError('roundtrip_mismatch')
    with tempfile.TemporaryDirectory(prefix='cryptkeep-review-extract-', dir='/private/tmp') as temp:
        destination = Path(temp)
        for name, body in verified.items():
            path = destination / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(body)
            if sha(path.read_bytes()) != sha(body):
                raise ValueError('extracted_digest_mismatch')
        compiled = 0
        for name, body in verified.items():
            if name.endswith('.py'):
                compile(body, name, 'exec', dont_inherit=True)
                compiled += 1
    for name, digest in input_hashes.items():
        if sha(read_public(name, MAX_TOTAL if name == recipe['previous_archive'] else MAX_FILE)) != digest:
            raise ValueError('input_changed_during_packaging')
    verification = {'scope': 'archive_integrity_only_not_runtime_tests', 'archive_sha256': sha(payload),
        'archive_bytes': len(payload), 'members': len(files), 'uncompressed_bytes': sum(map(len, files.values())),
        'python_members_compiled_not_executed': compiled, 'inactive_profiles': len(expected_profiles),
        'v3_members': 126, 'v3_replacements': len(replacements), 'deterministic_bytes_checked': True,
        'all_extracted_members_hash_checked': True, 'inputs_rechecked': len(input_hashes),
        'temporary_extraction_removed': True, 'runtime_or_strategy_test_executed': False}
    outputs = {'review-overlay.tar.gz': payload, 'MANIFEST.json': manifest_raw,
               'VERIFICATION.json': encoded_json(verification)}
    for name, body in outputs.items():
        with (output / name).open('xb') as stream:
            stream.write(body)
    with (output / 'SHA256SUMS').open('xb') as stream:
        stream.write(''.join(f'{sha(body)}  {name}\n' for name, body in outputs.items()).encode())
    print(json.dumps(verification, sort_keys=True))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', help='new child directory; existing revisions refuse')
    build(parser.parse_args().revision)
