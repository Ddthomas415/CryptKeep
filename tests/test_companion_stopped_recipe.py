"""Offline reconstruction, receipt validation and private-label pipe contracts."""
import copy
import json
import os
from pathlib import Path
import sys

import pytest

from scripts.research import companion_docker_transport as transport
from scripts.research import companion_install_env as encoder
from scripts.research import companion_runtime_adapter as adapter
from scripts.research import collect_companion_recreation_metadata as capture
from scripts.research.collect_companion_recreation_metadata import reconcile_manifest
from scripts.research.prepare_companion_stopped_recipe import compile_recipe

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def evidence():
    observation = json.loads((ROOT / "docs/review_artifacts/companion_recreation_metadata_20261017/capture4/observation.json").read_bytes())
    source = (ROOT / "docs/review_artifacts/companion_install_manifest_20261017/manifest.json").read_bytes()
    return observation, source


@pytest.mark.parametrize("change", ["id", "image", "name", "snapshot", "restart", "duplicate", "final"])
def test_receipt_forgery_is_rejected(evidence, change):
    observation, source = evidence
    if change in {"id", "image", "name"}:
        observation["observations"][0][change] = "forged"
    elif change == "snapshot":
        observation["snapshots"][0]["metadata"] = "0" * 64
    elif change == "restart":
        observation["observations"][0]["restarts"] = True
    elif change == "duplicate":
        observation["observations"][1] = copy.deepcopy(observation["observations"][0])
    else:
        observation["final_observations"] = []
    with pytest.raises(ValueError):
        reconcile_manifest(observation, source)


def test_legacy_evidence_not_upgraded_to_paired_proof(evidence):
    result = compile_recipe(*evidence)
    assert result["paired_payload_verified"] is False
    assert result["fingerprint_version"] == 2 and result["installation_authorized"] is False
    for app in result["applications"]:
        assert app["create_options"][2:4] == ["--log-driver", "local"]
        assert app["missing_executable_fields"] == []
        assert "MODELLED" in app["replacement_metadata_evidence"]
        assert app["network_options"]
    mount = result["applications"][-1]["create_options"]
    assert "--mount" in mount and "readonly,bind-propagation=rprivate" in mount[mount.index("--mount") + 1]


def test_paired_payload_can_be_verified_offline(evidence):
    observation, source = evidence
    observation["final_observations"] = copy.deepcopy(observation["observations"])
    assert reconcile_manifest(observation, source)["paired_payload_verified"] is True


@pytest.mark.parametrize("change", ["metadata", "foundation", "network", "extra_key",
                                   "missing_key", "relabeled_v2", "observation_row"])
def test_legacy_compatibility_still_rejects_tampered_evidence(evidence, change):
    observation, source = evidence
    if change in {"metadata", "foundation"}:
        observation["snapshots"][0][change] = "0" * 64
    elif change == "network":
        observation["snapshots"][0]["networks"] = ["0" * 64]
    elif change == "extra_key":
        observation["snapshots"][0]["configured_metadata"] = ""
    elif change == "missing_key":
        del observation["snapshots"][0]["attempt"]
    elif change == "relabeled_v2":
        observation["fingerprint_version"] = 2
    else:
        observation["observations"][0]["mounts"] = []
    with pytest.raises(ValueError, match="reconciliation_fingerprint_mismatch"):
        reconcile_manifest(observation, source)


@pytest.mark.parametrize("field,value", [("configured_metadata", "f" * 64),
                                        ("configured_networks", ("f" * 64,)),
                                        ("network_evidence", (("app", "net", "alias"),))])
def test_legacy_projection_refuses_nondefault_new_evidence(evidence, monkeypatch, field, value):
    observation, source = evidence
    original = capture.reconcile

    def changed(rows, *, fingerprint_version=2):
        snapshots = original(rows, fingerprint_version=fingerprint_version)
        snapshots[0][field] = value
        return snapshots

    monkeypatch.setattr(capture, "reconcile", changed)
    with pytest.raises(ValueError, match="reconciliation_fingerprint_mismatch"):
        reconcile_manifest(observation, source)


@pytest.mark.parametrize("change", [None, "missing_key", "metadata", "extra_key"])
def test_current_v2_evidence_requires_full_exact_snapshot(evidence, change):
    observation, source = evidence
    observation["fingerprint_version"] = 2
    observation["snapshots"] = capture.reconcile(observation["observations"])
    if change == "missing_key":
        del observation["snapshots"][0]["configured_metadata"]
    elif change == "metadata":
        observation["snapshots"][0]["metadata"] = "0" * 64
    elif change == "extra_key":
        observation["snapshots"][0]["unexpected"] = ""
    if change is None:
        result = reconcile_manifest(observation, source)
        assert result["fingerprint_version"] == 2
        assert result["baseline"] == observation["snapshots"]
        assert result["paired_payload_verified"] is False
    else:
        with pytest.raises(ValueError, match="reconciliation_fingerprint_mismatch"):
            reconcile_manifest(observation, source)


def test_equivalent_mount_and_network_renderings_share_fingerprint():
    before = {"mounts": [{"Type": "bind", "Source": "/source", "Destination": "/repo", "RW": False,
                           "Mode": "ro", "Propagation": "rprivate"}], "network_mode": "network-name",
              "networks": {"network-name": {"NetworkID": "f" * 64, "Aliases": ["app", "service"], "IPAMConfig": None}}}
    after = copy.deepcopy(before)
    after["mounts"][0]["Mode"] = ""
    after["network_mode"] = "f" * 64
    after["networks"]["network-name"]["Aliases"] = ["service", "app", "app"]
    assert adapter.preservation_digest(before) == adapter.preservation_digest(after)
    for changed in ("RW", "Source", "Propagation", "Mode"):
        altered = copy.deepcopy(after)
        altered["mounts"][0][changed] = {"RW": True, "Source": "/other", "Propagation": "rshared", "Mode": "Z"}[changed]
        assert adapter.preservation_digest(before) != adapter.preservation_digest(altered)


@pytest.mark.parametrize("field,value", [("privileged", True), ("user", "1001"), ("log_driver", "json-file"),
                                        ("memory", 1024), ("has_cap_add", True)])
def test_new_controls_are_fingerprinted(field, value):
    assert adapter.preservation_digest({}) != adapter.preservation_digest({field: value})


@pytest.mark.parametrize("bad", [b'[]', b'{"x":1}', b'{"bad key":"x"}', b'{"x":"a\\nb"}',
                                 b'{"x":"a","x":"b"}', b'{"x":"\\ud800"}'])
def test_labels_fail_closed_without_values_in_error(bad):
    with pytest.raises(Exception) as caught:
        encoder.encode_labels(bad)
    assert caught.value.args == ("install_labels_refused",)
    assert caught.value.__context__ is None


def test_labels_and_environment_stream_independently_without_files():
    labels = b"com.example.original=" + b"L" * 50_000 + b"\n"
    environment = b"KEY=" + b"E" * 50_000 + b"\n"
    script = "import pathlib,sys; e=sys.stdin.buffer.read(); l=pathlib.Path(sys.argv[1]).read_bytes(); print(len(e),len(l))"
    result = transport._run((sys.executable, "-B", "-c", script, transport.LABEL_DESCRIPTOR),
                            timeout=3, input_bytes=environment, label_bytes=labels, limit=100,
                            env={"PATH": "/usr/bin:/bin"})
    assert result.strip() == f"{len(environment)} {len(labels)}".encode()


def test_private_label_timeout_closes_descriptors(monkeypatch):
    descriptors = []
    pipe = transport.os.pipe
    def tracked():
        pair = pipe()
        descriptors.extend(pair)
        return pair
    monkeypatch.setattr(transport.os, "pipe", tracked)
    with pytest.raises(Exception, match="transport_timeout"):
        transport._run((sys.executable, "-c", "import time; time.sleep(2)", transport.LABEL_DESCRIPTOR),
                       timeout=0.05, input_bytes=None, label_bytes=b"X=" + b"v" * 60_000,
                       limit=100, env={"PATH": "/usr/bin:/bin"})
    for fd in descriptors:
        with pytest.raises(OSError):
            os.fstat(fd)


def test_label_values_preserve_whitespace_unicode_and_equals():
    labels = {"com.example.x": " leading = caf\u00e9\u2028trailing ", "empty": ""}
    encoded = encoder.encode_labels(json.dumps(labels).encode())
    assert dict(line.split("=", 1) for line in encoded.decode().split("\n")[:-1]) == labels
