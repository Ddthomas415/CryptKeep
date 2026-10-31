"""One-shot staged cutover; validation is inert and execution needs separate approval."""
from __future__ import annotations

import argparse
from copy import deepcopy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import stat
import sys
import tempfile

from scripts.research import companion_existing_controller as core
from scripts.research import companion_installer as install
from scripts.research import companion_network_configuration as network
from scripts.research import companion_prepare as preparation
from scripts.research import companion_runtime_adapter as adapter
from scripts.research import companion_staged_update as staged
from scripts.research import companion_cutover_continuation as continuation
from scripts.research.companion_docker_transport import DockerTransport, _path
from scripts.research.companion_install_docker import DockerInstallBackend

ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = preparation.LOCK_PATH
STATE_PARTS = ('.cbp_state', 'runtime', 'companion_cutovers')


def _read(path, limit=1_048_576):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            install.refuse()
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        install.refuse()
    return raw


def load_inputs(args):
    plan = preparation._manifest(args.manifest, args.reviewed_manifest_sha256)
    prepared = staged.ReviewedPreparation.load(_read(args.preparation_evidence),
        _read(args.preparation_review, 262_144), args.reviewed_preparation_review_sha256, plan)
    metadata = json.loads(_read(args.staged_metadata), object_pairs_hook=install._unique)
    if type(metadata.get('rows')) is not list or len(metadata['rows']) != 4:
        install.refuse()
    final_models = []
    for app, actual, row in zip(plan.applications, prepared.replacements, metadata['rows']):
        configured, ids, evidence = network.project(row, dict(plan.network_bindings))
        snapshot = install.Snapshot(row['name'].removeprefix('/'), row['id'], row['image'],
            row['state'], row['started'], row['restarts'], row['restart_policy'],
            adapter.preservation_digest(row), adapter.preservation_digest({**row, 'networks': {}}),
            tuple(sorted(n['NetworkID'] for n in row['networks'].values())), row['attempt'], configured, ids, evidence)
        if (snapshot != actual
                or app['network_options'][::2] != ['--alias'] * (len(app['network_options']) // 2)):
            install.refuse()
        model = deepcopy(row)
        for attachment in model['networks'].values():
            attachment['Aliases'] = app['network_options'][1::2]
        if network.project(model, dict(plan.network_bindings))[0] != app['replacement_configured_metadata']:
            install.refuse()
        final_models.append(model)
    review_raw = _read(args.runtime_review, 262_144)
    if (not install.ID.fullmatch(args.reviewed_runtime_review_sha256)
            or hashlib.sha256(review_raw).hexdigest() != args.reviewed_runtime_review_sha256
            or not 1 <= len(args.dependency_review) <= 7):
        install.refuse()
    review = adapter._review_json(review_raw)
    if type(review.get('subjects')) is not list or len(review['subjects']) != 7:
        install.refuse()
    targets = []
    for subject in review['subjects']:
        if (set(subject) != {'name', 'container_id', 'image_id', 'preservation_sha256', 'sources'}
                or type(subject['sources']) is not dict):
            install.refuse()
        for path, digest in subject['sources'].items():
            _path(path)
            if type(digest) is not str or not install.ID.fullmatch(digest):
                install.refuse()
        targets.append(adapter.TargetPin(subject['name'], subject['container_id'], subject['image_id'],
            subject['preservation_sha256'], tuple(sorted(subject['sources'].items()))))
    if tuple(p.name for p in targets) != core.TARGETS or type(review.get('dependency_reviews')) is not dict:
        install.refuse()
    topical = json.loads(_read(args.topical_approvals, 262_144), object_pairs_hook=install._unique)
    if type(topical) is not list:
        install.refuse()
    pins = adapter.ReviewedPins(tuple(targets), args.reviewed_runtime_review_sha256,
        tuple(sorted(review['dependency_reviews'].items())), tuple(topical), review_raw,
        tuple(_read(path, 262_144) for path in args.dependency_review))
    validator = adapter.PinnedRuntimeAdapter(None, pins)
    try:
        by_name = validator._pins()
        if (not validator._policy_reviews_match(by_name) or not validator._source_coverage(by_name)
                or not validator._topical_contract()):
            install.refuse()
        active_bindings = validator.reviewed_network_bindings()
        if active_bindings is not None and active_bindings != dict(plan.network_bindings):
            install.refuse()
    finally:
        validator.close()
    for before, pin in zip(plan.baseline[:3], pins.targets[:3]):
        if (pin.container_id, pin.image_id, pin.preservation_sha256) != (before.id, before.image, before.metadata):
            install.refuse()
    for app, actual, pin, model in zip(plan.applications, prepared.replacements, pins.targets[3:], final_models):
        expected = adapter.preservation_digest(model)
        if active_bindings is not None:
            model = network.final_model(model, active_bindings, app['network_options'][1::2])
            expected = network.project(model, active_bindings)[0]
        if ((pin.container_id, pin.image_id) != (actual.id, actual.image)
                or pin.preservation_sha256 != expected
                or any(dict(pin.source_sha256).get(s['destination']) != s['sha256'] for s in app['sources'])):
            install.refuse()
    return plan, prepared, pins


def _reserve(plan, *, execution_id=None):
    identity = plan.attempt if execution_id is None else execution_id
    if type(identity) is not str or not install.ATTEMPT.fullmatch(identity):
        install.refuse()
    fd = os.open(ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        preparation._directory(fd)
        for part in (*STATE_PARTS, identity):
            try:
                os.mkdir(part, mode=0o700, dir_fd=fd)
            except FileExistsError:
                if part == identity:
                    raise
            else:
                os.fsync(fd)
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
            preparation._directory(fd)
        result, fd = fd, None
        return result
    finally:
        if fd is not None:
            os.close(fd)


def _publish(directory_fd, raw):
    fd = os.open('provisional_result.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600, dir_fd=directory_fd)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.fsync(directory_fd)
    return True


def _summary(result):
    result = result if isinstance(result, dict) else {}
    keys = ('running_update_complete', 'query_attempted', 'query_passed', 'receipt_complete',
            'rollback_verified', 'rollback_exact_baseline', 'services_started',
            'prepared_ids_preserved', 'preparation_consumed')
    out = {k: result.get(k) if type(result.get(k)) is bool else None for k in keys}
    for key in ('unresolved_quiesce', 'unresolved_restart', 'unresolved_replacement_start',
                'unresolved_replacement_cleanup', 'unresolved_creation'):
        values = result.get(key)
        if type(values) not in (list, tuple, set):
            values = ()
        out[key] = sorted(n for n in values if type(n) is str and n in install.APPS)
    allowed_stages = {'reservation', 'inventory_preflight', 'baseline_preflight', 'staged_preflight',
        'inventory_recheck', 'quiesce', 'replacement', 'staged_activation', 'replacement_inventory',
        'replacement_checks', 'source_verification', 'postconditions', 'runtime_verification', 'receipt_commit'}
    stage = result.get('failure_stage')
    out['controller_failure_stage'] = stage if type(stage) is str and stage in allowed_stages else None
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description='Validate reviewed staged cutover inputs; no action by default')
    for name in ('manifest', 'preparation-evidence', 'preparation-review', 'staged-metadata', 'runtime-review', 'topical-approvals'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('manifest', 'preparation-review', 'runtime-review'):
        parser.add_argument('--reviewed-' + name + '-sha256', required=True)
    parser.add_argument('--dependency-review', type=Path, action='append', required=True)
    parser.add_argument('--continuation-review', type=Path)
    parser.add_argument('--reviewed-continuation-review-sha256')
    parser.add_argument('--token-fd', type=int)
    parser.add_argument('--execute-cutover', action='store_true')
    args = parser.parse_args(argv)
    lock = directory = receipt = runtime = runner = config = None
    token = None
    result = None
    signals = {}
    phase, reserved, actions = 'input_validation', False, False
    destination = None
    interrupted = False
    def cancel(signum, frame):
        nonlocal interrupted
        if interrupted:
            return
        interrupted = True
        # Never inject a second exception into failure handling or recovery.
        if sys.exc_info()[0] is not None or getattr(runner, 'recovering', False):
            return
        raise core.Refused('cutover_interrupted')
    try:
        if ((args.execute_cutover and (args.token_fd is None or args.token_fd <= 2))
                or (not args.execute_cutover and args.token_fd is not None)):
            install.refuse()
        plan, prepared, pins = load_inputs(args)
        resumed = continuation.load(args, plan, prepared, ROOT, STATE_PARTS, _read)
        execution_id = resumed.execution_id if resumed else plan.attempt
        destination = ROOT.joinpath(*STATE_PARTS, execution_id)
        if not args.execute_cutover:
            print(json.dumps({'state': 'READY_FOR_INDEPENDENT_REVIEW', 'actions_executed': False,
                'startup_authorized': False, 'input_bindings_validated': True,
                'manifest_sha256': plan.manifest_sha256, 'attempt': plan.attempt,
                'controller_budget_seconds': 600, 'recovery_reserve_seconds': 180,
                **({'continuation': resumed.evidence(plan.attempt)} if resumed else {})}))
            return 0
        phase = 'lock'
        lock = os.open(LOCK_PATH, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        info = os.fstat(lock)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600:
            install.refuse()
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if resumed is not None:
            phase = 'continuation_recheck'
            if continuation.load(args, plan, prepared, ROOT, STATE_PARTS, _read) != resumed:
                install.refuse()
        phase, reserved = 'reservation', None
        directory = (_reserve(plan, execution_id=execution_id) if resumed else _reserve(plan))
        reserved = True
        phase = 'receipt'
        receipt = preparation.PreparationReceipt(directory)
        os.fsync(directory)
        receipt.write({'phase': 'cutover_inputs_bound', 'installation_evidence': {
            'manifest_sha256': plan.manifest_sha256,
            'preparation_evidence_sha256': prepared.evidence_sha256,
            'preparation_review_sha256': args.reviewed_preparation_review_sha256,
            'runtime_review_sha256': args.reviewed_runtime_review_sha256,
            **(resumed.evidence(plan.attempt) if resumed else {})}})
        for sig in (signal.SIGINT, signal.SIGTERM):
            signals[sig] = signal.signal(sig, cancel)
        phase = 'token'
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        channel, args.token_fd = args.token_fd, None
        token = adapter.token_from_pipe(channel, timeout=2)
        phase = 'runtime_construction'
        config = tempfile.TemporaryDirectory(prefix='cryptkeep-cutover-cli-')
        transport = DockerTransport(plan.cli_sha256, Path(config.name).resolve(strict=True), authorized=True)
        runtime = adapter.PinnedRuntimeAdapter(transport, pins, service_token=token, enabled=True)
        token = None
        runner = install.Installer(DockerInstallBackend(plan, ROOT, enabled=True), receipt)
        phase, actions = 'cutover', True
        result = runner.run(plan, authorized=True, runtime=runtime, startup_authorized=True, prepared=prepared)
        if interrupted:
            install.refuse()
        if not (result.get('running_update_complete') is True and result.get('receipt_complete') is True
                and result.get('query_passed') is True and result.get('prepared_ids_preserved') is True):
            print(json.dumps({'state': 'INCOMPLETE', 'failure_phase': phase, 'actions_executed': actions,
                'attempt_reserved': reserved, 'receipt': str(destination / 'receipt.jsonl'), **_summary(result)}))
            return 1
        phase = 'result_publication'
        raw = install.canonical({'provisional': True, 'result': _summary(result),
                                 'manifest_sha256': plan.manifest_sha256})
        remaining = runner.work_end - runner.clock()
        if remaining <= 0 or runner.executor.call(_publish, (directory, raw), min(2, remaining)) is not True:
            install.refuse()
        phase = 'receipt_commit'
        runner._record('cutover_result_committed', evidence={'sha256': hashlib.sha256(raw).hexdigest()})
        print(json.dumps({'state': 'READY_FOR_INDEPENDENT_REVIEW', 'actions_executed': True,
            'attempt_reserved': True, 'receipt': str(destination / 'receipt.jsonl'), **_summary(result)}))
        return 0
    except (Exception, KeyboardInterrupt):
        if (runner is not None and runner.used and not getattr(runner, 'recovering', False)
                and (getattr(runner, 'quiesced', ()) or getattr(runner, 'quiesce_pending', ()))):
            runner.recovering = True
            try:
                runner._record('cutover_entrypoint_failed_before_recovery', evidence={'phase': phase})
            except Exception:
                pass
            try:
                recovered = runner._rollback()
            except Exception:
                recovered = False
            result = {'rollback_verified': recovered, 'running_update_complete': False,
                'query_attempted': runner.query_attempted, 'query_passed': False,
                'receipt_complete': runner.receipt_complete,
                'unresolved_quiesce': sorted(runner.quiesce_pending),
                'unresolved_restart': sorted(runner.restart_pending),
                'unresolved_replacement_start': sorted(runner.runtime_start_pending),
                'unresolved_replacement_cleanup': sorted(runner.replacement_cleanup_pending)}
        print(json.dumps({'state': 'INCOMPLETE', 'reason': 'cutover_refused', 'failure_phase': phase,
            'actions_executed': actions, 'attempt_reserved': reserved,
            'receipt': str(destination / 'receipt.jsonl') if receipt is not None else None, **_summary(result)}))
        return 1
    finally:
        token = None
        for sig, handler in signals.items():
            signal.signal(sig, handler)
        if runtime is not None:
            runtime.close()
        if args.execute_cutover and args.token_fd is not None and args.token_fd > 2:
            try:
                os.close(args.token_fd)
            except OSError:
                pass
        if receipt is not None:
            receipt.close()
        if directory is not None:
            os.close(directory)
        if config is not None:
            config.cleanup()
        if lock is not None:
            os.close(lock)


if __name__ == '__main__':
    import sys
    sys.exit(main())
