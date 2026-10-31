"""Two separately authorized phases, separated by external real-ID review.

This module supplies no CLI, approvals, pins or automatic retry. Preparation
does not interrupt originals. A failed cutover consumes the prepared evidence;
recovery may remove its owned replacements rather than recreate reviewed IDs.
"""
from dataclasses import asdict, dataclass
import hashlib
import json

from scripts.research import companion_existing_controller as core
from scripts.research import companion_installer as install


def _read(raw):
    if type(raw) is not bytes or len(raw) > 1_048_576:
        install.refuse()
    return json.loads(raw, object_pairs_hook=install._unique)


def _rows(plan, evidence):
    if (set(evidence) != {"schema", "state", "manifest_sha256", "attempt", "replacements"}
            or evidence["schema"] != "companion-staged-preparation-v1"
            or evidence["state"] != "READY_FOR_INDEPENDENT_REVIEW"
            or evidence["manifest_sha256"] != plan.manifest_sha256
            or evidence["attempt"] != plan.attempt):
        install.refuse()
    rows = tuple(install.Snapshot.from_record(r) for r in evidence["replacements"])
    if (tuple(r.name for r in rows) != tuple(plan.staged_name(n) for n in install.APPS)
            or len({r.id for r in rows}) != 4
            or {r.id for r in rows}.intersection(r.id for r in plan.baseline)):
        install.refuse()
    for row in rows:
        if (not install.ID.fullmatch(row.id) or not install.IMAGE.fullmatch(row.image)
                or not install.ID.fullmatch(row.metadata) or not install.ID.fullmatch(row.foundation)
                or row.state != "created" or row.started not in core.NEVER_STARTED
                or type(row.restarts) is not int or row.restarts != 0 or row.policy != "no"
                or row.attempt != plan.attempt or len(row.configured_networks) != 1):
            install.refuse()
        install._network_contract(row, dict(plan.network_bindings))
    return rows


@dataclass(frozen=True)
class ReviewedPreparation:
    """Load only with an externally supplied review hash, never self-generated."""

    manifest_sha256: str
    evidence_sha256: str
    replacements: tuple[install.Snapshot, ...]

    @classmethod
    def load(cls, evidence_raw, review_raw, trusted_review_sha256, plan):
        try:
            if (not plan.staged or not install.ID.fullmatch(trusted_review_sha256)
                    or hashlib.sha256(review_raw).hexdigest() != trusted_review_sha256):
                install.refuse()
            review, evidence = _read(review_raw), _read(evidence_raw)
            evidence_hash = hashlib.sha256(evidence_raw).hexdigest()
            if (set(review) != {"schema", "decision", "reviewer", "manifest_sha256", "evidence_sha256"}
                    or review["schema"] != "companion-preparation-review-v1"
                    or review["decision"] not in {"ACCEPTED", "ACCEPTED_WITH_RISK"}
                    or type(review["reviewer"]) is not str or not review["reviewer"].strip()
                    or review["manifest_sha256"] != plan.manifest_sha256
                    or review["evidence_sha256"] != evidence_hash):
                install.refuse()
            return cls(plan.manifest_sha256, evidence_hash, _rows(plan, evidence))
        except Exception:
            install.refuse()


def bind(runner, reviewed):
    if (not isinstance(reviewed, ReviewedPreparation)
            or reviewed.manifest_sha256 != runner.plan.manifest_sha256):
        install.refuse()
    evidence = {"schema": "companion-staged-preparation-v1", "state": "READY_FOR_INDEPENDENT_REVIEW",
                "manifest_sha256": reviewed.manifest_sha256, "attempt": runner.plan.attempt,
                "replacements": [asdict(r) for r in reviewed.replacements]}
    rows = _rows(runner.plan, evidence)
    runner.staged_current = dict(zip(install.APPS, rows))
    runner.known_replacement_ids = {r.id for r in rows}
    runner.images = {name: row.image for name, row in runner.staged_current.items()}


def _originals(runner, rows):
    if any(rows.get(r.name) != r for r in runner.plan.baseline):
        install.refuse()


def _stages(runner, rows):
    if any(rows.get(r.name) != r for r in runner.staged_current.values()):
        install.refuse()
    if {r.id for r in rows.values() if r.attempt == runner.plan.attempt} != runner.known_replacement_ids:
        install.refuse()


def cleanup_unpromoted(runner):
    complete = True
    for name, expected in reversed(tuple(runner.staged_current.items())):
        try:
            rows = runner._rows(recovery=True)
            actual = next((r for r in rows.values() if r.id == expected.id), None)
            # The existing rollback handles promoted resources at their final names.
            if actual is None or actual.name == name:
                continue
            runner.replacement_cleanup_pending.add(name)
            if actual != expected:
                install.refuse()
            runner._recovery_record("remove_staged_intended", name)
            runner._call("remove_staged", name, asdict(actual), recovery=True)
            if any(r.id == actual.id for r in runner._rows(recovery=True).values()):
                install.refuse()
            runner.replacement_cleanup_pending.remove(name)
        except Exception:
            complete = False
    return complete


def prepare(runner, plan, *, authorized=False):
    if (authorized is not True or runner.used or not isinstance(plan, install.Plan)
            or not plan.staged or not plan.manifest_sha256):
        install.refuse()
    runner._initialize(plan, None, preparation=True)
    runner.staged_current = {}
    evidence = None
    success = False
    stage = "preparation_reservation"
    cleaned = False
    try:
        runner._record("staged_preparation_reserved", evidence={"startup_authorized": False})
        stage = "preparation_baseline"
        baseline = runner._rows()
        _originals(runner, baseline)
        if (any(plan.staged_name(n) in baseline or plan.rollback_name(n) in baseline for n in install.APPS)
                or any(r.attempt == plan.attempt for r in baseline.values())):
            install.refuse()
        stage = "preparation_build"
        if runner._call("prepare") is not True:
            install.refuse()
        for name in install.APPS:
            image = runner._call("build", name)
            if type(image) is not str or not install.IMAGE.fullmatch(image):
                install.refuse()
            runner.images[name] = image
            if runner._rows() != baseline:
                install.refuse()
        for name in install.APPS:
            stage = "staged_creation"
            _originals(runner, runner._rows())
            _stages(runner, runner._rows())
            runner._record("create_staged_intended", name)
            runner.create_pending.add(name)
            cid = runner._call("create_staged", name, runner.images[name])
            if type(cid) is not str or not install.ID.fullmatch(cid) or cid in runner.known_replacement_ids:
                install.refuse()
            runner.known_replacement_ids.add(cid)
            rows = runner._rows()
            row = rows.get(plan.staged_name(name))
            if row is None or row.id != cid or row.image != runner.images[name]:
                install.refuse()
            # Only an acknowledged ID whose immutable created snapshot was checked
            # is eligible for cleanup. Failed/unknown creation is not adopted.
            candidate = {**runner.staged_current, name: row}
            if (row.state != "created" or row.started not in core.NEVER_STARTED
                    or row.restarts != 0 or row.policy != "no" or row.attempt != plan.attempt):
                install.refuse()
            runner.staged_current = candidate
            runner.create_pending.remove(name)
            stage = "staged_source_verification"
            if runner._call("verify_staged_sources", name, asdict(row)) is not True:
                install.refuse()
            _originals(runner, runner._rows())
            _stages(runner, runner._rows())
        evidence = {"schema": "companion-staged-preparation-v1", "state": "READY_FOR_INDEPENDENT_REVIEW",
                    "manifest_sha256": plan.manifest_sha256, "attempt": plan.attempt,
                    "replacements": [asdict(runner.staged_current[n]) for n in install.APPS]}
        _rows(plan, evidence)
        runner._record("staged_preparation_complete", evidence=evidence)
        success = True
    except Exception:
        runner.recovering = True
        try:
            runner._record("staged_preparation_failed", evidence={"stage": stage})
        except Exception:
            pass
        cleaned = cleanup_unpromoted(runner)
        try:
            rows = runner._rows(recovery=True)
            _originals(runner, rows)
            cleaned = (cleaned and not runner.create_pending and not runner.replacement_cleanup_pending
                       and not any(r.attempt == plan.attempt for r in rows.values()))
        except Exception:
            cleaned = False
    return {"state": "READY_FOR_INDEPENDENT_REVIEW" if success else "INCOMPLETE",
            "failure_stage": None if success else stage, "preparation_evidence": evidence if success else None,
            "services_started": False, "originals_interrupted": False,
            "cleanup_verified": cleaned, "unresolved_creation": sorted(runner.create_pending),
            "unresolved_cleanup": sorted(runner.replacement_cleanup_pending),
            "receipt_complete": runner.receipt_complete}


def preflight(runner, rows):
    _originals(runner, rows)
    _stages(runner, rows)
    # Review can take arbitrarily long. Revalidate CLI/engine, frozen sources
    # and baseline image prerequisites without building or changing resources.
    if runner._call("prepare") is not True:
        install.refuse()
    for name, row in runner.staged_current.items():
        if runner._call("verify_staged_sources", name, asdict(row)) is not True:
            install.refuse()
    expected = {r.name: runner._runtime_container(r) for r in runner.plan.baseline[:3]}
    expected.update({name: runner._runtime_container(row) for name, row in runner.staged_current.items()})
    if not core._all_true(runner._runtime_call("staged_checks", expected, cap=60),
                          core.COMPATIBILITY - {"recipient_bindings"}):
        install.refuse()
    if not core._all_true(runner._runtime_call("storage_checks"), {"postgres", "qdrant", "minio", "namespaces"}):
        install.refuse()
    current = runner._rows()
    _originals(runner, current)
    _stages(runner, current)


def activate(runner, name):
    expected = runner.staged_current[name]
    for method, args in (("disconnect_staged", ()),
                         ("rename_staged", (name,)), ("connect_staged", ())):
        rows = runner._rows()
        if rows.get(expected.name) != expected:
            install.refuse()
        runner._record(method + "_intended", name)
        runner._call(method, name, asdict(expected), *args)
        rows = runner._rows()
        after = next((r for r in rows.values() if r.id == expected.id), None)
        if (after is None or after.stable() != expected.stable() or after.state != "created"
                or after.attempt != expected.attempt):
            install.refuse()
        expected = runner.staged_current[name] = after
    if expected.name != name:
        install.refuse()
