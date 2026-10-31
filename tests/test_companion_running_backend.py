"""Offline command fakes only: no Docker, credentials or running services."""
from dataclasses import replace
import json

import pytest

from scripts.research import companion_existing_controller as core
from scripts.research import companion_install_docker as docker
from scripts.research import companion_installer as install


class Clock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class Commands:
    def __init__(self, rows, clock):
        self.rows = rows
        self.clock = clock
        self.calls = []
        self.ack = None
        self.responsive = True
        self.after_mutation = lambda: None
        self.wrong_binding = False
        self.duplicate = False

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        assert 0 < kwargs["timeout"] <= docker.LIFECYCLE_TIMEOUT
        self.clock.now += 0.001
        if args[:2] == ("container", "ls"):
            return "\n".join(r["id"] + " " + r["name"].removeprefix("/")
                             for r in self.rows.values()).encode()
        if args[:2] == ("network", "inspect"):
            return json.dumps({"id": ("f" if self.wrong_binding else "e") * 64,
                               "name": "synthetic"}).encode()
        if args[:2] == ("container", "inspect"):
            records = [self.rows[identity] for identity in args[4:]]
            if self.duplicate:
                records += records[:1]
            return "\n".join(json.dumps(row) for row in records).encode()
        assert args[:2] in {("container", "kill"), ("container", "start")}
        if self.ack == "before":
            raise TimeoutError("SYNTHETIC_PRIVATE_ERROR")
        row = self.rows[args[-1]]
        if self.responsive:
            if args[:2] == ("container", "kill"):
                assert args == ("container", "kill", "--signal=SIGTERM", row["id"])
                row["state"] = "exited"
                row["networks"]["synthetic"]["NetworkID"] = ""
            else:
                assert args == ("container", "start", row["id"])
                row.update(state="running", started="2026-10-20T12:00:01Z")
                row["networks"]["synthetic"]["NetworkID"] = "e" * 64
        self.after_mutation()
        if self.ack == "after":
            raise TimeoutError("SYNTHETIC_PRIVATE_ERROR")
        return b""

    def mutations(self):
        return [args for args, _ in self.calls
                if args[:2] in {("container", "kill"), ("container", "start")}]


@pytest.fixture
def backend(tmp_path, monkeypatch):
    clock = Clock()
    monkeypatch.setattr(docker.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(docker.time, "sleep", clock.sleep)
    monkeypatch.setattr(docker, "LIFECYCLE_TIMEOUT", 0.25)
    rows, baseline = {}, []
    bindings = {"synthetic": "e" * 64}
    for i, name in enumerate(core.TARGETS, 1):
        row = {"id": f"{i:064x}", "name": "/" + name,
               "image": "sha256:" + "a" * 64, "state": "running",
               "started": "2026-10-20T12:00:00Z", "restarts": 3,
               "restart_policy": "no", "attempt": None,
               "networks": {"synthetic": {"NetworkID": "e" * 64,
                                           "Aliases": [name], "IPAMConfig": {}}}}
        rows[row["id"]] = row
        metadata, networks, evidence = docker.configuration.project(row, bindings)
        baseline.append(install.Snapshot(name, row["id"], row["image"], row["state"],
            row["started"], row["restarts"], row["restart_policy"],
            docker.adapter.preservation_digest(row),
            docker.adapter.preservation_digest({**row, "networks": {}}), ("e" * 64,),
            configured_metadata=metadata, configured_networks=networks, network_evidence=evidence))
    plan = install.Plan("a1" * 8, "d" * 64, tuple(baseline), (),
                        network_bindings=tuple(bindings.items()), running_storage=True)
    result = docker.DockerInstallBackend(plan, tmp_path)
    commands = Commands(rows, clock)
    result._command = commands
    return result, commands, clock


def stopped_original(backend):
    native, commands, _ = backend
    before = native.plan.baseline[3]
    row = commands.rows[before.id]
    row["state"] = "exited"
    row["networks"]["synthetic"]["NetworkID"] = ""
    return before


def test_quiesce_is_single_sigterm_with_verified_stopped_inventory(backend):
    native, commands, _ = backend
    before = native.plan.baseline[3]
    storage = json.dumps([commands.rows[r.id] for r in native.plan.baseline[:3]], sort_keys=True)
    assert native.quiesce(before.id) is True
    assert commands.mutations() == [("container", "kill", "--signal=SIGTERM", before.id)]
    assert commands.calls[-1][0][:2] == ("container", "inspect")
    assert json.dumps([commands.rows[r.id] for r in native.plan.baseline[:3]], sort_keys=True) == storage
    assert commands.rows[before.id]["started"] == before.started


def test_restart_only_original_and_reconciles_new_start_time(backend):
    native, commands, _ = backend
    before = stopped_original(backend)
    assert native.restart_original(before.id) is True
    assert commands.mutations() == [("container", "start", before.id)]
    assert commands.rows[before.id]["started"] != before.started
    assert commands.rows[before.id]["restarts"] == before.restarts


@pytest.mark.parametrize("method", ["quiesce", "restart_original"])
@pytest.mark.parametrize("target", ["storage", "foreign", "replacement", "name", "malformed"])
def test_storage_foreign_and_non_id_targets_refused_before_commands(backend, method, target):
    native, commands, _ = backend
    before = native.plan.baseline[3]
    identity = {"storage": native.plan.baseline[0].id, "foreign": "9" * 64,
                "replacement": "8" * 64, "name": before.name, "malformed": None}[target]
    if target == "replacement":
        commands.rows[identity] = {**commands.rows[before.id], "id": identity,
                                   "attempt": native.plan.attempt, "state": "created"}
    with pytest.raises(core.Refused, match="^installation_refused$"):
        getattr(native, method)(identity)
    assert not commands.calls


@pytest.mark.parametrize("method", ["quiesce", "restart_original"])
def test_old_plan_cannot_signal_or_restart(backend, method):
    native, commands, _ = backend
    native.plan = replace(native.plan, running_storage=False)
    with pytest.raises(core.Refused):
        getattr(native, method)(native.plan.baseline[3].id)
    assert not commands.calls


@pytest.mark.parametrize("method", ["quiesce", "restart_original"])
@pytest.mark.parametrize("field", ["image", "started", "restarts", "restart_policy", "attempt",
                                   "foundation", "config", "network", "name", "missing", "state"])
def test_changed_original_is_refused_before_mutation(backend, method, field):
    native, commands, _ = backend
    before = stopped_original(backend) if method == "restart_original" else native.plan.baseline[3]
    row = commands.rows[before.id]
    if field == "image":
        row["image"] = "sha256:" + "b" * 64
    elif field == "started":
        row["started"] = "2026-10-20T12:00:02Z"
    elif field == "restarts":
        row["restarts"] += 1
    elif field == "restart_policy":
        row["restart_policy"] = "always"
    elif field == "attempt":
        row["attempt"] = native.plan.attempt
    elif field == "foundation":
        row["command"] = ["different"]
    elif field == "config":
        row["networks"]["synthetic"]["Aliases"] = ["different"]
    elif field == "network":
        row["networks"]["synthetic"]["NetworkID"] = "f" * 64
    elif field == "name":
        row["name"] = "/" + native.plan.rollback_name(before.name)
    elif field == "missing":
        del commands.rows[before.id]
    else:
        row["state"] = "paused"
    with pytest.raises(core.Refused):
        getattr(native, method)(before.id)
    assert not commands.mutations()


@pytest.mark.parametrize("method", ["quiesce", "restart_original"])
@pytest.mark.parametrize("guard", ["storage", "binding", "duplicate"])
def test_inventory_and_storage_guards_precede_mutation(backend, method, guard):
    native, commands, _ = backend
    before = stopped_original(backend) if method == "restart_original" else native.plan.baseline[3]
    if guard == "storage":
        commands.rows[native.plan.baseline[0].id]["started"] = "unexpected"
    elif guard == "binding":
        commands.wrong_binding = True
    else:
        commands.duplicate = True
    with pytest.raises(core.Refused):
        getattr(native, method)(before.id)
    assert not commands.mutations()


@pytest.mark.parametrize("method", ["quiesce", "restart_original"])
def test_lost_ack_never_confirms_transition_ownership(backend, method):
    native, commands, _ = backend
    before = stopped_original(backend) if method == "restart_original" else native.plan.baseline[3]
    commands.ack = "after"
    with pytest.raises(core.Refused):
        getattr(native, method)(before.id)
    assert len(commands.mutations()) == 1


@pytest.mark.parametrize("method", ["quiesce", "restart_original"])
def test_external_transition_after_failed_command_is_not_owned(backend, method):
    native, commands, _ = backend
    before = stopped_original(backend) if method == 'restart_original' else native.plan.baseline[3]
    commands.ack = 'before'
    def external(args, **kwargs):
        try:
            return commands(args, **kwargs)
        except TimeoutError:
            row = commands.rows[before.id]
            row.update(state='running' if method == 'restart_original' else 'exited',
                       started='2026-10-20T12:00:01Z' if method == 'restart_original' else before.started)
            raise
    native._command = external
    with pytest.raises(core.Refused):
        getattr(native, method)(before.id)
    assert len(commands.mutations()) == 1


@pytest.mark.parametrize("method", ["quiesce", "restart_original"])
@pytest.mark.parametrize("failure", ["before", "unresponsive"])
def test_unchanged_state_times_out_without_force_or_retry(backend, method, failure):
    native, commands, clock = backend
    before = stopped_original(backend) if method == "restart_original" else native.plan.baseline[3]
    commands.ack = "before" if failure == "before" else None
    commands.responsive = False
    with pytest.raises(core.Refused, match="^installation_refused$"):
        getattr(native, method)(before.id)
    assert len(commands.mutations()) == 1
    assert clock.now <= docker.LIFECYCLE_TIMEOUT + 0.01
    assert bool(clock.sleeps) is (failure == "unresponsive")
    assert all("stop" not in args and "SIGKILL" not in args and "--force" not in args
               for args, _ in commands.calls)


@pytest.mark.parametrize("method", ["quiesce", "restart_original"])
@pytest.mark.parametrize("change", ["storage", "image", "restarts", "config"])
def test_post_mutation_drift_is_not_accepted_as_recovery(backend, method, change):
    native, commands, _ = backend
    before = stopped_original(backend) if method == "restart_original" else native.plan.baseline[3]

    def drift():
        row = commands.rows[native.plan.baseline[0].id if change == "storage" else before.id]
        if change == "image":
            row["image"] = "sha256:" + "b" * 64
        elif change == "config":
            row["networks"]["synthetic"]["Aliases"] = ["different"]
        else:
            row["restarts"] += 1

    commands.after_mutation = drift
    with pytest.raises(core.Refused):
        getattr(native, method)(before.id)
    assert len(commands.mutations()) == 1


def test_restart_ack_without_new_start_time_is_refused(backend):
    native, commands, _ = backend
    before = stopped_original(backend)
    commands.after_mutation = lambda: commands.rows[before.id].update(started=before.started)
    with pytest.raises(core.Refused):
        native.restart_original(before.id)
    assert len(commands.mutations()) == 1


@pytest.mark.parametrize("enabled,child", [(False, True), (True, False)])
def test_native_transport_authorization_guards_remain_required(tmp_path, monkeypatch, enabled, child):
    monkeypatch.setattr(core, "_CHILD_CONTEXT", child)
    monkeypatch.setattr(docker, "_run", lambda *a, **k: pytest.fail("must not invoke any CLI"))
    native = docker.DockerInstallBackend(None, tmp_path, enabled=enabled)
    with pytest.raises(core.Refused):
        native._command(("container", "kill", "--signal=SIGTERM", "1" * 64), timeout=1)


def test_expired_deadline_never_dispatches_command(backend):
    native, commands, clock = backend
    with pytest.raises(core.Refused):
        native._inventory_command(("container", "kill", "--signal=SIGTERM", "1" * 64), clock.now)
    assert not commands.calls


class CleanupCommands(Commands):
    def __call__(self, args, **kwargs):
        if args[:2] != ("container", "rm"):
            return super().__call__(args, **kwargs)
        self.calls.append((args, kwargs))
        assert len(args) == 3 and 0 < kwargs["timeout"] <= docker.LIFECYCLE_TIMEOUT
        self.clock.now += 0.001
        if self.ack == "before":
            raise TimeoutError("SYNTHETIC_PRIVATE_ERROR")
        if self.responsive:
            del self.rows[args[-1]]
        self.after_mutation()
        if self.ack == "after":
            raise TimeoutError("SYNTHETIC_PRIVATE_ERROR")
        return b""

    def mutations(self):
        return [args for args, _ in self.calls
                if args[:2] in {("container", "kill"), ("container", "start"), ("container", "rm")}]


def cleanup_snapshot(native, commands, clock):
    return next(r for r in native.inventory(deadline=clock.now + docker.LIFECYCLE_TIMEOUT)
                if r["id"] == "9" * 64)


@pytest.fixture
def cleanup_backend(backend):
    native, original_commands, clock = backend
    before = native.plan.baseline[3]
    original = original_commands.rows[before.id]
    replacement = json.loads(json.dumps(original))
    original.update(name="/" + native.plan.rollback_name(before.name), state="exited")
    original["networks"]["synthetic"]["NetworkID"] = ""
    replacement.update(id="9" * 64, image="sha256:" + "8" * 64,
                       attempt=native.plan.attempt, restarts=0)
    original_commands.rows[replacement["id"]] = replacement
    commands = CleanupCommands(original_commands.rows, clock)
    native._command = commands
    expected = cleanup_snapshot(native, commands, clock)
    commands.calls.clear()
    return native, commands, clock, expected


def cleanup_stopped(cleanup_backend):
    native, commands, clock, _ = cleanup_backend
    commands.rows["9" * 64]["state"] = "exited"
    commands.rows["9" * 64]["networks"]["synthetic"]["NetworkID"] = ""
    expected = cleanup_snapshot(native, commands, clock)
    commands.calls.clear()
    return expected


def test_replacement_cleanup_returns_true_and_parent_can_inventory_then_remove(cleanup_backend):
    native, commands, clock, expected = cleanup_backend
    storage = json.dumps([commands.rows[r.id] for r in native.plan.baseline[:3]], sort_keys=True)
    assert native.quiesce_replacement(expected) is True
    stopped = cleanup_snapshot(native, commands, clock)
    assert stopped["state"] == "exited" and stopped["networks"] == ("",)
    assert stopped["configured_metadata"] == expected["configured_metadata"]
    assert native.remove_stopped_replacement(stopped) is True
    assert commands.mutations() == [("container", "kill", "--signal=SIGTERM", expected["id"]),
                                    ("container", "rm", expected["id"])]
    assert json.dumps([commands.rows[r.id] for r in native.plan.baseline[:3]], sort_keys=True) == storage


@pytest.mark.parametrize("method", ["quiesce_replacement", "remove_stopped_replacement"])
def test_cleanup_requires_every_known_snapshot_field_and_rejects_extra_keys(cleanup_backend, method):
    native, commands, _, expected = cleanup_backend
    if method == "remove_stopped_replacement":
        expected = cleanup_stopped(cleanup_backend)
    for key in expected:
        missing = {k: v for k, v in expected.items() if k != key}
        with pytest.raises(core.Refused, match="^installation_refused$"):
            getattr(native, method)(missing)
    with pytest.raises(core.Refused):
        getattr(native, method)({**expected, "unreviewed": True})
    assert not commands.calls


@pytest.mark.parametrize("method", ["quiesce_replacement", "remove_stopped_replacement"])
@pytest.mark.parametrize("field,value", [
    ("name", "phase1-timescaledb"), ("name", "foreign"), ("id", "1".zfill(64)),
    ("id", "4".zfill(64)), ("id", "bad"), ("image", "bad"), ("attempt", "foreign"),
    ("started", ""), ("started", "0001-01-01T00:00:00Z"), ("started", None),
    ("restarts", False), ("restarts", 1), ("metadata", "bad"), ("foundation", None),
    ("configured_metadata", "bad"), ("policy", "always"), ("state", "created"),
    ("networks", "e" * 64), ("networks", ["e" * 64, "e" * 64]),
    ("configured_networks", [1]), ("network_evidence", [["synthetic", "e" * 64]]),
    ("network_evidence", [["synthetic", "e" * 64, 1]]),
])
def test_cleanup_refuses_unowned_or_malformed_expected_before_commands(cleanup_backend, method, field, value):
    native, commands, _, expected = cleanup_backend
    if method == "remove_stopped_replacement":
        expected = cleanup_stopped(cleanup_backend)
    with pytest.raises(core.Refused):
        getattr(native, method)({**expected, field: value})
    assert not commands.calls


@pytest.mark.parametrize("method", ["quiesce_replacement", "remove_stopped_replacement"])
@pytest.mark.parametrize("change", ["image", "started", "restarts", "attempt", "foundation", "config",
                                    "network", "state", "storage", "missing"])
def test_cleanup_preflight_requires_exact_current_snapshot(cleanup_backend, method, change):
    native, commands, _, expected = cleanup_backend
    if method == "remove_stopped_replacement":
        expected = cleanup_stopped(cleanup_backend)
    row = commands.rows[expected["id"]]
    if change == "image":
        row["image"] = "sha256:" + "7" * 64
    elif change == "started":
        row["started"] = "2026-10-20T13:00:00Z"
    elif change == "restarts":
        row["restarts"] = 1
    elif change == "attempt":
        row["attempt"] = "foreign"
    elif change == "foundation":
        row["command"] = ["different"]
    elif change == "config":
        row["networks"]["synthetic"]["Aliases"] = ["different"]
    elif change == "network":
        row["networks"]["synthetic"]["NetworkID"] = "f" * 64
    elif change == "state":
        row["state"] = "exited" if method == "quiesce_replacement" else "running"
    elif change == "storage":
        commands.rows[native.plan.baseline[0].id]["restarts"] += 1
    else:
        del commands.rows[expected["id"]]
    with pytest.raises(core.Refused):
        getattr(native, method)(expected)
    assert not commands.mutations()


@pytest.mark.parametrize("method", ["quiesce_replacement", "remove_stopped_replacement"])
@pytest.mark.parametrize("ack", ["before", "after"])
def test_cleanup_lost_ack_is_unresolved_even_after_desired_state(cleanup_backend, method, ack):
    native, commands, _, expected = cleanup_backend
    if method == "remove_stopped_replacement":
        expected = cleanup_stopped(cleanup_backend)
    commands.ack = ack
    with pytest.raises(core.Refused, match="^installation_refused$"):
        getattr(native, method)(expected)
    assert len(commands.mutations()) == 1
    assert commands.calls[-1][0] == commands.mutations()[0]


def test_replacement_quiesce_timeout_never_forces_or_repeats_signal(cleanup_backend):
    native, commands, clock, expected = cleanup_backend
    commands.responsive = False
    began = clock.now
    with pytest.raises(core.Refused):
        native.quiesce_replacement(expected)
    assert clock.now - began <= docker.LIFECYCLE_TIMEOUT + 0.01
    assert commands.mutations() == [("container", "kill", "--signal=SIGTERM", expected["id"])]


@pytest.mark.parametrize("change", ["started", "foundation", "config", "storage"])
def test_replacement_quiesce_rejects_post_signal_drift(cleanup_backend, change):
    native, commands, _, expected = cleanup_backend

    def drift():
        row = commands.rows[expected["id"]]
        if change == "started":
            row["started"] = "2026-10-20T13:00:00Z"
        elif change == "foundation":
            row["command"] = ["different"]
        elif change == "config":
            row["networks"]["synthetic"]["Aliases"] = ["different"]
        else:
            commands.rows[native.plan.baseline[0].id]["restarts"] += 1

    commands.after_mutation = drift
    with pytest.raises(core.Refused):
        native.quiesce_replacement(expected)
    assert len(commands.mutations()) == 1


def test_replacement_rm_ack_does_not_hide_still_present_or_changed_storage(cleanup_backend):
    native, commands, _, _ = cleanup_backend
    expected = cleanup_stopped(cleanup_backend)
    commands.responsive = False
    with pytest.raises(core.Refused):
        native.remove_stopped_replacement(expected)
    assert commands.mutations() == [("container", "rm", expected["id"])]
    commands.responsive = True
    commands.after_mutation = lambda: commands.rows[native.plan.baseline[0].id].update(restarts=4)
    with pytest.raises(core.Refused):
        native.remove_stopped_replacement(expected)


@pytest.mark.parametrize("change", ["legacy", "attempt", "name", "restarts", "never_started", "policy"])
def test_started_stopped_placeholder_observation_is_v4_only_and_guarded(cleanup_backend, change):
    native, commands, _, _ = cleanup_backend
    cleanup_stopped(cleanup_backend)
    row = commands.rows["9" * 64]
    assert native._placeholder_allowed(row) is True
    if change == "legacy":
        native.plan = replace(native.plan, running_storage=False)
    elif change == "attempt":
        row["attempt"] = "foreign"
    elif change == "name":
        row["name"] = "/phase1-timescaledb"
    elif change == "restarts":
        row["restarts"] = 1
    elif change == "never_started":
        row["started"] = ""
    else:
        row["restart_policy"] = "always"
    assert native._placeholder_allowed(row) is False
    assert not commands.mutations()


@pytest.mark.parametrize("method", ["quiesce_replacement", "remove_stopped_replacement"])
def test_cleanup_methods_are_disabled_for_legacy_profiles(cleanup_backend, method):
    native, commands, _, expected = cleanup_backend
    if method == "remove_stopped_replacement":
        expected = cleanup_stopped(cleanup_backend)
    native.plan = replace(native.plan, running_storage=False)
    with pytest.raises(core.Refused):
        getattr(native, method)(expected)
    assert not commands.calls
