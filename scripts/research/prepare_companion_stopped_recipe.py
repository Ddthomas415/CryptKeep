"""Compile an offline, non-executable stopped-replacement recipe from checked evidence."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from scripts.research import companion_runtime_adapter as adapter
from scripts.research.collect_companion_recreation_metadata import reconcile_manifest


def compile_recipe(observation, source_bytes):
    manifest = reconcile_manifest(observation, source_bytes)
    overrides = {k: v for k, v in adapter.ENV_EXPECTED.items() if k not in {"POSTGRES_USER", "POSTGRES_DB"}}
    for app in manifest["applications"]:
        row = app["observed_recreation_metadata"]
        expected = {"user": "", "privileged": False, "readonly_rootfs": False, "tty": False,
                    "open_stdin": False, "stdin_once": False, "auto_remove": False,
                    "memory": 0, "nano_cpus": 0, "cpu_shares": 0, "cpu_quota": 0,
                    "cpu_period": 0, "pids_limit": None, "shm_size": 67_108_864, "init": None,
                    "stop_signal": None, "stop_timeout": None, "log_driver": "local"}
        expected.update({key: False for key in adapter.RECREATION_FIELDS if key.startswith("has_")})
        if any(key not in row or type(row[key]) is not type(value) or row[key] != value
               for key, value in expected.items()):
            raise ValueError("unmodeled_recreation_setting")
        if row["workdir"] != "/app" or row["entrypoint"] is not None:
            raise ValueError("unmodeled_application_layout")
        options = ["--workdir", "/app", "--log-driver", "local"]
        for port, binds in sorted(row["ports"].items()):
            for bind in binds:
                if bind["HostIp"] != "127.0.0.1" or not port.endswith("/tcp"):
                    raise ValueError("unmodeled_port_binding")
                options.extend(("--publish", "127.0.0.1:" + bind["HostPort"] + ":" + port))
        for mount in row["mounts"] or []:
            if (mount["Type"] != "bind" or mount["Destination"] != "/repo" or mount["RW"] is not False
                    or mount.get("Propagation") != "rprivate" or any(c in mount["Source"] for c in ",\r\n")):
                raise ValueError("unmodeled_mount")
            options.extend(("--mount", "type=bind,source=" + mount["Source"] + ",target=/repo,readonly,bind-propagation=rprivate"))
        health = row["healthcheck"]
        if health["Test"][0] != "CMD-SHELL" or set(health) - {"Test", "Interval", "Timeout", "Retries"}:
            raise ValueError("unmodeled_healthcheck")
        options.extend(("--health-cmd", health["Test"][1], "--health-interval", str(health["Interval"]) + "ns",
                        "--health-timeout", str(health["Timeout"]) + "ns", "--health-retries", str(health["Retries"])))
        projected = copy.deepcopy(row)
        flags = [dict(flag) for flag in row["flags"] if flag is not None]
        present = set()
        for flag in flags:
            if flag["key"] in overrides:
                flag["ok"] = True
            present.add(flag["key"])
        flags.extend({"key": key, "ok": True} for key in overrides if key not in present)
        projected["flags"] = [*flags, None]
        app.update(create_options=options, command=row["command"],
                   replacement_metadata=adapter.preservation_digest(projected),
                   replacement_metadata_evidence="MODELLED, not observed after creation",
                   label_handling="All original labels privately copied; attempt label added; values compared in child",
                   missing_executable_fields=[])
        app["recreation_limits"] = ["Inherited parent defaults and native CLI descriptor/parser still require installed proof",
                                    "Expected fingerprint is a projection, not a created-container receipt"]
    manifest["schema"] = "companion-stopped-recipe-review-v1"
    manifest["state"] = "READY_FOR_INDEPENDENT_REVIEW"
    manifest["installation_authorized"] = False
    manifest["compatible_with_executable_plan_loader"] = False
    manifest["unresolved"] = ["Native CLI private-label descriptor/parser and actual stopped replacement verification",
                              "Fresh retained paired metadata capture before operational use",
                              "Mounted imports, installed dependency policy and strict registry isolation"]
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compile_recipe(json.loads(args.observation.read_bytes()), args.source_manifest.read_bytes())
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"state": result["state"], "recipes": len(result["applications"]),
                      "installation_authorized": False, "paired_payload_verified": result["paired_payload_verified"]}))


if __name__ == "__main__":
    main()
