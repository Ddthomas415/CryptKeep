"""Real installer/runtime composition over synthetic native metadata, never Docker."""
import copy
from dataclasses import asdict, replace
import json
import socket
import subprocess

import pytest

from scripts.research import companion_docker_transport as transport
from scripts.research import companion_existing_controller as core
from scripts.research import companion_installer as install
from scripts.research import companion_network_configuration as configuration
from scripts.research import companion_runtime_adapter as adapter
from tests.test_companion_existing_controller import probe
from tests.test_companion_installer import Inline, Receipt
from tests.test_companion_runtime_adapter import FakeDocker, make_pins


NETWORK_ID = "e" * 64
BINDINGS = {"research": NETWORK_ID}
ATTEMPT = "a1" * 8
APP = "phase1-memory"
NETWORK_FORMAT = '{"id":{{json .Id}},"name":{{json .Name}}}'


@pytest.fixture(autouse=True)
def offline_only(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("composition test attempted real socket or process access")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(core, "_CHILD_CONTEXT", True)


def snapshot(row):
    configured, networks, evidence = configuration.project(row, BINDINGS)
    return install.Snapshot(
        row["name"].removeprefix("/"), row["id"], row["image"], row["state"], row["started"],
        row["restarts"], row["restart_policy"], adapter.preservation_digest(row),
        adapter.preservation_digest({**row, "networks": {}}),
        tuple(sorted(network["NetworkID"] for network in row["networks"].values())),
        attempt=row.get("attempt", ""), configured_metadata=configured,
        configured_networks=networks, network_evidence=evidence)


class NativeDocker(FakeDocker):
    def __init__(self):
        super().__init__()
        self.events, self.stuck = [], set()
        self.network_rows = [{"id": NETWORK_ID, "name": "research"}]
        for row in self.rows.values():
            row.update(state="running", network_mode=NETWORK_ID)
            row["networks"]["research"].update(NetworkID=NETWORK_ID, IPAMConfig=None)

    def command(self, args, **kwargs):
        transport._arguments(args)
        if args[:2] == ("network", "inspect"):
            assert args == ("network", "inspect", "--format", NETWORK_FORMAT, NETWORK_ID)
            assert kwargs.get("input_bytes") is None
            self.calls.append((args, kwargs["timeout"], None))
            self.events.append(("network_inspect",))
            return b"\n".join(json.dumps(row).encode() for row in self.network_rows)
        if args[:2] == ("container", "start"):
            row = next(row for row in self.rows.values() if row["id"] == args[-1])
            name = row["name"].removeprefix("/")
            assert name in install.APPS and row["state"] == "created"
            assert row["networks"]["research"]["NetworkID"] == ""
            row.update(state="running", started="2026-10-20T16:00:00Z")
            if name not in self.stuck:
                row["networks"]["research"].update(
                    NetworkID=NETWORK_ID, IPAMConfig=None, IPAddress="172.18.0.10", EndpointID="attached")
            self.events.append(("start", name))
        return super().command(args, **kwargs)


class RecordingAdapter(adapter.PinnedRuntimeAdapter):
    def recipient_checks(self):
        result = super().recipient_checks()
        self.transport.events.append(("recipients", result["recipient_bindings"]))
        return result


class InventoryBackend:
    """Share native rows with the real adapter, not independently canned snapshots."""
    def __init__(self, docker):
        self.docker = docker

    def inventory(self, extra_ids=()):
        return [asdict(snapshot(row)) for row in self.docker.rows.values()]


@pytest.fixture
def composition(monkeypatch):
    docker = NativeDocker()
    baseline = tuple(snapshot(docker.rows[name]) for name in core.TARGETS)
    for i, name in enumerate(install.APPS, 101):
        original = docker.rows[name]
        backup = copy.deepcopy(original)
        backup.update(name="/" + name + "-rollback-" + ATTEMPT, state="exited", networks={})
        docker.rows[backup["name"].removeprefix("/")] = backup
        replacement = copy.deepcopy(original)
        replacement.update(id=f"{i:064x}", state="created", started="", restarts=0, attempt=ATTEMPT)
        replacement["networks"]["research"].update(
            NetworkID="", IPAMConfig={}, IPAddress="", EndpointID="")
        docker.rows[name] = replacement
    pins = make_pins(docker)
    runtime = RecordingAdapter(docker, pins, service_token="FIXTURE_ONLY", enabled=True)
    plan = install.Plan(ATTEMPT, "d" * 64, baseline, (), network_bindings=tuple(BINDINGS.items()),
                        running_storage=True, staged=True, manifest_sha256="f" * 64)
    receipt = Receipt()
    runner = install.Installer(InventoryBackend(docker), receipt, executor=Inline(), clock=lambda: 0)
    runner._initialize(plan, runtime)

    def http(port, path, **kwargs):
        if port in {adapter.PORTS[name] for name in install.APPS}:
            assert ("recipients", True) in docker.events
            docker.events.append(("application_http", port, path))
        responses = {
            (6333, "/collections/documents"): {"status": "ok"},
            (8009, "/healthz"): {"service": "audit-log", "ok": True},
            (8009, "/v1/audit/events/recent?limit=1"): {"ok": True, "events": []},
            (8008, "/healthz"): {"service": "risk-stub", "ok": True, "no_trading": True},
            (8008, "/v1/risk/status"): {
                "gate": "NO_TRADING", "allow_trading": False, "execution_mode": "DISABLED"},
            (8007, "/healthz"): {"service": "memory-retrieval", "ok": True, "db": True,
                                  "qdrant": True, "minio": True, "memory_read_only_startup": True},
            (8002, "/healthz"): {"service": "orchestrator", "ok": True,
                                  "no_trading": True, "openai_enabled": False},
        }
        return json.dumps(responses.get((port, path), {"ok": True})).encode()

    def query(token):
        assert token == "FIXTURE_ONLY" and ("recipients", True) in docker.events
        docker.events.append(("query",))
        return probe()

    monkeypatch.setattr(runtime, "_http", http)
    monkeypatch.setattr(core, "dashboard_probe", query)
    yield docker, runtime, runner, receipt
    runtime.close()


def configured(runtime):
    result = runtime.configured_compatibility(runtime.inventory(), BINDINGS)
    assert set(result) == core.COMPATIBILITY
    assert all(type(value) is bool for value in result.values())
    return result


def test_native_created_projection_passes_without_promoting_raw_connectivity(composition):
    docker, runtime, _, _ = composition
    before = copy.deepcopy(docker.rows)
    baseline = runtime.inventory()
    strict = runtime.compatibility(baseline)
    assert strict["recipient_bindings"] is False
    assert all(value is True for key, value in strict.items() if key != "recipient_bindings")
    assert all(configured(runtime).values())
    assert runtime.recipient_checks() == {"recipient_bindings": False}
    assert docker.rows == before
    assert any(call[0][:2] == ("network", "inspect") for call in docker.calls)
    assert not any(call[0][:2] in {("container", "start"), ("container", "exec")} for call in docker.calls)


@pytest.mark.parametrize("rows", [[{"id": NETWORK_ID, "name": "other"}],
                                  [{"id": "f" * 64, "name": "research"}], [],
                                  [{"id": NETWORK_ID, "name": "research"}] * 2])
def test_daemon_network_identity_must_match_freshly_each_time(composition, rows):
    docker, runtime, _, _ = composition
    assert all(configured(runtime).values())
    docker.network_rows = rows
    assert configured(runtime)["recipient_bindings"] is False


@pytest.mark.parametrize("change", ["alias", "public_port", "wrong_port", "extra_host", "dns", "mount"])
def test_projection_does_not_waive_recipient_policy_even_with_matching_pins(composition, change):
    docker, runtime, _, _ = composition
    row = docker.rows[APP]
    if change == "alias":
        row["networks"]["research"]["Aliases"] = ["unreviewed-alias"]
    elif change in {"public_port", "wrong_port"}:
        row["ports"]["8007/tcp"][0].update(
            {"HostIp": "0.0.0.0"} if change == "public_port" else {"HostPort": "9999"})
    elif change == "extra_host":
        row["extra_hosts"] = ["memory-retrieval:203.0.113.1"]
    elif change == "dns":
        row["dns"] = ["203.0.113.1"]
    else:
        docker.rows["phase1-minio"]["mounts"][0]["Driver"] = "nfs"
    runtime.pins = make_pins(docker)
    assert configured(runtime)["recipient_bindings"] is False


@pytest.mark.parametrize("key,check", [("NO_TRADING", "no_trading"), ("OPENAI_API_KEY", "no_model"),
                                     ("MEMORY_READ_ONLY_STARTUP", "read_only_startup"),
                                     ("SERVICE_TOKEN", "effective_config")])
def test_projected_network_does_not_waive_effective_environment(composition, key, check):
    docker, runtime, _, _ = composition
    flags = docker.rows[APP]["flags"]
    flags[:] = [flag for flag in flags if flag is None or flag["key"] != key]
    runtime.pins = make_pins(docker)
    assert configured(runtime)[check] is False


def test_projected_network_does_not_waive_actual_source_bytes(composition):
    docker, runtime, _, _ = composition
    pin = next(pin for pin in runtime.pins.targets if pin.name == APP)
    docker.files[pin.container_id, pin.source_sha256[0][0]] = b"changed synthetic source"
    result = configured(runtime)
    assert result["installed_source"] is False
    assert result["zero_retries"] is False and result["entrypoint_side_effects"] is False


def test_projection_does_not_waive_external_policy_reviews(composition):
    _, runtime, _, _ = composition
    runtime.pins = replace(runtime.pins, review_manifest=runtime.pins.review_manifest + b" ")
    result = configured(runtime)
    assert result["zero_retries"] is False and result["no_proxy_redirect"] is False


@pytest.mark.parametrize("changes", [{"state": "running"}, {"state": "exited"},
                                     {"started": "previous-start"}, {"restarts": False},
                                     {"restarts": 1}, {"restart_policy": "always"}])
def test_blank_network_requires_never_started_created_applications(composition, changes):
    docker, runtime, _, _ = composition
    docker.rows[APP].update(changes)
    assert configured(runtime)["recipient_bindings"] is False


@pytest.mark.parametrize("field", ["EndpointID", "IPAddress", "IPv6Address", "GlobalIPv6Address",
                                  "Gateway", "IPv6Gateway"])
def test_blank_network_cannot_hide_endpoint_or_address_evidence(composition, field):
    docker, runtime, _, _ = composition
    docker.rows[APP]["networks"]["research"][field] = "unexpected-evidence"
    assert configured(runtime)["recipient_bindings"] is False


@pytest.mark.parametrize("network_name", ["research", "unbound-network"])
def test_unreviewed_blank_alias_owner_is_not_projected_away(composition, network_name):
    docker, runtime, _, _ = composition
    thief = copy.deepcopy(docker.rows[APP])
    thief.update(id="f" * 64, name="/alias-thief")
    thief["networks"] = {network_name: {"NetworkID": "", "Aliases": [adapter.ALIASES[APP]]}}
    docker.rows["alias-thief"] = thief
    assert configured(runtime)["recipient_bindings"] is False


def test_raw_recipient_gate_stays_false_until_all_four_actual_starts(composition):
    docker, runtime, _, _ = composition
    assert all(configured(runtime).values())
    for index, name in enumerate(install.APPS):
        assert runtime.recipient_checks() == {"recipient_bindings": False}
        runtime.start(docker.rows[name]["id"])
        assert runtime.recipient_checks() == {"recipient_bindings": index == 3}
    assert not any(event[0] in {"application_http", "query"} for event in docker.events)


@pytest.mark.parametrize("field,value", [("id", "f" * 64), ("image", "sha256:" + "f" * 64),
                                        ("restart_policy", "always")])
def test_poststart_recipients_still_require_pinned_identity(composition, field, value):
    docker, runtime, _, _ = composition
    for name in install.APPS:
        runtime.start(docker.rows[name]["id"])
    assert runtime.recipient_checks() == {"recipient_bindings": True}
    docker.rows[APP][field] = value
    assert runtime.recipient_checks() == {"recipient_bindings": False}


def test_installer_and_real_adapter_bridge_native_blank_shape_before_health_and_query(composition):
    docker, runtime, runner, receipt = composition
    assert all(configured(runtime).values())
    expected = {row.name: row for row in map(snapshot, docker.rows.values())}
    runner._verify_running_update(expected)
    assert runner.query_verified and runner.query_attempted
    assert len(runner.replacement_started) == 4
    starts = [index for index, event in enumerate(docker.events) if event[0] == "start"]
    recipients = docker.events.index(("recipients", True))
    app_http = next(index for index, event in enumerate(docker.events) if event[0] == "application_http")
    assert len(starts) == 4 and max(starts) < recipients < app_http < docker.events.index(("query",))
    assert sum(event == ("query",) for event in docker.events) == 1
    assert "FIXTURE_ONLY" not in json.dumps(receipt.events)
    assert all(docker.rows[name]["networks"]["research"]["NetworkID"] == NETWORK_ID for name in install.APPS)


def test_installer_refuses_unattached_started_app_before_health_or_query(composition):
    docker, _, runner, _ = composition
    docker.stuck.add(APP)
    expected = {row.name: row for row in map(snapshot, docker.rows.values())}
    with pytest.raises(core.Refused):
        runner._verify_running_update(expected)
    assert sum(event[0] == "start" for event in docker.events) == 4
    assert ("recipients", False) in docker.events
    assert not any(event[0] in {"application_http", "query"} for event in docker.events)
    assert not runner.query_attempted and not runner.query_verified
