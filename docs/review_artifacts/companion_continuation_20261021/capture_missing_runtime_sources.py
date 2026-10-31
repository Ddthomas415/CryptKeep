"""Explicit read-only source capture; no startup, exec, credentials or DB query."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import time

from scripts.research import companion_docker_transport as transport
from docs.review_artifacts.companion_continuation_20261021.capture_installed_facts import regular_member

HERE = Path(__file__).resolve().parent
POSTCHECK_SHA = "c505e4c6c3b2be5cd1054ac976fd69a503d0fcf2b2304cc6e6583ef1b1decb06"
CLI_SHA = "678271184175b40dfc4bd6f4582be00ae1538b0d1e031181f52ceedfae9af5fb"
PATHS = (
    "httpcore/_async/connection_pool.py", "httpcore/_async/connection.py",
    "uvicorn/main.py", "uvicorn/config.py", "uvicorn/importer.py",
    "uvicorn/server.py", "uvicorn/lifespan/on.py", "psycopg/conninfo.py",
)
FORMAT = ('{"id":{{json .Id}},"image":{{json .Image}},"state":{{json .State.Status}},'
          '"started":{{json .State.StartedAt}},"restarts":{{json .RestartCount}},'
          '"restart_policy":{{json .HostConfig.RestartPolicy.Name}}}')
FIELDS = ("id", "image", "state", "started", "restarts", "restart_policy")


def capture(output_name="missing_runtime_sources"):
    raw = (HERE / "s3_source_refresh_plan/actual_preparation_postcheck.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != POSTCHECK_SHA:
        raise ValueError("capture_input_changed")
    saved = json.loads(raw)
    selected = [r for r in saved["after"] if "-staged-s3refresh20261021c1eaae5a" in r["name"]]
    if len(selected) != 4 or any(r["state"] != "created" or r["restarts"] != 0 for r in selected):
        raise ValueError("invalid_capture_subjects")
    expected = [{k: r[k] for k in FIELDS} for r in selected]
    output = HERE / output_name
    output.mkdir(mode=0o700)
    report = {"schema": "companion-missing-runtime-sources-v1", "state": "INCOMPLETE",
        "recorded_utc": datetime.now(timezone.utc).isoformat(), "input_sha256": POSTCHECK_SHA,
        "files": [], "before": None, "after": None, "commands": 0,
        "services_started": False, "credentials_accessed": False, "error": None}
    start = time.monotonic()
    deadline, received = start + 120, 0
    try:
        with tempfile.TemporaryDirectory(prefix="cryptkeep-source-read-") as temporary:
            native = transport.DockerTransport(CLI_SHA, Path(temporary).resolve(), authorized=True)

            def command(args, limit):
                nonlocal received
                if report["commands"] >= 34 or not native._verify_cli(deadline):
                    raise ValueError("capture_cli_or_budget")
                remaining = deadline - time.monotonic()
                if remaining <= 0 or received + limit > 18 * 1024 * 1024:
                    raise ValueError("capture_budget")
                report["commands"] += 1
                data = transport._run((str(transport.CLI), "--host", transport.ENDPOINT,
                    "--config", temporary, *args), timeout=min(10, remaining),
                    input_bytes=None, limit=limit, env=dict(transport.ENV))
                received += len(data)
                return data

            def inventory():
                data = command(("container", "inspect", "--format", FORMAT,
                    *(r["id"] for r in selected)), 65536)
                rows = [json.loads(line) for line in data.splitlines()]
                if rows != expected:
                    raise ValueError("capture_subject_changed")
                return rows

            report["before"] = inventory()
            for subject in selected:
                for relative in PATHS:
                    path = "/usr/local/lib/python3.11/site-packages/" + relative
                    data = command(("container", "cp", subject["id"] + ":" + path, "-"), 534528)
                    content = regular_member(data, path, 524288)
                    filename = str(len(report["files"])) + "_" + relative.replace("/", "_")
                    with (output / filename).open("xb") as stream:
                        stream.write(content)
                    report["files"].append({"container_id": subject["id"], "image_id": subject["image"],
                        "path": path, "saved_file": filename, "bytes": len(content),
                        "sha256": hashlib.sha256(content).hexdigest()})
            report["after"] = inventory()
            report["state"] = "READY_FOR_INDEPENDENT_REVIEW"
    except Exception as exc:
        # Never retain arbitrary subprocess messages or payloads in the receipt.
        report["error"] = type(exc).__name__
        if str(exc) in {"transport_cli_unverified", "transport_command_failed", "transport_timeout",
                        "transport_output_limit", "capture_subject_changed", "capture_budget",
                        "capture_cli_or_budget"}:
            report["error_category"] = str(exc)
    report["elapsed_seconds"] = round(time.monotonic() - start, 3)
    report["transfer_bytes"] = received
    with (output / "report.json").open("x") as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
    print(json.dumps({k: report[k] for k in ("state", "commands", "elapsed_seconds", "error")}))
    return 0 if report["state"] == "READY_FOR_INDEPENDENT_REVIEW" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-capture", action="store_true")
    parser.add_argument("--output", choices=("missing_runtime_sources", "missing_runtime_sources_authorized"),
        default="missing_runtime_sources")
    args = parser.parse_args()
    if args.execute_capture:
        exit(capture(args.output))
    print(json.dumps({"native_operations": False, "file_paths": PATHS, "subjects": 4}))
