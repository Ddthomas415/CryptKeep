"""One explicitly authorized metadata pair; no service or credential operations."""
import hashlib
import json
import signal
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from scripts.research import collect_companion_recreation_metadata as metadata
from scripts.research.companion_docker_transport import CLI, ENDPOINT
from . import refresh_sources as sources


HERE = Path(__file__).resolve().parent


def capture(output, runner=metadata.readonly_run):
    started = time.monotonic()
    observed_start = datetime.now(timezone.utc).isoformat()
    source = sources.refresh()
    manifest = json.loads(sources.checked(*sources.PINS["manifest"]))
    if hashlib.sha256(CLI.read_bytes()).hexdigest() != manifest["cli_sha256"]:
        raise ValueError("cli_identity_changed_no_commands_run")
    output.mkdir(exist_ok=False)
    report = {"schema": "companion-paired-baseline-v1", "state": "INCOMPLETE",
              "cli_sha256": manifest["cli_sha256"], "native_inspections": 0,
              "observations": [], "raw_sha256": [], "selected_observations_equal": False,
              "metadata_complete_for_selected_fields": False,
              "observed_start_utc": observed_start,
              "source_refresh_sha256": hashlib.sha256(
                  (HERE / "source_refresh.json").read_bytes()).hexdigest()}
    def expired(*_):
        raise TimeoutError("capture_deadline")

    prior_handler = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, 30 - (time.monotonic() - started)))
    try:
        with tempfile.TemporaryDirectory(prefix="ck-v6g-metadata-") as config:
            args = (str(CLI), "--config", config, "--host", ENDPOINT,
                    "container", "inspect", "--format", metadata.capture_format(),
                    *[row["id"] for row in source["expected_original_targets"]])
            for number in (1, 2):
                remaining = 30 - (time.monotonic() - started)
                if remaining <= 0:
                    raise TimeoutError("capture_deadline")
                report["native_inspections"] += 1
                raw = runner(args, timeout=min(10, remaining), input_bytes=None,
                             limit=1_048_576, env={"PATH": "/usr/bin:/bin"})
                # Save exact sanitized bytes before parsing; a parse failure
                # must not erase the only observation or cause another read.
                with (output / f"capture_{number}.jsonl").open("xb") as stream:
                    stream.write(raw)
                report["raw_sha256"].append(hashlib.sha256(raw).hexdigest())
                report["observations"].append([json.loads(line) for line in raw.splitlines()])
        pair = report["observations"]
        report["selected_observations_equal"] = pair[0] == pair[1]
        report["metadata_complete_for_selected_fields"] = all(
            len(rows) == 7 and all(type(row) is dict and "flags" in row for row in rows)
            for rows in pair)
        if report["selected_observations_equal"] and report["metadata_complete_for_selected_fields"]:
            report["state"] = "READY_FOR_INDEPENDENT_REVIEW"
    except Exception as error:
        report["failure_category"] = type(error).__name__
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, prior_handler)
    report["observed_end_utc"] = datetime.now(timezone.utc).isoformat()
    report["elapsed_seconds"] = time.monotonic() - started
    with (output / "baseline_observation.json").open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return report


if __name__ == "__main__":
    if sys.argv[1:] != ["--capture-once"]:
        print(json.dumps({"actions_executed": False, "state": "INCOMPLETE"}))
    else:
        result = capture(HERE / "actual_baseline")
        print(json.dumps({k: result.get(k) for k in (
            "state", "native_inspections", "selected_observations_equal",
            "metadata_complete_for_selected_fields", "elapsed_seconds", "failure_category")}))
        sys.exit(0 if result["state"] == "READY_FOR_INDEPENDENT_REVIEW" else 1)
