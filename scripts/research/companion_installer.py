"""One-shot stopped-application installation. Inert until explicitly authorized.

The reviewed manifest hash is an external trust input, not an approval generated
by this tool. No startup, trading, migrations or automatic recovery retries.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import time

from scripts.research import companion_existing_controller as core
from scripts.research import companion_network_configuration as configuration
from scripts.research import companion_metadata_diagnostics as metadata_diagnostics

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

    @classmethod
    def load(cls, raw, trusted_sha256):
        try:
            if (type(raw) is not bytes or len(raw) > 1_048_576 or type(trusted_sha256) is not str
                    or not ID.fullmatch(trusted_sha256) or hashlib.sha256(raw).hexdigest() != trusted_sha256):
                refuse()
            data = json.loads(raw, object_pairs_hook=_unique)
            configured = data.get("schema") == "companion-configured-install-v3"
            keys = {"schema", "decision", "reviewer", "attempt", "cli_sha256", "policies", "baseline", "applications"}
            if configured:
                keys.add("network_contract")
            if (set(data) != keys
                    or data["schema"] not in {"companion-install-v1", "companion-stopped-install-v2", "companion-configured-install-v3"}
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
                        or row.state != "exited" or row.policy != "no" or row.attempt
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
            return cls(data["attempt"], data["cli_sha256"], rows, tuple(apps), tuple(sorted(deferred)), tuple(sorted(bindings.items())))
        except Exception:
            refuse()

    def rollback_name(self, name):
        return name + "-rollback-" + self.attempt


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

    def _record(self, phase, name=None, evidence=None):
        record = {"phase": phase}
        if name in APPS:
            record["target"] = name
        if evidence is not None:
            record["installation_evidence"] = evidence
        remaining = self.end - self.clock()
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
        raw = self._call("inventory", recovery=recovery)
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
        return {r.name: r for r in rows}

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
        complete = True
        for before in reversed(self.plan.baseline[3:]):
            try:
                rows = self._rows(recovery=True)
                replacement = rows.get(before.name)
                if replacement is not None and replacement.id != before.id:
                    if (replacement.attempt != self.plan.attempt or replacement.image != self.images.get(before.name)
                            or replacement.state != "created" or replacement.started not in core.NEVER_STARTED
                            or replacement.restarts != 0):
                        refuse()
                    self._recovery_record("remove_replacement_intended", before.name)
                    self._call("remove", replacement.id, recovery=True)
                    rows = self._rows(recovery=True)
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
        try:
            final = self._rows(recovery=True)
            self.rollback_exact_baseline = all(final.get(r.name) == r for r in self.plan.baseline)
            if self.plan.network_bindings:
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

    def run(self, plan, *, authorized=False):
        if authorized is not True or self.used or not isinstance(plan, Plan):
            refuse()
        self.used = True
        self.plan, self.images = plan, {}
        self.receipt_complete = True
        self.rollback_exact_baseline = None
        self.end = self.clock() + 300
        self.work_end = self.end - 120
        changed = success = recovered = False
        evidence = None
        stage = "reservation"
        try:
            self._record("installation_reserved", evidence={"startup_authorized": False,
                "deferred_startup_policies": list(plan.deferred_startup_policies),
                **({"network_contract": configuration.CONTRACT, "network_connectivity_verified": False}
                   if plan.network_bindings else {})})
            stage = "inventory_preflight"
            rows = self._rows()
            stage = "baseline_preflight"
            if (any(rows.get(r.name) != r for r in plan.baseline)
                    or any(plan.rollback_name(n) in rows for n in APPS)
                    or any(r.attempt == plan.attempt for r in rows.values())):
                refuse()
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
            stage = "replacement"
            for before in plan.baseline[3:]:
                self._record("rename_intended", before.name)
                changed = True  # An uncertain operation may already have happened.
                self._call("rename", before.id, plan.rollback_name(before.name))
                self._original(self._rows(), before)
                self._record("detach_intended", before.name)
                self._call("disconnect", before.name)
                self._original(self._rows(), before, detached=True)
                self._record("create_intended", before.name)
                stage = "create"
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
            evidence = {"attempt": plan.attempt, "startup_authorized": False,
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
            try:
                self._record("installation_failed", evidence={"stage": stage})
            except Exception:
                pass
        finally:
            if changed and not success:
                recovered = self._rollback()
        return {"state": "READY_FOR_INDEPENDENT_REVIEW" if success else "INCOMPLETE",
                "failure_stage": None if success else stage,
                "rollback_scope": "configuration_only" if plan.network_bindings else "exact_selected_metadata",
                "rollback_exact_baseline": self.rollback_exact_baseline,
                "network_connectivity_verified": False,
                "installed_stopped": success, "rollback_verified": recovered, "services_started": False,
                "startup_authorized": False, "deferred_startup_policies": list(plan.deferred_startup_policies),
                "receipt_complete": self.receipt_complete,
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
