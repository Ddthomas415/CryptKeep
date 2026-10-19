"""Offline saved-daemon fixtures; configured identity is not connectivity."""
import copy
import json
from pathlib import Path

import pytest

from scripts.research import companion_network_configuration as network
from scripts.research import companion_runtime_adapter as adapter

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "docs/review_artifacts/companion_install_candidate_20261018"


@pytest.fixture
def observations():
    before = json.loads((ARTIFACTS / "capture/observation.json").read_bytes())["observations"]
    after = json.loads((ARTIFACTS / "recovery_after_capture/observation.json").read_bytes())["observations"]
    bindings = {name: data["NetworkID"] for row in before for name, data in row["networks"].items()}
    return before, after, bindings


def test_actual_stopped_reconnect_preserves_raw_mismatch_and_separate_configuration(observations):
    before, after, bindings = observations
    saved = copy.deepcopy(after)
    for left, right in zip(before, after):
        digest, ids, evidence = network.project(right, bindings)
        assert digest == network.project(left, bindings)[0]
        assert ids == tuple(sorted(bindings.values()))
        assert evidence[0][2] == ("configured_only" if right["networks"][next(iter(bindings))]["NetworkID"] == "" else "reported_id")
    assert adapter.preservation_digest(before[3]) != adapter.preservation_digest(after[3])
    assert after == saved


@pytest.mark.parametrize("change", ["wrong_id", "unknown_name", "missing_id", "endpoint", "address", "bad_bindings"])
def test_unresolved_or_contradictory_identity_is_refused(observations, change):
    _, after, bindings = observations
    row = copy.deepcopy(after[3])
    name = next(iter(bindings))
    if change == "wrong_id":
        row["networks"][name]["NetworkID"] = "f" * 64
    elif change == "unknown_name":
        row["networks"]["unknown"] = row["networks"].pop(name)
    elif change == "missing_id":
        del row["networks"][name]["NetworkID"]
    elif change == "endpoint":
        row["networks"][name]["EndpointID"] = "e" * 64
    elif change == "address":
        row["networks"][name]["IPAddress"] = "192.0.2.1"
    else:
        bindings = {name: "not-an-id"}
    with pytest.raises(ValueError, match="^network_configuration_refused$"):
        network.project(row, bindings)


@pytest.mark.parametrize("change", ["aliases", "static_ip", "health", "mount", "flag"])
def test_configuration_drift_remains_visible(observations, change):
    _, after, bindings = observations
    row = copy.deepcopy(after[3])
    original = network.project(row, bindings)[0]
    name = next(iter(bindings))
    if change == "aliases":
        row["networks"][name]["Aliases"] = ["different"]
    elif change == "static_ip":
        row["networks"][name]["IPAMConfig"] = {"IPv4Address": "192.0.2.1"}
    elif change == "health":
        row["healthcheck"] = {"Test": ["CMD", "different"]}
    elif change == "mount":
        row["mounts"] = [{"Source": "/different", "Destination": "/app", "RW": True}]
    else:
        row["flags"] = [{"key": "NO_TRADING", "ok": False}]
    assert network.project(row, bindings)[0] != original
