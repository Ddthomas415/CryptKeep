"""Strict value projection and reuse of the existing reviewed one-shot controller."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tarfile
import types
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CONTROLLER_SHA = '5ef1b78ab179d5808bd95d6c3453ff665030e78cf1fe902bed36eafc2fcc3389'
PRIOR_SHA = '9c241fd523215b5a65d5f6652503642ce7252c8c8dde6a5ac45bef484176ee52'
REMOTE_SHA = '496c783cbaaf1ba86d1be087afe4a3bf70ee8b6f3f116d194817c56a3adf19d4'
CANDIDATE_SHA = '724b4785dd627f9ff35bc91b939788d6ac90850458ba4f4333f7c7231f3dac1d'
MANIFEST_SHA = '928b12da4275a76c44728cdd141b76d7c0899c99fa3d28204a86bb03ec26ea03'
RELEASE = 'ga724b4785dd62'
VERSION = re.compile(r'[0-9]{1,4}(?:\.[0-9]{1,4}){1,3}(?:(?:a|b|rc|\.post|\.dev)[0-9]{1,4})?')
UNIT = re.compile(r'cbp-[a-zA-Z0-9@_.:-]{1,190}\.(?:service|target|timer)')


def controller():
    path = HERE/'instrumented_ssh_preflight_20261111.py'
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CONTROLLER_SHA:
        raise ValueError('controller_hash_changed')
    scope = {'__name__': 'reviewed_controller', '__file__': str(path)}
    exec(compile(raw, str(path), 'exec'), scope)
    return scope


def profile():
    candidate = ROOT/'docs/review_artifacts/group_a_composed_candidate_20261111_v3'
    manifest_raw = (candidate/'MANIFEST.json').read_bytes()
    if hashlib.sha256(manifest_raw).hexdigest() != MANIFEST_SHA:
        raise ValueError('candidate_manifest_changed')
    manifest = json.loads(manifest_raw)
    archive = candidate/'source-test-overlay.tar.gz'
    if hashlib.sha256(archive.read_bytes()).hexdigest() != CANDIDATE_SHA:
        raise ValueError('candidate_hash_changed')
    name = 'services/control/group_a_systemd_policy.py'
    with tarfile.open(archive) as source:
        raw = source.extractfile(name).read()
    if hashlib.sha256(raw).hexdigest() != manifest['files'][name]['sha256']:
        raise ValueError('candidate_policy_changed')
    module = types.ModuleType('readonly_candidate_policy')
    sys.modules[module.__name__] = module
    try:
        exec(compile(raw, name, 'exec'), module.__dict__)
        policy = module.render_group_a_policy(RELEASE)
    finally:
        del sys.modules[module.__name__]
    return {'candidate_sha256': CANDIDATE_SHA, 'release': RELEASE,
            'units': [policy.target, *policy.services, *policy.failure_services,
                      f'cbp-group-a-{RELEASE}-failed@.service'],
            'paths': [f'/srv/cryptkeep/releases/{RELEASE}', f'/srv/cryptkeep/state/{RELEASE}',
                      f'/srv/cryptkeep/alert-state/{RELEASE}'],
            'users': ['cbp-ga-paper', 'cbp-ga-alert']}


def render(profile_value):
    old = (HERE/'host_preflight_command_20261110.py').read_bytes()
    if hashlib.sha256(old).hexdigest() != PRIOR_SHA:
        raise ValueError('prior_command_changed')
    extra = (HERE/'compatibility_remote_20261111.py').read_bytes()
    if hashlib.sha256(extra).hexdigest() != REMOTE_SHA:
        raise ValueError('supplemental_command_changed')
    prefix = ('PRIOR_SOURCE='+repr(old)+'\nEXPECTED_BASE='+repr('580ca31ea983af6452a1e02ab8d4b51645e9b43c')
              +'\nPROFILE='+repr(profile_value)+'\n').encode()
    return prefix+extra


def number(value):
    if type(value) is not int or not 0 <= value < 2**64:
        raise ValueError('invalid_metadata_number')
    return value


def version(value):
    if type(value) is not str or not VERSION.fullmatch(value):
        raise ValueError('invalid_package_version')
    return value


def path_value(value):
    if type(value) is not str or len(value) > 512 or not re.fullmatch(r'[A-Za-z0-9_./ -]*', value):
        return None
    parts = value.split()
    roots = ('/srv/cryptkeep', '/var/lib/cryptkeep', '/run/cryptkeep', '/etc/systemd/system',
             '/lib/systemd/system', '/usr/lib/systemd/system')
    if any('..' in Path(item.lstrip('-')).parts
           or not any(item.lstrip('-') == root or item.lstrip('-').startswith(root+'/') for root in roots)
           for item in parts):
        return None
    return value


def paths(rows, expected):
    if type(rows) is not list or len(rows) != len(expected):
        raise ValueError('path_roster_invalid')
    result = {}
    fields = {'path', 'present', 'uid', 'gid', 'mode', 'directory', 'symlink',
              'available_bytes', 'available_inodes', 'status', 'error'}
    for row in rows:
        if type(row) is not dict or not set(row) <= fields or row.get('path') not in expected or row['path'] in result:
            raise ValueError('path_metadata_invalid')
        clean = {}
        if row.get('present') is False:
            if set(row) != {'path', 'present'}:
                raise ValueError('absent_path_metadata_invalid')
        elif 'error' not in row and 'status' not in row:
            if row.get('present') is not True or not {'uid','gid','mode','directory','symlink'} <= set(row):
                raise ValueError('path_metadata_incomplete')
        for key in ('present', 'directory', 'symlink'):
            if key in row:
                if type(row[key]) is not bool:
                    raise ValueError('path_metadata_invalid')
                clean[key] = row[key]
        for key in ('uid', 'gid', 'available_bytes', 'available_inodes'):
            if key in row:
                clean[key] = number(row[key])
        if 'mode' in row:
            if type(row['mode']) is not str or not re.fullmatch(r'0o[0-7]{1,4}', row['mode']):
                raise ValueError('path_mode_invalid')
            clean['mode'] = row['mode']
        if 'status' in row or 'error' in row:
            clean['status'] = 'unavailable'
        result[row['path']] = clean
    return result


def units(record, expected=None):
    if type(record) is not dict:
        raise ValueError('unit_record_invalid')
    if record.get('exit') != 0 or record.get('truncated') is not False:
        return {'status': 'unavailable'}
    output = record.get('output')
    if type(output) is not str or len(output) > 16384:
        raise ValueError('unit_output_invalid')
    allowed = {'Id', 'LoadState', 'ActiveState', 'SubState', 'FragmentPath', 'User', 'Group',
        'Restart', 'NoNewPrivileges', 'ProtectSystem', 'ReadWritePaths', 'ReadOnlyPaths',
        'StateDirectory', 'UMask', 'WorkingDirectory', 'OnFailure', 'PartOf', 'ConditionResult'}
    enums = {
        'LoadState': {'loaded', 'not-found', 'masked', 'error', 'bad-setting', 'stub', 'merged'},
        'ActiveState': {'active', 'inactive', 'failed', 'activating', 'deactivating', 'reloading', 'maintenance', 'refreshing'},
        'Restart': {'no', 'always', 'on-success', 'on-failure', 'on-abnormal', 'on-watchdog', 'on-abort'},
        'NoNewPrivileges': {'yes', 'no'}, 'ConditionResult': {'yes', 'no'},
        'ProtectSystem': {'no', 'yes', 'full', 'strict'},
        'SubState': {'running', 'dead', 'failed', 'exited', 'waiting', 'auto-restart', 'start', 'stop', 'listening'}}
    result = {}
    for block in output.strip().split('\n\n'):
        if not block:
            continue
        fields = {}
        for line in block.splitlines():
            key, separator, value = line.partition('=')
            if not separator or key not in allowed or key in fields:
                raise ValueError('unit_fields_invalid')
            fields[key] = value
        identity = fields.get('Id', '')
        if not {'Id', 'LoadState', 'ActiveState'} <= set(fields):
            raise ValueError('unit_fields_incomplete')
        if not UNIT.fullmatch(identity) or identity in result or (expected is not None and identity not in expected):
            raise ValueError('unit_identity_invalid')
        clean = {'Id': identity}
        for key, value in fields.items():
            if key == 'Id':
                continue
            if key in enums:
                clean[key] = value if value in enums[key] else None
            elif key in {'FragmentPath', 'WorkingDirectory', 'ReadWritePaths', 'ReadOnlyPaths'}:
                clean[key] = path_value(value)
            elif key in {'OnFailure', 'PartOf'}:
                clean[key] = value.split() if all(UNIT.fullmatch(x) for x in value.split()) else None
            elif key in {'User', 'Group', 'StateDirectory'}:
                clean[key] = value if re.fullmatch(r'[a-z0-9_/-]{0,96}', value) else None
            elif key == 'UMask':
                clean[key] = value if re.fullmatch(r'[0-7]{4}', value) else None
        result[identity] = clean
    if not result or (expected is not None and set(result) != set(expected)):
        raise ValueError('unit_roster_incomplete')
    return {'status': 'observed', 'units': result}


def project(raw, specification, ctl):
    value = ctl['_json'](raw)
    if type(value) is not dict or set(value) != {'base', 'compatibility'}:
        raise ValueError('compatibility_schema_invalid')
    base, extra = value['base'], value['compatibility']
    required = {'candidate_sha256', 'release', 'manager', 'package_metadata', 'proposed_units',
                'candidate_paths', 'proposed_users', 'finished_utc'}
    if type(extra) is not dict or set(extra) != required or extra['candidate_sha256'] != CANDIDATE_SHA or extra['release'] != RELEASE:
        raise ValueError('compatibility_identity_invalid')
    summary = ctl['inventory_summary'](json.dumps(base, allow_nan=False).encode())
    if summary['checkout_head'] != '580ca31ea983af6452a1e02ab8d4b51645e9b43c':
        raise ValueError('host_base_changed')
    manager = extra['manager']
    match = re.match(r'\Asystemd ([0-9]{1,5})(?:\s|$)', manager.get('output', '')) if manager.get('exit') == 0 and manager.get('truncated') is False else None
    safe = {'systemd_version': int(match.group(1)) if match else None}
    safe['existing_unit_policy'] = units(base['selected_unit_properties'])
    safe['proposed_unit_collision_observations'] = units(extra['proposed_units'], specification['units'])
    safe['paths'] = paths(base['paths'], ['/srv/cryptkeep', '/srv/cryptkeep/app', '/srv/cryptkeep/releases',
        '/srv/cryptkeep/state', '/var/lib/cryptkeep', '/run/cryptkeep', '/etc/systemd/system'])
    safe['candidate_paths'] = paths(extra['candidate_paths'], specification['paths'])
    memory = base['memory']
    if type(memory) is not dict or not set(memory) <= {'MemTotal_bytes', 'MemAvailable_bytes', 'status'}:
        raise ValueError('memory_metadata_invalid')
    safe['memory'] = ({key: number(item) for key, item in memory.items()} if set(memory) == {'MemTotal_bytes', 'MemAvailable_bytes'}
                      else {'status': 'unavailable'})
    runtime = base['checkout_runtime']
    if runtime.get('exit') == 0 and runtime.get('truncated') is False:
        parsed = ctl['_json'](runtime['output'])
        safe['venv_interpreter'] = {'python': ctl['_version'](parsed['python']), 'sqlite': version(parsed['sqlite'])}
    else:
        safe['venv_interpreter'] = {'status': 'unavailable'}
    packages = extra['package_metadata']
    safe['venv_package_metadata'] = {'status': 'unavailable'}
    if packages.get('exit') == 0 and packages.get('truncated') is False:
        metadata = ctl['_json'](packages['output'])
        if (set(metadata) != {'site', 'packages'} or not re.fullmatch(r'/srv/cryptkeep/app/\.venv/lib/python[0-9]{1,2}\.[0-9]{1,2}/site-packages', metadata['site'])
                or set(metadata['packages']) != {'ccxt', 'pyyaml', 'numpy', 'pytest'}):
            raise ValueError('package_roster_invalid')
        checked = {}
        for name, entry in metadata['packages'].items():
            if set(entry) == {'version'}:
                checked[name] = {'version': version(entry['version'])}
            elif set(entry) == {'status'} and entry['status'] in {'absent_at_inspected_site', 'ambiguous', 'unavailable'}:
                checked[name] = entry
            else:
                raise ValueError('package_metadata_invalid')
        safe['venv_package_metadata'] = {'site': metadata['site'], 'packages': checked}
    if set(extra['proposed_users']) != set(specification['users']):
        raise ValueError('user_roster_invalid')
    safe['proposed_users'] = {}
    for name, entry in extra['proposed_users'].items():
        if (type(entry) is dict and set(entry) == {'present'} and entry['present'] is False) or entry == {'status': 'unavailable'}:
            safe['proposed_users'][name] = entry
        elif set(entry) == {'present', 'uid', 'gid'} and entry['present'] is True:
            safe['proposed_users'][name] = {'present': True, 'uid': number(entry['uid']), 'gid': number(entry['gid'])}
        else:
            raise ValueError('user_metadata_invalid')
    stamp = datetime.fromisoformat(extra['finished_utc'])
    if stamp.utcoffset() is None:
        raise ValueError('capture_time_invalid')
    summary.update(safe_values=safe, compatibility_capture_finished_utc=stamp.astimezone(timezone.utc).isoformat(),
                   atomic_inventory=False, candidate_sha256=CANDIDATE_SHA, release=RELEASE,
                   full_runtime_readiness_verified=False)
    return summary


def run(receipt, *, execute=False, show_url=False):
    if execute is not True:
        return {'status': 'INCOMPLETE', 'outcome': 'not_executed', 'connection_processes_started': 0}
    receipt = Path(receipt)
    if receipt.parent.resolve() != HERE or not re.fullmatch(r'compatibility_attempt_[A-Za-z0-9_-]{1,80}\.json', receipt.name):
        raise ValueError('receipt_path_refused')
    ctl = controller()
    specification = profile()
    argv, _, reducer = ctl['prepare']()
    command = render(specification)
    fd = os.open(receipt, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w+b') as handle:
        state = {'status': 'INCOMPLETE', 'outcome': 'prepared', 'connection_processes_started': 0,
                 'candidate_sha256': CANDIDATE_SHA, 'remote_command_sha256': hashlib.sha256(command).hexdigest(),
                 'bot_relation': 'BOT_RULES', 'runtime_trading_configuration_checked': False,
                 'controller_sha256': CONTROLLER_SHA, 'owner_url_display_enabled': show_url is True}
        state.update(adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                     supplemental_source_sha256=REMOTE_SHA, prior_collector_sha256=PRIOR_SHA,
                     candidate_manifest_sha256=MANIFEST_SHA)
        ctl['_save'](handle, state)
        raw = ctl['_collect'](argv, command, reducer, handle, state, emit=ctl['_terminal_emit'](show_url))
        if state['outcome'] == 'stdout_received':
            try:
                state['inventory_summary'] = project(raw, specification, ctl)
                state['outcome'] = 'candidate_compatibility_values_received'
            except Exception:
                state['outcome'] = 'compatibility_projection_refused'
        ctl['_save'](handle, state)
        return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--show-owner-approval-url', action='store_true')
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    try:
        result = run(args.receipt, execute=args.execute, show_url=args.show_owner_approval_url)
        print(json.dumps({key: result[key] for key in ('status', 'outcome', 'connection_processes_started')}))
        sys.exit(0 if result['outcome'] == 'candidate_compatibility_values_received' else 1)
    except Exception:
        print('{"status":"INCOMPLETE","outcome":"compatibility_preflight_refused"}')
        sys.exit(1)
