"""Synthetic ownership/cleanup and no-network import runner contracts."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import subprocess
import sys

import pytest

from scripts.research import prove_companion_installed_imports as proof

ROOT = Path(__file__).resolve().parents[1]


def test_wrong_runner_hash_never_calls_docker(tmp_path):
    calls = []
    with pytest.raises(ValueError, match="runner_identity"):
        proof.run(ROOT, tmp_path / "out", "0" * 64, runner=lambda *a, **k: calls.append(a))
    assert calls == []


@pytest.mark.parametrize("fault", [None, "volumes", "loader", "ownership", "timeout", "import", "validation", "final", "success_diagnostics"])
@pytest.mark.parametrize("remaining_only", [False, True])
@pytest.mark.parametrize("allow_probe", [False, True])
def test_owned_isolated_four_image_import_check(tmp_path, monkeypatch, fault, remaining_only, allow_probe):
    baseline = json.loads((ROOT / proof.BASE).read_bytes())["targets"]
    originals = [{"id": r["id"], "image": r["image_id"], "state": "exited", "restarts": 0, "policy": "no"} for r in baseline]
    real_checked = proof.checked
    monkeypatch.setattr(proof, "checked", lambda p, h: b"fake-cli" if p == proof.CLI else real_checked(p, h))
    rows, calls, configurations = {}, [], {}
    original_reads = []
    def runner(argv, **kwargs):
        args = argv[5:]
        calls.append(args)
        assert kwargs["env"] == {"PATH": "/usr/bin:/bin"}
        assert 0 < kwargs["timeout"] <= 20
        rc, out, err = 0, b"", b""
        if args[:2] == ("image", "inspect"):
            out = json.dumps({"id": args[-1], "volumes": fault == "volumes",
                              "loader_env": [fault == "loader"]}).encode()
        elif args[:2] == ("container", "inspect"):
            if args[3] == proof.ORIGINAL_FORMAT:
                original_reads.append(True)
                current = originals if fault != "final" or len(original_reads) == 1 else []
                out = b"\n".join(json.dumps(r).encode() for r in current)
            elif args[-1] not in rows:
                rc, err = 1, b"No such container"
            else:
                row = dict(rows[args[-1]])
                if fault == "ownership":
                    row["attempt"] = "not-owned"
                out = json.dumps(row).encode()
        elif args[:2] == ("container", "create"):
            name = args[args.index("--name") + 1]
            label = args[args.index("--label") + 1].split("=", 1)[1]
            identity = f"{100 + len(configurations):064x}"
            image = args[args.index("--entrypoint") + 2]
            rows[name] = {"id": identity, "name": "/" + name, "image": image, "state": "created", "exit": 0, "attempt": label}
            configurations[identity] = args
            out = identity.encode()
            assert "--pull=never" in args and "--read-only" in args and "--no-healthcheck" in args
            assert args[args.index("--network") + 1] == "none"
            assert args[args.index("--user") + 1] == "65534:65534"
            assert args[args.index("--entrypoint") + 3:args.index("--entrypoint") + 6] == ("-I", "-S", "-B")
            assert not any(arg in {"--publish", "--env-file", "--privileged", "--volumes-from"} for arg in args)
        elif args[:2] == ("container", "start"):
            row = next(r for r in rows.values() if r["id"] == args[-1])
            row["state"] = "running"
            if fault == "timeout":
                raise subprocess.TimeoutExpired("SYNTHETIC_PRIVATE", 1)
            row["state"] = "exited"
            create = configurations[row["id"]]
            module = create[-2] if allow_probe else create[-1]
            stage = create[create.index("--mount") + 1].split(",")[1].removeprefix("source=")
            p = Path(stage) / module / "main.py"
            payload = {"ok": fault not in {"import", "validation"}, "module": module, "python": [3, 11],
                       "denied": {"network": 0, "repository": 0}, "synthetic_settings": True,
                       "network_events": [],
                       "allow_blocked_local_probe": allow_probe,
                       "lifespan_run": False, "stage": "complete",
                       "loaded_sources": {module + "/main.py": hashlib.sha256(p.read_bytes()).hexdigest()}}
            if allow_probe:
                payload.update(denied={"network": 1, "repository": 0}, network_events=[proof.local_probe_event()])
            if fault == "import":
                rc, row["exit"] = 1, 1
                payload.update(stage="application_import", failure_type="ModuleNotFoundError", missing_module="synthetic_missing")
            elif fault == "validation":
                rc, row["exit"] = 1, 1
                payload.update(stage="source_validation", failure_type="RuntimeError",
                               failure_category="forbidden_import_activity", denied={"network": 1, "repository": 0},
                               network_events=[{"operation": "bind", "module": "synthetic.library",
                                                "function": "feature_probe", "line": 42}])
            elif fault == "success_diagnostics":
                payload["network_events"] = [{"operation": "bind", "module": "synthetic.library",
                    "function": "probe", "line": 42, "private": "SYNTHETIC_PRIVATE"}] * 9
            out = json.dumps(payload).encode()
        elif args[:2] == ("container", "stop"):
            next(r for r in rows.values() if r["id"] == args[-1])["state"] = "exited"
        elif args[:2] == ("container", "rm"):
            name = next(name for name, r in rows.items() if r["id"] == args[-1])
            assert rows[name]["state"] in {"created", "exited"}
            del rows[name]
        else:
            pytest.fail("unexpected operation")
        return SimpleNamespace(returncode=rc, stdout=out, stderr=err)
    report = proof.run(ROOT, tmp_path / "out", hashlib.sha256(Path(proof.__file__).read_bytes()).hexdigest(),
                       remaining_only=remaining_only, allow_blocked_local_probe=allow_probe, runner=runner)
    selected = list(proof.MODULES[2:] if remaining_only else proof.MODULES)
    assert report["selected_modules"] == selected
    started = [configurations[c[-1]][-2 if allow_probe else -1]
               for c in calls if c[:2] == ("container", "start")]
    assert report["import_contract"] == ("blocked_local_probe_v2" if allow_probe else "zero_denials_v1")
    assert started == selected[:len(started)]
    assert len(started) <= (len(selected) if fault in {None, "final"} else 1)
    assert (report["state"] == "READY_FOR_INDEPENDENT_REVIEW") == (fault is None)
    assert "SYNTHETIC_PRIVATE" not in json.dumps(report)
    original_ids = {r["id"] for r in baseline}
    assert all(c[-1] not in original_ids for c in calls if c[:2] in {("container", "start"), ("container", "stop"), ("container", "rm")})
    assert not any("--force" in c or "--volumes" in c or c[0] in {"build", "exec", "pull"} for c in calls)
    if fault is None:
        assert len(report["results"]) == len(report["removed"]) == len(selected) and not rows
        assert all(result["denied"]["network"] == int(allow_probe) for result in report["results"])
    elif fault == "ownership":
        assert report["cleanup_incomplete"] and rows
        assert not any(c[:2] in {("container", "start"), ("container", "stop"), ("container", "rm")} for c in calls)
    elif fault == "timeout":
        assert not rows and len(report["removed"]) == 1
    elif fault == "import":
        assert report["diagnostics"][0]["missing_module"] == "synthetic_missing" and not rows
    elif fault == "validation":
        diagnostic = report["diagnostics"][0]
        assert diagnostic["failure_category"] == "forbidden_import_activity"
        assert diagnostic["denied"] == {"network": 1, "repository": 0} and not rows
        assert diagnostic["network_events"] == [{"operation": "bind", "module": "synthetic.library",
                                                  "function": "feature_probe", "line": 42}]
    elif fault == "success_diagnostics":
        assert not report["results"] and "network_events" not in report["diagnostics"][0] and not rows


def test_payload_is_inert_on_unknown_module_and_reports_safe_missing_import(tmp_path):
    payload = ROOT / proof.PAYLOAD
    result = subprocess.run([sys.executable, "-I", "-S", "-B", str(payload), "audit_log"], cwd=tmp_path,
                            capture_output=True, timeout=20, env={"PATH": "/usr/bin:/bin"})
    report = json.loads(result.stdout)
    assert result.returncode == 1 and report["ok"] is False
    assert report["stage"] == "configuration_import" and report["missing_module"] == "shared"
    assert report["denied"] == {"network": 0, "repository": 0}


@pytest.mark.parametrize("override", [
    {"operation": "unknown"}, {"operation": {}}, {"module": "secret/address"}, {"function": "raw traceback\n"},
    {"line": True}, {"line": -1}, {"line": 10_000_001}, {"address": "SYNTHETIC_PRIVATE"},
])
def test_network_diagnostics_reject_unapproved_fields(override):
    event = {"operation": "bind", "module": "synthetic.library", "function": "probe", "line": 42}
    assert proof.safe_network_events([event]) == [event]
    assert proof.safe_network_events([{**event, **override}]) is None
    assert proof.safe_network_events([event] * 9) is None
    assert proof.safe_network_events("SYNTHETIC_PRIVATE") is None


def test_payload_records_each_operation_without_arguments_and_caps_events(tmp_path):
    code = '''
import json, runpy, sys
payload = runpy.run_path(sys.argv[1], run_name="diagnostic_fixture")
def feature_probe(operation):
    try:
        payload["block_network"](operation)("SYNTHETIC_PRIVATE", token="SYNTHETIC_PRIVATE")
    except RuntimeError as error:
        assert str(error) == "import_network_forbidden"
for operation in ("connect", "connect_ex", "bind", "listen", "getaddrinfo") * 2:
    feature_probe(operation)
print(json.dumps({"events": payload["network_events"], "denied": payload["denied"]}))
'''
    result = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", code, str(ROOT / proof.PAYLOAD)],
                            cwd=tmp_path, capture_output=True, timeout=20, env={"PATH": "/usr/bin:/bin"})
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["denied"] == {"network": 10, "repository": 0}
    assert len(report["events"]) == 8
    assert [event["operation"] for event in report["events"][:5]] == [
        "connect", "connect_ex", "bind", "listen", "getaddrinfo"]
    assert all(event["function"] == "feature_probe" and event["module"] == "__main__"
               and event["line"] > 0 for event in report["events"])
    assert "SYNTHETIC_PRIVATE" not in result.stdout.decode()


@pytest.mark.parametrize("scenario", ["valid", "strict", "wrong_host", "source_changed", "code_changed", "repeated"])
def test_exact_blocked_probe_with_verified_source(tmp_path, scenario):
    source = tmp_path / "connection.py"
    source.write_bytes((ROOT / "docs/review_artifacts/companion_ipv6_source_20261018/memory_connection.py").read_bytes())
    code = '''
import json, runpy, socket, sys, types
from pathlib import Path
payload = runpy.run_path(sys.argv[1], run_name="diagnostic_fixture")
scope = payload["block_network"].__globals__
source = Path(sys.argv[2]).resolve()
scope["IPV6_SOURCE"] = source
scenario = sys.argv[3]
scope["allow_blocked_local_probe"] = scenario != "strict"
raw = source.read_bytes()
if scenario == "code_changed":
    raw = raw.replace(b"has_ipv6 = False", b"has_ipv6 = True")
compiled = compile(raw, str(source), "exec", dont_inherit=True)
function_code = next(c for c in compiled.co_consts if isinstance(c, types.CodeType) and c.co_name == "_has_ipv6")
if scenario == "source_changed":
    source.write_bytes(raw + b"\\n# changed source\\n")
socket.has_ipv6 = True
socket.socket.bind = payload["block_network"]("bind")
probe = types.FunctionType(function_code, {"__name__": "urllib3.util.connection", "socket": socket})
probe("::2" if scenario == "wrong_host" else "::1")
if scenario == "repeated":
    probe("::1")
print(json.dumps({"events": payload["network_events"], "denied": payload["denied"]}))
'''
    result = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", code,
                             str(ROOT / proof.PAYLOAD), str(source), scenario],
                            cwd=tmp_path, capture_output=True, timeout=20, env={"PATH": "/usr/bin:/bin"})
    assert result.returncode == 0, result.stderr.decode()
    report = json.loads(result.stdout)
    assert report["denied"] == {"network": 2 if scenario == "repeated" else 1, "repository": 0}
    events = proof.safe_network_events(report["events"])
    assert events is not None
    assert proof.activity_valid(report["denied"], events, scenario != "strict") == (scenario == "valid")
    assert ("classification" in events[0]) == (scenario in {"valid", "repeated"})
    if scenario == "repeated":
        assert "classification" not in events[1]


@pytest.mark.parametrize("operation", ["connect", "connect_ex", "listen", "getaddrinfo"])
def test_other_operations_and_mixed_denials_remain_fatal(operation):
    event = {**proof.local_probe_event(), "operation": operation}
    assert proof.safe_network_events([event]) is None
    assert not proof.activity_valid({"network": 1, "repository": 0}, [event], True)
    assert not proof.activity_valid({"network": 2, "repository": 0}, [proof.local_probe_event()], True)
    assert not proof.activity_valid({"network": 1, "repository": 1}, [proof.local_probe_event()], True)
    assert not proof.activity_valid({"network": True, "repository": 0}, [proof.local_probe_event()], True)
