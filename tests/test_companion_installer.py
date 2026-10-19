"""Offline installation state machine and concrete command construction."""
from dataclasses import asdict, replace
import hashlib
import io
import json
from pathlib import Path
import struct
import tarfile
from types import SimpleNamespace

import pytest

from scripts.research import companion_existing_controller as core
from scripts.research import companion_runtime_adapter as adapter
from scripts.research import companion_installer as install
from scripts.research import companion_install_docker as docker
from scripts.research import companion_docker_transport as transport
from scripts.research import companion_network_configuration as network


def manifest():
    baseline = [asdict(install.Snapshot(n, f"{i:064x}", "sha256:" + "a" * 64,
        "exited", "old", 0, "no", "f" * 64, "b" * 64, ("e" * 64,)))
        for i, n in enumerate(core.TARGETS, 1)]
    apps = []
    for name in install.APPS:
        paths = adapter.required_app_sources(name)
        apps.append({"name": name, "create_options": ["--publish", "127.0.0.1:8002:8002"],
            "command": ["python", "-B", "module.py"], "network_options": ["--alias", adapter.ALIASES[name]],
            "replacement_metadata": "c" * 64,
            "sources": [{"local": "phase1_research_copilot/" + p.removeprefix("/app/"),
                         "destination": p, "sha256": hashlib.sha256(b"fixture").hexdigest()} for p in sorted(paths)]})
    return {"schema": "companion-install-v1", "decision": "ACCEPTED_WITH_RISK", "reviewer": "SYNTHETIC_ONLY",
            "attempt": "a1" * 8, "cli_sha256": "d" * 64, "policies": dict.fromkeys(install.POLICIES, True),
            "baseline": baseline, "applications": apps}


def load(data=None):
    raw = install.canonical(manifest() if data is None else data)
    return install.Plan.load(raw, hashlib.sha256(raw).hexdigest())


@pytest.mark.parametrize("missing", ["/app/shared/answer_metadata.py", "/app/shared/prompting.py",
                                     "/app/shared/__init__.py", "/app/orchestrator/__init__.py"])
def test_manifest_requires_imported_orchestrator_sources(missing):
    data = manifest()
    app = data["applications"][-1]
    for path in {"/app/shared/answer_metadata.py", "/app/shared/prompting.py",
                 "/app/shared/__init__.py", "/app/orchestrator/__init__.py"}:
        if not any(row["destination"] == path for row in app["sources"]):
            app["sources"].append({"local": "phase1_research_copilot/" + path.removeprefix("/app/"),
                                   "destination": path, "sha256": "f" * 64})
    app["sources"] = [row for row in app["sources"] if row["destination"] != missing]
    with pytest.raises(core.Refused):
        load(data)


class Inline:
    def call(self, fn, args, timeout):
        assert 0 < timeout <= 60
        return fn(*args)


class Receipt:
    def __init__(self):
        self.events = []
    def write(self, value):
        self.events.append(value)


class Backend:
    def __init__(self, plan, fail=None, after=False):
        self.plan, self.fail, self.after = plan, fail, after
        self.rows = {r.name: r for r in plan.baseline}
        self.calls, self.failed = [], False
        self.images = {n: "sha256:" + f"{i:064x}" for i, n in enumerate(install.APPS, 100)}

    def effect(self, method, fn, *args):
        self.calls.append((method, args))
        fails = self.fail == method and not self.failed
        if fails:
            self.failed = True
            if not self.after:
                raise RuntimeError("SYNTHETIC_SECRET")
        result = fn()
        if fails:
            raise TimeoutError("SYNTHETIC_SECRET")
        return result

    def inventory(self):
        return self.effect("inventory", lambda: [asdict(r) for r in self.rows.values()])
    def prepare(self):
        return self.effect("prepare", lambda: True)
    def build(self, name):
        return self.effect("build", lambda: self.images[name], name)
    def rename(self, cid, name):
        def change():
            key, row = next((n, r) for n, r in self.rows.items() if r.id == cid)
            del self.rows[key]
            self.rows[name] = replace(row, name=name)
        return self.effect("rename", change, cid, name)
    def disconnect(self, name):
        def change():
            key = self.plan.rollback_name(name)
            self.rows[key] = replace(self.rows[key], networks=(), metadata="d" * 64)
        return self.effect("disconnect", change, name)
    def create(self, name, image):
        def change():
            old = next(r for r in self.plan.baseline if r.name == name)
            self.rows[name] = replace(old, id=f"{len(self.rows) + 1000:064x}", image=image,
                state="created", started="0001-01-01T00:00:00Z", metadata="c" * 64, attempt=self.plan.attempt)
        return self.effect("create", change, name, image)
    def remove(self, cid):
        def change():
            key = next(n for n, r in self.rows.items() if r.id == cid)
            del self.rows[key]
        return self.effect("remove", change, cid)
    def connect(self, name):
        def change():
            old = next(r for r in self.plan.baseline if r.name == name)
            self.rows[name] = replace(self.rows[name], networks=old.networks, metadata=old.metadata)
        return self.effect("connect", change, name)
    def verify_sources(self, name):
        return self.effect("verify_sources", lambda: True, name)


def runner(plan=None, **kwargs):
    plan = plan or load()
    backend, receipt = Backend(plan, **kwargs), Receipt()
    result = install.Installer(backend, receipt, executor=Inline())
    return plan, backend, receipt, result


def configured_manifest():
    data = manifest()
    data["schema"] = "companion-configured-install-v3"
    data["policies"].update(dict.fromkeys(install.STARTUP_POLICIES, False))
    data["network_contract"] = {"schema": network.CONTRACT,
        "bindings": {"synthetic": "e" * 64}, "connectivity_verified": False}
    for row in data["baseline"]:
        row.update(configured_metadata="b" * 64, configured_networks=["e" * 64],
                   network_evidence=[["synthetic", "e" * 64, "reported_id"]])
    for app in data["applications"]:
        app["replacement_configured_metadata"] = app.pop("replacement_metadata")
    return data


class ConfiguredBackend(Backend):
    def disconnect(self, name):
        def change():
            key = self.plan.rollback_name(name)
            self.rows[key] = replace(self.rows[key], networks=(), metadata="d" * 64,
                configured_networks=(), network_evidence=(), configured_metadata="d" * 64)
        return self.effect("disconnect", change, name)

    def create(self, name, image):
        def change():
            old = next(r for r in self.plan.baseline if r.name == name)
            self.rows[name] = replace(old, id=f"{len(self.rows) + 1000:064x}", image=image,
                state="created", started="0001-01-01T00:00:00Z", networks=("",), metadata="8" * 64,
                attempt=self.plan.attempt, configured_metadata="c" * 64,
                network_evidence=(("synthetic", "e" * 64, "configured_only"),))
        return self.effect("create", change, name, image)

    def connect(self, name):
        def change():
            old = next(r for r in self.plan.baseline if r.name == name)
            self.rows[name] = replace(self.rows[name], networks=("",), metadata="9" * 64,
                configured_metadata=old.configured_metadata, configured_networks=old.configured_networks,
                network_evidence=(("synthetic", "e" * 64, "configured_only"),))
        return self.effect("connect", change, name)


def test_configured_install_labels_raw_and_configuration_separately():
    plan = load(configured_manifest())
    backend, receipt = ConfiguredBackend(plan), Receipt()
    result = install.Installer(backend, receipt, executor=Inline()).run(plan, authorized=True)
    assert result["installed_stopped"] and not result["network_connectivity_verified"]
    assert result["rollback_scope"] == "configuration_only"
    assert result["startup_authorized"] is False
    for row in result["installation_evidence"]["applications"]:
        assert row["metadata_sha256"] == "8" * 64
        assert row["configured_metadata_sha256"] == "c" * 64
        assert row["network_evidence"][0][2] == "configured_only"
    assert not {"start", "stop", "exec"}.intersection(c[0] for c in backend.calls)


@pytest.mark.parametrize("failure", ["create", "verify_sources"])
def test_owned_placeholder_rollback_restores_configuration_without_claiming_raw_match(failure):
    plan = load(configured_manifest())
    backend, receipt = ConfiguredBackend(plan, fail=failure, after=True), Receipt()
    result = install.Installer(backend, receipt, executor=Inline()).run(plan, authorized=True)
    assert not result["installed_stopped"] and result["rollback_verified"]
    assert result["rollback_exact_baseline"] is False
    assert result["rollback_scope"] == "configuration_only" and not result["network_connectivity_verified"]
    assert all(backend.rows[r.name] == r for r in plan.baseline[:3])
    assert not any(row.attempt for row in backend.rows.values())
    event = next(r for r in receipt.events if r["phase"] == "rollback_checks_completed")
    assert event["installation_evidence"] == {"configuration_restored": True,
        "exact_baseline_restored": False, "network_connectivity_verified": False}


@pytest.mark.parametrize("change", ["legacy", "connectivity", "startup", "evidence", "binding", "raw_id"])
def test_configured_contract_cannot_be_inferred_or_promoted(change):
    data = configured_manifest()
    if change == "legacy":
        data["schema"] = "companion-stopped-install-v2"
    elif change == "connectivity":
        data["network_contract"]["connectivity_verified"] = True
    elif change == "startup":
        data["policies"]["sdk_startup_compatible"] = True
    elif change == "evidence":
        data["baseline"][0]["network_evidence"][0][2] = "attached"
    elif change == "binding":
        data["network_contract"]["bindings"]["synthetic"] = "f" * 64
    else:
        data["baseline"][0]["networks"] = [""]
    with pytest.raises(core.Refused):
        load(data)


@pytest.mark.parametrize("schema", ["companion-install-v1", "companion-stopped-install-v2"])
def test_legacy_manifest_still_rejects_stopped_blank_network(schema):
    data = manifest()
    data["schema"] = schema
    if schema.endswith("v2"):
        data["policies"].update(dict.fromkeys(install.STARTUP_POLICIES, False))
    data["baseline"][3]["networks"] = [""]
    with pytest.raises(core.Refused):
        load(data)


def test_configured_commands_use_resolved_id_not_blank_observed_id(tmp_path, monkeypatch):
    data = configured_manifest()
    data["baseline"][3]["networks"] = [""]
    data["baseline"][3]["network_evidence"][0][2] = "configured_only"
    plan = load(data)
    backend = docker.DockerInstallBackend(plan, tmp_path)
    name = install.APPS[0]
    monkeypatch.setattr(docker.resource, "setrlimit", lambda *a: None)
    backend._environment = lambda n: b"SYNTHETIC=private\n"
    backend._labels = lambda n: b"synthetic=label\n"
    backend._verify_labels = lambda *a: None
    calls = []
    def command(args, **kwargs):
        calls.append(args)
        return b"9" * 64
    backend._command = command
    backend.disconnect(name)
    backend.connect(name)
    backend.create(name, "sha256:" + "8" * 64)
    assert calls[0] == ("network", "disconnect", "e" * 64, plan.baseline[3].id)
    assert calls[1][-2:] == ("e" * 64, plan.baseline[3].id)
    assert calls[2][calls[2].index("--network") + 1] == "e" * 64


@pytest.mark.parametrize("wrong_network", [False, True])
def test_configured_inventory_verifies_daemon_binding_without_mutation(tmp_path, wrong_network):
    plan = load(configured_manifest())
    before = plan.baseline[3]
    row = {"id": before.id, "name": "/" + before.name, "image": before.image,
        "state": "exited", "started": before.started, "restarts": 0, "restart_policy": "no",
        "attempt": None, "networks": {"synthetic": {"NetworkID": "", "Aliases": ["audit-log"], "IPAMConfig": {}}}}
    backend = docker.DockerInstallBackend(plan, tmp_path)
    calls = []
    def command(args, **kwargs):
        calls.append(args)
        if args[:2] == ("container", "ls"):
            return (before.id + " " + before.name).encode()
        if args[:2] == ("network", "inspect"):
            assert args == ("network", "inspect", "--format", docker.NETWORK_FORMAT, "e" * 64)
            return json.dumps({"id": "f" * 64 if wrong_network else "e" * 64, "name": "synthetic"}).encode()
        assert args[:2] == ("container", "inspect")
        return json.dumps(row).encode()
    backend._command = command
    if wrong_network:
        with pytest.raises(core.Refused):
            backend.inventory()
        assert len(calls) == 2
    else:
        result = backend.inventory()[0]
        assert result["networks"] == ("",)
        assert result["configured_networks"] == ("e" * 64,)
        assert result["network_evidence"] == (("synthetic", "e" * 64, "configured_only"),)
        assert result["metadata"] == adapter.preservation_digest(row)


@pytest.mark.parametrize("change", ["foreign", "running", "restarted", "prior_start"])
def test_placeholder_inventory_refuses_nonowned_or_active_created_object(tmp_path, change):
    plan = load(configured_manifest())
    name = install.APPS[0]
    row = {"id": "9" * 64, "name": "/" + name, "image": "sha256:" + "8" * 64,
        "state": "created", "started": "0001-01-01T00:00:00Z", "restarts": 0,
        "restart_policy": "no", "attempt": plan.attempt}
    row.update({"foreign": {"attempt": "foreign"}, "running": {"state": "running"},
        "restarted": {"restarts": 1}, "prior_start": {"started": "yesterday"}}[change])
    assert docker.DockerInstallBackend(plan, tmp_path)._placeholder_allowed(row) is False


def test_original_placeholder_preserves_reviewed_nonzero_restart_history(tmp_path):
    data = configured_manifest()
    data["baseline"][3]["restarts"] = 3
    plan = load(data)
    before = plan.baseline[3]
    row = {"id": before.id, "name": "/" + before.name, "image": before.image,
        "state": "exited", "started": before.started, "restarts": 3, "restart_policy": "no", "attempt": None}
    backend = docker.DockerInstallBackend(plan, tmp_path)
    assert backend._placeholder_allowed(row)
    row["restarts"] = 4
    assert not backend._placeholder_allowed(row)


def test_inert_default_never_contacts_backend():
    plan, backend, _, run = runner()
    with pytest.raises(core.Refused):
        run.run(plan)
    assert not backend.calls


@pytest.mark.parametrize("stopped_only", [False, True])
def test_four_created_apps_and_original_storage_and_rollback_preserved(stopped_only):
    data = manifest()
    if stopped_only:
        data["schema"] = "companion-stopped-install-v2"
        data["policies"].update(dict.fromkeys(install.STARTUP_POLICIES, False))
    plan, backend, receipt, run = runner(load(data))
    result = run.run(plan, authorized=True)
    assert result["installed_stopped"] and not result["services_started"]
    assert all(backend.rows[r.name] == r for r in plan.baseline[:3])
    assert all(backend.rows[n].state == "created" for n in install.APPS)
    assert all(backend.rows[plan.rollback_name(n)].state == "exited" for n in install.APPS)
    assert len([c for c in backend.calls if c[0] == "create"]) == 4
    assert not {"start", "stop", "exec"}.intersection(c[0] for c in backend.calls)
    with pytest.raises(core.Refused):
        run.run(plan, authorized=True)
    assert "SYNTHETIC_SECRET" not in json.dumps(receipt.events)
    evidence = result["installation_evidence"]
    assert len(evidence["applications"]) == 4 and len(evidence["storage"]) == 3
    for app in evidence["applications"]:
        assert app["replacement_id"] == backend.rows[app["name"]].id
        assert app["replacement_image"] == backend.rows[app["name"]].image
        assert app["source_check"] == "verified_at_creation" and app["source_sha256"]
    assert receipt.events[-1]["installation_evidence"] == evidence
    assert result["startup_authorized"] is evidence["startup_authorized"] is False
    deferred = sorted(install.STARTUP_POLICIES) if stopped_only else []
    assert result["deferred_startup_policies"] == evidence["deferred_startup_policies"] == deferred
    assert receipt.events[0]["installation_evidence"] == {
        "startup_authorized": False, "deferred_startup_policies": deferred}


@pytest.mark.parametrize("policy", sorted(install.POLICIES))
def test_stage_policy_requirements_cannot_be_skipped_or_promoted(policy):
    legacy = manifest()
    legacy["policies"][policy] = False
    with pytest.raises(core.Refused):
        load(legacy)
    stopped = manifest()
    stopped["schema"] = "companion-stopped-install-v2"
    stopped["policies"].update(dict.fromkeys(install.STARTUP_POLICIES, False))
    stopped["policies"][policy] = policy in install.STARTUP_POLICIES
    with pytest.raises(core.Refused):
        load(stopped)


def test_stopped_plan_failure_keeps_deferrals_and_rolls_back():
    data = manifest()
    data["schema"] = "companion-stopped-install-v2"
    data["policies"].update(dict.fromkeys(install.STARTUP_POLICIES, False))
    plan, backend, receipt, run = runner(load(data), fail="create", after=True)
    result = run.run(plan, authorized=True)
    assert not result["installed_stopped"] and result["rollback_verified"]
    assert result["startup_authorized"] is False
    assert result["deferred_startup_policies"] == sorted(install.STARTUP_POLICIES)
    assert all(backend.rows[r.name] == r for r in plan.baseline)
    assert not {"start", "stop", "exec"}.intersection(c[0] for c in backend.calls)


@pytest.mark.parametrize("fail_phase,occurrence", [
    ("detach_intended", 1), ("create_intended", 1), ("rename_intended", 2),
    ("replacement_checks", 1),
    ("installation_checks_passed_pending_return", 1),
])
def test_persistent_receipt_failure_cannot_skip_recovery(fail_phase, occurrence):
    plan, backend, receipt, run = runner()
    count = 0
    failed = False
    write = receipt.write
    def failing(event):
        nonlocal count, failed
        if event["phase"] == fail_phase:
            count += 1
            failed |= count == occurrence
        if failed:
            raise OSError("SYNTHETIC_SECRET")
        write(event)
    receipt.write = failing
    result = run.run(plan, authorized=True)
    assert not result["installed_stopped"] and result["rollback_verified"]
    assert result["receipt_complete"] is False and result["installation_evidence"] is None
    assert all(backend.rows.get(r.name) == r for r in plan.baseline)


@pytest.mark.parametrize("step", ["prepare", "build", "rename", "disconnect", "create", "verify_sources"])
@pytest.mark.parametrize("after", [False, True])
def test_failure_and_timeout_after_effect_reconcile_without_retry(step, after):
    plan, backend, receipt, run = runner(fail=step, after=after)
    result = run.run(plan, authorized=True)
    assert not result["installed_stopped"]
    assert all(backend.rows.get(r.name) == r for r in plan.baseline)
    assert "SYNTHETIC_SECRET" not in json.dumps(receipt.events)
    if step not in {"prepare", "build"}:
        assert result["rollback_verified"]


@pytest.mark.parametrize("step,stage", [("inventory", "inventory_preflight"),
    ("prepare", "prepare"), ("build", "build"), ("create", "create")])
def test_failure_diagnostics_record_only_fixed_stage(step, stage):
    plan, backend, receipt, run = runner(fail=step)
    result = run.run(plan, authorized=True)
    assert result.get("failure_stage") == stage
    event = next(r for r in receipt.events if r["phase"] == "installation_failed")
    assert event["installation_evidence"] == {"stage": stage}
    assert "SYNTHETIC_SECRET" not in json.dumps(result)
    assert "SYNTHETIC_SECRET" not in json.dumps(receipt.events)


def test_metadata_failure_is_recorded_before_rollback_without_relaxing_gate():
    plan, backend, receipt, run = runner()
    original_create = backend.create
    def create(name, image):
        original_create(name, image)
        backend.rows[name] = replace(backend.rows[name], metadata="0" * 64)
    backend.create = create
    result = run.run(plan, authorized=True)
    assert not result["installed_stopped"] and result["rollback_verified"]
    assert result["failure_stage"] == "replacement_checks"
    event = next(e for e in receipt.events if e["phase"] == "replacement_checks")
    assert event["installation_evidence"]["checks"]["metadata_matches"] is False
    assert all(type(v) is bool for v in event["installation_evidence"]["checks"].values())
    assert receipt.events.index(event) < next(i for i, e in enumerate(receipt.events)
                                            if e["phase"] == "remove_replacement_intended")
    assert not any(c[0] == "verify_sources" for c in backend.calls)


def test_source_failure_has_separate_stage_after_passing_replacement_checks():
    plan, backend, receipt, run = runner(fail="verify_sources")
    result = run.run(plan, authorized=True)
    assert not result["installed_stopped"] and result["rollback_verified"]
    assert result["failure_stage"] == "source_verification"
    event = next(e for e in receipt.events if e["phase"] == "replacement_checks")
    assert all(event["installation_evidence"]["checks"].values())
    assert "SYNTHETIC_SECRET" not in json.dumps(receipt.events)


@pytest.mark.parametrize("field,value,check", [
    ("id", "original", "new_identity"), ("state", "running", "created"),
    ("started", "yesterday", "never_started"), ("restarts", 1, "zero_restarts"),
    ("policy", "always", "restart_disabled"), ("image", "sha256:" + "f" * 64, "image_matches"),
    ("attempt", "foreign", "attempt_matches"), ("metadata", "0" * 64, "metadata_matches"),
    ("networks", ("0" * 64,), "network_ids_match")])
def test_check_diagnostics_preserve_each_existing_replacement_gate(field, value, check):
    plan, backend, _, run = runner()
    run.plan, run.images = plan, backend.images
    before = plan.baseline[3]
    backend.create(before.name, backend.images[before.name])
    row = backend.rows[before.name]
    assert run._replacement(row, before)
    altered = replace(row, **{field: before.id if value == "original" else value})
    assert run._replacement_checks(altered, before)[check] is False
    assert not run._replacement(altered, before)
    assert run._replacement_checks(None, before) == {"present": False}


@pytest.mark.parametrize("mutation", ["running", "foreign_label", "changed_image", "restarted"])
def test_ambiguous_or_running_replacement_never_removed(mutation):
    plan, backend, _, run = runner()
    def changed(name):
        row = backend.rows[name]
        changes = {"running": {"state": "running", "started": "new"},
                   "foreign_label": {"attempt": "foreign"}, "changed_image": {"image": "sha256:" + "9" * 64},
                   "restarted": {"restarts": 1}}[mutation]
        backend.rows[name] = replace(row, **changes)
        return False
    backend.verify_sources = changed
    result = run.run(plan, authorized=True)
    assert not result["installed_stopped"] and not result["rollback_verified"]
    assert not any(c[0] == "remove" for c in backend.calls)


def test_final_recheck_catches_earlier_replacement_change():
    plan, backend, _, run = runner()
    verify = backend.verify_sources
    def change(name):
        if name == install.APPS[-1]:
            first = install.APPS[0]
            backend.rows[first] = replace(backend.rows[first], state="running", started="external")
        return verify(name)
    backend.verify_sources = change
    assert not run.run(plan, authorized=True)["installed_stopped"]
    assert backend.rows[install.APPS[0]].state == "running"


def test_foreign_rollback_name_refuses_before_prepare():
    plan, backend, _, run = runner()
    old = plan.baseline[3]
    backend.rows[plan.rollback_name(old.name)] = replace(old, id="8" * 64, name=plan.rollback_name(old.name))
    assert not run.run(plan, authorized=True)["installed_stopped"]
    assert not any(c[0] == "prepare" for c in backend.calls)


def test_work_deadline_keeps_recovery_reserve():
    plan, backend, receipt, _ = runner()
    clock = SimpleNamespace(now=0)
    run = install.Installer(backend, receipt, executor=Inline(), clock=lambda: clock.now)
    create = backend.create
    def expire(name, image):
        create(name, image)
        clock.now = 181
    backend.create = expire
    result = run.run(plan, authorized=True)
    assert not result["installed_stopped"] and result["rollback_verified"]


@pytest.mark.parametrize("change", [
    lambda d: d.update(decision="CLAIMED"),
    lambda d: d["policies"].update(builder_local_only=False),
    lambda d: d["baseline"][0].update(state="created"),
    lambda d: d["applications"][0].update(create_options=["--privileged", "true"]),
    lambda d: d["applications"][0].update(create_options=["--env", "SECRET=value"]),
    lambda d: d["applications"][0].update(network_options=["--alias"]),
    lambda d: d["applications"][0]["sources"][0].update(local="../../.env"),
    lambda d: d["applications"][0]["sources"].pop(),
])
def test_manifest_refuses_incomplete_or_unsafe_contract(change):
    data = manifest()
    change(data)
    with pytest.raises(core.Refused, match="installation_refused"):
        load(data)


def test_hash_mismatch_and_duplicate_keys_refused():
    raw = install.canonical(manifest())
    with pytest.raises(core.Refused):
        install.Plan.load(raw, "0" * 64)
    raw = b'{"schema":1,"schema":2}'
    with pytest.raises(core.Refused):
        install.Plan.load(raw, hashlib.sha256(raw).hexdigest())


def test_default_cli_is_manifest_check_only(tmp_path, capsys):
    path = tmp_path / "public_manifest.json"
    path.write_bytes(install.canonical(manifest()))
    assert install.main(["--manifest", str(path), "--reviewed-manifest-sha256", hashlib.sha256(path.read_bytes()).hexdigest()]) == 0
    assert json.loads(capsys.readouterr().out)["actions_executed"] is False


def test_concrete_backend_guard_prevents_real_commands(tmp_path):
    backend = docker.DockerInstallBackend(load(), tmp_path)
    with pytest.raises(core.Refused):
        backend._command(("container", "ls"))


def test_inventory_format_handles_absent_healthcheck_without_relaxing_fields():
    expected = adapter.INSPECT_FORMAT.replace(".Config.Healthcheck", '(index .Config "Healthcheck")')
    expected = expected[:-1] + ',"attempt":{{json (index .Config.Labels "cryptkeep.install-attempt")}}}'
    assert docker.FORMAT == expected
    assert ".Config.Healthcheck" not in docker.FORMAT
    assert "{{json .Config.Env}}" not in docker.FORMAT
    assert "{{json .Config.Labels}}" not in docker.FORMAT


@pytest.mark.parametrize("healthcheck", [None, {"Test": ["CMD", "synthetic-health"]}])
def test_inventory_keeps_null_and_present_healthchecks_fingerprinted(tmp_path, healthcheck):
    plan = load()
    before = plan.baseline[0]
    row = {"id": before.id, "name": "/" + before.name, "image": before.image,
           "state": "exited", "started": before.started, "restarts": 0,
           "restart_policy": "no", "healthcheck": healthcheck, "attempt": None,
           "networks": {"synthetic": {"NetworkID": before.networks[0]}}}
    calls = []
    def command(args, **kwargs):
        calls.append(args)
        if args[:2] == ("container", "ls"):
            return (before.id + " " + before.name + "\n").encode()
        assert args == ("container", "inspect", "--format", docker.FORMAT, before.id)
        return json.dumps(row).encode()
    backend = docker.DockerInstallBackend(plan, tmp_path)
    backend._command = command
    result = backend.inventory()
    assert len(calls) == 2 and len(result) == 1
    assert result[0]["metadata"] == adapter.preservation_digest(row)
    changed = {**row, "healthcheck": {"Test": ["CMD", "different-health"]}}
    assert result[0]["metadata"] != adapter.preservation_digest(changed)


def test_source_only_build_uses_minimal_context_and_no_run(tmp_path):
    plan = load()
    name = install.APPS[0]
    for source in plan.applications[0]["sources"]:
        p = tmp_path / source["local"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"fixture")
    backend = docker.DockerInstallBackend(plan, tmp_path)
    calls = []
    image = "sha256:" + "8" * 64
    count = len(plan.applications[0]["sources"])
    def command(args, **kw):
        calls.append((args, kw))
        if args[0] == "version":
            return b'{"version":"29.8.2","commit":"8af9fe3"}'
        if args[:2] == ("image", "inspect"):
            layers = ["sha256:" + "0" * 64]
            if args[-1] == image:
                layers += ["sha256:" + "1" * 64] * count
            return json.dumps({"id": args[-1], "layers": layers, "onbuild": None}).encode()
        if args[0] == "build":
            with tarfile.open(fileobj=io.BytesIO(kw["payload"])) as archive:
                names = archive.getnames()
                text = archive.extractfile("Dockerfile").read().decode()
            assert len(names) == count + 1 and not any(".env" in n for n in names)
            assert all(line.startswith(("FROM ", "COPY ")) for line in text.splitlines())
            assert text.splitlines()[0] == "FROM " + plan.baseline[3].image.removeprefix("sha256:")
            assert "--pull=false" in args and "--network=none" in args and args[-1] == "-"
            return image.encode()
        return b""
    backend._command = command
    assert backend.build(name) == image
    assert not any(args[:2] in {("image", "ls"), ("image", "tag")} for args, _ in calls)


@pytest.mark.parametrize("reply", [b'{}', b'null', b'not-json',
    b'{"version":"29.8.3","commit":"8af9fe3"}',
    b'{"version":"29.8.2","commit":"different"}'])
def test_unreviewed_engine_refused_before_private_prepare_or_build(tmp_path, reply):
    backend = docker.DockerInstallBackend(load(), tmp_path)
    calls = []
    def command(args, **kw):
        calls.append(args)
        assert args[0] == "version"
        return reply
    backend._command = command
    for operation in (backend.prepare, lambda: backend.build(install.APPS[0])):
        with pytest.raises(core.Refused):
            operation()
    assert len(calls) == 2


def test_missing_local_parent_stops_before_build_and_any_tag(tmp_path):
    backend = docker.DockerInstallBackend(load(), tmp_path)
    calls = []
    def command(args, **kw):
        calls.append(args)
        if args[0] == "version":
            return json.dumps(docker.REVIEWED_ENGINE).encode()
        assert args[:2] == ("image", "inspect")
        raise core.Refused("SYNTHETIC_PARENT_MISSING")
    backend._command = command
    with pytest.raises(core.Refused):
        backend.build(install.APPS[0])
    assert [args[0] for args in calls] == ["version", "image"]


def test_install_transport_forces_legacy_builder_without_host_environment(tmp_path, monkeypatch):
    backend = docker.DockerInstallBackend(load(), tmp_path, enabled=True)
    monkeypatch.setattr(core, "_CHILD_CONTEXT", True)
    monkeypatch.setattr(docker.DockerTransport, "verify_cli", lambda self: True)
    monkeypatch.setenv("DOCKER_BUILDKIT", "1")
    monkeypatch.setenv("DOCKER_CONTEXT", "unapproved-context")
    seen = []
    def run(argv, **kwargs):
        seen.append((argv, kwargs))
        assert kwargs["env"] == {"PATH": "/usr/bin:/bin", "DOCKER_BUILDKIT": "0"}
        assert argv[3:5] == ("--host", docker.ENDPOINT)
        return b"synthetic"
    monkeypatch.setattr(docker, "_run", run)
    assert backend._command(("version", "--format", docker.ENGINE_FORMAT)) == b"synthetic"
    assert len(seen) == 1


@pytest.mark.parametrize("valid_pin", [True, False])
def test_install_transport_canonicalizes_private_temp_path_before_real_verifier(tmp_path, monkeypatch, valid_pin):
    real = tmp_path / "real-temp"
    real.mkdir()
    alias = tmp_path / "temp-alias"
    alias.symlink_to(real, target_is_directory=True)
    monkeypatch.setattr(docker.tempfile, "tempdir", str(alias))
    cli = tmp_path / "synthetic-macho"
    data = struct.pack("<IIIIIIII", 0xFEEDFACF, 0x0100000C, 0, 2, 0, 0, 0, 0) + b"fixture"
    cli.write_bytes(data)
    cli.chmod(0o700)
    monkeypatch.setattr(transport, "CLI", cli)
    monkeypatch.setattr(docker, "CLI", cli)
    monkeypatch.setattr(core, "_CHILD_CONTEXT", True)
    pin = hashlib.sha256(data).hexdigest() if valid_pin else "0" * 64
    backend = docker.DockerInstallBackend(replace(load(), cli_sha256=pin), tmp_path, enabled=True)
    calls = []
    def run(argv, **kwargs):
        calls.append(argv)
        config = Path(argv[argv.index("--config") + 1])
        assert config.resolve(strict=True) == config
        assert config.parent == real.resolve(strict=True)
        assert list(config.iterdir()) == []
        return b"synthetic"
    monkeypatch.setattr(docker, "_run", run)
    if valid_pin:
        assert backend._command(("version", "--format", docker.ENGINE_FORMAT)) == b"synthetic"
        assert len(calls) == 1
    else:
        with pytest.raises(core.Refused):
            backend._command(("version", "--format", docker.ENGINE_FORMAT))
        assert calls == []
    assert list(real.iterdir()) == []


def test_private_environment_only_in_stdin_and_no_core_dump(tmp_path, monkeypatch):
    backend = docker.DockerInstallBackend(load(), tmp_path)
    calls, limits = [], []
    monkeypatch.setattr(docker.resource, "setrlimit", lambda *a: limits.append(a))
    env = [key + "=SYNTHETIC_SECRET" for key in ("SERVICE_TOKEN", "POSTGRES_PASSWORD", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY")]
    def command(args, **kwargs):
        calls.append((args, kwargs))
        if args[:2] == ("container", "inspect"):
            if args[3] == "{{json .Config.Env}}":
                return json.dumps(env).encode()
            labels = {"original.key": "SYNTHETIC_LABEL"}
            if args[-1] == "f" * 64:
                labels[docker.LABEL] = backend.plan.attempt
            return json.dumps(labels).encode()
        return b"f" * 64
    backend._command = command
    backend.create(install.APPS[0], "sha256:" + "8" * 64)
    create_args, options = next(call for call in calls if call[0][:2] == ("container", "create"))
    assert b"SYNTHETIC_SECRET" in options["payload"]
    assert "SYNTHETIC_SECRET" not in repr(create_args)
    assert "/dev/stdin" in create_args and "--label" in create_args
    assert "--pull=never" in create_args
    assert options["label_payload"] == b"original.key=SYNTHETIC_LABEL\n"
    assert "SYNTHETIC_LABEL" not in repr(create_args)
    assert limits and all(item == (docker.resource.RLIMIT_CORE, (0, 0)) for item in limits)


def test_separate_source_verification_worker_guards_private_label_reads(tmp_path, monkeypatch):
    backend = docker.DockerInstallBackend(load(), tmp_path)
    name, identity = install.APPS[0], "f" * 64
    backend.inventory = lambda: [{"name": name, "id": identity}]
    guarded = []
    original_limit = docker.resource.setrlimit
    def protect(which, value):
        assert which == docker.resource.RLIMIT_CORE and value == (0, 0)
        guarded.append(True)
        original_limit(which, value)
    monkeypatch.setattr(docker.resource, "setrlimit", protect)
    def command(args, **kwargs):
        if args[:2] == ("container", "inspect"):
            assert guarded, "private inspection ran without this worker's core protection"
            assert docker.resource.getrlimit(docker.resource.RLIMIT_CORE) == (0, 0)
            labels = {"original.key": "synthetic-only"}
            if args[-1] == identity:
                labels[docker.LABEL] = backend.plan.attempt
            return json.dumps(labels).encode()
        assert args[:2] == ("container", "cp")
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as archive:
            member = tarfile.TarInfo(args[-2].rsplit("/", 1)[1])
            member.size = len(b"fixture")
            archive.addfile(member, io.BytesIO(b"fixture"))
        return stream.getvalue()
    backend._command = command
    assert core.ProcessExecutor().call(backend.verify_sources, (name,), 2) is True
    assert guarded == [], "child guard state must not come from the parent"


def test_failed_label_core_protection_prevents_private_inspection(tmp_path, monkeypatch):
    backend = docker.DockerInstallBackend(load(), tmp_path)
    def fail(*args):
        raise OSError("synthetic core limit failure")
    monkeypatch.setattr(docker.resource, "setrlimit", fail)
    backend._command = lambda *a, **kw: pytest.fail("private read must not run")
    with pytest.raises(OSError):
        backend._labels(install.APPS[0])
