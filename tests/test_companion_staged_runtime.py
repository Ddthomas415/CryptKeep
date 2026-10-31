"""Synthetic staged-ID checks only; no Docker, network or operational approval."""
import copy
from dataclasses import replace
import json
import socket
import subprocess

import pytest

from scripts.research import companion_existing_controller as core
from scripts.research import companion_runtime_adapter as adapter
from tests.test_companion_runtime_adapter import FakeDocker, make_pins, seal_fixture_reviews


CHECKS = core.COMPATIBILITY - {"recipient_bindings"}
APP = "phase1-memory"


class StagedDocker(FakeDocker):
    def command(self, args, **kwargs):
        assert args[:2] in {("container", "ls"), ("container", "inspect")}
        assert kwargs.get("input_bytes") is None
        return super().command(args, **kwargs)


@pytest.fixture(autouse=True)
def offline_only(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("staged test attempted real process or network access")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)


@pytest.fixture
def staged(monkeypatch):
    monkeypatch.setattr(core, "_CHILD_CONTEXT", True)
    docker = StagedDocker()
    # Review final configuration with actual new IDs, before adding stage aliases.
    for i, name in enumerate(core.TARGETS, 101):
        row = docker.rows[name]
        if name in adapter.APP_MODULES:
            row.update(id=f"{i:064x}", state="created", started="")
        else:
            row["state"] = "running"
    final_rows = copy.deepcopy(docker.rows)
    pins = make_pins(docker)
    for name in adapter.APP_MODULES:
        original = copy.deepcopy(docker.rows[name])
        original.update(id=f"{core.TARGETS.index(name) + 1:064x}", state="running",
                        started="2026-10-11T00:00:00Z")
        row = docker.rows.pop(name)
        stage_name = name + "-stage-fixture"
        row["name"] = "/" + stage_name
        row["networks"]["research"]["Aliases"] = [stage_name]
        docker.rows[stage_name] = row
        docker.rows[name] = original
    runtime = adapter.PinnedRuntimeAdapter(docker, pins, service_token="FIXTURE_ONLY", enabled=True)
    inventory = runtime.inventory()
    expected = {name: inventory[name + "-stage-fixture" if name in adapter.APP_MODULES else name]
                for name in core.TARGETS}
    docker.calls.clear()
    yield docker, pins, runtime, expected, final_rows
    runtime.close()


def stage_row(docker, expected, name=APP):
    return docker.rows[expected[name].name]


def refresh_expected(docker, expected, name):
    row = stage_row(docker, expected, name)
    expected[name] = core.Container(row["name"].removeprefix("/"), row["id"], row["image"], row["state"],
                                    row["started"], row["restarts"], row["restart_policy"],
                                    adapter.preservation_digest(row))


def assert_refused(result):
    assert set(result) == CHECKS
    assert all(type(value) is bool for value in result.values())
    assert not all(result.values())


def test_staged_checks_use_actual_reviewed_ids_not_original_names_or_final_hashes(staged):
    docker, pins, runtime, expected, _ = staged
    inventory = runtime.inventory()
    for pin in pins.targets[3:]:
        assert pin.container_id == expected[pin.name].id != docker.rows[pin.name]["id"]
        assert pin.preservation_sha256 != expected[pin.name].preservation_digest
        assert inventory[expected[pin.name].name] == expected[pin.name]
    result = runtime.staged_checks(expected)
    assert set(result) == CHECKS and all(value is True for value in result.values())
    assert runtime.pins is pins
    assert {call[0][1] for call in docker.calls if call[0][0] == "container"} == {"ls", "inspect"}
    assert all(call[2] is None for call in docker.calls)
    assert "FIXTURE_ONLY" not in repr(docker.calls) and "FIXTURE_ONLY" not in repr(runtime)


def test_staged_checks_do_not_apply_final_recipient_bindings(staged, monkeypatch):
    _, _, runtime, expected, _ = staged
    def forbidden(*args):
        pytest.fail("staged checks applied final alias bindings")
    monkeypatch.setattr(runtime, "_bindings", forbidden)
    assert all(runtime.staged_checks(expected).values())


def test_final_preservation_subject_still_requires_external_review_binding(staged):
    _, pins, runtime, expected, _ = staged
    runtime.pins = replace(pins, targets=tuple(
        replace(pin, preservation_sha256="f" * 64) if pin.name == APP else pin for pin in pins.targets))
    result = runtime.staged_checks(expected)
    assert_refused(result)
    assert result["installed_source"] is True
    assert all(result[key] is False for key in ("zero_retries", "no_proxy_redirect", "entrypoint_side_effects"))


@pytest.mark.parametrize("enabled,child", [(False, True), (True, False)])
def test_disabled_or_unbounded_staged_checks_are_inert(staged, monkeypatch, enabled, child):
    docker, _, runtime, expected, _ = staged
    runtime._enabled = enabled
    monkeypatch.setattr(core, "_CHILD_CONTEXT", child)
    with pytest.raises(core.Refused, match="adapter_not_authorized_or_not_bounded"):
        runtime.staged_checks(expected)
    assert docker.calls == []


def test_constructor_does_not_inspect_or_read_sources():
    docker = StagedDocker()
    runtime = adapter.PinnedRuntimeAdapter(docker, make_pins(docker), service_token="FIXTURE_ONLY")
    assert docker.calls == []
    runtime.close()


@pytest.mark.parametrize("change", ["missing", "extra", "not_container", "not_map"])
def test_expected_requires_exact_logical_targets(staged, change):
    docker, _, runtime, expected, _ = staged
    if change == "missing":
        del expected[APP]
    elif change == "extra":
        expected["unreviewed"] = expected[APP]
    elif change == "not_container":
        expected[APP] = vars(expected[APP])
    else:
        expected = list(expected.values())
    assert_refused(runtime.staged_checks(expected))
    assert docker.calls == []


@pytest.mark.parametrize("field,value", [("id", "f" * 64), ("image", "sha256:" + "f" * 64),
                                        ("name", "/unreviewed-stage"), ("workdir", "/other"),
                                        ("state", "running"), ("started", "previous-start"),
                                        ("restarts", 1), ("restart_policy", "always")])
def test_changed_actual_stage_snapshot_refuses(staged, field, value):
    docker, _, runtime, expected, _ = staged
    stage_row(docker, expected)[field] = value
    assert_refused(runtime.staged_checks(expected))


@pytest.mark.parametrize("field,value", [("id", "f" * 64), ("image", "sha256:" + "f" * 64),
                                        ("name", "another-stage"), ("preservation_digest", "f" * 64),
                                        ("started_at", "different-history"), ("restarts", False)])
def test_changed_expected_stage_snapshot_refuses(staged, field, value):
    _, _, runtime, expected, _ = staged
    expected[APP] = replace(expected[APP], **{field: value})
    assert_refused(runtime.staged_checks(expected))


@pytest.mark.parametrize("changes", [{"state": "running"}, {"state": "exited"},
                                     {"started": "previous-start"}, {"started": None},
                                     {"restarts": 1}, {"restarts": False}, {"restarts": -1},
                                     {"restart_policy": "always"}, {"name": "/" + APP}])
def test_matching_snapshot_cannot_authorize_started_or_nonstaged_application(staged, changes):
    docker, _, runtime, expected, _ = staged
    stage_row(docker, expected).update(changes)
    refresh_expected(docker, expected, APP)
    if "name" in changes:
        del docker.rows[APP]
    assert_refused(runtime.staged_checks(expected))


@pytest.mark.parametrize("started", core.NEVER_STARTED)
def test_both_never_started_markers_are_supported(staged, started):
    docker, _, runtime, expected, _ = staged
    stage_row(docker, expected)["started"] = started
    refresh_expected(docker, expected, APP)
    assert all(runtime.staged_checks(expected).values())


@pytest.mark.parametrize("name", core.TARGETS[:3])
@pytest.mark.parametrize("field,value", [("state", "exited"), ("started", "changed"),
                                        ("restarts", 1), ("restart_policy", "always"),
                                        ("name", "/renamed-storage"), ("workdir", "/changed")])
def test_running_storage_must_match_immutable_expected(staged, name, field, value):
    docker, _, runtime, expected, _ = staged
    stage_row(docker, expected, name)[field] = value
    assert_refused(runtime.staged_checks(expected))


@pytest.mark.parametrize("field,value", [("state", "exited"), ("name", "/staged-storage")])
def test_matching_snapshot_still_requires_running_normally_named_storage(staged, field, value):
    docker, _, runtime, expected, _ = staged
    name = core.TARGETS[0]
    stage_row(docker, expected, name)[field] = value
    refresh_expected(docker, expected, name)
    assert_refused(runtime.staged_checks(expected))


@pytest.mark.parametrize("key,check", [("NO_TRADING", "no_trading"), ("OPENAI_API_KEY", "no_model"),
                                     ("MEMORY_READ_ONLY_STARTUP", "read_only_startup"),
                                     ("SERVICE_TOKEN", "effective_config"),
                                     ("POSTGRES_PASSWORD", "effective_config"),
                                     ("REQUEST_TIMEOUT_SECONDS", "effective_config")])
@pytest.mark.parametrize("value", [False, None])
def test_reviewed_snapshot_cannot_override_unsafe_or_missing_flags(staged, key, check, value):
    docker, _, runtime, expected, _ = staged
    row = stage_row(docker, expected)
    row["flags"] = [flag for flag in row["flags"] if flag is None or flag["key"] != key]
    if value is not None:
        row["flags"].append({"key": key, "ok": value})
    refresh_expected(docker, expected, APP)
    result = runtime.staged_checks(expected)
    assert_refused(result)
    assert result[check] is False


def test_duplicate_flags_raise_fixed_refusal(staged):
    docker, _, runtime, expected, _ = staged
    stage_row(docker, expected)["flags"].append({"key": "NO_TRADING", "ok": True})
    refresh_expected(docker, expected, APP)
    with pytest.raises(core.Refused, match="ambiguous_environment_flags"):
        runtime.staged_checks(expected)


@pytest.mark.parametrize("change", ["manifest", "dependency_records", "topical", "schema"])
def test_unapproved_or_unbound_policy_reviews_refuse(staged, change):
    _, pins, runtime, expected, _ = staged
    if change == "manifest":
        runtime.pins = replace(pins, review_manifest=pins.review_manifest + b" ")
    elif change == "dependency_records":
        runtime.pins = replace(pins, dependency_review_records=())
    elif change == "topical":
        runtime.pins = replace(pins, topical_approvals=())
    else:
        manifest = json.loads(pins.review_manifest)
        manifest["schema"] = "companion-configured-install-v3"
        raw = adapter._canonical(manifest)
        runtime.pins = replace(pins, review_manifest=raw, review_record_sha256=adapter.hashlib.sha256(raw).hexdigest())
    result = runtime.staged_checks(expected)
    assert_refused(result)
    assert all(result[key] is False for key in ("zero_retries", "no_proxy_redirect", "entrypoint_side_effects"))


@pytest.mark.parametrize("change", ["bytes", "coverage", "sdk_coverage"])
def test_actual_sources_and_required_sdk_coverage_remain_mandatory(staged, change):
    docker, pins, runtime, expected, _ = staged
    pin = next(pin for pin in pins.targets if pin.name == APP)
    if change == "bytes":
        docker.files[pin.container_id, pin.source_sha256[0][0]] = b"changed synthetic source"
    else:
        path = "/app/shared/config.py" if change == "coverage" else next(
            path for path, _ in pin.source_sha256 if "/qdrant_client/" in path)
        pin = replace(pin, source_sha256=tuple(item for item in pin.source_sha256 if item[0] != path))
        runtime.pins = seal_fixture_reviews(replace(pins, targets=tuple(
            pin if original.name == APP else original for original in pins.targets)))
    result = runtime.staged_checks(expected)
    assert_refused(result)
    assert result["installed_source"] is False
    assert all(result[key] is False for key in ("zero_retries", "no_proxy_redirect", "entrypoint_side_effects"))


@pytest.mark.parametrize("marker", [b"", b"15\n", b"16"])
def test_pg_version_marker_is_still_required(staged, marker):
    docker, pins, runtime, expected, _ = staged
    pg = pins.targets[0]
    docker.files[pg.container_id, "/var/lib/postgresql/data/PG_VERSION"] = marker
    result = runtime.staged_checks(expected)
    assert_refused(result)
    assert result["entrypoint_side_effects"] is False


@pytest.mark.parametrize("failure", ["cli", "token", "token_newline"])
def test_cli_and_token_guards_remain_inert(staged, failure):
    docker, _, runtime, expected, _ = staged
    if failure == "cli":
        docker.cli_ok = False
    else:
        runtime._token = "" if failure == "token" else "FIXTURE_ONLY\n"
    assert_refused(runtime.staged_checks(expected))
    assert docker.calls == []


def test_staged_success_is_not_final_compatibility_or_activation(staged):
    docker, pins, runtime, expected, final_rows = staged
    assert all(runtime.staged_checks(expected).values())
    assert not any(runtime.compatibility(expected).values())
    docker.rows = final_rows
    baseline = runtime.inventory()
    assert all(runtime.compatibility(baseline).values())
    assert runtime.pins is pins


@pytest.mark.parametrize("change", ["alias", "preservation"])
def test_final_recipient_and_preservation_checks_remain_mandatory(staged, change):
    docker, _, runtime, expected, final_rows = staged
    assert all(runtime.staged_checks(expected).values())
    docker.rows = final_rows
    if change == "alias":
        docker.rows["alias-thief"] = {**copy.deepcopy(final_rows[APP]), "name": "/alias-thief", "id": "f" * 64}
    else:
        docker.rows[APP]["workdir"] = "/not-reviewed-final"
    result = runtime.compatibility(runtime.inventory())
    assert not all(result.values())
    if change == "alias":
        assert result["recipient_bindings"] is False
