"""One approved fixed-file read from four stopped IDs; no container execution."""
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import time

from scripts.research import companion_docker_transport as transport
from scripts.research import companion_installer as install

HERE = Path(__file__).resolve().parent
SOURCE = "/usr/local/lib/python3.11/site-packages/uvicorn/__main__.py"
FORMAT = ('{"id":{{json .Id}},"name":{{json .Name}},"image":{{json .Image}},'
          '"state":{{json .State.Status}},"started":{{json .State.StartedAt}},'
          '"restarts":{{json .RestartCount}},"command":{{json .Config.Cmd}},'
          '"entrypoint":{{json (index .Config "Entrypoint")}},"workdir":{{json .Config.WorkingDir}}}')
INPUTS = {
    "manifest": ("refresh_inputs/reviewed_preparation_manifest.json", "67e29202a3bcd78f050f94b42bc87f91c7a50be90d3485ebd1fc0cfac0b7485e"),
    "subjects": ("runtime_packet_v6b/subjects.draft.json", "afadff45eafff21a102c0d4a9ba153e30b248d79f480540a976669f9b852d8dd"),
    "metadata": ("actual_b/staged_metadata.json", "28256b005e8414a542f3f894cff1cc285b095d2b42cf9398980e8496f847d198"),
    "review": ("runtime_packet_v6b/independent_review.json", "b8e72a553264b02357b6ccd569b82551fd016b0c4d3e1c151259bfe3be78e33a"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def file_from_tar(raw):
    member = tarfile.TarInfo.frombuf(raw[:512], "utf-8", "strict")
    end = 512 + ((member.size + 511) // 512) * 512
    if (member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE)
            or member.name != "__main__.py" or not 0 < member.size <= 65_536
            or len(raw) < end + 1024 or any(raw[end:])):
        raise ValueError("launcher_archive_refused")
    return raw[512:512 + member.size]


def main():
    began, deadline = time.monotonic(), time.monotonic() + 120
    inputs = {}
    for name, (path, expected) in INPUTS.items():
        raw = (HERE / path).read_bytes()
        if digest(raw) != expected:
            raise ValueError("launcher_input_changed")
        inputs[name] = json.loads(raw)
    plan = install.Plan.load((HERE / INPUTS["manifest"][0]).read_bytes(), INPUTS["manifest"][1])
    expected_rows = inputs["metadata"]["rows"]
    subjects = inputs["subjects"][3:]
    if len(subjects) != 4 or [s["container_id"] for s in subjects] != [r["id"] for r in expected_rows]:
        raise ValueError("launcher_subjects_refused")
    ids = tuple(s["container_id"] for s in subjects)
    output = HERE / "launcher_capture"
    output.mkdir(mode=0o700)  # One-use output prevents an unnoticed repeat capture.
    report = {"schema": "companion-v6b-uvicorn-launcher-capture-v1", "state": "INCOMPLETE",
        "source_path": SOURCE, "inputs_sha256": {p: h for p, h in INPUTS.values()},
        "cli_sha256": plan.cli_sha256, "files": [], "commands_completed": 0,
        "overall_bound_seconds": 120, "per_command_bound_seconds": 15, "source_limit_bytes": 65_536,
        "container_exec": False, "container_lifecycle": False, "credential_access": False,
        "runtime_authorized": False, "started_utc_epoch": time.time()}
    with tempfile.TemporaryDirectory(prefix="cryptkeep-launcher-readonly-") as config:
        guard = transport.DockerTransport(plan.cli_sha256, Path(config).resolve())

        def run(args, limit):
            if not guard._verify_cli(deadline):
                raise ValueError("launcher_cli_unverified")
            remaining = min(15, deadline - time.monotonic())
            if remaining <= 0:
                raise ValueError("launcher_deadline")
            raw = transport._run((str(transport.CLI), "--host", transport.ENDPOINT,
                "--config", config, *args), timeout=remaining, input_bytes=None, limit=limit,
                env=dict(transport.ENV))
            report["commands_completed"] += 1
            return raw

        def inventory():
            raw = run(("container", "inspect", "--format", FORMAT, *ids), 65_536)
            rows = [json.loads(line) for line in raw.splitlines()]
            if len(rows) != 4:
                raise ValueError("launcher_inventory_refused")
            for row, old, subject in zip(rows, expected_rows, subjects):
                if (row["id"] != subject["container_id"] or row["image"] != subject["image_id"]
                        or row["state"] != "created" or row["restarts"] != 0
                        or any(row[k] != old[k] for k in row)):
                    raise ValueError("launcher_identity_or_state_changed")
            return rows

        try:
            report["before"] = inventory()
            for subject in subjects:
                # Separate fixed-path capture, not a relaxation of runtime _path policy.
                raw = run(("container", "cp", subject["container_id"] + ":" + SOURCE, "-"), 75_776)
                payload = file_from_tar(raw)
                payload.decode("utf-8", "strict")
                saved = subject["name"] + ".__main__.py.source.txt"
                with (output / saved).open("xb") as stream:
                    stream.write(payload)
                report["files"].append({"name": subject["name"], "container_id": subject["container_id"],
                    "image_id": subject["image_id"], "path": SOURCE, "saved_file": saved,
                    "size_bytes": len(payload), "sha256": digest(payload)})
            report["after"] = inventory()
            if report["before"] != report["after"]:
                raise ValueError("launcher_inventory_changed")
            report["state"] = "READY_FOR_INDEPENDENT_REVIEW"
        except Exception as exc:
            report["failure_class"] = type(exc).__name__
            # Diagnostics contain only a fixed exception class, never native stderr.
            raise
        finally:
            report["elapsed_seconds"] = time.monotonic() - began
            with (output / "report.json").open("xb") as stream:
                stream.write(install.canonical(report))
    print(json.dumps({"state": report["state"], "files": len(report["files"]),
        "commands_completed": report["commands_completed"], "elapsed_seconds": report["elapsed_seconds"],
        "report_sha256": digest((output / "report.json").read_bytes()),
        "container_exec": False, "container_lifecycle": False, "credential_access": False}))


if __name__ == "__main__":
    main()
