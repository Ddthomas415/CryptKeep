"""Bounded stderr reducer and argv recipe. This module never launches SSH."""
import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTRACT_SHA = 'f4efff14b1c78804b58d7f957f57fed03223c7add9078b34057af2b1e3f308a9'
COMMAND_SHA = '9c241fd523215b5a65d5f6652503642ce7252c8c8dde6a5ac45bef484176ee52'
MAX_LINE = 4096
CHECK = b'# Tailscale SSH requires an additional check.'
LINK = re.compile(rb'# To authenticate, visit: (https://login\.tailscale\.com/a/[A-Za-z0-9]{1,128})')
# Full-line matches prevent paths, key fingerprints and remote text being logged.
STAGES = (
    (re.compile(rb'debug1: Connection established\.'), 'transport_connected'),
    (re.compile(rb'Authenticated to 100\.86\.128\.9 \(\[100\.86\.128\.9\]:22\) using "[a-z-]+"\.'), 'ssh_authenticated'),
    (re.compile(rb'debug1: Sending command: python3 -I -S -B -'), 'remote_command_requested'),
    (re.compile(rb'debug1: Exit status [0-9]{1,3}'), 'remote_exit_reported'),
)


def _contract():
    path = ROOT / 'live_ssh_contract_20261110.py'
    command = ROOT / 'host_preflight_command_20261110.py'
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != CONTRACT_SHA:
        raise ValueError('contract_hash_changed')
    if hashlib.sha256(command.read_bytes()).hexdigest() != COMMAND_SHA:
        raise ValueError('command_hash_changed')
    namespace = {'__file__': str(path), '__name__': 'reviewed_ssh_contract'}
    exec(compile(source, str(path), 'exec'), namespace)
    return namespace


def diagnostic_argv():
    """Prepare reviewed argv plus DEBUG1 only, without running a command."""
    argv = _contract()['live_argv']()
    if argv.count('LogLevel=VERBOSE') != 1:
        raise ValueError('unexpected_logging_contract')
    return ['LogLevel=DEBUG1' if item == 'LogLevel=VERBOSE' else item for item in argv]


def validate_diagnostic(argv, fields):
    if argv != diagnostic_argv():
        raise ValueError('diagnostic_argv_changed')
    # Installed ssh -G renders the DEBUG1 synonym as DEBUG.
    if fields.get('loglevel') != 'DEBUG':
        raise ValueError('diagnostic_loglevel_changed')
    normalized = dict(fields, loglevel='VERBOSE')
    _contract()['validate_effective'](normalized)


class StageFilter:
    """Streaming state; receipts contain fixed labels, never raw lines or links."""

    def __init__(self):
        self._pending = bytearray()
        self._discard = False
        self._seen = set()
        self._events = []
        self._link_emitted = False
        self._check_seen = False

    def _line(self, raw):
        raw = raw.removesuffix(b'\r')
        if raw == CHECK:
            self._check_seen = True
            event = 'ssh_check_requested'
        else:
            match = LINK.fullmatch(raw)
            if match:
                if self._check_seen and not self._link_emitted:
                    self._link_emitted = True
                    # Caller must not put this user-handoff value in a receipt.
                    return [('approval_url', match.group(1).decode('ascii'))]
                return []
            event = next((label for pattern, label in STAGES if pattern.fullmatch(raw)), None)
        if event is None or event in self._seen:
            return []
        self._seen.add(event)
        self._events.append(event)
        return [('stage', event)]

    def feed(self, data):
        if type(data) is not bytes:
            raise TypeError('bytes_required')
        out = []
        for value in data:
            if value == 10:
                if not self._discard:
                    out.extend(self._line(bytes(self._pending)))
                self._pending.clear()
                self._discard = False
            elif not self._discard:
                if len(self._pending) == MAX_LINE:
                    self._pending.clear()
                    self._discard = True
                else:
                    self._pending.append(value)
        return out

    def finish(self):
        # Unterminated/truncated lines are not enough evidence for a stage.
        self._pending.clear()
        self._discard = False

    def receipt(self):
        return {'observed_client_markers': list(self._events),
                'remote_inventory_validated': False,
                'causal_diagnosis': 'UNVERIFIED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--show-owner-approval-url', action='store_true',
                        help='User handoff only; output may persist in chat history. Never save as a repo log.')
    args = parser.parse_args()
    reducer = StageFilter()
    while chunk := sys.stdin.buffer.read1(4096):
        for kind, value in reducer.feed(chunk):
            if kind == 'stage':
                print('SSH_STAGE ' + value, flush=True)
            elif args.show_owner_approval_url:
                print('SSH_APPROVAL_URL ' + value, flush=True)
    reducer.finish()


if __name__ == '__main__':
    main()
