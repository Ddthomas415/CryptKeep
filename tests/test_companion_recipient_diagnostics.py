"""Offline recipient reasons and receipt boundary; no native services or tokens."""
from copy import deepcopy
import json
import socket
import subprocess

import pytest

from scripts.research import companion_existing_controller as core
from scripts.research import companion_runtime_adapter as adapter
from tests.test_companion_active_network_contract import upgrade
from tests.test_companion_staged_composition import composition, BINDINGS, APP
from tests.test_companion_running_update import harness, run


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("recipient diagnostic test attempted native process/network access")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(core, "_CHILD_CONTEXT", True)


def reason(predicate="alias_owner", role="selected", target=APP, category="none"):
    return {"schema": adapter.BINDING_DIAGNOSTIC_SCHEMA, "predicate": predicate,
            "role": role, "target": target, "exception_category": category}


@pytest.mark.parametrize("change,predicate,role,target,category", [
    ("binding", "bindings_contract", "none", None, "invalid_input"),
    ("inspect", "network_inspect", "none", None, "timeout"),
    ("json", "network_inspect", "none", None, "invalid_input"),
    ("identity", "network_identity", "none", None, "none"),
    ("target_networks", "target_networks", "selected", APP, "none"),
    ("started", "configured_eligibility", "selected", APP, "none"),
    ("address", "network_projection", "selected", APP, "invalid_input"),
    ("wrong_id", "network_projection", "selected", APP, "invalid_input"),
    ("outsider_same", "configured_eligibility", "unselected", None, "none"),
    ("outsider_other", "unselected_alias_without_id", "unselected", None, "none"),
    ("dns", "dns_override", "selected", APP, "none"),
    ("ports", "loopback_ports", "selected", APP, "none"),
    ("alias", "recipient_alias", "selected", APP, "none"),
    ("mount", "storage_mount", "selected", "phase1-qdrant", "none"),
    ("alias_owner", "alias_owner", "unselected", None, "none"),
])
def test_configured_reasons_preserve_refusal_and_hide_values(
        composition, monkeypatch, change, predicate, role, target, category):
    docker, runtime, _, _ = composition
    rows, bindings = deepcopy(docker.rows), dict(BINDINGS)
    attachment = rows[APP]["networks"]["research"]
    if change == "binding":
        bindings = {"SYNTHETIC_SECRET": "invalid"}
    elif change in {"inspect", "json"}:
        original = runtime._command
        def command(args, **kwargs):
            if args[:2] == ("network", "inspect"):
                if change == "inspect":
                    raise TimeoutError("SYNTHETIC_SECRET")
                return b"SYNTHETIC_SECRET"
            return original(args, **kwargs)
        monkeypatch.setattr(runtime, "_command", command)
    elif change == "identity":
        docker.network_rows[0]["id"] = "f" * 64
    elif change == "target_networks":
        rows[APP]["networks"] = {}
    elif change == "started":
        rows[APP].update(state="running", started="2026-10-24T00:00:00Z")
    elif change == "address":
        attachment["IPAddress"] = "SYNTHETIC_SECRET"
    elif change == "wrong_id":
        attachment["NetworkID"] = "f" * 64
    elif change.startswith("outsider") or change == "alias_owner":
        outsider = deepcopy(rows[APP])
        outsider.update(name="/SYNTHETIC_SECRET", id="f" * 64)
        net = outsider["networks"].pop("research")
        net["Aliases"] = [adapter.ALIASES[APP]]
        if change == "alias_owner":
            net["NetworkID"] = BINDINGS["research"]
        outsider["networks"]["other" if change == "outsider_other" else "research"] = net
        rows["SYNTHETIC_SECRET"] = outsider
    elif change == "dns":
        rows[APP]["dns"] = ["SYNTHETIC_SECRET"]
    elif change == "ports":
        rows[APP]["ports"] = {}
    elif change == "alias":
        attachment["Aliases"] = ["SYNTHETIC_SECRET"]
    else:
        rows["phase1-qdrant"]["mounts"] = []
    original_rows = deepcopy(rows)
    diagnostic = {}
    assert runtime._configured_bindings(rows, bindings) is False
    assert runtime._configured_bindings(rows, bindings, diagnostic=diagnostic) is False
    assert diagnostic == reason(predicate, role, target, category)
    assert rows == original_rows
    assert "SYNTHETIC_SECRET" not in json.dumps(diagnostic)
    assert adapter.sanitize_binding_diagnostic(diagnostic) == diagnostic


@pytest.mark.parametrize("change,predicate", [
    ("networks", "network_count"), ("split", "shared_network"),
])
def test_raw_recipient_predicates_remain_strict(composition, change, predicate):
    docker, runtime, _, _ = composition
    rows = deepcopy(docker.rows)
    for name in core.TARGETS:
        rows[name]["networks"]["research"]["NetworkID"] = BINDINGS["research"]
    if change == "networks":
        rows[APP]["networks"]["extra"] = deepcopy(rows[APP]["networks"]["research"])
    else:
        rows[APP]["networks"]["research"]["NetworkID"] = "f" * 64
    diagnostic = {}
    assert runtime._bindings(rows) is False
    assert runtime._bindings(rows, diagnostic=diagnostic) is False
    assert diagnostic == reason(predicate, "selected" if change == "networks" else "none",
                                APP if change == "networks" else None)


@pytest.mark.parametrize("error,category", [
    (ValueError, "invalid_input"), (KeyError, "invalid_input"),
    (core.Refused, "refused"), (TimeoutError, "timeout"), (RuntimeError, "operation_error"),
])
def test_exception_categories_are_fixed(composition, monkeypatch, error, category):
    docker, runtime, _, _ = composition
    def fail(*args, **kwargs):
        raise error("SYNTHETIC_SECRET")
    monkeypatch.setattr(runtime, "_command", fail)
    diagnostic = {}
    assert runtime._configured_bindings(docker.rows, BINDINGS, diagnostic=diagnostic) is False
    assert diagnostic == reason("network_inspect", "none", None, category)


def test_v2_success_and_failure_envelope_does_not_retain_stale_reason(composition):
    docker, runtime, _, _ = upgrade(composition)
    inventory = runtime.inventory()
    report = runtime.configured_compatibility(inventory, BINDINGS)
    assert all(report["checks"].values()) and report["recipient_diagnostic"] is None
    docker.network_rows[0]["id"] = "f" * 64
    report = runtime.configured_compatibility(inventory, BINDINGS)
    assert report["checks"]["recipient_bindings"] is False
    assert report["precondition"] == {"predicate": "complete", "target": None}
    assert report["recipient_diagnostic"] == reason("network_identity", "none", None)
    docker.network_rows[0]["id"] = BINDINGS["research"]
    assert runtime.configured_compatibility(inventory, BINDINGS)["recipient_diagnostic"] is None


@pytest.mark.parametrize("bad", [
    None, [], "SYNTHETIC_SECRET", {},
    {**reason(), "predicate": "SYNTHETIC_SECRET"},
    {**reason(), "predicate": []},
    {**reason(), "exception_category": ["SYNTHETIC_SECRET"]},
    {**reason(), "role": "SYNTHETIC_SECRET"},
    {**reason(), "role": "unselected"},
    {**reason(), "target": "SYNTHETIC_SECRET"},
    {**reason(), "extra": "SYNTHETIC_SECRET"},
])
def test_receipt_boundary_drops_malformed_diagnostics_without_weakening_refusal(bad):
    h = harness()
    _, backend, receipt, _, runtime = h
    checks = dict.fromkeys(core.COMPATIBILITY, True)
    checks["recipient_bindings"] = False
    runtime.compatibility_result = {"checks": checks,
        "precondition": {"predicate": "complete", "target": None}, "recipient_diagnostic": bad}
    result = run(h)
    assert not result["running_update_complete"] and result["rollback_verified"]
    event = next(e for e in receipt.events if e["phase"] == "runtime_compatibility_checks")
    assert event["installation_evidence"]["recipient_diagnostic"] is None
    assert event["installation_evidence"]["checks"]["recipient_bindings"] is False
    assert not any(method in {"runtime_start", "runtime_explain"} for method, _ in backend.calls)
    assert "SYNTHETIC_SECRET" not in json.dumps(receipt.events)


def test_valid_diagnostic_reaches_receipt_before_cleanup_without_authorizing_start():
    h = harness()
    _, backend, receipt, _, runtime = h
    checks = dict.fromkeys(core.COMPATIBILITY, True)
    checks["recipient_bindings"] = False
    diagnostic = reason("configured_eligibility", "unselected", None)
    runtime.compatibility_result = {"checks": checks,
        "precondition": {"predicate": "complete", "target": None},
        "recipient_diagnostic": diagnostic}
    result = run(h)
    assert not result["running_update_complete"] and result["rollback_verified"]
    event = next(e for e in receipt.events if e["phase"] == "runtime_compatibility_checks")
    assert event["installation_evidence"]["recipient_diagnostic"] == diagnostic
    assert receipt.events.index(event) < next(i for i, e in enumerate(receipt.events)
                                             if e["phase"] == "remove_replacement_intended")
    assert not any(method in {"runtime_start", "runtime_explain"} for method, _ in backend.calls)


@pytest.mark.parametrize("change,passes", [
    ("dormant_nonrecipient", True), ("reserved_alias", False),
    ("running", False), ("previous_start", False), ("restart_count", False),
    ("boolean_restart_count", False), ("restart_policy", False),
    ("address", False), ("endpoint", False), ("wrong_network_id", False),
])
def test_unselected_dormant_nonrecipient_does_not_block_selected_apps(composition, change, passes):
    docker, runtime, _, _ = upgrade(composition)
    row = deepcopy(docker.rows[APP])
    row.update(name="/unselected-dormant", id="f" * 64)
    attachment = row["networks"]["research"]
    attachment["Aliases"] = ["unselected-dormant"]
    if change == "reserved_alias":
        attachment["Aliases"].append(adapter.ALIASES[APP])
    elif change == "running":
        row["state"] = "running"
    elif change == "previous_start":
        row["started"] = "2026-10-23T00:00:00Z"
    elif change == "restart_count":
        row["restarts"] = 1
    elif change == "boolean_restart_count":
        row["restarts"] = False
    elif change == "restart_policy":
        row["restart_policy"] = "always"
    elif change == "address":
        attachment["IPAddress"] = "192.0.2.1"
    elif change == "endpoint":
        attachment["EndpointID"] = "not-empty"
    elif change == "wrong_network_id":
        attachment["NetworkID"] = "a" * 64
    docker.rows["unselected-dormant"] = row
    before = deepcopy(docker.rows)
    report = runtime.configured_compatibility(runtime.inventory(), BINDINGS)
    assert report["checks"]["recipient_bindings"] is passes
    assert report["precondition"] == {"predicate": "complete", "target": None}
    assert all(value for key, value in report["checks"].items() if key != "recipient_bindings")
    assert docker.rows == before
    assert not any(event[0] in {"start", "query", "application_http"} for event in docker.events)
    if passes:
        assert report["recipient_diagnostic"] is None
        assert row["networks"]["research"]["NetworkID"] == ""
        assert runtime._bindings(docker.rows) is False  # No post-start attachment inferred.
    else:
        assert report["recipient_diagnostic"]["role"] == "unselected"
        assert report["recipient_diagnostic"]["target"] is None


def test_selected_storage_blank_network_remains_refused(composition):
    docker, runtime, _, _ = composition
    docker.rows["phase1-qdrant"]["networks"]["research"]["NetworkID"] = ""
    diagnostic = {}
    assert runtime._configured_bindings(docker.rows, BINDINGS, diagnostic=diagnostic) is False
    assert diagnostic == reason("configured_eligibility", "selected", "phase1-qdrant")
