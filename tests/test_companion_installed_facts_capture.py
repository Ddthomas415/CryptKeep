import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "docs/review_artifacts/companion_continuation_20261021/capture_installed_facts.py"
spec = importlib.util.spec_from_file_location("installed_capture_test", SCRIPT)
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


def archive(name="main.py", content=b"public source", kind=tarfile.REGTYPE):
    result = io.BytesIO()
    with tarfile.open(fileobj=result, mode="w") as stream:
        item = tarfile.TarInfo(name)
        item.type = kind
        item.size = len(content) if kind == tarfile.REGTYPE else 0
        stream.addfile(item, io.BytesIO(content) if item.size else None)
    return result.getvalue()


def test_frozen_inputs_and_exact_read_selection():
    manifest, evidence = capture.checked_inputs()
    targets, selected = capture.selection(manifest, evidence)
    assert len(targets) == 11
    assert sum(expected is not None for _, _, _, expected in selected) == 43
    assert len(selected) < 150
    assert len({(name, path) for name, path, _, _ in selected}) == len(selected)
    assert all("credential" not in path and ".env" not in path for _, path, _, _ in selected)
    assert all(targets[name]["state"] == "created" for name, path, _, _ in selected if path.startswith("/app/"))


def test_regular_single_member():
    assert capture.regular_member(archive(), "/app/example/main.py", 100) == b"public source"


@pytest.mark.parametrize("data", [archive("../main.py"), archive(kind=tarfile.SYMTYPE),
                                 archive(content=b"a" * 101), archive()[:-1024] + b"x" * 1024])
def test_unsafe_archive_refused(data):
    with pytest.raises((ValueError, tarfile.TarError)):
        capture.regular_member(data, "/app/example/main.py", 100)


def test_sql_is_fixed_read_only_aggregate():
    sql = capture.lineage_sql().decode()
    assert sql.startswith("BEGIN READ ONLY;") and sql.endswith("ROLLBACK;")
    assert "statement_timeout='2000ms'" in sql
    assert "'expected',55" in sql and "p.raw_object_key IS NOT DISTINCT FROM e.raw_object_key" in sql
    assert "p.published_at IS NOT DISTINCT FROM e.published_at" in sql
    assert not any(word in sql.upper() for word in ("INSERT INTO", "UPDATE PUBLIC", "DELETE FROM", "CREATE TABLE"))


def test_default_inert(tmp_path):
    result = subprocess.run([str(ROOT / ".venv/bin/python"), "-B", str(SCRIPT)], cwd=tmp_path,
                            env={"PATH": "/usr/bin:/bin"}, capture_output=True, timeout=10)
    assert result.returncode == 0 and json.loads(result.stdout)["actions_executed"] is False


def test_unapproved_execution_refused(tmp_path):
    result = subprocess.run([str(ROOT / ".venv/bin/python"), "-B", str(SCRIPT), "--execute",
                             "--approved-sha256", "0" * 64], cwd=tmp_path,
                            env={"PATH": "/usr/bin:/bin"}, capture_output=True, timeout=10)
    assert result.returncode == 1 and json.loads(result.stdout)["actions_executed"] is False


def test_changed_input_refuses(monkeypatch):
    monkeypatch.setattr(capture, "PINS", {"scripts/research/companion_installer.py": "0" * 64})
    with pytest.raises(ValueError, match="input_changed"):
        capture.checked_inputs()


@pytest.mark.parametrize("failed_transfers", [False, True])
def test_aggregate_exhaustion_stops_work_preserves_final_inventory(tmp_path, monkeypatch, failed_transfers):
    from scripts.research import companion_docker_transport as transport
    from scripts.research import companion_runtime_adapter as adapter
    original = json.loads((ROOT / "docs/review_artifacts/companion_continuation_20261020/fresh_v5_capture_20261020/capture.json").read_bytes())["observations"]
    staged = json.loads((SCRIPT.parent / "staged_metadata_diagnostic.json").read_bytes())["rows"]
    copied, inspected = [], []

    def forbidden(*args, **kwargs):
        raise AssertionError("native operation forbidden")

    def fake_run(argv, **kwargs):
        args = argv[5:]
        if args[:2] == ("container", "inspect"):
            inspected.append(args)
            return b"\n".join(json.dumps(row).encode() for row in original + staged)
        if args[:2] == ("container", "cp"):
            path = args[2].split(":", 1)[1]
            copied.append(path)
            if failed_transfers:
                raise transport.controller.Refused("transport_command_failed")
            result = archive(PureName(path), b"x" * (1 << 20))
            if len(result) > kwargs["limit"]:
                raise transport.controller.Refused("transport_output_limit")
            return result
        raise AssertionError("storage work must not follow budget exhaustion")

    monkeypatch.setattr(transport.DockerTransport, "_verify_cli", lambda *a, **k: True)
    monkeypatch.setattr(transport, "_run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    import httpx
    monkeypatch.setattr(httpx, "Client", forbidden)
    report = capture.capture(tmp_path / "capture", runner=fake_run)
    assert report["error"] == "file_budget_exhausted" and report["state"] == "INCOMPLETE"
    assert report["inventory_preserved"] and len(inspected) == 2
    assert len(copied) < len(capture.selection(*capture.checked_inputs())[1])
    assert report["file_transfer_upper_bound_bytes"] <= capture.FILE_BUDGET
    assert report["captured_bytes"] <= capture.FILE_BUDGET and report["storage"] == {}


def PureName(path):
    return Path(path).name
