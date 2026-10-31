"""Preparation-only entry point; default validation never contacts Docker.

An execution flag does not replace separate operator authorization. This command
has no startup, token, query or cutover option. Existing installer CLI is unchanged.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat

from scripts.research import companion_existing_controller as core
from scripts.research import companion_installer as install
from scripts.research import companion_staged_update as staged
from scripts.research.companion_install_docker import DockerInstallBackend

ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = Path('/private/tmp/cryptkeep-companion-install.lock')
STATE_PARTS = ('.cbp_state', 'runtime', 'companion_preparations')


class PreparationReceipt(core.Receipt):
    def __init__(self, directory_fd):
        fd = os.open('receipt.jsonl', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=directory_fd)
        self.file = os.fdopen(fd, 'w', encoding='ascii')


def _manifest(path, trusted_hash):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > 1_048_576:
            install.refuse()
        plan = install.Plan.load(stream.read(1_048_577), trusted_hash)
    if not plan.staged:
        install.refuse()
    return plan


def _directory(fd):
    info = os.fstat(fd)
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) & 0o022):
        install.refuse()


def _reserve(plan):
    """Fixed per-attempt directory is the durable consumption marker; never erase."""
    fd = os.open(ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        _directory(fd)
        for part in STATE_PARTS:
            try:
                os.mkdir(part, mode=0o700, dir_fd=fd)
            except FileExistsError:
                pass
            else:
                os.fsync(fd)  # Persist each new ancestor before descending.
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
            _directory(fd)
        # No exist_ok: even a failed/empty attempt is consumed across processes.
        os.mkdir(plan.attempt, mode=0o700, dir_fd=fd)
        os.fsync(fd)
        child = os.open(plan.attempt, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
        try:
            _directory(child)
        except Exception:
            os.close(child)
            raise
        return child
    finally:
        os.close(fd)


def _publish(directory_fd, raw):
    fd = os.open('evidence.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600, dir_fd=directory_fd)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.fsync(directory_fd)
    return True


def _cleanup_after_publication_failure(runner):
    runner.recovering = True
    cleaned = staged.cleanup_unpromoted(runner)
    try:
        rows = runner._rows(recovery=True)
        staged._originals(runner, rows)
        return (cleaned and not runner.create_pending and not runner.replacement_cleanup_pending
                and not any(row.attempt == runner.plan.attempt for row in rows.values()))
    except Exception:
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(description='Validate preparation inputs; no operation by default')
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--reviewed-manifest-sha256', required=True)
    parser.add_argument('--execute-preparation', action='store_true')
    args = parser.parse_args(argv)
    lock = directory = receipt = runner = None
    reserved = False
    result = None
    phase = 'manifest_validation'
    try:
        plan = _manifest(args.manifest, args.reviewed_manifest_sha256)
        destination = ROOT.joinpath(*STATE_PARTS, plan.attempt)
        if not args.execute_preparation:
            print(json.dumps({'state': 'READY_FOR_INDEPENDENT_REVIEW', 'actions_executed': False,
                'startup_authorized': False, 'manifest_sha256': plan.manifest_sha256,
                'attempt': plan.attempt, 'output_directory': str(destination),
                'controller_budget_seconds': 300, 'recovery_reserve_seconds': 120}))
            return 0
        phase = 'lock'
        lock = os.open(LOCK_PATH, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        info = os.fstat(lock)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o600):
            install.refuse()
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        phase = 'reservation'
        reserved = None  # Reservation failure may leave a durable consumed marker.
        directory = _reserve(plan)
        reserved = True
        phase = 'receipt'
        receipt = PreparationReceipt(directory)
        os.fsync(directory)
        phase = 'backend'
        backend = DockerInstallBackend(plan, ROOT, enabled=True)
        runner = install.Installer(backend, receipt)
        phase = 'preparation'
        result = runner.prepare_staged(plan, authorized=True)
        if result['state'] != 'READY_FOR_INDEPENDENT_REVIEW' or not result['receipt_complete']:
            install.refuse()
        phase = 'evidence_publication'
        staged._rows(plan, result['preparation_evidence'])
        raw = install.canonical(result['preparation_evidence'])
        remaining = runner.work_end - runner.clock()
        if remaining <= 0 or runner.executor.call(_publish, (directory, raw), min(2, remaining)) is not True:
            install.refuse()
        evidence_hash = hashlib.sha256(raw).hexdigest()
        phase = 'receipt_confirmation'
        runner._record('preparation_evidence_published', evidence={'sha256': evidence_hash})
        print(json.dumps({'state': 'READY_FOR_INDEPENDENT_REVIEW', 'preparation_complete': True,
            'actions_executed': True, 'startup_authorized': False, 'services_started': False,
            'originals_interrupted': False, 'attempt_reserved': True,
            'receipt': str(destination / 'receipt.jsonl'), 'evidence': str(destination / 'evidence.json'),
            'evidence_sha256': evidence_hash, 'manifest_sha256': plan.manifest_sha256}))
        return 0
    except Exception:
        cleanup = result.get('cleanup_verified') if isinstance(result, dict) else None
        if runner is not None and isinstance(result, dict) and result.get('state') == 'READY_FOR_INDEPENDENT_REVIEW':
            cleanup = _cleanup_after_publication_failure(runner)
            try:
                runner._record('preparation_publication_failed', evidence={'cleanup_verified': cleanup})
            except Exception:
                pass
        failure_stage = result.get('failure_stage') if isinstance(result, dict) else None
        allowed_stages = {'preparation_reservation', 'preparation_baseline', 'preparation_build',
                          'staged_creation', 'staged_source_verification'}
        details = {'failure_phase': phase,
            'preparation_failure_stage': failure_stage if failure_stage in allowed_stages else None,
            'unresolved_creation': sorted(name for name in getattr(runner, 'create_pending', ()) if name in install.APPS),
            'unresolved_cleanup': sorted(name for name in getattr(runner, 'replacement_cleanup_pending', ()) if name in install.APPS),
            'receipt': str(destination / 'receipt.jsonl') if receipt is not None else None}
        if runner is not None and runner.used:
            runner.recovering = True
            try:
                runner._record('preparation_entrypoint_failed', evidence=details)
            except Exception:
                pass
        print(json.dumps({'state': 'INCOMPLETE', 'reason': 'preparation_refused',
                          'attempt_reserved': reserved, 'cleanup_verified': cleanup, **details}))
        return 1
    finally:
        if receipt is not None:
            receipt.close()
        if directory is not None:
            os.close(directory)
        if lock is not None:
            os.close(lock)


if __name__ == '__main__':
    import sys
    sys.exit(main())
