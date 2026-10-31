"""Saved observations: correct model inputs without relaxing runtime comparisons."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import runpy
import socket
import subprocess

import pytest

from scripts.research import companion_installer as install
from scripts.research import companion_network_configuration as network
from scripts.research import companion_runtime_adapter as adapter
from scripts.research import companion_staged_update as staged

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "docs/review_artifacts/companion_continuation_20261021/reconcile_metadata_20261021.py"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("reconciliation attempted native or network operation")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    read_bytes = Path.read_bytes
    def public_only(path):
        if ".cbp_state" in path.parts:
            pytest.fail("reconciliation attempted private operational-state access")
        return read_bytes(path)
    monkeypatch.setattr(Path, "read_bytes", public_only)


@pytest.fixture
def case():
    recipe = runpy.run_path(str(RECIPE))
    raw = recipe["inputs"]()
    draft, provenance = recipe["derive"](raw)
    old = install.Plan.load(raw["manifest"], recipe["INPUTS"]["manifest"][1])
    # Synthetic acceptance stays local to the test; no artifact is approved.
    accepted = {**draft, "decision": "ACCEPTED_WITH_RISK", "reviewer": "SYNTHETIC_ONLY"}
    accepted_raw = install.canonical(accepted)
    plan = install.Plan.load(accepted_raw, hashlib.sha256(accepted_raw).hexdigest())
    diagnostic = json.loads(raw["diagnostic"])
    return recipe, raw, draft, provenance, old, plan, diagnostic


def final_row(case, index=0):
    _, _, _, _, _, plan, diagnostic = case
    row = deepcopy(diagnostic["rows"][index])
    row["name"] = "/" + plan.applications[index]["name"]
    for net in row["networks"].values():
        net["Aliases"] = plan.applications[index]["network_options"][1::2]
    configured, ids, evidence = network.project(row, dict(plan.network_bindings))
    snapshot = install.Snapshot(row["name"].removeprefix("/"), row["id"], row["image"],
        row["state"], row["started"], row["restarts"], row["restart_policy"],
        adapter.preservation_digest(row), adapter.preservation_digest({**row, "networks": {}}),
        tuple(sorted(n["NetworkID"] for n in row["networks"].values())), row["attempt"],
        configured, ids, evidence)
    return row, snapshot


def checks(plan, snapshot, index=0):
    runner = install.Installer(None, None)
    runner.plan = plan
    runner.images = {plan.applications[index]["name"]: snapshot.image}
    return runner._replacement_checks(snapshot, plan.baseline[3 + index])


def test_only_four_predictions_and_unapproved_review_fields_change(case):
    _, raw, draft, provenance, old, plan, _ = case
    restored = deepcopy(draft)
    previous = json.loads(raw["manifest"])
    restored["decision"], restored["reviewer"] = previous["decision"], previous["reviewer"]
    for app, before in zip(restored["applications"], previous["applications"]):
        assert app["replacement_configured_metadata"] != before["replacement_configured_metadata"]
        app["replacement_configured_metadata"] = before["replacement_configured_metadata"]
    assert restored == previous and len(provenance["changes"]) == 4
    assert old.baseline == plan.baseline and old.attempt == plan.attempt
    assert old.deferred_startup_policies == plan.deferred_startup_policies
    with pytest.raises(install.core.Refused):
        install.Plan.load(install.canonical(draft), install.digest(draft))


def test_public_fixture_hash_and_provenance_do_not_need_private_state(case):
    recipe, raw, _, provenance, *_ = case
    assert all(".cbp_state" not in Path(path).parts for path, _ in recipe["INPUTS"].values())
    assert hashlib.sha256(raw["evidence"]).hexdigest() == provenance["original_evidence"]["sha256"]
    assert provenance["original_evidence"]["public_copy_byte_identical"] is True


@pytest.mark.parametrize("index", range(4))
def test_unchanged_gate_accepts_corrected_model_but_not_old_prediction(case, index):
    _, _, _, _, old, plan, _ = case
    row, snapshot = final_row(case, index)
    before = deepcopy(row)
    assert all(checks(plan, snapshot, index).values())
    assert checks(old, snapshot, index)["metadata_matches"] is False
    assert row == before


@pytest.mark.parametrize("field,value", [("dns", ["203.0.113.1"]),
    ("extra_hosts", ["audit-log:203.0.113.1"]), ("dns", []), ("extra_hosts", [])])
def test_nonempty_or_different_empty_representation_still_fails(case, field, value):
    _, _, _, _, _, plan, _ = case
    row, snapshot = final_row(case)
    row[field] = value
    changed = replace(snapshot, configured_metadata=network.project(row, dict(plan.network_bindings))[0])
    assert checks(plan, changed)["metadata_matches"] is False


@pytest.mark.parametrize("change", ["staged_alias", "other_alias", "flag", "port", "mount"])
def test_unrelated_policy_or_alias_change_still_fails(case, change):
    _, _, _, _, _, plan, diagnostic = case
    row, snapshot = final_row(case)
    if change.endswith("alias"):
        for net in row["networks"].values():
            net["Aliases"] = [diagnostic["rows"][0]["name"].removeprefix("/")] if change == "staged_alias" else ["wrong"]
    elif change == "flag":
        row["flags"] = [{"key": "NO_TRADING", "ok": False}]
    elif change == "port":
        row["ports"] = {"8009/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8009"}]}
    else:
        row["mounts"] = [{"Source": "/other", "Destination": "/app", "RW": True}]
    changed = replace(snapshot, configured_metadata=network.project(row, dict(plan.network_bindings))[0])
    assert checks(plan, changed)["metadata_matches"] is False


def test_old_evidence_cannot_be_silently_used_with_corrected_manifest(case):
    _, raw, _, _, old, plan, _ = case
    evidence = json.loads(raw["evidence"])
    old_rows = staged._rows(old, evidence)
    with pytest.raises(install.core.Refused):
        staged._rows(plan, evidence)
    rebound = {**evidence, "manifest_sha256": plan.manifest_sha256}
    assert staged._rows(plan, rebound) == old_rows
    assert json.loads(raw["evidence"]) == evidence


@pytest.mark.parametrize("key", ["manifest", "evidence", "diagnostic"])
def test_changed_source_artifact_refused_before_derivation(case, key):
    recipe, raw, *_ = case
    with pytest.raises(ValueError, match="^reconciliation_input_changed$"):
        recipe["derive"]({**raw, key: raw[key] + b" "})


@pytest.mark.parametrize("field,value", [("id", "a" * 64), ("image", "sha256:" + "b" * 64),
    ("state", "running"), ("started", "2026-10-21T00:00:00Z"), ("restarts", 1),
    ("policy", "always"), ("attempt", "wrong")])
def test_identity_and_lifecycle_gates_remain_independent_of_corrected_metadata(case, field, value):
    _, raw, _, _, _, plan, _ = case
    evidence = {**json.loads(raw["evidence"]), "manifest_sha256": plan.manifest_sha256}
    encoded = install.canonical(evidence)
    review = {"schema": "companion-preparation-review-v1", "decision": "ACCEPTED_WITH_RISK",
              "reviewer": "SYNTHETIC_ONLY", "manifest_sha256": plan.manifest_sha256,
              "evidence_sha256": hashlib.sha256(encoded).hexdigest()}
    review_raw = install.canonical(review)
    pin = hashlib.sha256(review_raw).hexdigest()
    assert len(staged.ReviewedPreparation.load(encoded, review_raw, pin, plan).replacements) == 4
    evidence["replacements"][0][field] = value
    with pytest.raises(install.core.Refused):
        staged.ReviewedPreparation.load(install.canonical(evidence), review_raw, pin, plan)
