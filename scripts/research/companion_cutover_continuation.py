"""Offline-reviewed continuation of an exact pre-start failure, never a retry loop."""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat

from scripts.research import companion_installer as install
from scripts.research import companion_network_configuration as network
from scripts.research import companion_prepare as preparation

CONSUMERS = tuple('scripts/research/' + name + '.py' for name in (
    'companion_cutover', 'companion_cutover_continuation', 'companion_runtime_adapter',
    'companion_existing_controller', 'companion_installer', 'companion_staged_update',
    'companion_docker_transport', 'companion_install_docker', 'companion_prepare',
    'companion_network_configuration',
))


def consumer_paths(plan):
    return CONSUMERS + (("scripts/research/companion_worker_shutdown.py",)
                        if plan.worker_shutdown else ())


@dataclass(frozen=True)
class Continuation:
    execution_id: str
    review_sha256: str
    prior_receipt_sha256: str

    def evidence(self, preparation_attempt):
        return {'execution_id': self.execution_id, 'preparation_attempt': preparation_attempt,
                'continuation_review_sha256': self.review_sha256,
                'prior_receipt_sha256': self.prior_receipt_sha256}


def prior_receipt(root, parts, attempt):
    """Read only the fixed original receipt, without following any symlink."""
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        preparation._directory(directory)
        for part in (*parts, attempt):
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
            preparation._directory(directory)
        fd = os.open('receipt.jsonl', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size > 65_536):
                install.refuse()
            raw = stream.read(65_537)
        if not raw or len(raw) > 65_536:
            install.refuse()
        return raw
    finally:
        os.close(directory)


def load(args, plan, prepared, root, parts, read):
    path = getattr(args, 'continuation_review', None)
    trusted = getattr(args, 'reviewed_continuation_review_sha256', None)
    if path is None and trusted is None:
        return None
    if (path is None or type(trusted) is not str or not install.ID.fullmatch(trusted)
            or not plan.staged or not plan.running_storage or not plan.network_bindings):
        install.refuse()
    raw = read(path, 65_536)
    if hashlib.sha256(raw).hexdigest() != trusted:
        install.refuse()
    record = json.loads(raw, object_pairs_hook=install._unique)
    keys = {'schema', 'decision', 'reviewer', 'execution_id', 'manifest_sha256',
            'preparation_evidence_sha256', 'preparation_review_sha256', 'runtime_review_sha256',
            'prepared_ids', 'prior_receipt_sha256', 'consumer_sha256'}
    if (type(record) is not dict or set(record) != keys
            or record['schema'] != 'companion-prestart-continuation-v1'
            or record['decision'] not in {'ACCEPTED', 'ACCEPTED_WITH_RISK'}
            or type(record['reviewer']) is not str or not record['reviewer'].strip()
            or type(record['execution_id']) is not str
            or not install.ATTEMPT.fullmatch(record['execution_id'])
            or record['execution_id'] == plan.attempt
            or record['manifest_sha256'] != plan.manifest_sha256
            or record['preparation_evidence_sha256'] != prepared.evidence_sha256
            or record['preparation_review_sha256'] != args.reviewed_preparation_review_sha256
            or record['runtime_review_sha256'] != args.reviewed_runtime_review_sha256
            or record['prepared_ids'] != [row.id for row in prepared.replacements]
            or type(record['prior_receipt_sha256']) is not str
            or not install.ID.fullmatch(record['prior_receipt_sha256'])
            or type(record['consumer_sha256']) is not dict
            or set(record['consumer_sha256']) != set(consumer_paths(plan))):
        install.refuse()
    for name, digest in record['consumer_sha256'].items():
        if (type(digest) is not str or not install.ID.fullmatch(digest)
                or hashlib.sha256(read(Path(root) / name)).hexdigest() != digest):
            install.refuse()
    prior = prior_receipt(root, parts, plan.attempt)
    if hashlib.sha256(prior).hexdigest() != record['prior_receipt_sha256']:
        install.refuse()
    rows = [json.loads(line, object_pairs_hook=install._unique) for line in prior.splitlines()]
    expected = [
        {'phase': 'cutover_inputs_bound', 'installation_evidence': {
            'manifest_sha256': plan.manifest_sha256,
            'preparation_evidence_sha256': prepared.evidence_sha256,
            'preparation_review_sha256': args.reviewed_preparation_review_sha256,
            'runtime_review_sha256': args.reviewed_runtime_review_sha256}},
        {'phase': 'installation_reserved', 'installation_evidence': {
            'startup_authorized': True, 'deferred_startup_policies': list(plan.deferred_startup_policies),
            'network_contract': network.CONTRACT, 'network_connectivity_verified': False}},
        {'phase': 'runtime_operation_intended', 'installation_evidence': {'operation': 'staged_checks'}},
        {'phase': 'installation_failed', 'installation_evidence': {'stage': 'staged_preflight'}},
    ]
    if install.canonical(rows) != install.canonical(expected):
        install.refuse()
    return Continuation(record['execution_id'], trusted, record['prior_receipt_sha256'])
