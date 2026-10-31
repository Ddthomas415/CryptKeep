"""Opt-in model/loader/adapter composition. Synthetic authority only; no Docker."""
from copy import deepcopy
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import socket
import subprocess

import pytest

from scripts.research import companion_cutover as entry
from scripts.research import companion_existing_controller as core
from scripts.research import companion_network_configuration as network
from scripts.research import companion_runtime_adapter as adapter
from tests.test_companion_cutover_inputs import inputs, write_pins
from tests.test_companion_runtime_adapter import make_pins, seal_fixture_reviews
from tests.test_companion_staged_composition import composition, BINDINGS, APP


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("active-network test attempted real process/network access")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(core, "_CHILD_CONTEXT", True)


def v2(pins, bindings):
    pins = seal_fixture_reviews(pins)
    record = json.loads(pins.review_manifest)
    record.update(schema="companion-runtime-pins-v2", network_configuration={
        "contract": network.CONTRACT, "bindings": bindings})
    raw = adapter._canonical(record)
    return replace(pins, review_manifest=raw, review_record_sha256=adapter.hashlib.sha256(raw).hexdigest())


def upgrade(composition):
    docker, runtime, runner, expected = composition
    pins = make_pins(docker)
    targets = tuple(replace(p, preservation_sha256=network.project(docker.rows[p.name], BINDINGS)[0])
                    if p.name in adapter.APP_MODULES else p for p in pins.targets)
    runtime.pins = v2(replace(pins, targets=targets), BINDINGS)
    return docker, runtime, runner, expected


@pytest.mark.parametrize("reported", [False, True])
@pytest.mark.parametrize("ipam", [None, {}])
def test_composed_gate_start_and_query_keep_raw_inventory(composition, reported, ipam):
    docker, runtime, runner, expected = upgrade(composition)
    for name in adapter.APP_MODULES:
        attachment = docker.rows[name]["networks"]["research"]
        attachment["IPAMConfig"] = deepcopy(ipam)
        # Native fixture starts configured-only rows; this representation is
        # checked separately, then returned to the fixture's pre-start shape.
        attachment["NetworkID"] = BINDINGS["research"] if reported else ""
    inventory = runtime.inventory()
    report = runtime.configured_compatibility(inventory, BINDINGS)
    assert report["precondition"] == {"predicate": "complete", "target": None}
    assert all(report["checks"].values())
    for name in adapter.APP_MODULES:
        assert runtime._target(docker.rows[name]["id"])[0].name == name
        assert inventory[name].preservation_digest == adapter.preservation_digest(docker.rows[name])
        docker.rows[name]["networks"]["research"]["NetworkID"] = ""
    expected = runner._rows()
    runner._verify_running_update(expected)
    assert sum(e[0] == "query" for e in docker.events) == 1
    assert all(docker.rows[n]["state"] == "running" for n in adapter.APP_MODULES)


@pytest.mark.parametrize("change", ["network", "alias", "ipam", "image", "id", "source", "health", "flags"])
def test_drift_refused_before_start(composition, change):
    docker, runtime, _, _ = upgrade(composition)
    row = docker.rows[APP]
    if change == "network":
        row["networks"]["research"]["NetworkID"] = "f" * 64
    elif change == "alias":
        row["networks"]["research"]["Aliases"].append("unexpected-daemon-alias")
    elif change == "ipam":
        row["networks"]["research"]["IPAMConfig"] = {"IPv4Address": "192.0.2.8"}
    elif change in {"image", "id"}:
        row[change] = ("sha256:" if change == "image" else "") + "f" * 64
    elif change == "source":
        pin = next(p for p in runtime.pins.targets if p.name == APP)
        docker.files[pin.container_id, pin.source_sha256[0][0]] = b"changed"
    elif change == "health":
        row["healthcheck"] = {"Test": ["CMD", "changed"]}
    else:
        next(f for f in row["flags"] if f and f["key"] == "NO_TRADING")["ok"] = False
    try:
        report = runtime.configured_compatibility(runtime.inventory(), BINDINGS)
        passed = all(report["checks"].values())
        if change in {"network", "alias", "ipam", "health", "flags"}:
            assert report["precondition"] == {"predicate": "preservation", "target": APP}
        elif change in {"image", "id"}:
            assert report["precondition"] == {"predicate": "image" if change == "image" else "identity", "target": APP}
    except (core.Refused, ValueError):
        passed = False
    assert not passed
    with pytest.raises((core.Refused, ValueError)):
        runtime.start(next(p.container_id for p in runtime.pins.targets if p.name == APP))
    assert not any(e[0] == "start" for e in docker.events)


def test_stale_blank_id_rejected_after_start(composition):
    docker, runtime, _, _ = upgrade(composition)
    row = docker.rows[APP]
    row.update(state="running", started="2026-10-23T12:00:00Z")
    with pytest.raises(core.Refused, match="network_configuration_refused"):
        runtime._target(row["id"])


def test_alias_order_duplicates_preserved_but_extra_name_not_ignored(composition):
    docker, _, _, _ = composition
    row = deepcopy(docker.rows[APP])
    aliases = ["memory", APP]
    model = network.final_model(row, BINDINGS, aliases)
    other = network.final_model(row, BINDINGS, list(reversed(aliases)) + aliases)
    assert network.project(model, BINDINGS)[0] == network.project(other, BINDINGS)[0]
    assert network.project(network.final_model(row, BINDINGS, aliases + ["unexpected"]), BINDINGS)[0] != network.project(model, BINDINGS)[0]


@pytest.mark.parametrize("reported", [False, True])
@pytest.mark.parametrize("ipam", [None, {}])
def test_producer_loader_share_opt_in_contract(inputs, reported, ipam):
    bindings = dict(inputs.plan.network_bindings)
    targets = list(inputs.pins.targets)
    for index, (app, row) in enumerate(zip(inputs.plan.applications, inputs.metadata["rows"]), 3):
        row = deepcopy(row)
        for name, attachment in row["networks"].items():
            attachment.update(NetworkID=bindings[name] if reported else "", IPAMConfig=deepcopy(ipam))
        subject = network.final_subject(adapter._subject(targets[index]), row, bindings, app["network_options"][1::2])
        targets[index] = replace(targets[index], preservation_sha256=subject["preservation_sha256"])
    pins = v2(replace(inputs.pins, targets=tuple(targets)), bindings)
    write_pins(inputs, pins)
    assert entry.load_inputs(inputs.args)[2] == pins
    # A self-consistent but wrong final pin still cannot replace the plan.
    target = replace(pins.targets[3], preservation_sha256="f" * 64)
    write_pins(inputs, v2(replace(pins, targets=pins.targets[:3] + (target,) + pins.targets[4:]), bindings))
    with pytest.raises(core.Refused):
        entry.load_inputs(inputs.args)


def test_changed_binding_or_unreviewed_contract_is_not_an_override(composition):
    docker, runtime, _, _ = upgrade(composition)
    with pytest.raises(core.Refused, match="network_binding_changed"):
        runtime.configured_compatibility(runtime.inventory(), {"research": "f" * 64})
    manifest = json.loads(runtime.pins.review_manifest)
    manifest["network_configuration"]["bindings"]["research"] = "f" * 64
    runtime.pins = replace(runtime.pins, review_manifest=adapter._canonical(manifest))
    with pytest.raises(core.Refused, match="network_review_invalid"):
        runtime._target(docker.rows[APP]["id"])


def test_historical_counterfactual_is_inert_and_preserves_storage():
    root = Path(__file__).resolve().parents[1]
    base = root / "docs/review_artifacts/companion_worker_preparation_20261023"
    spec = importlib.util.spec_from_file_location("active_proposal", base / "derive_active_network_proposal.py")
    recipe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recipe)
    result = recipe.derive()
    original = json.loads((base / recipe.INPUTS["subjects"][0]).read_bytes())
    assert result["candidate_subjects"][:3] == original[:3]
    assert all(a["preservation_sha256"] != b["preservation_sha256"] for a, b in zip(result["candidate_subjects"][3:], original[3:]))
    assert result["state"] == "INCOMPLETE" and result["evidence"] == "MODELLED"
    assert result["historical_removed_ids_only"] and not result["runtime_authorized"]
