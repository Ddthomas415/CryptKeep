"""One-shot installation and optional bound-runtime verification.

The reviewed manifest hash is an external trust input, not an approval generated
by this tool. CLI v4 application remains refused. The optional running-storage
API requires separate startup authorization and externally reviewed runtime pins.
No trading, migrations or automatic recovery retries.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
import time

from scripts.research import companion_existing_controller as core
from scripts.research import companion_network_configuration as configuration
from scripts.research import companion_metadata_diagnostics as metadata_diagnostics
from scripts.research import companion_runtime_adapter as runtime_adapter

APPS = core.TARGETS[3:]
POLICIES = frozenset({"builder_local_only", "env_stdin_lossless", "image_provenance",
                      "recreation_complete", "sdk_startup_compatible", "source_imports_frozen"})
STARTUP_POLICIES = frozenset({"sdk_startup_compatible", "source_imports_frozen"})
STOPPED_POLICIES = POLICIES - STARTUP_POLICIES
ID = re.compile(r"[0-9a-f]{64}\Z")
IMAGE = re.compile(r"sha256:[0-9a-f]{64}\Z")
ATTEMPT = re.compile(r"[a-z0-9]{16,32}\Z")
OPTIONS = {"--publish", "--mount", "--user", "--workdir", "--entrypoint", "--health-cmd",
           "--health-interval", "--health-timeout", "--health-retries", "--label",
           "--memory", "--cpus", "--pids-limit", "--security-opt", "--cap-drop", "--log-driver"}


def refuse():
    raise core.Refused("installation_refused") from None


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def validate_quiesce_report(report):
    keys = {'schema', 'stage', 'command_attempted', 'command_acknowledged', 'confirmed'}
    if (type(report) is not dict or set(report) != keys
            or report['schema'] != 'companion-quiesce-report-v1'
            or any(type(report[k]) is not bool for k in keys - {'schema', 'stage'})
            or type(report['stage']) is not str):
        refuse()
    expected = {
        'target_validation': (False, False, False),
        'pre_observation': (False, False, False),
        'pre_state': (False, False, False),
        'signal_command': (True, False, False),
        'post_observation': (True, True, False),
        'exit_timeout': (True, True, False),
        'exit_verified': (True, True, True),
    }
    if expected.get(report['stage']) != tuple(report[k] for k in
            ('command_attempted', 'command_acknowledged', 'confirmed')):
        refuse()
    return report


def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            refuse()
        out[key] = value
    return out


@dataclass(frozen=True)
class Snapshot:
    name: str
    id: str
    image: str
    state: str
    started: str
    restarts: int
    policy: str
    metadata: str
    foundation: str
    networks: tuple[str, ...]
    attempt: str = ""
    configured_metadata: str = ""
    configured_networks: tuple[str, ...] = ()
    network_evidence: tuple[tuple[str, str, str], ...] = ()

    @classmethod
    def from_record(cls, row):
        return cls(**{**row, "networks": tuple(row["networks"]),
                      "configured_networks": tuple(row.get("configured_networks", ())),
                      "network_evidence": tuple(tuple(e) for e in row.get("network_evidence", ()))})

    def stable(self):
        return self.id, self.image, self.started, self.restarts, self.policy, self.foundation


@dataclass(frozen=True)
class Plan:
    attempt: str
    cli_sha256: str
    baseline: tuple[Snapshot, ...]
    applications: tuple[dict, ...]
    deferred_startup_policies: tuple[str, ...] = ()
    network_bindings: tuple[tuple[str, str], ...] = ()
    running_storage: bool = False
    staged: bool = False
    manifest_sha256: str = ""
    worker_shutdown: bool = False

    @classmethod
    def load(cls, raw, trusted_sha256):
        try:
            if (type(raw) is not bytes or len(raw) > 1_048_576 or type(trusted_sha256) is not str
                    or not ID.fullmatch(trusted_sha256) or hashlib.sha256(raw).hexdigest() != trusted_sha256):
                refuse()
            data = json.loads(raw, object_pairs_hook=_unique)
            worker_shutdown = data.get("schema") == "companion-worker-staged-update-v6"
            staged = data.get("schema") == "companion-staged-update-v5" or worker_shutdown
            running = data.get("schema") == "companion-running-storage-install-v4" or staged
            configured = data.get("schema") == "companion-configured-install-v3" or running
            keys = {"schema", "decision", "reviewer", "attempt", "cli_sha256", "policies", "baseline", "applications"}
            if configured:
                keys.add("network_contract")
            if (set(data) != keys
                    or data["schema"] not in {"companion-install-v1", "companion-stopped-install-v2", "companion-configured-install-v3", "companion-running-storage-install-v4", "companion-staged-update-v5", "companion-worker-staged-update-v6"}
                    or data["decision"] not in {"ACCEPTED", "ACCEPTED_WITH_RISK"}
                    or type(data["reviewer"]) is not str or not data["reviewer"]
                    or not ATTEMPT.fullmatch(data["attempt"]) or not ID.fullmatch(data["cli_sha256"])
                    or set(data["policies"]) != POLICIES):
                refuse()
            deferred = STARTUP_POLICIES if data["schema"] != "companion-install-v1" else frozenset()
            if any(data["policies"][key] is not (False if key in deferred else True) for key in POLICIES):
                refuse()
            bindings = {}
            if configured:
                contract = data["network_contract"]
                if (set(contract) != {"schema", "bindings", "connectivity_verified"}
                        or contract["schema"] != configuration.CONTRACT
                        or contract["connectivity_verified"] is not False):
                    refuse()
                bindings = contract["bindings"]
                configuration.validate_bindings(bindings)
            rows = tuple(Snapshot.from_record(r) for r in data["baseline"])
            if tuple(r.name for r in rows) != core.TARGETS or len({r.id for r in rows}) != 7:
                refuse()
            for row in rows:
                if (not ID.fullmatch(row.id) or not IMAGE.fullmatch(row.image)
                        or not ID.fullmatch(row.metadata) or not ID.fullmatch(row.foundation)
                        or row.state != ("running" if running else "exited") or row.policy != "no" or row.attempt
                        or type(row.restarts) is not int or row.restarts < 0
                        or type(row.started) is not str or len(row.networks) != 1):
                    refuse()
                _network_contract(row, bindings)
            apps = data["applications"]
            if tuple(a["name"] for a in apps) != APPS:
                refuse()
            for app in apps:
                metadata_key = "replacement_configured_metadata" if configured else "replacement_metadata"
                if (set(app) != {"name", "sources", "create_options", "command", "network_options", metadata_key}
                        or not ID.fullmatch(app[metadata_key])):
                    refuse()
                options = app["create_options"]
                if type(options) is not list or len(options) % 2 or len(options) > 128:
                    refuse()
                for flag, value in zip(options[::2], options[1::2]):
                    if (flag not in OPTIONS or type(value) is not str or not value
                            or any(c in value for c in "\0\r\n") or value.startswith("-")
                            or (flag == "--label" and value.startswith("cryptkeep.install-attempt="))):
                        refuse()
                    if flag == "--log-driver" and value != "local":
                        refuse()
                for flag, value in zip(app["network_options"][::2], app["network_options"][1::2]):
                    if flag not in {"--alias", "--ip", "--ip6", "--link-local-ip"} or type(value) is not str or not value or value.startswith("-") or any(c.isspace() for c in value):
                        refuse()
                if len(app["network_options"]) % 2 or not app["network_options"]:
                    refuse()
                if type(app["command"]) is not list or any(type(a) is not str or "\0" in a for a in app["command"]):
                    refuse()
                if worker_shutdown:
                    from scripts.research.companion_worker_shutdown import replacement_command
                    if (app["command"] != replacement_command(app["name"])
                            or "--entrypoint" in options[::2]):
                        refuse()
                if type(app["sources"]) is not list or not app["sources"]:
                    refuse()
                destinations = set()
                for source in app["sources"]:
                    if (set(source) != {"local", "destination", "sha256"}
                            or not re.fullmatch(r"phase1_research_copilot/(?:[A-Za-z0-9_]+/)+[A-Za-z0-9_]+\.py", source["local"])
                            or source["destination"] != "/app/" + source["local"].split("/", 1)[1]
                            or not ID.fullmatch(source["sha256"]) or source["destination"] in destinations):
                        refuse()
                    destinations.add(source["destination"])
                from scripts.research import companion_runtime_adapter as adapter
                required = adapter.required_app_sources(app["name"])
                if not required.issubset(destinations):
                    refuse()
            return cls(data["attempt"], data["cli_sha256"], rows, tuple(apps), tuple(sorted(deferred)), tuple(sorted(bindings.items())), running, staged, trusted_sha256, worker_shutdown)
        except Exception:
            refuse()

    def rollback_name(self, name):
        return name + "-rollback-" + self.attempt

    def staged_name(self, name):
        return name + "-staged-" + self.attempt


def _network_contract(row, bindings):
    if not bindings:
        if (any(not ID.fullmatch(n) for n in row.networks) or row.configured_metadata
                or row.configured_networks or row.network_evidence):
            refuse()
        return
    if not ID.fullmatch(row.configured_metadata) or len(row.networks) != len(row.network_evidence):
        refuse()
    expected, observed = [], []
    for name, identity, status in row.network_evidence:
        if bindings.get(name) != identity or status not in {"reported_id", "configured_only"}:
            refuse()
        expected.append(identity)
        observed.append(identity if status == "reported_id" else "")
    if (row.configured_networks != tuple(sorted(expected)) or row.networks != tuple(sorted(observed))
            or len(set(expected)) != len(expected)):
        refuse()


class Installer:
    """Backend methods execute in bounded children; parent holds public state only."""

    def __init__(self, backend, receipt, *, executor=None, clock=time.monotonic):
        self.backend, self.receipt = backend, receipt
        self.executor, self.clock = executor or core.ProcessExecutor(), clock
        self.used = False

    def _call(self, method, *args, recovery=False):
        remaining = (self.end if recovery else self.work_end) - self.clock()
        if remaining <= 0:
            refuse()
        return self.executor.call(getattr(self.backend, method), args, min(60, remaining))

    def _runtime_call(self, method, *args, cap=30, recovery=False):
        if method not in {"inventory", "compatibility", "configured_compatibility", "recipient_checks", "staged_checks", "storage_checks", "start", "health_checks", "explain", "verify_evidence", "verify_evidence_diagnostic"}:
            refuse()
        self._record("runtime_operation_intended", evidence={"operation": method})
        remaining = (self.end if recovery else self.work_end) - self.clock()
        if remaining <= 0:
            refuse()
        return self.executor.call(getattr(self.runtime, method), args, min(cap, remaining))

    def _record(self, phase, name=None, evidence=None):
        record = {"phase": phase}
        if name in APPS:
            record["target"] = name
        if evidence is not None:
            record["installation_evidence"] = evidence
        deadline = self.end
        if self.plan.running_storage and not self.recovering:
            deadline = self.work_end
        remaining = deadline - self.clock()
        if remaining <= 0:
            refuse()
        try:
            self.executor.call(self.receipt.write, (record,), min(2, remaining))
        except Exception:
            self.receipt_complete = False
            raise

    def _recovery_record(self, phase, name):
        try:
            self._record(phase, name)
        except Exception:
            self.receipt_complete = False

    def _rows(self, recovery=False):
        raw = (self._call("inventory", tuple(sorted(self.known_replacement_ids)), recovery=recovery)
               if self.plan.staged else self._call("inventory", recovery=recovery))
        rows = tuple(Snapshot.from_record(r) for r in raw)
        if len({r.id for r in rows}) != len(rows) or len({r.name for r in rows}) != len(rows):
            refuse()
        for row in rows:
            if (not ID.fullmatch(row.id) or not IMAGE.fullmatch(row.image)
                    or not ID.fullmatch(row.metadata) or not ID.fullmatch(row.foundation)
                    or type(row.restarts) is not int or row.restarts < 0
                    or type(row.started) is not str or type(row.name) is not str):
                refuse()
            _network_contract(row, dict(self.plan.network_bindings))
        result = {r.name: r for r in rows}
        if self.plan.running_storage:
            self._storage_unchanged(result)
        return result

    def _storage_unchanged(self, rows):
        if any(rows.get(before.name) != before for before in self.plan.baseline[:3]):
            refuse()

    @staticmethod
    def _runtime_container(row):
        return core.Container(row.name, row.id, row.image, row.state, row.started,
                              row.restarts, row.policy, row.metadata)

    def _runtime_observation(self, recovery=False):
        raw = self._runtime_call("inventory", recovery=recovery)
        if not isinstance(raw, dict):
            refuse()
        rows = {}
        for name, row in raw.items():
            if isinstance(row, dict) and set(row) == {"__container__"}:
                fields = row["__container__"]
                if not isinstance(fields, dict) or set(fields) != set(core.Container.__dataclass_fields__):
                    refuse()
                row = core.Container(**fields)
            if (not isinstance(row, core.Container) or row.name != name
                    or not ID.fullmatch(row.id) or not IMAGE.fullmatch(row.image)
                    or not ID.fullmatch(row.preservation_digest)):
                refuse()
            rows[name] = row
        if len({row.id for row in rows.values()}) != len(rows):
            refuse()
        return rows

    def _runtime_inventory(self, expected):
        rows = self._runtime_observation()
        if (not set(core.TARGETS).issubset(rows)
                or any(rows[name] != self._runtime_container(expected[name]) for name in core.TARGETS)):
            refuse()
        return rows

    def _runtime_guard(self):
        rows = self._rows()
        if any(rows.get(name) != self.runtime_expected[name] for name in core.TARGETS):
            refuse()
        for before in self.plan.baseline[3:]:
            self._original(rows, before, detached=True)
        self._runtime_inventory(rows)
        return rows

    @staticmethod
    def _replacement_transition(row, before, state):
        return (row is not None and row.name == before.name and row.id == before.id
                and row.image == before.image and row.state == state
                and row.policy == "no" and row.attempt == before.attempt
                and row.foundation == before.foundation and row.restarts == before.restarts
                and row.configured_metadata == before.configured_metadata
                and row.configured_networks == before.configured_networks
                and row.started not in core.NEVER_STARTED
                and (state != "exited" or row.started == before.started))

    def _verify_running_update(self, expected):
        # The caller supplies an independently bound adapter. Observed IDs are
        # compared with its pins; they never become a generated trust manifest.
        self.runtime_expected = {name: expected[name] for name in core.TARGETS}
        runtime_rows = self._runtime_inventory(expected)
        try:
            checks = (self._runtime_call("configured_compatibility", runtime_rows, dict(self.plan.network_bindings), cap=60)
                      if self.plan.staged else self._runtime_call("compatibility", runtime_rows, cap=60))
        except Exception:
            self._record("runtime_compatibility_exception", evidence={"outcome": "exception_or_timeout"})
            raise
        precondition = recipient_diagnostic = None
        if type(checks) is dict and set(checks) in (
                {"checks", "precondition"}, {"checks", "precondition", "recipient_diagnostic"}):
            candidate = checks["precondition"]
            if (type(candidate) is dict and set(candidate) == {"predicate", "target"}
                    and type(candidate["predicate"]) is str
                    and candidate["predicate"] in {"baseline", "authorization", "cli", "identity", "image",
                                                   "preservation", "staged_state", "complete"}
                    and (candidate["target"] is None or type(candidate["target"]) is str
                         and candidate["target"] in core.TARGETS)):
                precondition = dict(candidate)
                recipient_diagnostic = runtime_adapter.sanitize_binding_diagnostic(
                    checks.get("recipient_diagnostic"))
                checks = checks["checks"]
        self._record("runtime_compatibility_checks", evidence={
            "shape_valid": type(checks) is dict and set(checks) == core.COMPATIBILITY,
            "false_meaning": "not_established_or_not_evaluated",
            "precondition": precondition,
            "recipient_diagnostic": recipient_diagnostic,
            "checks": {key: type(checks) is dict and checks.get(key) is True
                       for key in sorted(core.COMPATIBILITY)}})
        if not core._all_true(checks, core.COMPATIBILITY):
            refuse()
        self._runtime_guard()
        if not core._all_true(self._runtime_call("storage_checks"), {"postgres", "qdrant", "minio", "namespaces"}):
            refuse()
        for name in APPS:
            before = self._runtime_guard()[name]
            self._record("replacement_start_intended", name)
            self.runtime_start_pending.add(name)
            self._runtime_call("start", before.id, cap=15)
            after = self._rows().get(name)
            if not self._replacement_transition(after, before, "running"):
                refuse()
            self.replacement_started[name] = after
            self.runtime_expected[name] = after
            self.runtime_start_pending.remove(name)
            self._record("replacement_start_confirmed", name)
        self._runtime_guard()
        if self.plan.staged and not core._all_true(self._runtime_call("recipient_checks"), {"recipient_bindings"}):
            refuse()
        if not core._all_true(self._runtime_call("health_checks"), set(APPS)):
            refuse()
        self._runtime_guard()
        self._record("query_intended")
        self.query_attempted = True
        probe = self._runtime_call("explain", cap=45)
        from dashboard.services.views._explain_diagnostics import sanitize_events
        self.query_diagnostics = sanitize_events(probe.get("diagnostics")) if isinstance(probe, dict) else []
        self._record("query_diagnostics", evidence={"events": self.query_diagnostics})
        core.explanation_gates(probe)
        method = ("verify_evidence_diagnostic" if callable(getattr(self.runtime, "verify_evidence_diagnostic", None))
                  else "verify_evidence")
        try:
            evidence = self._runtime_call(method, probe["raw"], cap=10)
        except Exception:
            self._record("evidence_verification_checks", evidence={
                "outcome": "exception_or_timeout", "shape_valid": False,
                "checks": dict.fromkeys(sorted(core.EVIDENCE), False),
                "diagnostic": {"stage": "parent_boundary", "code": "unavailable"},
                "false_meaning": "not_established_or_not_evaluated"})
            raise
        diagnostic = {"stage": "legacy_result", "code": "unavailable"}
        if (method == "verify_evidence_diagnostic"
                or (type(evidence) is dict and set(evidence) == {"checks", "diagnostic"})):
            from scripts.research.companion_evidence_checks import diagnostic_result_valid
            if diagnostic_result_valid(evidence):
                diagnostic = dict(evidence["diagnostic"])
                evidence = evidence["checks"]
            else:
                diagnostic = {"stage": "parent_boundary", "code": "invalid"}
                evidence = None
        shape_valid = (type(evidence) is dict and set(evidence) == core.EVIDENCE
                       and all(type(v) is bool for v in evidence.values()))
        checks = {key: evidence.get(key) is True if type(evidence) is dict else False
                  for key in sorted(core.EVIDENCE)}
        self._record("evidence_verification_checks", evidence={
            "outcome": "complete" if shape_valid else "invalid_shape",
            "shape_valid": shape_valid, "checks": checks,
            "diagnostic": diagnostic,
            "false_meaning": "not_established_or_not_evaluated"})
        if not core._all_true(evidence, core.EVIDENCE):
            refuse()
        self._runtime_guard()
        self.query_verified = True

    def _remove_started_replacement(self, current):
        owned = self.replacement_started.get(current.name)
        if current != owned or current.name in self.runtime_start_pending:
            refuse()
        self._recovery_record("replacement_quiesce_intended", current.name)
        self.replacement_cleanup_pending.add(current.name)
        if self._call("quiesce_replacement", asdict(current), recovery=True) is not True:
            refuse()
        stopped = self._rows(recovery=True).get(current.name)
        if not self._replacement_transition(stopped, current, "exited"):
            refuse()
        self._recovery_record("remove_stopped_replacement_intended", current.name)
        self._call("remove_stopped_replacement", asdict(stopped), recovery=True)
        if any(row.id == current.id for row in self._runtime_observation(recovery=True).values()):
            refuse()
        self.replacement_cleanup_pending.remove(current.name)

    def _quiesce_applications(self):
        for before in reversed(self.plan.baseline[3:]):
            rows = self._rows()
            self._storage_unchanged(rows)
            if rows.get(before.name) != before:
                refuse()
            self._record("quiesce_intended", before.name)
            # A lost acknowledgment is not proof that we own an interruption.
            self.quiesce_pending.add(before.name)
            report = None
            if callable(getattr(self.backend, 'quiesce_report', None)):
                report = validate_quiesce_report(self._call('quiesce_report', before.id))
                if report['confirmed'] is not True:
                    self._record('quiesce_diagnostic', before.name, report)
                    refuse()
            elif self._call("quiesce", before.id) is not True:
                refuse()
            try:
                rows = self._rows()
                self._storage_unchanged(rows)
                self._original(rows, before)
            except Exception:
                if report is not None:
                    self._record('quiesce_diagnostic', before.name, report)
                raise
            self.quiesced.add(before.name)
            self.quiesce_pending.remove(before.name)
            if report is not None:
                self._record('quiesce_diagnostic', before.name, report)
            self._record("quiesce_confirmed", before.name)

    def _restored_running_original(self, row, before):
        return (row is not None and row.name == before.name and row.id == before.id
                and row.image == before.image and row.state == "running"
                and row.policy == before.policy and row.foundation == before.foundation
                and row.restarts == before.restarts and not row.attempt
                and row.started not in (*core.NEVER_STARTED, before.started)
                and row.configured_metadata == before.configured_metadata
                and row.configured_networks == before.configured_networks)

    def _replacement_checks(self, row, before):
        app = next(a for a in self.plan.applications if a["name"] == before.name)
        if row is None:
            return {"present": False}
        if self.plan.network_bindings:
            metadata_match = row.configured_metadata == app["replacement_configured_metadata"]
            network_match = row.configured_networks == before.configured_networks
        else:
            metadata_match = row.metadata == app["replacement_metadata"]
            network_match = row.networks == before.networks
        return {"present": True, "new_identity": row.id != before.id,
                "created": row.state == "created", "never_started": row.started in core.NEVER_STARTED,
                "zero_restarts": row.restarts == 0, "restart_disabled": row.policy == "no",
                "image_matches": row.image == self.images[before.name],
                "attempt_matches": row.attempt == self.plan.attempt,
                "metadata_matches": metadata_match, "network_ids_match": network_match}

    def _replacement(self, row, before):
        return all(self._replacement_checks(row, before).values())

    def _metadata_diagnostic(self, replacement, before, checks):
        detail = metadata_diagnostics.unavailable()
        if all(value for key, value in checks.items() if key != 'metadata_matches'):
            try:
                observed = replacement.configured_metadata if self.plan.network_bindings else replacement.metadata
                detail = metadata_diagnostics.validate_report(self._call(
                    'replacement_diagnostics', before.name, replacement.id, observed))
                if detail.get('available') is True and detail['aggregate_matches'] is not False:
                    detail = metadata_diagnostics.unavailable()
            except Exception:
                pass  # Diagnostics cannot bypass the original refusal or expose errors.
        self._record('replacement_metadata_diagnostic', before.name, evidence=detail)

    def _original(self, rows, before, *, detached=False):
        row = rows.get(self.plan.rollback_name(before.name)) or rows.get(before.name)
        if row is None:
            refuse()
        configured = bool(self.plan.network_bindings)
        networks = row.configured_networks if configured else row.networks
        expected = before.configured_networks if configured else before.networks
        if (row is None or row.stable() != before.stable() or row.state != "exited"
                or row.attempt or networks != (() if detached else expected)):
            refuse()
        if not detached and ((row.configured_metadata != before.configured_metadata) if configured else
                             (row.metadata != before.metadata)):
            refuse()
        return row

    def _rollback(self):
        self.recovering = True
        complete = True
        if self.plan.staged:
            from scripts.research import companion_staged_update as staged
            complete = staged.cleanup_unpromoted(self)
        for before in reversed(self.plan.baseline[3:]):
            try:
                rows = self._rows(recovery=True)
                if self.plan.running_storage:
                    self._storage_unchanged(rows)
                    if before.name in self.quiesce_pending:
                        complete = False
                        continue
                    if before.name not in self.quiesced:
                        if rows.get(before.name) != before:
                            refuse()
                        continue
                replacement = rows.get(before.name)
                if replacement is not None and replacement.id != before.id:
                    if (replacement.attempt != self.plan.attempt or replacement.image != self.images.get(before.name)
                            or replacement.restarts != 0):
                        refuse()
                    self.known_replacement_ids.add(replacement.id)
                    if (replacement.state == "created" and replacement.started in core.NEVER_STARTED):
                        self._recovery_record("remove_replacement_intended", before.name)
                        self._call("remove", replacement.id, recovery=True)
                    elif self.runtime is not None:
                        self._remove_started_replacement(replacement)
                    else:
                        refuse()
                    rows = self._rows(recovery=True)
                    if any(row.id == replacement.id for row in rows.values()):
                        refuse()
                    if before.name in self.runtime_start_pending:
                        self.runtime_start_pending.remove(before.name)
                        self._recovery_record("pending_start_resolved_by_resource_removal", before.name)
                original = self._original(rows, before, detached=not bool((rows.get(self.plan.rollback_name(before.name)) or rows.get(before.name)).networks))
                if original.name != before.name:
                    self._recovery_record("restore_name_intended", before.name)
                    self._call("rename", before.id, before.name, recovery=True)
                rows = self._rows(recovery=True)
                original = rows[before.name]
                if not original.networks:
                    self._recovery_record("restore_network_intended", before.name)
                    self._call("connect", before.name, recovery=True)
            except Exception:
                complete = False
        if self.plan.running_storage:
            # Dependency order, unlike the reverse-order teardown above.
            for before in self.plan.baseline[3:]:
                if before.name not in self.quiesced:
                    continue
                try:
                    earlier = self.plan.baseline[3:core.TARGETS.index(before.name)]
                    if any(r.name in self.quiesce_pending
                           or (r.name in self.quiesced and r.name not in self.restored) for r in earlier):
                        refuse()
                    rows = self._rows(recovery=True)
                    self._storage_unchanged(rows)
                    if any(rows.get(r.name) != self.restored.get(r.name, r) for r in earlier):
                        refuse()
                    self._original(rows, before)
                    self._recovery_record("restart_original_intended", before.name)
                    self.restart_pending.add(before.name)
                    if self._call("restart_original", before.id, recovery=True) is not True:
                        refuse()
                    after = self._rows(recovery=True).get(before.name)
                    if not self._restored_running_original(after, before):
                        refuse()
                    self.restored[before.name] = after
                    self.restart_pending.remove(before.name)
                except Exception:
                    complete = False
                    # Do not start dependents after their prerequisite failed.
                    break
        try:
            final = self._rows(recovery=True)
            self.rollback_exact_baseline = all(final.get(r.name) == r for r in self.plan.baseline)
            if self.plan.running_storage:
                self._storage_unchanged(final)
                complete = complete and not (self.quiesce_pending or self.runtime_start_pending
                                             or self.replacement_cleanup_pending or self.create_pending) and all(
                    final.get(before.name) == (self.restored.get(before.name)
                                              if before.name in self.quiesced else before)
                    and (before.name not in self.quiesced or before.name in self.restored)
                    for before in self.plan.baseline[3:])
                if self.runtime is not None:
                    observed = self._runtime_observation(recovery=True)
                    complete = complete and not self.known_replacement_ids.intersection(
                        row.id for row in observed.values()) and all(
                        observed.get(name) == self._runtime_container(final[name]) for name in core.TARGETS)
            elif self.plan.network_bindings:
                for before in self.plan.baseline[3:]:
                    complete = self._original(final, before).name == before.name and complete
                complete = complete and all(final.get(r.name) == r for r in self.plan.baseline[:3])
            else:
                complete = complete and self.rollback_exact_baseline
            complete = complete and not any(r.attempt == self.plan.attempt for r in final.values())
            if self.plan.network_bindings:
                self._record("rollback_checks_completed", evidence={
                    "configuration_restored": complete, "exact_baseline_restored": self.rollback_exact_baseline,
                    "network_connectivity_verified": False})
        except Exception:
            complete = False
        return complete

    def _initialize(self, plan, runtime, *, preparation=False):
        self.used = True
        self.plan, self.images = plan, {}
        self.runtime = runtime
        self.recovering = False
        self.replacement_started = {}
        self.runtime_start_pending, self.replacement_cleanup_pending = set(), set()
        self.create_pending, self.known_replacement_ids = set(), set()
        self.query_attempted = self.query_verified = False
        self.query_diagnostics = []
        self.receipt_complete = True
        self.rollback_exact_baseline = None
        self.quiesced, self.quiesce_pending, self.restored = set(), set(), {}
        self.restart_pending = set()
        self.end = self.clock() + (300 if preparation or not plan.running_storage else 600)
        self.work_end = self.end - (120 if preparation or not plan.running_storage else 180)

    def prepare_staged(self, plan, *, authorized=False):
        from scripts.research import companion_staged_update as staged
        return staged.prepare(self, plan, authorized=authorized)

    def run(self, plan, *, authorized=False, runtime=None, startup_authorized=False, prepared=None):
        if (authorized is not True or self.used or not isinstance(plan, Plan)
                or (runtime is not None and (not plan.running_storage or startup_authorized is not True))
                or (startup_authorized is not False and runtime is None)
                or (plan.staged and (runtime is None or prepared is None))
                or (not plan.staged and prepared is not None)):
            refuse()
        self._initialize(plan, runtime)
        if plan.staged:
            from scripts.research import companion_staged_update as staged
            staged.bind(self, prepared)
        changed = success = recovered = False
        evidence = None
        stage = "reservation"
        try:
            self._record("installation_reserved", evidence={"startup_authorized": runtime is not None,
                "deferred_startup_policies": list(plan.deferred_startup_policies),
                **({"network_contract": configuration.CONTRACT, "network_connectivity_verified": False}
                   if plan.network_bindings else {})})
            stage = "inventory_preflight"
            rows = self._rows()
            stage = "baseline_preflight"
            if (any(rows.get(r.name) != r for r in plan.baseline)
                    or (plan.running_storage and any(r.state != "running" for r in plan.baseline))
                    or any(plan.rollback_name(n) in rows for n in APPS)
                    or (not plan.staged and any(r.attempt == plan.attempt for r in rows.values()))):
                refuse()
            if plan.staged:
                stage = "staged_preflight"
                staged.preflight(self, rows)
            else:
                stage = "prepare"
                if self._call("prepare") is not True:
                    refuse()
                stage = "build"
                for name in APPS:
                    image = self._call("build", name)
                    if type(image) is not str or not IMAGE.fullmatch(image):
                        refuse()
                    self.images[name] = image
            stage = "inventory_recheck"
            if self._rows() != rows:
                refuse()
            if plan.running_storage:
                stage = "quiesce"
                changed = True
                self._quiesce_applications()
            stage = "replacement"
            for before in plan.baseline[3:]:
                if plan.running_storage:
                    current = self._rows()
                    self._storage_unchanged(current)
                    self._original(current, before)
                self._record("rename_intended", before.name)
                changed = True  # An uncertain operation may already have happened.
                self._call("rename", before.id, plan.rollback_name(before.name))
                self._original(self._rows(), before)
                self._record("detach_intended", before.name)
                self._call("disconnect", before.name)
                self._original(self._rows(), before, detached=True)
                if plan.staged:
                    stage = "staged_activation"
                    staged.activate(self, before.name)
                else:
                    self._record("create_intended", before.name)
                    stage = "create"
                    if runtime is not None:
                        self.create_pending.add(before.name)
                    self._call("create", before.name, self.images[before.name])
                stage = "replacement_inventory"
                replacement = self._rows().get(before.name)
                stage = "replacement_checks"
                checks = self._replacement_checks(replacement, before)
                self._record("replacement_checks", before.name, evidence={"checks": checks})
                if checks.get('metadata_matches') is False:
                    self._metadata_diagnostic(replacement, before, checks)
                if not all(checks.values()):
                    refuse()
                self.known_replacement_ids.add(replacement.id)
                self.create_pending.discard(before.name)
                stage = "source_verification"
                if self._call("verify_sources", before.name) is not True:
                    refuse()
                stage = "replacement"
            stage = "postconditions"
            final = self._rows()
            if any(final.get(r.name) != r for r in plan.baseline[:3]):
                refuse()
            for before in plan.baseline[3:]:
                self._original(final, before, detached=True)
                if not self._replacement(final.get(before.name), before):
                    refuse()
            if runtime is not None:
                stage = "runtime_verification"
                self._verify_running_update(final)
            evidence = {"attempt": plan.attempt, "startup_authorized": runtime is not None,
                **({"snapshot_phase": "installed_before_startup"} if runtime is not None else {}),
                **({"network_contract": configuration.CONTRACT, "network_connectivity_verified": False}
                   if plan.network_bindings else {}),
                "deferred_startup_policies": list(plan.deferred_startup_policies), "applications": [
                {"name": before.name, "original_id": before.id, "original_image": before.image,
                 "replacement_id": final[before.name].id, "replacement_image": final[before.name].image,
                 "metadata_sha256": final[before.name].metadata, "state": final[before.name].state,
                 **({"configured_metadata_sha256": final[before.name].configured_metadata,
                     "network_evidence": final[before.name].network_evidence}
                    if plan.network_bindings else {}),
                 "source_check": "verified_at_creation", "source_sha256": {
                     s["destination"]: s["sha256"] for s in next(a for a in plan.applications if a["name"] == before.name)["sources"]}}
                for before in plan.baseline[3:]],
                "storage": [{"name": r.name, "id": r.id, "image": r.image, "metadata_sha256": r.metadata}
                            for r in plan.baseline[:3]]}
            stage = "receipt_commit"
            self._record("installation_checks_passed_pending_return", evidence=evidence)
            success = True
        except Exception:
            self.recovering = True
            try:
                self._record("installation_failed", evidence={"stage": stage})
                if self.query_attempted:
                    self._record("query_failure_diagnostics", evidence={"events": self.query_diagnostics})
            except Exception:
                pass
        finally:
            if changed and not success:
                recovered = self._rollback()
        return {"state": "READY_FOR_INDEPENDENT_REVIEW" if success else "INCOMPLETE",
                "failure_stage": None if success else stage,
                "rollback_scope": ("application_configuration_and_running_state" if plan.running_storage
                                   else "configuration_only" if plan.network_bindings else "exact_selected_metadata"),
                "rollback_exact_baseline": self.rollback_exact_baseline,
                "network_connectivity_verified": False,
                "installed_stopped": success and runtime is None, "rollback_verified": recovered,
                "services_started": (None if self.restart_pending or self.runtime_start_pending
                                     else bool(self.restored or self.replacement_started)) if plan.running_storage else False,
                "startup_authorized": runtime is not None,
                "deferred_startup_policies": [] if success and self.query_verified else list(plan.deferred_startup_policies),
                **({"running_storage": True, "running_update_complete": success and self.query_verified,
                    "query_attempted": self.query_attempted, "query_passed": success and self.query_verified,
                    "rollback_service_health_verified": False,
                    "unresolved_quiesce": sorted(self.quiesce_pending),
                    "unresolved_restart": sorted(self.restart_pending),
                    "unresolved_replacement_start": sorted(self.runtime_start_pending),
                    "unresolved_replacement_cleanup": sorted(self.replacement_cleanup_pending),
                    "unresolved_creation": sorted(self.create_pending)} if plan.running_storage else {}),
                "receipt_complete": self.receipt_complete,
                **({"prepared_ids_preserved": success, "preparation_consumed": changed,
                    "preparation_reusable": False if changed else None} if plan.staged else {}),
                "installation_evidence": evidence if success else None}


def main(argv=None):
    import argparse
    import fcntl
    import os
    from pathlib import Path
    import stat

    parser = argparse.ArgumentParser(description="Verify a reviewed installation manifest; no action by default")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--reviewed-manifest-sha256", required=True)
    parser.add_argument("--apply-install", action="store_true")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument('--metadata-expectations', type=Path)
    parser.add_argument('--reviewed-metadata-expectations-sha256')
    args = parser.parse_args(argv)
    lock = receipt = None
    try:
        with args.manifest.open("rb") as stream:
            plan = Plan.load(stream.read(1_048_577), args.reviewed_manifest_sha256)
        expectations = None
        if bool(args.metadata_expectations) != bool(args.reviewed_metadata_expectations_sha256):
            refuse()
        if args.metadata_expectations:
            expectations = metadata_diagnostics.read_profile(args.metadata_expectations,
                args.reviewed_metadata_expectations_sha256, plan, args.reviewed_manifest_sha256)
        if not args.apply_install:
            print(json.dumps({"state": "READY_FOR_INDEPENDENT_REVIEW", "actions_executed": False,
                "startup_authorized": False, "deferred_startup_policies": list(plan.deferred_startup_policies),
                "network_contract": configuration.CONTRACT if plan.network_bindings else "legacy_observed",
                "network_connectivity_verified": False}))
            return 0
        # v4 is installation-stage proof only. It must not leave an operational
        # stack quiesced before shared-deadline startup/query wiring is reviewed.
        if plan.running_storage:
            refuse()
        # An API/CLI flag does not replace the separately required human approval.
        if args.receipt is None:
            refuse()
        lock = os.open("/private/tmp/cryptkeep-companion-install.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        info = os.fstat(lock)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600:
            refuse()
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        from scripts.research.companion_install_docker import DockerInstallBackend
        receipt = core.Receipt(args.receipt)
        backend = DockerInstallBackend(plan, Path(__file__).resolve().parents[2], enabled=True,
                                       metadata_expectations=expectations)
        result = Installer(backend, receipt).run(plan, authorized=True)
        print(json.dumps(result))
        return 0 if result["installed_stopped"] else 1
    except Exception:
        print('{"state":"INCOMPLETE","reason":"installation_refused"}')
        return 1
    finally:
        if receipt is not None:
            receipt.close()
        if lock is not None:
            os.close(lock)


if __name__ == "__main__":
    import sys
    sys.exit(main())
