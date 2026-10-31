"""Sanitized stopped-container startup options; no environment values exported."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import time

from scripts.research import companion_docker_transport as transport

HERE = Path(__file__).resolve().parent
INPUT = HERE / "s3_source_refresh_plan/actual_preparation_postcheck.json"
INPUT_SHA = "c505e4c6c3b2be5cd1054ac976fd69a503d0fcf2b2304cc6e6583ef1b1decb06"
CLI_SHA = "678271184175b40dfc4bd6f4582be00ae1538b0d1e031181f52ceedfae9af5fb"
COMMAND = ["sh", "-c", "uvicorn ${SERVICE_MODULE}:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000}"]
APPS = {"phase1-audit-log": ("audit_log.main", "8009"), "phase1-risk-stub": ("risk_stub.main", "8008"),
        "phase1-memory": ("memory_retrieval.main", "8007"), "phase1-orchestrator": ("orchestrator.main", "8002")}
IDENTITY = ("id", "image", "state", "started", "restarts", "restart_policy")
PATH_VALUES = ("/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
               "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")


def matches(key, values):
    tests = ["(eq . " + json.dumps(key + "=" + value) + ")" for value in values]
    comparison = tests[0] if len(tests) == 1 else "(or " + " ".join(tests) + ")"
    return ("[{{range .Config.Env}}{{if eq (index (split . \"=\") 0) " + json.dumps(key)
            + "}}{{" + comparison + "}},{{end}}{{end}}null]")


def inspect_format(module, port):
    fields = {"id": ".Id", "image": ".Image", "state": ".State.Status",
        "started": ".State.StartedAt", "restarts": ".RestartCount", "restart_policy": ".HostConfig.RestartPolicy.Name"}
    pieces = [json.dumps(k) + ":{{json " + value + "}}" for k, value in fields.items()]
    cmd = json.dumps(json.dumps(COMMAND, separators=(",", ":")))
    pieces += ['"command_matches":{{eq (json .Config.Cmd) ' + cmd + '}}',
               '"entrypoint_empty":{{not .Config.Entrypoint}}',
               '"workdir_matches":{{eq .Config.WorkingDir "/app"}}']
    checks = {"SERVICE_MODULE": (module,), "SERVICE_PORT": (port,), "PYTHONPATH": ("/app:/repo",),
        "WEB_CONCURRENCY": ("1",), "FORWARDED_ALLOW_IPS": ("127.0.0.1",),
        "BASH_ENV": ("",), "ENV": ("",), "PATH": PATH_VALUES}
    pieces += [json.dumps(k) + ":" + matches(k, values) for k, values in checks.items()]
    pieces.append('"uvicorn_overrides":[{{range .Config.Env}}{{$key := index (split . "=") 0}}'
        '{{if ge (len $key) 8}}{{if eq (slice $key 0 8) "UVICORN_"}}true,{{end}}{{end}}{{end}}null]')
    return "{" + ",".join(pieces) + "}"


def profile_ok(row, *, requires_repo_import_path):
    required = ("SERVICE_MODULE", "SERVICE_PORT", "PATH")
    optional = ("WEB_CONCURRENCY", "FORWARDED_ALLOW_IPS", "BASH_ENV", "ENV")
    return (all(row[k] is True for k in ("command_matches", "entrypoint_empty", "workdir_matches"))
        and all(row[k] == [True, None] for k in required)
        and all(row[k] in ([None], [True, None]) for k in optional)
        and (row["PYTHONPATH"] == [True, None] if requires_repo_import_path
             else row["PYTHONPATH"] in ([None], [True, None]))
        and row["uvicorn_overrides"] == [None])


def capture():
    raw = INPUT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != INPUT_SHA:
        raise ValueError("profile_input_changed")
    selected = [r for r in json.loads(raw)["after"] if "-staged-s3refresh20261021c1eaae5a" in r["name"]]
    if len(selected) != 4 or {r["name"].removeprefix("/").split("-staged-")[0] for r in selected} != set(APPS):
        raise ValueError("profile_subjects_invalid")
    output = HERE / "startup_profile"
    output.mkdir(mode=0o700)
    report = {"schema": "companion-sanitized-startup-profile-v1", "state": "INCOMPLETE",
        "recorded_utc": datetime.now(timezone.utc).isoformat(), "input_sha256": INPUT_SHA,
        "before": [], "after": [], "commands": 0, "error": None,
        "environment_values_exported": False, "services_started": False}
    start = time.monotonic()
    deadline = start + 60
    try:
        with tempfile.TemporaryDirectory(prefix="cryptkeep-profile-") as temporary:
            native = transport.DockerTransport(CLI_SHA, Path(temporary).resolve(), authorized=True)
            for phase in ("before", "after"):
                for subject in selected:
                    if report["commands"] >= 8 or not native._verify_cli(deadline):
                        raise ValueError("profile_budget_or_cli")
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise ValueError("profile_budget_or_cli")
                    logical = subject["name"].removeprefix("/").split("-staged-")[0]
                    report["commands"] += 1
                    result = transport._run((str(transport.CLI), "--host", transport.ENDPOINT,
                        "--config", temporary, "container", "inspect", "--format",
                        inspect_format(*APPS[logical]), subject["id"]), timeout=min(10, remaining),
                        input_bytes=None, limit=16384, env=dict(transport.ENV))
                    row = json.loads(result)
                    if any(row.get(k) != subject[k] for k in IDENTITY):
                        raise ValueError("profile_subject_changed")
                    report[phase].append(row)
            if report["before"] != report["after"]:
                raise ValueError("profile_changed")
            report["profile_matches"] = all(profile_ok(row, requires_repo_import_path=
                subject["name"].startswith("/phase1-orchestrator-staged-"))
                for row, subject in zip(report["after"], selected))
            report["state"] = "READY_FOR_INDEPENDENT_REVIEW"
    except Exception as exc:
        report["error"] = type(exc).__name__
    report["elapsed_seconds"] = round(time.monotonic() - start, 3)
    with (output / "report.json").open("x") as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
    print(json.dumps({k: report[k] for k in ("state", "commands", "elapsed_seconds", "error")}
        | {"profile_matches": report.get("profile_matches")}))
    return report["state"] == "READY_FOR_INDEPENDENT_REVIEW"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-capture", action="store_true")
    args = parser.parse_args()
    if args.execute_capture:
        assert capture(), "sanitized profile capture incomplete"
    else:
        print(json.dumps({"native_operations": False, "subjects": 4, "max_commands": 8}))
