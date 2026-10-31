"""Offline controller tests; no actual CLI read, daemon, copy or execution."""
from copy import deepcopy
import hashlib
import importlib
import io
import json
from pathlib import Path
import tarfile

import pytest

from tests.test_companion_archive_contract import offline


capture = importlib.import_module(
    "docs.review_artifacts.companion_integration_inputs_v6i_20261027.capture_memory_image")


@pytest.fixture(autouse=True)
def no_operations(monkeypatch):
    offline(monkeypatch)


def archive(path, payload, kind=tarfile.REGTYPE):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as output:
        member = tarfile.TarInfo(Path(path).name)
        member.size, member.type = len(payload), kind
        output.addfile(member, io.BytesIO(payload) if kind == tarfile.REGTYPE else None)
    return stream.getvalue()


def synthetic(monkeypatch, tmp_path, defect=None):
    plan, rows, selected, layers = capture.inputs()
    payload = b"public synthetic source\n"
    selected = {path: capture.digest(payload) for path in selected}
    expected = deepcopy(rows)
    monkeypatch.setattr(capture, "HERE", tmp_path)
    monkeypatch.setattr(capture, "inputs", lambda: (plan, expected, selected, layers))
    monkeypatch.setattr(capture.transport.DockerTransport, "_verify_cli", lambda *_: True)
    calls = []
    images = [{"id": row["image"], "layers": ["sha256:" + "a" * 64], "onbuild_empty": True} for row in rows]
    images[1]["layers"] += ["sha256:" + "b" * 64] * layers

    def runner(argv, *, timeout, input_bytes, limit, env):
        args = argv[5:]
        calls.append(args)
        assert 0 < timeout <= 10 and input_bytes is None and env == {"PATH": "/usr/bin:/bin"}
        if args[:2] == ("container", "inspect"):
            current = deepcopy(rows)
            if defect == "identity" or (defect == "after_state" and len(calls) > 1):
                current[1]["state"] = "running"
            return b"".join(json.dumps(row).encode() + b"\n" for row in current)
        if args[:2] == ("image", "inspect"):
            observed = deepcopy(images)
            if defect == "lineage":
                observed[1]["layers"][0] = "sha256:" + "c" * 64
            elif defect == "onbuild":
                observed[1]["onbuild_empty"] = False
            elif defect == "image_id":
                observed[1]["id"] = "sha256:" + "c" * 64
            return b"".join(json.dumps(row).encode() + b"\n" for row in observed)
        assert args[:2] == ("container", "cp") and args[-1] == "-"
        identity, path = args[2].split(":", 1)
        assert identity == rows[1]["id"] and path in selected
        if defect == "partial_transfer":
            raise capture.transport.controller.Refused("synthetic transport failure")
        value = b"changed\n" if defect == "hash" else payload
        result = archive(path, value, tarfile.SYMTYPE if defect == "symlink" else tarfile.REGTYPE)
        assert len(result) <= limit
        return result

    monkeypatch.setattr(capture.transport, "_run", runner)
    return calls


def test_fixed_current_inputs_and_one_app_source_delta():
    plan, rows, selected, layers = capture.inputs()
    assert len(rows) == 2 and rows[0]["state"] == "running" and rows[1]["state"] == "created"
    assert len(selected) == 48 and layers == 11
    assert rows[1]["id"] == "50998076e44610503e9e72d5e9135541ebbfc0d0abd3980d8b90a6dc32f4a8e6"
    assert rows[1]["image"] == "sha256:989471c8465a31e06f6a6765a919422a36d3f96f67f799cbaeebee6c3ab75e05"
    assert selected["/app/memory_retrieval/main.py"] == "9f68fe4d09c00c11a659bb705f6c885939e717d70f9d7b1b43cd995e440b52cf"


def test_synthetic_whole_capture_is_bounded_and_not_policy_approval(monkeypatch, tmp_path):
    calls = synthetic(monkeypatch, tmp_path)
    report = capture.capture()
    assert report["state"] == "READY_FOR_INDEPENDENT_REVIEW"
    assert report["commands_attempted"] == len(calls) == 51
    assert len(report["files"]) == 48 and report["before"] == report["after"]
    assert report["source_policy_accepted"] is False and report["runtime_authorized"] is False
    assert report["file_transfer_bytes_charged"] <= capture.FILE_BUDGET
    assert {args[:2] for args in calls} == {("container", "inspect"), ("image", "inspect"), ("container", "cp")}
    for row in report["files"]:
        assert capture.digest((tmp_path / "memory_image_capture" / row["saved_file"]).read_bytes()) == row["sha256"]


@pytest.mark.parametrize("defect", ["identity", "after_state", "lineage", "onbuild", "image_id", "hash", "symlink", "partial_transfer"])
def test_synthetic_failure_stops_work_and_saves_final_evidence(monkeypatch, tmp_path, defect):
    calls = synthetic(monkeypatch, tmp_path, defect)
    report = capture.capture()
    assert report["state"] == "INCOMPLETE"
    assert report["commands_attempted"] == len(calls) <= 51
    assert calls[-1][:2] == ("container", "inspect")
    assert len([args for args in calls if args[:2] == ("container", "cp")]) <= (48 if defect == "after_state" else 1)
    assert (tmp_path / "memory_image_capture/report.json").is_file()
    if defect == "partial_transfer":
        assert report["file_transfer_bytes_charged"] == capture.PER_FILE + 10240 + 1


def test_synthetic_aggregate_budget_stops_before_overrun(monkeypatch, tmp_path):
    calls = synthetic(monkeypatch, tmp_path)
    monkeypatch.setattr(capture, "FILE_BUDGET", 10241)
    report = capture.capture()
    assert report["state"] == "INCOMPLETE"
    assert len(calls) == 3 and not report["files"]
    assert report["file_transfer_bytes_charged"] <= capture.FILE_BUDGET


def test_expired_budget_never_calls_runner(monkeypatch, tmp_path):
    calls = synthetic(monkeypatch, tmp_path)
    readings = iter([0, *([121] * 20)])
    monkeypatch.setattr(capture.time, "monotonic", lambda: next(readings))
    report = capture.capture()
    assert report["state"] == "INCOMPLETE" and calls == []


def test_slow_cli_verification_preserves_final_inventory_reserve(monkeypatch, tmp_path):
    calls = synthetic(monkeypatch, tmp_path)
    now, deadlines = [0.0], []
    monkeypatch.setattr(capture.time, "monotonic", lambda: now[0])

    def verify(_self, deadline):
        deadlines.append(deadline)
        if len(deadlines) == 1:
            now[0] = min(119, deadline)
            return now[0] < deadline
        return True

    monkeypatch.setattr(capture.transport.DockerTransport, "_verify_cli", verify)
    original = capture.transport._run
    timeouts = []

    def runner(*args, **kwargs):
        timeouts.append(kwargs["timeout"])
        return original(*args, **kwargs)

    monkeypatch.setattr(capture.transport, "_run", runner)
    report = capture.capture()
    assert report["state"] == "INCOMPLETE"
    assert deadlines == [110, 120]
    assert len(calls) == 1 and timeouts == [10]
    assert report["after"] is not None


def test_existing_output_refuses_without_commands(monkeypatch, tmp_path):
    calls = synthetic(monkeypatch, tmp_path)
    (tmp_path / "memory_image_capture").mkdir()
    with pytest.raises(FileExistsError):
        capture.capture()
    assert calls == []


def test_default_is_inert_and_unapproved_execution_refused(monkeypatch, capsys):
    monkeypatch.setattr(capture, "inputs", lambda: pytest.fail("default read evidence"))
    monkeypatch.setattr(capture, "capture", lambda: pytest.fail("default executed capture"))
    assert capture.main([]) == 0
    assert json.loads(capsys.readouterr().out)["native_operations"] is False
    with pytest.raises(ValueError, match="source_not_approved"):
        capture.main(["--execute-capture", "--approved-sha256", "0" * 64])


def test_fixed_input_hash_drift_refuses(monkeypatch):
    key = next(iter(capture.PINS))
    monkeypatch.setitem(capture.PINS, key, "0" * 64)
    with pytest.raises(ValueError, match="input_changed"):
        capture.inputs()
