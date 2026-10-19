"""Diagnostic guard, two-request budget, sanitized failure and immutable inventory."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import tarfile
import io

import pytest

from scripts.research import prove_companion_local_parent as proof

ROOT = Path(__file__).resolve().parents[1]


def test_bad_hash_never_invokes_runner(tmp_path):
    calls = []
    with pytest.raises(ValueError, match="identity_changed"):
        proof.run(ROOT, tmp_path / "result", "0" * 64, runner=lambda *a, **k: calls.append(a))
    assert calls == []


def test_changed_target_file_refused_before_any_command(tmp_path, monkeypatch):
    original = Path.read_bytes
    def changed(path):
        if path == ROOT / proof.BASELINE:
            data = json.loads(original(path))
            data["targets"][3]["image_id"] = "sha256:" + "f" * 64
            return json.dumps(data).encode()
        return original(path)
    monkeypatch.setattr(Path, "read_bytes", changed)
    calls = []
    with pytest.raises(ValueError, match="baseline_identity_changed"):
        proof.run(ROOT, tmp_path / "result", hashlib.sha256(original(Path(proof.__file__))).hexdigest(),
                  runner=lambda *a, **k: calls.append(a))
    assert calls == []


def test_diagnostic_has_only_standard_library_imports():
    import ast
    tree = ast.parse(Path(proof.__file__).read_bytes())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0 and node.module.split(".")[0] in __import__("sys").stdlib_module_names
        elif isinstance(node, ast.Import):
            assert all(alias.name.split(".")[0] in __import__("sys").stdlib_module_names for alias in node.names)


@pytest.mark.parametrize("fault", [None, "engine", "missing", "negative", "inventory", "timeout"])
def test_bounded_public_build_proof(tmp_path, fault):
    base = json.loads((ROOT / "docs/review_artifacts/companion_compatibility_20261016.json").read_bytes())["targets"]
    parent = base[3]["image_id"]
    built = "sha256:" + "b" * 64
    calls, contexts, inspections = [], [], []
    rows = [{"id": r["id"], "image": r["image_id"], "state": "exited", "restarts": 0,
             "restart_policy": "no"} for r in base]
    def runner(argv, **kwargs):
        args = argv[5:]
        calls.append(args)
        assert kwargs["env"] == {"PATH": "/usr/bin:/bin", "DOCKER_BUILDKIT": "0"}
        assert 0 < kwargs["timeout"] <= 45
        rc, out, err = 0, b"", b""
        if args[0] == "version":
            out = json.dumps({} if fault == "engine" else proof.REVIEWED_ENGINE).encode()
        elif args[:2] == ("container", "inspect"):
            inspections.append(True)
            current = rows if len(inspections) == 1 or fault != "inventory" else []
            out = b"\n".join(json.dumps(row).encode() for row in current)
        elif args[:2] == ("image", "inspect"):
            if args[-1] == "sha256:" + proof.MISSING:
                rc, err = (1, b"No such image") if fault != "missing" else (1, b"SYNTHETIC_PRIVATE_FAILURE")
            else:
                out = json.dumps({"id": args[-1], "layers": ["parent"] + (["new"] if args[-1] == built else []),
                                  "onbuild": None}).encode()
        elif args[0] == "build":
            contexts.append(kwargs["input"])
            if fault == "timeout":
                import subprocess
                raise subprocess.TimeoutExpired("SYNTHETIC_PRIVATE_FAILURE", 1)
            if len(contexts) == 1:
                out = built.encode()
            else:
                rc = 1
                err = b"cannot specify 64-byte hexadecimal strings" if fault != "negative" else b"SYNTHETIC_PRIVATE_FAILURE"
        else:
            pytest.fail("unexpected operation")
        return SimpleNamespace(returncode=rc, stdout=out, stderr=err)
    report = proof.run(ROOT, tmp_path / "result", hashlib.sha256(Path(proof.__file__).read_bytes()).hexdigest(), runner=runner)
    assert len(contexts) <= 2
    assert not any(c[0] in {"start", "stop", "exec", "pull"} or c[:2] == ("image", "tag") for c in calls)
    assert "SYNTHETIC_PRIVATE_FAILURE" not in json.dumps(report)
    assert (report["state"] == "READY_FOR_INDEPENDENT_REVIEW") == (fault is None)
    if fault is None:
        assert report["build_requests"] == 2 and report["negative_parser_refusal"]
        for payload, identity in zip(contexts, (parent.removeprefix("sha256:"), proof.MISSING)):
            with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
                assert archive.getnames() == ["Dockerfile", "app/shared/probe.py"]
                assert archive.extractfile("Dockerfile").read().splitlines()[0] == ("FROM " + identity).encode()
