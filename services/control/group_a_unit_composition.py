"""Pure Group A unit composition, never installation or readiness certification."""

from dataclasses import dataclass
import re

from services.control.group_a_account_units import _STARTUP_ENV
from services.control.group_a_alert_units import render_group_a_alert_units
from services.control.group_a_quote_routing import render_group_a_quote_routing
from services.control.group_a_systemd_policy import render_group_a_policy


ENTRYPOINTS = (
    'scripts/run_strategy_runner.py',
    'scripts/run_paper_engine.py',
    'scripts/run_group_a_quote_publisher.py',
    'scripts/run_group_a_alert.py',
    'scripts/run_group_a_backup.py',
)
UNVERIFIED_REQUIREMENTS = (
    'source_bytes_and_independent_review',
    'backup_runtime_and_R10',
    'sizing_and_effective_configuration',
    'permissions_and_namespaces',
    'target_dependencies_and_effective_policy',
    'delivery_and_commissioning',
)


@dataclass(frozen=True)
class GroupAUnitComposition:
    target_name: str
    files: tuple[tuple[str, str], ...]
    launch_args: tuple[tuple[str, tuple[str, ...]], ...]
    stop_argv: tuple[str, ...]
    runtime_source_refs: tuple[tuple[str, str], ...]
    missing_entrypoints: tuple[str, ...]
    deployment_status: str = 'INCOMPLETE'
    unverified_requirements: tuple[str, ...] = UNVERIFIED_REQUIREMENTS

    @property
    def composition_complete(self) -> bool:
        """Structural roster only, not functioning programs or deployment approval."""
        return not self.missing_entrypoints and bool(self.files)


def _exec_start(argv, *, instance=False):
    if type(argv) is not tuple or not 3 <= len(argv) <= 64 or argv[:2] != ('/usr/bin/env', '-i'):
        raise ValueError('invalid_group_a_launch_argument')
    quoted = []
    for index, arg in enumerate(argv):
        if (type(arg) is not str or len(arg) > 512 or ';' in arg
                or any(not 32 <= ord(char) <= 126 for char in arg)):
            raise ValueError('invalid_group_a_launch_argument')
        # systemd parses this directly; shell quoting would not prevent expansion.
        token = arg.replace('\\', '\\\\').replace('"', '\\"').replace('$', '$$')
        if not (instance and index == len(argv)-1 and arg == '%i'):
            token = token.replace('%', '%%')
        quoted.append('"'+token+'"')
    return 'ExecStart='+' '.join(quoted)+'\n'


def _with_start(fragment, argv, *, instance=False):
    if (type(fragment) is not str or len(fragment) > 16384
            or any(char != '\n' and not 32 <= ord(char) <= 126 for char in fragment)):
        raise ValueError('invalid_group_a_unit_fragment')
    section = None
    seen_service = False
    service_type = None
    for line in fragment.splitlines():
        line = line.strip()
        if not line or line.startswith(('#', ';')):
            continue
        if line.endswith('\\'):
            raise ValueError('invalid_group_a_unit_fragment')
        if line.startswith('['):
            if line not in ('[Unit]', '[Service]') or (line == '[Service]' and seen_service):
                raise ValueError('invalid_group_a_unit_fragment')
            section = line
            seen_service |= line == '[Service]'
            continue
        key, separator, value = line.partition('=')
        if not separator or section is None or key.strip().lower().startswith('exec'):
            raise ValueError('invalid_group_a_unit_fragment')
        if section == '[Service]' and key.strip() == 'Type':
            if service_type is not None or value.strip() not in ('exec', 'oneshot'):
                raise ValueError('invalid_group_a_unit_fragment')
            service_type = value.strip()
    if section != '[Service]':
        raise ValueError('invalid_group_a_unit_fragment')
    return (fragment.rstrip()+'\n'+('Type=exec\n' if service_type is None else '')
            +_exec_start(argv, instance=instance))


def _indexed(rows):
    if type(rows) is not tuple or len(rows) > 64:
        raise ValueError('invalid_group_a_composition_roster')
    result = {}
    for row in rows:
        if type(row) is not tuple or len(row) != 2 or type(row[0]) is not str or row[0] in result:
            raise ValueError('invalid_group_a_composition_roster')
        result[row[0]] = row[1]
    return result


def _backup_fragment(release, service_user):
    """A launch boundary for a separately implemented program, not that program."""
    source = f'/srv/cryptkeep/releases/{release}'
    state = f'/srv/cryptkeep/state/{release}'
    support = f'{state}/support/backup'
    fragment = (
        '[Unit]\nDescription=CryptKeep Group A backup supervisor\n'
        f'AssertPathIsDirectory={state}\nAssertPathIsDirectory={support}\n'
        '[Service]\nType=exec\n'
        f'User={service_user}\nWorkingDirectory={source}\n'
        'NoNewPrivileges=yes\nProtectSystem=strict\nProtectHome=yes\nPrivateTmp=yes\n'
        'UMask=0077\nLimitCORE=0\nCapabilityBoundingSet=\nRestrictSUIDSGID=yes\n'
        f'ReadOnlyPaths={state}\nReadWritePaths={support}\n'
        f'UnsetEnvironment={_STARTUP_ENV}\n'
    )
    argv = ('/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', f'CBP_STATE_DIR={support}',
            f'{source}/.venv/bin/python', '-I', '-B',
            f'{source}/scripts/run_group_a_backup.py', release)
    return fragment, argv


def compose_group_a_units(release, *, service_user, alert_user, runtime_sources):
    """Return in-memory unit text only, with no target if source refs are missing.

    runtime_sources contains caller-supplied relative-path -> SHA256 references
    from a separately verified complete runtime manifest. This function neither
    reads source bytes nor reviews their behavior. In particular a supplied
    backup hash does not establish R10. Deployment remains INCOMPLETE even when
    all structural files are rendered. No files are written and no commands run.
    """
    policy = render_group_a_policy(release)
    quote = render_group_a_quote_routing(release, service_user=service_user)
    alert = render_group_a_alert_units(release, service_user=service_user, alert_user=alert_user)
    if type(runtime_sources) is not dict or len(runtime_sources) > 10000:
        raise ValueError('invalid_group_a_source_reference')
    references, missing = [], []
    for name in ENTRYPOINTS:
        if name not in runtime_sources:
            missing.append(name)
            continue
        digest = runtime_sources[name]
        if type(digest) is not str or re.fullmatch('[0-9a-f]{64}', digest) is None:
            raise ValueError('invalid_group_a_source_reference')
        references.append((name, digest))
    if missing:
        return GroupAUnitComposition(policy.target, (), (), policy.stop_argv,
                                     tuple(references), tuple(missing))

    prefix = policy.target.removesuffix('.target')
    failure = prefix+'-failed@.service'
    backup_name = prefix+'-backup.service'
    backup_text, backup_args = _backup_fragment(release, service_user)
    # Routing already replaces all eighteen account fragments; never merge the
    # earlier unbound account copies over them.
    fragments = _indexed((*quote.fragments, *alert.fragments, (backup_name, backup_text)))
    launches = _indexed((*quote.launch_args, *alert.launch_args, (backup_name, backup_args)))
    expected = {*policy.services, failure}
    if (len(policy.services) != 21 or len(policy.failure_services) != 21
            or len(expected) != 22 or set(fragments) != expected or set(launches) != expected
            or quote.target_name != policy.target):
        raise ValueError('invalid_group_a_composition_roster')
    files = _indexed(policy.files)
    expected_policy = {policy.target, f'{failure}.d/50-group-a-lifecycle.conf',
                       *(f'{name}.d/50-group-a-lifecycle.conf' for name in policy.services)}
    if set(files) != expected_policy or set(files) & expected:
        raise ValueError('invalid_group_a_composition_roster')
    for name in sorted(expected):
        files[name] = _with_start(fragments[name], launches[name], instance=name == failure)
    return GroupAUnitComposition(policy.target, tuple(sorted(files.items())),
        tuple(sorted(launches.items())), policy.stop_argv, tuple(references), ())
