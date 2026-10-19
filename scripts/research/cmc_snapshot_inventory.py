"""Content inventory for published CMC snapshots; not source authentication."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.research.cmc_snapshot_evidence import load_snapshot


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _scan(directory, now_ms):
    result = {}
    for path in sorted(directory.glob('*.json')):
        if path.name.startswith('.'):
            continue  # Unpublished reservations are not snapshot evidence.
        if path.is_symlink() or not path.is_file():
            raise ValueError('snapshot must be a regular non-symlink file')
        raw = path.read_bytes()
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError('invalid snapshot object')
        sha = hashlib.sha256(raw).hexdigest()
        if data.get('schema_version') == 3:
            envelope = load_snapshot(path)
            if envelope['sha256'] != sha:
                raise ValueError('snapshot changed during scan')
            if int(envelope['snapshot_utc'].timestamp()*1000) > now_ms:
                raise ValueError('future snapshot')
            classification = 'V3_STRUCTURAL_ENVELOPE'
        else:
            classification = 'LEGACY_BASELINE_ONLY_NOT_PRIMARY_INPUT'
        result[path.name] = {'sha256': sha, 'classification': classification}
    if not result:
        raise ValueError('no published snapshots')
    return result


def seal(directory, *, now_ms, previous=None):
    directory = Path(directory).resolve()
    if not directory.is_dir() or type(now_ms) is not int or now_ms < 0:
        raise ValueError('valid directory and time required')
    before = _scan(directory, now_ms)
    parent = None
    if previous is not None:
        previous = Path(previous)
        raw = previous.read_bytes()
        prior = json.loads(raw)
        if (prior.get('kind') != 'CMC_PUBLISHED_SNAPSHOT_INVENTORY'
                or prior.get('directory') != str(directory)
                or type(prior.get('sealed_at_ms')) is not int
                or prior['sealed_at_ms'] > now_ms
                or prior.get('scoring_authorized') is not False):
            raise ValueError('invalid prior seal')
        if not isinstance(prior.get('files'), dict) or not prior['files']:
            raise ValueError('prior inventory missing')
        for name, record in prior['files'].items():
            if before.get(name) != record:
                raise ValueError('previous snapshot missing or changed:' + name)
        for name in before.keys() - prior['files'].keys():
            if before[name]['classification'] != 'V3_STRUCTURAL_ENVELOPE':
                raise ValueError('new legacy snapshot cannot enter sealed chain')
        parent = hashlib.sha256(raw).hexdigest()
    after = _scan(directory, now_ms)
    if before != after:
        raise ValueError('inventory changed during scan; retry without overwriting evidence')
    return {'kind': 'CMC_PUBLISHED_SNAPSHOT_INVENTORY', 'directory': str(directory),
            'sealed_at_ms': now_ms, 'files': before, 'parent_sha256': parent,
            'scoring_authorized': False, 'source_authentication': 'UNVERIFIED',
            'past_completeness_before_baseline': 'UNVERIFIED',
            'scope': 'PUBLISHED_NONHIDDEN_TOP_LEVEL_JSON_IN_DECLARED_DIRECTORY',
            'inventory_consistency': 'TWO_EQUAL_SCANS_NOT_ATOMIC_DIRECTORY_SNAPSHOT',
            'implementation_sha256': digest(__file__)}


def verified_manifest(seal_path, *, now_ms):
    """Check current corpus against seal before selecting all its v3 sources."""
    raw = Path(seal_path).read_bytes()
    saved = json.loads(raw)
    checked = seal(saved['directory'], now_ms=now_ms, previous=seal_path)
    if checked['files'] != saved['files']:
        raise ValueError('new published files require a new chained seal')
    return [{'file': str(Path(saved['directory']) / name), 'sha256': record['sha256']}
            for name, record in sorted(saved['files'].items())
            if record['classification'] == 'V3_STRUCTURAL_ENVELOPE']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshots', type=Path, required=True)
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        output, directory = args.output.resolve(), args.snapshots.resolve()
        if output == directory or directory in output.parents:
            raise ValueError('seal output must be outside the snapshot directory')
        result = seal(args.snapshots, now_ms=int(time.time()*1000), previous=args.previous)
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write('\n')
        print(json.dumps({'published_files': len(result['files']), 'seal_sha256': digest(args.output),
                          'scoring_authorized': False}))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'INCOMPLETE', 'reason': str(exc), 'scoring_authorized': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
