"""Explicit approved download-only action; never launches restic or rclone."""
import argparse
import json
from pathlib import Path
import re
import sys
import time

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from services.control.group_a_backup_process import OwnedProcessExecutor
from services.control import group_a_backup_tools as tools


def _worker(parent, pins, digest, deadline):
    try:
        result = tools.prepare(Path(parent), pins_path=Path(pins), pins_sha256=digest, deadline=deadline)
        return {'status': 'COMPLETE', **result}
    except Exception as error:
        reason = str(error) if isinstance(error, tools.core.BundleError) else 'download_preparation_failed'
        if re.fullmatch('[a-z0-9_]{1,80}', reason) is None:
            reason = 'download_preparation_failed'
        return {'status': 'INCOMPLETE', 'reason': reason, 'clients_executed': False}


def main(argv=None, *, executor=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--pins', type=Path, required=True)
    parser.add_argument('--pins-sha256', required=True)
    parser.add_argument('--download-only', action='store_true')
    args = parser.parse_args(argv)
    try:
        tools.load_pins(args.pins, args.pins_sha256)
        tools.core._private(args.parent)
        if not args.download_only:
            result = {'status': 'INCOMPLETE', 'reason': 'explicit_download_flag_required', 'clients_executed': False}
        else:
            # Gated worker has160s; parent retains an unreaped ownership fence
            # through signalling, within the180s action/cleanup budget.
            result = (executor or OwnedProcessExecutor()).call(_worker,
                (str(args.parent), str(args.pins), args.pins_sha256, time.monotonic() + 160), 180)
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get('status') == 'COMPLETE' else 1
    except (Exception, KeyboardInterrupt):
        print(json.dumps({'status': 'INCOMPLETE', 'reason': 'download_controller_refused_or_uncertain',
                          'clients_executed': False}, sort_keys=True))
        return 1


if __name__ == '__main__':
    sys.exit(main())
