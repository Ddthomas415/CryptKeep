"""Pure adapter fixtures. Never invoke Docker, live HTTP or real credentials."""
from dataclasses import replace
import hashlib
import json
import os
import socket
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.research import companion_existing_controller as core
from scripts.research import companion_runtime_adapter as adapter


@pytest.fixture(autouse=True)
def no_real_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("offline adapter test attempted real network access")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class FakeDocker:
    def __init__(self):
        self.calls, self.files = [], {}
        self.cli_ok = True
        self.pg_result = {"postgres": True, "documents": True, "audit_events": True}
        self.head = b"200"
        self.rows = {}
        for i, name in enumerate(core.TARGETS, 1):
            port = str(adapter.PORTS[name])
            volume = adapter.VOLUMES.get(name)
            self.rows[name] = {
                "id": f"{i:064x}", "name": "/" + name, "image": "sha256:" + f"{i:064x}",
                "state": "exited", "started": "2026-10-11T00:00:00Z", "restarts": 0, "restart_policy": "no",
                "mounts": [{"Type": "volume", "Driver": "local", "Name": volume[0], "Destination": volume[1]}] if volume else [],
                "networks": {"research": {"NetworkID": "n" * 64, "Aliases": [adapter.ALIASES[name]],
                                            "IPAddress": "", "EndpointID": ""}},
                "ports": {port + "/tcp": [{"HostIp": "127.0.0.1", "HostPort": port}]},
                "entrypoint": ["/reviewed/entrypoint"], "command": ["reviewed-service"], "healthcheck": {},
                "workdir": "/app", "flags": [{"key": k, "ok": True} for k in sorted(set(adapter.ENV_EXPECTED) | adapter.SECRET_PRESENCE)] + [None],
            }

    def command(self, args, *, timeout, input_bytes=None, limit=1_048_576):
        self.calls.append((args, timeout, input_bytes))
        if args[:2] == ("container", "ls"):
            return ("\n".join(r["id"] for r in self.rows.values()) + "\n").encode()
        if args[:2] == ("container", "inspect"):
            assert args[3] == adapter.INSPECT_FORMAT
            return b"\n".join(json.dumps(r).encode() for r in self.rows.values())
        if args[:2] == ("container", "exec"):
            if "FIXTURE_SCRIPT" in args:
                return json.dumps({"checks": dict.fromkeys(core.EVIDENCE, True),
                                   "diagnostic": {"stage": "complete", "code": "ok"}}).encode()
            if adapter._PG_CHECK in args:
                assert input_bytes == adapter._SCHEMA_SQL.encode()
                return json.dumps(self.pg_result).encode()
            if adapter._MINIO_HEAD in args:
                assert input_bytes is None
                return self.head
            return json.dumps(dict.fromkeys(core.EVIDENCE, True)).encode()
        if args[:2] in (("container", "start"), ("container", "stop")):
            return b""
        raise AssertionError("unexpected synthetic command")

    def read_file(self, container_id, path, limit=1_048_576):
        self.calls.append((("read_file", container_id, path), limit, None))
        return self.files[container_id, path]

    def verify_cli(self):
        return self.cli_ok


def make_pins(docker):
    pins = []
    for name in core.TARGETS:
        row = docker.rows[name]
        paths = set()
        if name in adapter.APP_MODULES:
            paths |= adapter.required_app_sources(name)
            if name == "phase1-memory":
                paths |= {"/usr/local/lib/python3.11/site-packages/" + p + "/client.py" for p in
                          ("qdrant_client", "httpx", "httpcore", "botocore", "boto3", "urllib3", "psycopg")}
        if name == "phase1-timescaledb":
            paths.add("/usr/local/bin/docker-entrypoint.sh")
            docker.files[row["id"], "/var/lib/postgresql/data/PG_VERSION"] = b"16\n"
        if name == "phase1-minio":
            paths |= {"/usr/bin/curl", "/bin/bash"}
        for path in paths:
            docker.files[row["id"], path] = (name + path).encode()
        pins.append(adapter.TargetPin(name, row["id"], row["image"], adapter.preservation_digest(row),
                                      tuple(sorted((p, sha(docker.files[row["id"], p])) for p in paths))))
    return seal_fixture_reviews(adapter.ReviewedPins(tuple(pins), "a" * 64, (),
                                                    ({"document_id": 42, "question": core.QUESTION,
                                                      "original_content_hash": "c" * 64, "body_sha256": "d" * 64,
                                                      "excerpt": "SYNTHETIC reviewed witness"},)))


def seal_fixture_reviews(pins):
    """Synthetic accepted records ONLY: not a real operator approval generator."""
    subjects = [adapter._subject(p) for p in pins.targets]
    records, reviews = [], []
    for image in sorted({p.image_id for p in pins.targets}):
        record = adapter._canonical({"schema": "companion-installed-policy-review-v1", "decision": "ACCEPTED_WITH_RISK",
                                     "reviewer": "synthetic-test-reviewer", "image_id": image,
                                     "subjects": [s for s in subjects if s["image_id"] == image],
                                     "policies": dict.fromkeys(("zero_retries", "no_proxy_redirect", "entrypoint_side_effects"), "SHOWN")})
        records.append(record)
        reviews.append((image, sha(record)))
    manifest = adapter._canonical({"schema": "companion-runtime-pins-v1", "decision": "ACCEPTED_WITH_RISK",
                                   "reviewer": "synthetic-test-reviewer", "subjects": subjects,
                                   "dependency_reviews": dict(reviews),
                                   "topical_approvals_sha256": sha(adapter._canonical(pins.topical_approvals))})
    return replace(pins, dependency_review_sha256=tuple(reviews), dependency_review_records=tuple(records),
                   review_manifest=manifest, review_record_sha256=sha(manifest))


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setattr(core, "_CHILD_CONTEXT", True)
    docker = FakeDocker()
    pins = make_pins(docker)
    runtime = adapter.PinnedRuntimeAdapter(docker, pins, service_token="FIXTURE_ONLY", enabled=True)
    yield docker, pins, runtime
    runtime.close()


@pytest.mark.parametrize("schema", ["companion-install-v1", "companion-stopped-install-v2",
                                    "companion-configured-install-v3"])
def test_install_schema_cannot_authorize_runtime_even_with_other_valid_fields(setup, schema):
    _, pins, runtime = setup
    data = json.loads(pins.review_manifest)
    data["schema"] = schema
    raw = adapter._canonical(data)
    runtime.pins = replace(pins, review_manifest=raw, review_record_sha256=sha(raw))
    assert runtime._policy_reviews_match({p.name: p for p in pins.targets}) is False


def test_constructor_and_disabled_adapter_are_inert(monkeypatch):
    docker = FakeDocker()
    runtime = adapter.PinnedRuntimeAdapter(docker, make_pins(docker), service_token="FIXTURE_ONLY")
    assert docker.calls == [] and "FIXTURE_ONLY" not in repr(runtime)
    with pytest.raises(core.Refused):
        runtime.inventory()
    assert docker.calls == []


def test_compatibility_derives_flags_and_compares_exact_sources(setup):
    docker, _, runtime = setup
    result = runtime.compatibility(runtime.inventory())
    assert set(result) == core.COMPATIBILITY
    assert all(v is True for v in result.values())
    assert any(call[0][0] == "read_file" for call in docker.calls)
    # Source hashes and synthetic review records here are NOT live acceptance.


@pytest.mark.parametrize("field", ["container_id", "image_id", "preservation_sha256"])
def test_changed_pin_refuses_before_lifecycle(setup, field):
    docker, pins, runtime = setup
    value = "sha256:" + "f" * 64 if field == "image_id" else "f" * 64
    runtime.pins = replace(pins, targets=(replace(pins.targets[0], **{field: value}),) + pins.targets[1:])
    assert not all(runtime.compatibility(runtime.inventory()).values())
    assert not any(c[0][:2] == ("container", "start") for c in docker.calls)


@pytest.mark.parametrize("key", ["NO_TRADING", "OPENAI_API_KEY", "SERVICE_TOKEN", "POSTGRES_PASSWORD",
                                  "MINIO_ENDPOINT", "MEMORY_READ_ONLY_STARTUP", "REQUEST_TIMEOUT_SECONDS"])
def test_unsafe_or_missing_effective_config_never_passes(setup, key):
    docker, pins, runtime = setup
    flags = docker.rows["phase1-memory"]["flags"]
    flags[:] = [f for f in flags if f is None or f["key"] != key]
    # Re-pin metadata only to isolate the semantic config check.
    p = next(p for p in pins.targets if p.name == "phase1-memory")
    runtime.pins = replace(pins, targets=tuple(replace(x, preservation_sha256=adapter.preservation_digest(docker.rows[x.name]))
                                             if x == p else x for x in pins.targets))
    assert not all(runtime.compatibility(runtime.inventory()).values())


def test_duplicate_environment_flags_are_ambiguous(setup):
    docker, _, runtime = setup
    docker.rows["phase1-memory"]["flags"].append({"key": "NO_TRADING", "ok": True})
    with pytest.raises(core.Refused):
        runtime._flags(docker.rows["phase1-memory"])


def test_inspect_format_never_requests_raw_environment():
    assert "{{json .Config.Env}}" not in adapter.INSPECT_FORMAT
    assert "{{.Config.Env}}" not in adapter.INSPECT_FORMAT
    assert "SERVICE_TOKEN=" in adapter.INSPECT_FORMAT
    assert "{{ne ." in adapter.INSPECT_FORMAT


def test_optional_healthcheck_uses_null_preserving_map_lookup():
    assert '"healthcheck":{{json (index .Config "Healthcheck")}}' in adapter.INSPECT_FORMAT
    assert ".Config.Healthcheck" not in adapter.INSPECT_FORMAT


@pytest.mark.parametrize("healthcheck", [None, {"Test": ["CMD", "/health"]}])
def test_metadata_keeps_optional_healthcheck_and_unrelated_container(setup, healthcheck):
    docker, _, runtime = setup
    unrelated = dict(docker.rows["phase1-audit-log"])
    unrelated.update(id="f" * 64, name="/unrelated", healthcheck=healthcheck)
    docker.rows["unrelated"] = unrelated
    rows = runtime._metadata()
    assert len(rows) == len(core.TARGETS) + 1
    assert rows["unrelated"]["healthcheck"] == healthcheck
    assert rows["phase1-audit-log"] == docker.rows["phase1-audit-log"]
    assert all(call[0][:2] in {("container", "ls"), ("container", "inspect")}
               for call in docker.calls)


def test_dynamic_address_fields_do_not_change_preservation_identity(setup):
    docker, _, _ = setup
    row = docker.rows["phase1-memory"]
    before = adapter.preservation_digest(row)
    row["networks"]["research"].update(IPAddress="172.18.0.5", EndpointID="allocated")
    assert adapter.preservation_digest(row) == before


@pytest.mark.parametrize("mutation", [
    lambda d: d.rows["phase1-memory"]["ports"]["8007/tcp"][0].update(HostIp="0.0.0.0"),
    lambda d: d.rows["phase1-risk-stub"]["networks"]["research"].update(NetworkID="another"),
    lambda d: d.rows["phase1-orchestrator"]["networks"]["research"].update(Aliases=[]),
    lambda d: d.rows["phase1-minio"]["mounts"][0].update(Name="other-volume"),
])
def test_recipient_or_volume_binding_change_rejected(setup, mutation):
    docker, _, runtime = setup
    mutation(docker)
    assert runtime._bindings(docker.rows) is False


@pytest.mark.parametrize("driver", [None, "nfs", "remote"])
def test_storage_driver_must_be_explicitly_local_even_with_matching_pins(setup, driver):
    docker, _, runtime = setup
    docker.rows["phase1-minio"]["mounts"][0]["Driver"] = driver
    runtime.pins = make_pins(docker)
    result = runtime.compatibility(runtime.inventory())
    assert result["recipient_bindings"] is False


@pytest.mark.parametrize("mutation", [
    lambda p: replace(p, review_manifest=b""),
    lambda p: replace(p, dependency_review_records=()),
    lambda p: replace(p, dependency_review_sha256=tuple((i, "c" * 64) for i, _ in p.dependency_review_sha256)),
    lambda p: replace(p, review_manifest=p.review_manifest + b" "),
    lambda p: replace(p, topical_approvals=({"document_id": 99},)),
])
def test_hash_shapes_or_changed_unbound_records_are_not_policy_proof(setup, mutation):
    _, pins, runtime = setup
    runtime.pins = mutation(pins)
    result = runtime.compatibility(runtime.inventory())
    assert all(result[k] is False for k in ("zero_retries", "no_proxy_redirect", "entrypoint_side_effects"))


def test_custom_resolution_or_duplicate_service_alias_is_not_pinned_identity(setup):
    docker, _, runtime = setup
    row = docker.rows["phase1-orchestrator"]
    row["extra_hosts"] = ["memory-retrieval:203.0.113.1"]
    assert runtime._bindings(docker.rows) is False
    row["extra_hosts"] = []
    docker.rows["unrelated"] = {"networks": {"research": {"NetworkID": "n" * 64, "Aliases": ["memory-retrieval"]}}}
    assert runtime._bindings(docker.rows) is False


def test_mismatched_installed_source_and_pg_version_never_pass(setup):
    docker, pins, runtime = setup
    p = next(p for p in pins.targets if p.name == "phase1-memory")
    docker.files[p.container_id, p.source_sha256[0][0]] = b"changed"
    result = runtime.compatibility(runtime.inventory())
    assert result["installed_source"] is False and result["zero_retries"] is False
    assert result["entrypoint_side_effects"] is False


def test_missing_topical_review_or_token_aborts_preflight(setup):
    docker, pins, runtime = setup
    runtime.pins = replace(pins, topical_approvals=())
    assert not any(runtime.compatibility(runtime.inventory()).values())
    runtime.pins, runtime._token = pins, ""
    assert not any(runtime.compatibility(runtime.inventory()).values())


def test_lifecycle_exact_ids_only_and_no_recreate(setup):
    docker, pins, runtime = setup
    with pytest.raises(core.Refused):
        runtime.start("f" * 64)
    runtime.start(pins.targets[0].container_id)
    assert docker.calls[-1][0] == ("container", "start", pins.targets[0].container_id)
    docker.rows[pins.targets[0].name]["state"] = "running"
    runtime.stop(pins.targets[0].container_id, 8)
    assert docker.calls[-1][0] == ("container", "stop", "--time", "8", pins.targets[0].container_id)


@pytest.mark.parametrize("name", core.TARGETS[3:])
@pytest.mark.parametrize("started", ["", "0001-01-01T00:00:00Z"])
def test_created_application_start_is_pinned_and_allowed(setup, name, started):
    docker, _, runtime = setup
    row = docker.rows[name]
    row.update(state="created", started=started)
    runtime.start(row["id"])
    assert docker.calls[-1][0] == ("container", "start", row["id"])


@pytest.mark.parametrize("name", core.TARGETS[:3])
def test_created_storage_start_refused(setup, name):
    docker, _, runtime = setup
    row = docker.rows[name]
    row.update(state="created", started="")
    with pytest.raises(core.Refused):
        runtime.start(row["id"])
    assert not any(call[0][:2] == ("container", "start") for call in docker.calls)


@pytest.mark.parametrize("changes", [
    {"started": "previous-start"}, {"started": None}, {"restarts": 1},
    {"restarts": False}, {"restart_policy": "always"}, {"state": "paused"},
])
def test_created_application_bad_history_refused(setup, changes):
    docker, _, runtime = setup
    row = docker.rows[core.TARGETS[3]]
    row.update(state="created", started="")
    row.update(changes)
    with pytest.raises(core.Refused):
        runtime.start(row["id"])
    assert not any(call[0][:2] == ("container", "start") for call in docker.calls)


def test_storage_checks_before_apps_use_internal_auth_and_read_only_sql(setup, monkeypatch):
    docker, _, runtime = setup
    monkeypatch.setattr(runtime, "_http", lambda *a, **k: b"ready")
    monkeypatch.setattr(runtime, "_json", lambda *a, **k: {"status": "ok"})
    assert all(runtime.storage_checks().values())
    commands = json.dumps(docker.calls, default=lambda value: value.decode("utf-8"))
    assert "FIXTURE_ONLY" not in commands
    assert "BEGIN READ ONLY" in commands and "ROLLBACK" in commands
    assert "PGPASSWORD" in commands  # variable reference only; no value exported
    minio_exec = next(call[0] for call in docker.calls if adapter._MINIO_HEAD in call[0])
    assert minio_exec == ("container", "exec", next(p.container_id for p in runtime.pins.targets if p.name == "phase1-minio"),
                          "/bin/bash", "-p", "-c", adapter._MINIO_HEAD)
    docker.head = b"404"
    assert runtime.storage_checks()["namespaces"] is False


def test_minio_source_pins_require_regular_bash_not_shell_alias(setup):
    docker, pins, runtime = setup
    minio = next(pin for pin in pins.targets if pin.name == "phase1-minio")
    legacy = replace(minio, source_sha256=tuple(("/bin/sh" if path == "/bin/bash" else path, sha)
                                               for path, sha in minio.source_sha256))
    runtime.pins = seal_fixture_reviews(replace(pins, targets=tuple(legacy if pin.name == minio.name else pin for pin in pins.targets)))
    assert runtime._source_coverage(runtime._pins()) is False


def test_pinned_bash_mode_ignores_inherited_startup_file(tmp_path):
    import subprocess
    startup = tmp_path / "synthetic_bash_env"
    startup.write_text("printf synthetic_startup_ran\n")
    env = {"BASH_ENV": str(startup)}
    control = subprocess.run(("/bin/bash", "-c", ":"), env=env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2, check=True)
    restricted = subprocess.run(("/bin/bash", "-p", "-c", ":"), env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2, check=True)
    assert control.stdout == b"synthetic_startup_ran"
    assert restricted.stdout == b"" and restricted.stderr == b""


def test_unknown_http_recipient_refused_before_client_construction(setup, monkeypatch):
    import httpx
    _, _, runtime = setup
    monkeypatch.setattr(httpx, "Client", lambda *a, **k: pytest.fail("HTTP constructed"))
    with pytest.raises(core.Refused):
        runtime._http(8003, "/healthz")
    with pytest.raises(core.Refused):
        runtime._http(6333, "/healthz", auth=True)


def test_http_transport_never_proxies_redirects_or_leaks_auth(setup, monkeypatch):
    import httpx
    _, _, runtime = setup
    real = httpx.Client
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"ok": True})
    def client(**kwargs):
        assert kwargs["trust_env"] is False and kwargs["follow_redirects"] is False
        assert kwargs["timeout"].connect == 2 and kwargs["timeout"].read == 5
        kwargs["transport"] = httpx.MockTransport(handler)
        return real(**kwargs)
    monkeypatch.setattr(httpx, "Client", client)
    runtime._http(6333, "/healthz")
    runtime._http(8008, "/v1/risk/status", auth=True)
    assert "Authorization" not in seen[0].headers
    assert seen[1].headers["Authorization"] == "Bearer FIXTURE_ONLY"
    assert all(r.headers["X-CryptKeep-Probe"] == core.PROTOCOL for r in seen)


@pytest.mark.parametrize("failure", [None, "risk", "memory", "model", "audit"])
def test_health_checks_keep_safety_connectivity_separate(setup, monkeypatch, failure):
    _, _, runtime = setup
    responses = {
        (8009, "/healthz"): {"service": "audit-log", "ok": True},
        (8009, "/v1/audit/events/recent?limit=1"): {"ok": True, "events": []},
        (8008, "/healthz"): {"service": "risk-stub", "ok": True, "no_trading": True},
        (8008, "/v1/risk/status"): {"gate": "NO_TRADING", "allow_trading": False, "execution_mode": "DISABLED"},
        (8007, "/healthz"): {"service": "memory-retrieval", "ok": True, "db": True, "qdrant": True,
                              "minio": True, "memory_read_only_startup": True},
        (8002, "/healthz"): {"service": "orchestrator", "ok": True, "no_trading": True, "openai_enabled": False},
    }
    if failure == "risk":
        responses[8008, "/v1/risk/status"]["allow_trading"] = True
    if failure == "memory":
        responses[8007, "/healthz"]["db"] = False
    if failure == "model":
        responses[8002, "/healthz"]["openai_enabled"] = True
    if failure == "audit":
        responses[8009, "/v1/audit/events/recent?limit=1"]["ok"] = False
    monkeypatch.setattr(runtime, "_json", lambda port, path, **kw: responses[port, path])
    result = runtime.health_checks()
    assert all(result.values()) is (failure is None)


def test_query_uses_existing_dashboard_probe_and_evidence_is_private_stdin(setup, monkeypatch):
    docker, pins, runtime = setup
    monkeypatch.setattr(core, "dashboard_probe", lambda token: {"token_supplied": token == "FIXTURE_ONLY"})
    assert runtime.explain() == {"token_supplied": True}
    # No actual query is sent by this fixture.
    from scripts.research.companion_evidence_checks import diagnostic_result_valid
    monkeypatch.setitem(__import__("sys").modules, "scripts.research.companion_evidence_checks",
                        SimpleNamespace(DIAGNOSTIC_EVIDENCE_SCRIPT="FIXTURE_SCRIPT",
                                        diagnostic_result_valid=diagnostic_result_valid))
    assert all(runtime.verify_evidence({"asset": "BTC"}).values())
    argv, cap, body = docker.calls[-1]
    assert argv[:3] == ("container", "exec", "-i") and cap == 10
    assert "FIXTURE_ONLY" not in repr(argv) and b"FIXTURE_ONLY" not in body
    assert json.loads(body)["raw"] == {"asset": "BTC"}


def test_private_pipe_consumed_and_closed_without_file_fallback(tmp_path):
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"FIXTURE_ONLY")
    os.close(write_fd)
    assert adapter.token_from_pipe(read_fd) == "FIXTURE_ONLY"
    with pytest.raises(OSError):
        os.fstat(read_fd)
    path = tmp_path / "not-a-token-channel"
    path.write_bytes(b"FIXTURE_ONLY")
    fd = os.open(path, os.O_RDONLY)
    with pytest.raises(core.Refused):
        adapter.token_from_pipe(fd)


@pytest.mark.parametrize("payload", [b"", b"fixture\n", b"fixture\r", b"a" * 4097, b"\x00"])
def test_token_channel_invalid_payload_never_returns_secret(payload):
    read_fd, write_fd = os.pipe()
    os.write(write_fd, payload)
    os.close(write_fd)
    with pytest.raises(core.Refused) as error:
        adapter.token_from_pipe(read_fd)
    assert "fixture" not in str(error.value)
