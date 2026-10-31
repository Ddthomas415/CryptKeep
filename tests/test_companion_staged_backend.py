"""Staged native command fakes; never contact Docker or read private settings."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import tarfile

import pytest

from scripts.research import companion_existing_controller as core
from scripts.research import companion_install_docker as docker
from scripts.research import companion_installer as install


ENVIRONMENT = ["SYNTHETIC=value", "SERVICE_TOKEN=fixture", "POSTGRES_PASSWORD=fixture",
               "MINIO_ACCESS_KEY=fixture", "MINIO_SECRET_KEY=fixture"]


class Commands:
    def __init__(self, rows, plan):
        self.rows, self.plan = rows, plan
        self.calls = []
        self.ack = None
        self.after_mutation = lambda: None
        self.environment = {identity: list(ENVIRONMENT) for identity in rows}
        self.labels = {identity: {} for identity in rows}
        self.source = b"fixture"

    def mutations(self):
        return [args for args, _ in self.calls if args[:2] in {
            ("container", "create"), ("container", "rename"), ("container", "rm"),
            ("network", "disconnect"), ("network", "connect")}]

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if args[:2] == ("container", "ls"):
            return "\n".join(r["id"] + " " + r["name"].removeprefix("/")
                             for r in self.rows.values()).encode()
        if args[:2] == ("network", "inspect"):
            return json.dumps({"id": "e" * 64, "name": "synthetic"}).encode()
        if args[:2] == ("container", "inspect"):
            if args[3] == "{{json .Config.Env}}":
                return json.dumps(self.environment[args[4]]).encode()
            if args[3] == "{{json .Config.Labels}}":
                return json.dumps(self.labels[args[4]]).encode()
            assert args[3] == docker.FORMAT
            return "\n".join(json.dumps(self.rows[identity]) for identity in args[4:]).encode()
        if args[:2] == ("container", "cp"):
            result = io.BytesIO()
            with tarfile.open(fileobj=result, mode="w") as archive:
                info = tarfile.TarInfo(Path(args[2]).name)
                info.size = len(self.source)
                archive.addfile(info, io.BytesIO(self.source))
            return result.getvalue()
        if self.ack == "before":
            raise TimeoutError("SYNTHETIC_PRIVATE_ERROR")
        if args[:2] == ("container", "create"):
            identity = "9" * 64
            name = args[args.index("--name") + 1]
            logical = next(n for n in install.APPS if self.plan.staged_name(n) == name)
            original = next(r for r in self.plan.baseline if r.name == logical)
            row = deepcopy(self.rows[original.id])
            row.update(id=identity, name="/" + name, image="sha256:" + "c" * 64,
                       state="created", started=core.NEVER_STARTED[1], restarts=0,
                       attempt=self.plan.attempt)
            row["networks"] = {"synthetic": {"NetworkID": "", "Aliases": [name], "IPAMConfig": {}}}
            self.rows[identity] = row
            self.environment[identity] = list(self.environment[original.id])
            self.labels[identity] = {docker.LABEL: self.plan.attempt}
            output = identity.encode()
        elif args[:2] == ("container", "rename"):
            self.rows[args[2]]["name"] = "/" + args[3]
            output = b""
        elif args[:2] == ("container", "rm"):
            assert len(args) == 3
            del self.rows[args[2]]
            output = b""
        elif args[:2] == ("network", "disconnect"):
            assert args[2] == "e" * 64
            self.rows[args[3]]["networks"] = {}
            output = b""
        elif args[:2] == ("network", "connect"):
            assert args[-2] == "e" * 64
            aliases = [v for flag, v in zip(args[2:-2:2], args[3:-2:2]) if flag == "--alias"]
            self.rows[args[-1]]["networks"] = {
                "synthetic": {"NetworkID": "", "Aliases": aliases, "IPAMConfig": {}}}
            output = b""
        else:
            raise AssertionError(args)
        self.after_mutation()
        if self.ack == "after":
            raise TimeoutError("SYNTHETIC_PRIVATE_ERROR")
        return output


@pytest.fixture
def backend(tmp_path):
    bindings = {"synthetic": "e" * 64}
    rows, baseline = {}, []
    for i, name in enumerate(core.TARGETS, 1):
        row = {"id": f"{i:064x}", "name": "/" + name, "image": "sha256:" + "a" * 64,
               "state": "running", "started": "2026-10-20T12:00:00Z", "restarts": 2,
               "restart_policy": "no", "attempt": None, "command": ["python", "module.py"],
               "networks": {"synthetic": {"NetworkID": "e" * 64, "Aliases": [name], "IPAMConfig": {}}}}
        rows[row["id"]] = row
        metadata, networks, evidence = docker.configuration.project(row, bindings)
        baseline.append(install.Snapshot(name, row["id"], row["image"], row["state"], row["started"],
            row["restarts"], "no", docker.adapter.preservation_digest(row),
            docker.adapter.preservation_digest({**row, "networks": {}}), ("e" * 64,),
            configured_metadata=metadata, configured_networks=networks, network_evidence=evidence))
    source = tmp_path / "phase1_research_copilot/shared/module.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"fixture")
    applications = tuple({"name": name, "create_options": ["--publish", "127.0.0.1:8002:8002"],
        "command": ["python", "module.py"], "network_options": ["--alias", "production-" + name],
        "sources": [{"local": str(source.relative_to(tmp_path)), "destination": "/app/shared/module.py",
                     "sha256": hashlib.sha256(b"fixture").hexdigest()}]} for name in install.APPS)
    plan = install.Plan("a1" * 8, "d" * 64, tuple(baseline), applications,
                        network_bindings=tuple(bindings.items()), running_storage=True,
                        staged=True, manifest_sha256="f" * 64)
    native = docker.DockerInstallBackend(plan, tmp_path)
    commands = Commands(rows, plan)
    native._command = commands
    return native, commands


def staged(backend):
    native, commands = backend
    name = install.APPS[0]
    identity = native.create_staged(name, "sha256:" + "c" * 64)
    expected = next(r for r in native.inventory(extra_ids=(identity,)) if r["id"] == identity)
    commands.calls.clear()
    return name, expected


def invoke(native, method, name, expected):
    if method == "rename_staged":
        return native.rename_staged(name, expected, name)
    return getattr(native, method)(name, expected)


def test_create_uses_unique_alias_private_transport_and_never_starts(backend):
    native, commands = backend
    name, expected = staged(backend)
    assert expected["name"] == native.plan.staged_name(name)
    assert expected["state"] == "created" and expected["started"] in core.NEVER_STARTED
    commands.calls.clear()
    other = install.APPS[1]
    with pytest.raises(core.Refused):
        native.create_staged(other, "sha256:" + "c" * 64)


def test_create_command_and_existing_name_refusal(backend):
    native, commands = backend
    name = install.APPS[0]
    assert native.create_staged(name, "sha256:" + "c" * 64) == "9" * 64
    args, private = next((a, k) for a, k in commands.calls if a[:2] == ("container", "create"))
    assert args == ("container", "create", "--pull=never", "--name", native.plan.staged_name(name),
        "--network", "e" * 64, "--network-alias", native.plan.staged_name(name),
        "--restart=no", "--label", docker.LABEL + "=" + native.plan.attempt,
        "--label-file", docker.LABEL_DESCRIPTOR, "--env-file", "/dev/stdin",
        "--publish", "127.0.0.1:8002:8002", "sha256:" + "c" * 64, "python", "module.py")
    assert private == {"payload": docker.encode_environment(json.dumps(ENVIRONMENT).encode()), "label_payload": b""}
    assert len(commands.mutations()) == 1
    with pytest.raises(core.Refused):
        native.create_staged(name, "sha256:" + "c" * 64)
    assert len(commands.mutations()) == 1


def test_extra_ids_are_read_only_selection_not_ownership(backend):
    native, commands = backend
    identity = "8" * 64
    commands.rows[identity] = {**deepcopy(commands.rows[native.plan.baseline[3].id]),
                              "id": identity, "name": "/foreign"}
    assert not any(r["id"] == identity for r in native.inventory())
    row = next(r for r in native.inventory(extra_ids=(identity,)) if r["id"] == identity)
    with pytest.raises(core.Refused):
        native.remove_staged(install.APPS[0], row)
    assert not commands.mutations()


@pytest.mark.parametrize("extra", [None, "a" * 64, ("g" * 64,), (None,), ("A" * 64,), tuple(f"{i:064x}" for i in range(5))])
def test_invalid_extra_ids_refused_before_commands(backend, extra):
    native, commands = backend
    with pytest.raises(core.Refused):
        native.inventory(extra_ids=extra)
    assert not commands.calls


def test_verify_sources_hashes_and_compares_fresh_baseline_id_env_after_rename(backend):
    native, commands = backend
    name, expected = staged(backend)
    original = native._before(name)
    commands.rows[original.id]["name"] = "/" + native.plan.rollback_name(name)
    assert native.verify_staged_sources(name, expected) is True
    env_calls = [a for a, _ in commands.calls if a[:4] == ("container", "inspect", "--format", "{{json .Config.Env}}")]
    assert [a[-1] for a in env_calls] == [original.id, expected["id"]]
    assert not commands.mutations()
    assert not any("SYNTHETIC=value" in str(a) for a, _ in commands.calls)


@pytest.mark.parametrize("change", ["original_env", "staged_env", "copied_source", "local_source", "label"])
def test_changed_private_or_source_inputs_refuse(backend, change):
    native, commands = backend
    name, expected = staged(backend)
    if change == "original_env":
        commands.environment[native._before(name).id][0] = "SYNTHETIC=changed"
    elif change == "staged_env":
        commands.environment[expected["id"]][0] = "SYNTHETIC=changed"
    elif change == "copied_source":
        commands.source = b"changed"
    elif change == "local_source":
        (native.root / native._app(name)["sources"][0]["local"]).write_bytes(b"changed")
    else:
        commands.labels[expected["id"]]["extra"] = "changed"
    with pytest.raises(core.Refused, match="^installation_refused$"):
        native.verify_staged_sources(name, expected)
    assert not commands.mutations()


def test_staged_transition_commands_and_renamed_id_visibility(backend):
    native, commands = backend
    name, expected = staged(backend)
    commands.rows[native._before(name).id]["name"] = "/" + native.plan.rollback_name(name)
    assert native.disconnect_staged(name, expected) is True
    expected = next(r for r in native.inventory(extra_ids=(expected["id"],)) if r["id"] == expected["id"])
    assert expected["networks"] == ()
    assert native.rename_staged(name, expected, name) is True
    expected = next(r for r in native.inventory(extra_ids=(expected["id"],)) if r["id"] == expected["id"])
    assert native.connect_staged(name, expected) is True
    expected = next(r for r in native.inventory(extra_ids=(expected["id"],)) if r["id"] == expected["id"])
    assert native.rename_staged(name, expected, native.plan.staged_name(name)) is True
    expected = next(r for r in native.inventory(extra_ids=(expected["id"],)) if r["id"] == expected["id"])
    assert native.remove_staged(name, expected) is True
    assert commands.mutations() == [
        ("network", "disconnect", "e" * 64, expected["id"]),
        ("container", "rename", expected["id"], name),
        ("network", "connect", "--alias", "production-" + name, "e" * 64, expected["id"]),
        ("container", "rename", expected["id"], native.plan.staged_name(name)),
        ("container", "rm", expected["id"])]


METHODS = ["verify_staged_sources", "rename_staged", "disconnect_staged", "connect_staged", "remove_staged"]


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("field,value", [("id", f"{1:064x}"), ("name", "foreign"), ("image", "bad"),
    ("attempt", "other"), ("started", "real-start"), ("state", "exited"), ("restarts", True),
    ("policy", "always"), ("networks", "e" * 64), ("configured_metadata", None)])
def test_invalid_expected_snapshot_never_mutates(backend, method, field, value):
    native, commands = backend
    name, expected = staged(backend)
    expected[field] = value
    with pytest.raises(core.Refused):
        invoke(native, method, name, expected)
    assert not commands.calls


@pytest.mark.parametrize("field", list(install.Snapshot.__dataclass_fields__) + ["unknown"])
def test_missing_or_unknown_expected_keys_refuse(backend, field):
    native, commands = backend
    name, expected = staged(backend)
    if field == "unknown":
        expected[field] = "unexpected"
    else:
        del expected[field]
    with pytest.raises(core.Refused):
        native.remove_staged(name, expected)
    assert not commands.calls


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("change", ["storage", "config", "image", "started", "attempt", "missing", "old_profile"])
def test_stale_inventory_or_old_profile_refuses_before_mutation(backend, method, change):
    native, commands = backend
    name, expected = staged(backend)
    row = commands.rows[expected["id"]]
    if change == "storage":
        commands.rows[native.plan.baseline[0].id]["started"] = "changed"
    elif change == "config":
        row["networks"]["synthetic"]["Aliases"] = ["changed"]
    elif change == "missing":
        del commands.rows[expected["id"]]
    elif change == "old_profile":
        native.plan = replace(native.plan, staged=False)
    else:
        row[change] = {"image": "sha256:" + "b" * 64, "started": "real-start", "attempt": "other"}[change]
    with pytest.raises(core.Refused):
        invoke(native, method, name, expected)
    assert not commands.mutations()


@pytest.mark.parametrize("method", ["rename_staged", "disconnect_staged", "connect_staged", "remove_staged"])
@pytest.mark.parametrize("ack", ["before", "after"])
def test_failed_ack_refuses_without_retry_or_observed_ownership(backend, method, ack):
    native, commands = backend
    name, expected = staged(backend)
    if method == "rename_staged":
        commands.rows[native._before(name).id]["name"] = "/" + native.plan.rollback_name(name)
    if method == "connect_staged":
        commands.rows[expected["id"]]["networks"] = {}
        expected = next(r for r in native.inventory(extra_ids=(expected["id"],)) if r["id"] == expected["id"])
    commands.calls.clear()
    commands.ack = ack
    with pytest.raises(core.Refused, match="^installation_refused$"):
        invoke(native, method, name, expected)
    assert len(commands.mutations()) == 1
    assert commands.calls[-1][0] == commands.mutations()[0]


@pytest.mark.parametrize("method", ["disconnect_staged", "remove_staged"])
def test_storage_change_after_ack_refuses(backend, method):
    native, commands = backend
    name, expected = staged(backend)
    commands.after_mutation = lambda: commands.rows[native.plan.baseline[0].id].update(started="changed")
    with pytest.raises(core.Refused):
        invoke(native, method, name, expected)
    assert len(commands.mutations()) == 1


def test_rename_foreign_occupied_and_same_names_refuse(backend):
    native, commands = backend
    name, expected = staged(backend)
    for target in ("foreign", install.APPS[1], name, expected["name"]):
        with pytest.raises(core.Refused):
            native.rename_staged(name, expected, target)
    assert not commands.mutations()
