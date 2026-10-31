"""Read-only, sanitized metadata capture. No installer, startup or credential export."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from scripts.research import companion_runtime_adapter as adapter
from scripts.research.companion_docker_transport import CLI, ENDPOINT
from scripts.research.companion_installer import Snapshot
from scripts.research.companion_worker_shutdown import APP_SPEC, replacement_command

# Docker Desktop 4.96.0 arm64; native signature verified 2026-10-20.
CLI_SHA256 = "678271184175b40dfc4bd6f4582be00ae1538b0d1e031181f52ceedfae9af5fb"
APP_COMMAND = ["sh", "-c", "uvicorn ${SERVICE_MODULE}:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000}"]


class CaptureFailure(RuntimeError):
    def __init__(self, category):
        self.category = category
        super().__init__(category)


def readonly_run(argv, *, timeout, input_bytes, limit, env):
    result = subprocess.run(argv, input=input_bytes, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout, env=env, close_fds=True)
    if result.returncode:
        error = result.stderr.decode(errors="replace").lower()
        category = next((label for marker, label in (("permission denied", "socket_permission_denied"),
                        ("cannot connect", "daemon_unreachable"), ("template", "metadata_template_error"),
                        ("no such", "target_missing")) if marker in error), "metadata_command_failed")
        if category == "metadata_template_error":
            field = re.search(r"at <([.a-zA-Z0-9_ ]+)>", error)
            if field:
                category += ":" + field.group(1)
        raise CaptureFailure(category)
    if len(result.stdout) > limit:
        raise CaptureFailure("metadata_output_limit")
    return result.stdout


def equals(expression, allowed):
    tests = ["(eq (json " + expression + ") " + json.dumps(json.dumps(value, separators=(",", ":"))) + ")"
             for value in allowed]
    return tests[0] if len(tests) == 1 else "(or " + " ".join(tests) + ")"


def capture_format():
    # Unknown command/health text never crosses the daemon boundary.
    command = equals(".Config.Cmd", [APP_COMMAND, *[replacement_command(n) for n in APP_SPEC], ["postgres"], ["./entrypoint.sh"],
                     ["server", "/data", "--console-address", ":9001"], None, []])
    entry = equals(".Config.Entrypoint", [None, [], ["docker-entrypoint.sh"],
                    ["/usr/bin/docker-entrypoint.sh"], ["./entrypoint.sh"]])
    tests = [["CMD-SHELL", "pg_isready -U copilot -d copilot"]]
    tests += [["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:"
               + str(port) + "/healthz', timeout=2).read()\""] for port in (8009, 8008, 8007, 8002)]
    health = '(or (not (index .Config "Healthcheck")) ' + equals('.Config.Healthcheck.Test', tests) + ')'
    fallback = ('{"id":{{json .Id}},"name":{{json .Name}},"image":{{json .Image}},'
                '"state":{{json .State.Status}},"command_recognized":{{' + command + '}},'
                '"entrypoint_recognized":{{' + entry + '}},"healthcheck_recognized":{{' + health + '}}}')
    fields = {"user": ".Config.User", "stop_signal": 'index .Config "StopSignal"',
              "stop_timeout": 'index .Config "StopTimeout"', "hostname": ".Config.Hostname",
              "tty": ".Config.Tty", "open_stdin": ".Config.OpenStdin", "stdin_once": ".Config.StdinOnce",
              "readonly_rootfs": ".HostConfig.ReadonlyRootfs", "privileged": ".HostConfig.Privileged",
              "memory": ".HostConfig.Memory", "nano_cpus": ".HostConfig.NanoCpus",
              "cpu_shares": ".HostConfig.CpuShares", "cpu_quota": ".HostConfig.CpuQuota",
              "cpu_period": ".HostConfig.CpuPeriod", "pids_limit": ".HostConfig.PidsLimit",
              "shm_size": ".HostConfig.ShmSize", "auto_remove": ".HostConfig.AutoRemove",
              "init": ".HostConfig.Init", "log_driver": ".HostConfig.LogConfig.Type"}
    parts = [json.dumps(key) + ':{{json (' + expression + ')}}' for key, expression in fields.items()
             if key not in adapter.RECREATION_FIELDS]
    # Presence only for potentially arbitrary option values, never raw option contents.
    for key, expression in {"has_security_options": ".HostConfig.SecurityOpt", "has_cap_add": ".HostConfig.CapAdd",
                            "has_cap_drop": ".HostConfig.CapDrop", "has_devices": ".HostConfig.Devices",
                            "has_device_requests": ".HostConfig.DeviceRequests", "has_ulimits": ".HostConfig.Ulimits",
                            "has_sysctls": ".HostConfig.Sysctls", "has_tmpfs": ".HostConfig.Tmpfs",
                            "has_log_options": ".HostConfig.LogConfig.Config"}.items():
        if key not in adapter.RECREATION_FIELDS:
            parts.append(json.dumps(key) + ':{{not (not ' + expression + ')}}')
    for key, value in {"PYTHONPATH": "/app:/repo", "BASH_ENV": "", "ENV": ""}.items():
        parts.append(json.dumps(key + "_matches") + ':[{{range .Config.Env}}{{if eq (index (split . "=") 0) '
                     + json.dumps(key) + '}}{{eq . ' + json.dumps(key + "=" + value) + '}},{{end}}{{end}}null]')
    # Raw labels are not needed to discover whether an unmodeled label must be preserved.
    parts.append('"label_count":{{if .Config.Labels}}{{len .Config.Labels}}{{else}}0{{end}}')
    full = adapter.INSPECT_FORMAT[:-1] + ',' + ','.join(parts) + '}'
    result = '{{if and ' + command + ' ' + entry + ' ' + health + '}}' + full + '{{else}}' + fallback + '{{end}}'
    def optional(match):
        parts = match.group(0).split(".")[1:]
        value = "." + parts[0]
        for field in parts[1:]:
            value = "(index " + value + " " + json.dumps(field) + ")"
        return value
    return re.sub(r"\.(?:Config|HostConfig)\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*", optional, result)


LEGACY_SNAPSHOT_KEYS = ("attempt", "foundation", "id", "image", "metadata", "name", "networks",
                        "policy", "restarts", "started", "state")
LEGACY_DEFAULTS = {"configured_metadata": "", "configured_networks": (), "network_evidence": ()}


def reconcile(rows, *, fingerprint_version=2):
    """Derive evidence fingerprints, not accepted replacement fingerprints."""
    snapshots = []
    fingerprint = adapter.legacy_preservation_digest if fingerprint_version == 1 else adapter.preservation_digest
    for row in rows:
        if "flags" not in row:
            continue
        networks = tuple(sorted(network["NetworkID"] for network in (row.get("networks") or {}).values()))
        snapshots.append(asdict(Snapshot(row["name"].removeprefix("/"), row["id"], row["image"], row["state"],
            row["started"], row["restarts"], row["restart_policy"], fingerprint(row),
            fingerprint({**row, "networks": {}}), networks)))
    return snapshots


def reconcile_manifest(observation, source_bytes):
    if (observation.get("state") != "READY_FOR_INDEPENDENT_REVIEW"
            or observation.get("final_observations_match") is not True
            or observation.get("metadata_complete_for_selected_fields") is not True
            or hashlib.sha256(source_bytes).hexdigest() != observation.get("source_manifest_sha256")):
        raise ValueError("reconciliation_evidence_incomplete")
    source = json.loads(source_bytes)
    rows = observation.get("observations")
    expected = source.get("baseline_observations")
    if (type(rows) is not list or len(rows) != 7 or type(expected) is not list or len(expected) != 7
            or observation.get("baseline_ids_images_states_match") is not True
            or [(r.get("name", "").removeprefix("/"), r.get("id"), r.get("image")) for r in rows]
               != [(r["name"], r["id"], r["image_id"]) for r in expected]
            or any(r.get("state") != "exited" or type(r.get("restarts")) is not int
                   or r["restarts"] != 0 or r.get("restart_policy") != "no" for r in rows)):
        raise ValueError("reconciliation_identity_mismatch")
    version = observation.get("fingerprint_version", 1)
    if type(version) is not int or version not in (1, 2):
        raise ValueError("reconciliation_fingerprint_version")
    computed = reconcile(rows, fingerprint_version=version)
    if version == 1:
        # v1 receipts predate these fields. Never discard non-default current evidence.
        if any(s[k] != LEGACY_DEFAULTS[k] for s in computed for k in LEGACY_DEFAULTS):
            raise ValueError("reconciliation_fingerprint_mismatch")
        computed = [{k: s[k] for k in LEGACY_SNAPSHOT_KEYS} for s in computed]
    if adapter._canonical(computed) != adapter._canonical(observation.get("snapshots")):
        raise ValueError("reconciliation_fingerprint_mismatch")
    final = observation.get("final_observations")
    if final is not None and final != rows:
        raise ValueError("reconciliation_final_payload_mismatch")
    source["schema"] = "companion-install-reconciled-review-v1"
    source["observed_at"] = observation["observed_utc"]
    source["baseline"] = reconcile(rows)
    source["fingerprint_version"] = 2
    source["paired_payload_verified"] = final is not None
    source["observation_sha256"] = hashlib.sha256(json.dumps(observation, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    by_name = {row["name"].removeprefix("/"): row for row in observation["observations"]}
    for app in source["applications"]:
        row = by_name[app["name"]]
        app["observed_recreation_metadata"] = row
        networks = list(row["networks"].values())
        if len(networks) == 1 and networks[0].get("IPAMConfig") is None:
            app["network_options"] = [item for alias in networks[0]["Aliases"] for item in ("--alias", alias)]
        app["missing_executable_fields"] = ["create_options", "replacement_metadata"]
        app["recreation_limits"] = ["Container labels counted but values deliberately not exported",
                                    "Log driver observed, not pinned by current create option allowlist",
                                    "Exact replacement alias/mount representation requires verification"]
    source["unresolved"] = ["Exact stopped-replacement recipe including ownership labels/logging and mount representation",
                            "Replacement preservation fingerprints are not observed replacement evidence",
                            "Mounted source/import isolation and complete installed dependency review",
                            "Hard registry isolation remains unverified"]
    return source


def collect(root, output, runner=readonly_run, *, source_manifest=None):
    if hashlib.sha256(CLI.read_bytes()).hexdigest() != CLI_SHA256:
        raise ValueError("cli_identity_changed_no_commands_run")
    root = root.resolve()
    baseline = json.loads((root / "docs/review_artifacts/companion_compatibility_20261016.json").read_bytes())
    source = Path(source_manifest) if source_manifest is not None else Path(
        "docs/review_artifacts/companion_install_manifest_20261017/manifest.json")
    if not source.is_absolute():
        source = root / source
    if (source.name != "manifest.json" or not source.is_relative_to(root / "docs/review_artifacts")
            or source.is_symlink() or source.resolve(strict=True) != source or not source.is_file()):
        raise ValueError("source_manifest_path_refused")
    with source.open("rb") as stream:
        source_bytes = stream.read(1_048_577)
    if len(source_bytes) > 1_048_576:
        raise ValueError("source_manifest_size_refused")
    output.mkdir(parents=True, exist_ok=False)
    report = {"schema": "companion-recreation-observation-v1", "state": "INCOMPLETE",
              "observed_utc": datetime.now(timezone.utc).isoformat(), "commands": [],
              "source_manifest_sha256": hashlib.sha256(source_bytes).hexdigest(),
              "source_manifest_path": source.relative_to(root).as_posix(),
              "cli_sha256": CLI_SHA256, "installation_authorized": False}
    report["fingerprint_version"] = 2
    with tempfile.TemporaryDirectory(prefix="cki-recreation-") as config:
        def read():
            args = (str(CLI), "--config", config, "--host", ENDPOINT, "container", "inspect", "--format",
                    capture_format(), *[row["id"] for row in baseline["targets"]])
            report["commands"].append("selected container inspect of seven pinned IDs")
            return [json.loads(line) for line in runner(args, timeout=10, input_bytes=None, limit=1_048_576,
                    env={"PATH": "/usr/bin:/bin"}).splitlines()]
        try:
            rows = read()
            report["observations"] = rows
            expected = [(r["id"], r["image_id"], "exited") for r in baseline["targets"]]
            report["baseline_ids_images_states_match"] = [(r["id"], r["image"], r["state"]) for r in rows] == expected
            report["snapshots"] = reconcile(rows)
            final = read()
            report["final_observations"] = final
            report["final_observations_match"] = final == rows
            report["metadata_complete_for_selected_fields"] = len(report["snapshots"]) == 7
            if all(report.get(key) is True for key in ("baseline_ids_images_states_match", "final_observations_match",
                                                       "metadata_complete_for_selected_fields")):
                report["state"] = "READY_FOR_INDEPENDENT_REVIEW"
        except Exception as error:
            # Transport failures contain fixed categories, not stderr or server payloads.
            report["failure_category"] = type(error).__name__
            if isinstance(error, CaptureFailure):
                report["sanitized_detail"] = error.category
        (output / "observation.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report.get(key) for key in ("state", "baseline_ids_images_states_match",
                        "final_observations_match", "metadata_complete_for_selected_fields", "failure_category", "sanitized_detail")}))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path,
                        help="Explicit public manifest.json under docs/review_artifacts; legacy default preserved")
    args = parser.parse_args()
    collect(Path(__file__).resolve().parents[2], args.output, source_manifest=args.source_manifest)


if __name__ == "__main__":
    main()
