"""One authorized synthetic import check; no existing service startup."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import time
import uuid

CLI = Path("/Applications/Docker.app/Contents/Resources/bin/docker")
CLI_HASH = "31ae2d64e51d9dfc728a2934941615cdd92f31279ed6d5c1fb2bfc0a44637a8f"
ENDPOINT = "unix:///Users/baitus/.docker/run/docker.sock"
BASE = "docs/review_artifacts/companion_compatibility_20261016.json"
BASE_HASH = "85d226fc1e347ecd4187877f6c60a51f53fb75428f89f00d82854dbc5e764d69"
MANIFEST = "docs/review_artifacts/companion_import_inventory_20261018/source_bundle/manifest.json"
MANIFEST_HASH = "973da853c3c2aabdce982c677b5b6ab9c6d7cbab5061ec27ab28197b07b3c875"
PAYLOAD = "scripts/research/companion_import_payload.py"
PAYLOAD_HASH = "c62e27b04494eb5dab51fc7d72c3403ea44cec7c72ab5267c4c5dc5c20888a13"
LABEL = "cryptkeep.import-proof"
MODULES = ("audit_log", "risk_stub", "memory_retrieval", "orchestrator")
IPV6_SOURCE_HASH = "2633bbdb69731e5ccb5cf4e4afd65605d86c7979cc5633126f50c92d5ad74a74"
ID = re.compile(r"[0-9a-f]{64}\Z")
ORIGINAL_FORMAT = ('{"id":{{json .Id}},"image":{{json .Image}},"state":{{json .State.Status}},'
                   '"restarts":{{json .RestartCount}},"policy":{{json .HostConfig.RestartPolicy.Name}}}')
OWN_FORMAT = ('{"id":{{json .Id}},"name":{{json .Name}},"image":{{json .Image}},'
              '"state":{{json .State.Status}},"exit":{{json .State.ExitCode}},'
              '"attempt":{{json (index .Config.Labels "cryptkeep.import-proof")}}}')
IMAGE_FORMAT = ('{"id":{{json .Id}},"volumes":{{not (not (index .Config "Volumes"))}},'
                '"loader_env":[{{range (index .Config "Env")}}{{if or '
                '(and (ge (len .) 3) (eq (slice . 0 3) "LD_")) '
                '(eq (index (split . "=") 0) "GCONV_PATH")}}{{true}},{{end}}{{end}}false]}')


def checked(path, expected):
    if path.is_symlink() or path.resolve(strict=True) != path:
        raise ValueError("source_path_refused")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("source_hash_refused")
    return raw


def safe_network_events(value):
    """Accept bounded caller identifiers only, never arguments or tracebacks."""
    if type(value) is not list or len(value) > 8:
        return None
    for event in value:
        if type(event) is not dict or set(event) not in (
                {"operation", "module", "function", "line"},
                {"operation", "module", "function", "line", "classification", "source_sha256"}):
            return None
        if type(event["operation"]) is not str or event["operation"] not in {
                "connect", "connect_ex", "bind", "listen", "getaddrinfo"}:
            return None
        if any(not isinstance(event[key], str) or not re.fullmatch(
                r"[A-Za-z_][A-Za-z0-9_.]{0,127}", event[key]) for key in ("module", "function")):
            return None
        if type(event["line"]) is not int or not 0 <= event["line"] <= 10_000_000:
            return None
        if "classification" in event and event != local_probe_event():
            return None
    return value


def local_probe_event():
    return {"operation": "bind", "module": "urllib3.util.connection", "function": "_has_ipv6",
            "line": 127, "classification": "blocked_ipv6_capability_probe", "source_sha256": IPV6_SOURCE_HASH}


def activity_valid(denied, events, allow_blocked_local_probe):
    if (type(denied) is not dict or set(denied) != {"network", "repository"}
            or any(type(value) is not int for value in denied.values())):
        return False
    return ((denied == {"network": 0, "repository": 0} and events == [])
            or (allow_blocked_local_probe is True and denied == {"network": 1, "repository": 0}
                and events == [local_probe_event()]))


def freeze(root, output):
    """Write only exact regular application source members, never /repo or .env."""
    manifest_path = root / MANIFEST
    manifest = json.loads(checked(manifest_path, MANIFEST_HASH))
    payload = checked(root / PAYLOAD, PAYLOAD_HASH)
    apps = []
    for app, module in zip(manifest["applications"], MODULES, strict=True):
        stage = output / module
        stage.mkdir(mode=0o755)
        archive_path = manifest_path.parent / app["source_snapshot"]
        checked(archive_path, app["snapshot_sha256"])
        expected = {}
        with tarfile.open(archive_path) as archive:
            members = archive.getmembers()
            by_name = {m.name: m for m in members}
            if len(by_name) != len(members):
                raise ValueError("archive_duplicates")
            for source in app["sources"]:
                relative = source["destination"].removeprefix("/app/")
                if not re.fullmatch(r"[a-z_]+/[a-z_]+\.py", relative):
                    raise ValueError("application_path_refused")
                member = by_name[source["local"]]
                if not member.isreg() or member.size > 1_048_576:
                    raise ValueError("archive_member_refused")
                raw = archive.extractfile(member).read()
                if hashlib.sha256(raw).hexdigest() != source["sha256"]:
                    raise ValueError("archive_member_hash_refused")
                target = stage / relative
                target.parent.mkdir(mode=0o755, exist_ok=True)
                target.write_bytes(raw)
                target.chmod(0o444)
                expected[relative] = source["sha256"]
        script = stage / "import_check.py"
        script.write_bytes(payload)
        script.chmod(0o444)
        apps.append({"name": app["name"], "module": module, "image": app["parent_image"],
                     "stage": str(stage), "expected": expected})
    return apps


def run(root, output, approved_sha256, *, remaining_only=False, allow_blocked_local_probe=False,
        runner=subprocess.run):
    root = root.resolve()
    own_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if own_hash != approved_sha256:
        raise ValueError("runner_identity_refused")
    checked(CLI, CLI_HASH)
    baseline = json.loads(checked(root / BASE, BASE_HASH))["targets"]
    output.mkdir(parents=True, exist_ok=False)
    output = output.resolve()
    stages = output / "frozen"
    stages.mkdir(mode=0o755)
    apps = freeze(root, stages)
    if [a["name"] for a in apps] != [r["name"] for r in baseline[3:]] or any(
            a["image"] != r["image_id"] for a, r in zip(apps, baseline[3:], strict=True)):
        raise ValueError("parent_identity_refused")
    if remaining_only:
        apps = apps[2:]
    # Preserve the exact executed code before any later corrective edits.
    with tarfile.open(output / "executed_sources.tar", "x") as archive:
        for relative in (__file__, str(root / PAYLOAD)):
            archive.add(relative, arcname=Path(relative).name, recursive=False)
    attempt = uuid.uuid4().hex
    report = {"state": "INCOMPLETE", "attempt": attempt, "runner_sha256": own_hash,
              "payload_sha256": PAYLOAD_HASH, "manifest_sha256": MANIFEST_HASH,
              "selected_modules": [app["module"] for app in apps],
              "import_contract": "blocked_local_probe_v2" if allow_blocked_local_probe else "zero_denials_v1",
              "observed_utc": datetime.now(timezone.utc).isoformat(), "commands": [], "results": [], "diagnostics": [],
              "owned": [], "removed": [], "runtime_state": "INCOMPLETE"}
    deadline = time.monotonic() + 180
    work_end = deadline - 30

    def save():
        (output / "receipt.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    with tempfile.TemporaryDirectory(prefix="cki-import-cli-") as config:
        def call(args, *, timeout=10, failure=False, cleanup=False):
            remaining = (deadline if cleanup else work_end) - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("deadline")
            report["commands"].append(list(args))
            save()
            result = runner((str(CLI), "--config", config, "--host", ENDPOINT, *args),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True,
                            timeout=min(timeout, remaining), env={"PATH": "/usr/bin:/bin"})
            if len(result.stdout) + len(result.stderr) > 1_048_576:
                raise RuntimeError("output_limit")
            if result.returncode and not failure:
                raise RuntimeError("command_failed")
            return result

        def inventory(*, cleanup=False):
            result = call(("container", "inspect", "--format", ORIGINAL_FORMAT,
                           *[r["id"] for r in baseline]), cleanup=cleanup)
            return [json.loads(line) for line in result.stdout.splitlines()]

        def owned(app, *, cleanup=False):
            result = call(("container", "inspect", "--format", OWN_FORMAT, app["test_name"]), cleanup=cleanup)
            row = json.loads(result.stdout)
            if (not ID.fullmatch(row["id"]) or row["id"] in {r["id"] for r in baseline}
                    or row["name"] != "/" + app["test_name"] or row["image"] != app["image"]
                    or row["attempt"] != attempt or app.get("test_id", row["id"]) != row["id"]):
                raise RuntimeError("ownership_unknown")
            return row

        def remove(app, row, *, cleanup=False):
            call(("container", "rm", row["id"]), cleanup=cleanup)
            absent = call(("container", "inspect", "--format", "{{json .Id}}", app["test_name"]),
                          failure=True, cleanup=cleanup)
            if absent.returncode != 1 or b"no such" not in absent.stderr.lower():
                raise RuntimeError("removal_unverified")
            report["removed"].append(row["id"])

        all_passed = False
        pending = []
        try:
            report["before"] = inventory()
            expected = [{"id": r["id"], "image": r["image_id"], "state": "exited", "restarts": 0,
                         "policy": "no"} for r in baseline]
            if report["before"] != expected:
                raise RuntimeError("originals_changed")
            for app in apps:
                image = json.loads(call(("image", "inspect", "--format", IMAGE_FORMAT, app["image"])).stdout)
                if image["id"] != app["image"] or image["volumes"] or any(image["loader_env"]):
                    raise RuntimeError("image_configuration_refused")
            for index, app in enumerate(apps):
                app["test_name"] = "cryptkeep-import-" + attempt + "-" + str(index)
                absent = call(("container", "inspect", "--format", "{{json .Id}}", app["test_name"]), failure=True)
                if absent.returncode != 1 or b"no such" not in absent.stderr.lower():
                    raise RuntimeError("test_name_not_available")
                pending.append(app)
                mount = "type=bind,source=" + app["stage"] + ",target=/frozen,readonly,bind-propagation=rprivate"
                if any(c in app["stage"] for c in ",\r\n"):
                    raise RuntimeError("stage_path_refused")
                created = call(("container", "create", "--pull=never", "--name", app["test_name"],
                    "--label", LABEL + "=" + attempt, "--network", "none", "--read-only", "--no-healthcheck",
                    "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "64",
                    "--memory", "512m", "--cpus", "1", "--restart", "no", "--user", "65534:65534",
                    "--workdir", "/tmp", "--tmpfs", "/tmp:rw,noexec,nosuid,size=16777216,mode=1777",
                    "--mount", mount, "--entrypoint", "/usr/local/bin/python", app["image"],
                    "-I", "-S", "-B", "/frozen/import_check.py", app["module"],
                    *(("--allow-blocked-local-probe",) if allow_blocked_local_probe else ())))
                app["test_id"] = created.stdout.decode("ascii").strip()
                if not ID.fullmatch(app["test_id"]) or owned(app)["state"] != "created":
                    raise RuntimeError("creation_unverified")
                report["owned"].append(app["test_id"])
                result = call(("container", "start", "--attach", app["test_id"]), timeout=20, failure=True)
                row = owned(app)
                payload = json.loads(result.stdout)
                diagnostic = {"module": app["module"], "exit": row["exit"], "cli_returncode": result.returncode}
                for key in ("stage", "failure_type", "failure_category", "missing_module"):
                    value = payload.get(key) if isinstance(payload, dict) else None
                    if isinstance(value, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]{0,127}", value):
                        diagnostic[key] = value
                denied = payload.get("denied") if isinstance(payload, dict) else None
                if (type(denied) is dict and set(denied) == {"network", "repository"}
                        and all(type(v) is int and 0 <= v <= 100_000 for v in denied.values())):
                    diagnostic["denied"] = denied
                events = safe_network_events(payload.get("network_events")) if isinstance(payload, dict) else None
                if events is not None:
                    diagnostic["network_events"] = events
                report["diagnostics"].append(diagnostic)
                save()
                if result.returncode or row["state"] != "exited" or row["exit"] != 0:
                    raise RuntimeError("import_process_failed")
                loaded = payload.get("loaded_sources")
                if (payload.get("ok") is not True or payload.get("module") != app["module"]
                        or payload.get("python") != [3, 11] or payload.get("synthetic_settings") is not True
                        or payload.get("lifespan_run") is not False
                        or payload.get("allow_blocked_local_probe") is not allow_blocked_local_probe
                        or not activity_valid(payload.get("denied"), events, allow_blocked_local_probe)
                        or type(loaded) is not dict or not loaded
                        or loaded.get(app["module"] + "/main.py") != app["expected"][app["module"] + "/main.py"]
                        or any(app["expected"].get(p) != digest for p, digest in loaded.items())):
                    raise RuntimeError("import_evidence_refused")
                report["results"].append({"image": app["image"], "test_id": app["test_id"],
                    "ok": True, "module": app["module"], "python": [3, 11],
                    "synthetic_settings": True, "lifespan_run": False, "stage": "complete",
                    "denied": payload["denied"], "network_events": events,
                    "allow_blocked_local_probe": allow_blocked_local_probe,
                    "loaded_sources": loaded})
                remove(app, row)
                pending.remove(app)
            all_passed = True
        except Exception as error:
            report["failure_type"] = type(error).__name__
        finally:
            for app in reversed(pending):
                try:
                    row = owned(app, cleanup=True)
                    if row["state"] not in {"created", "exited"}:
                        call(("container", "stop", "--time", "1", row["id"]), cleanup=True)
                        row = owned(app, cleanup=True)
                    if row["state"] not in {"created", "exited"}:
                        raise RuntimeError("cleanup_state_unknown")
                    remove(app, row, cleanup=True)
                except Exception:
                    report["cleanup_incomplete"] = True
            try:
                report["after"] = inventory(cleanup=True)
                report["originals_unchanged"] = report["after"] == report.get("before")
            except Exception:
                report["originals_unchanged"] = False
            if all_passed and not pending and report.get("originals_unchanged") is True:
                report["state"] = "READY_FOR_INDEPENDENT_REVIEW"
            save()
    print(json.dumps({"state": report["state"], "imports": len(report["results"]),
                      "removed": len(report["removed"]), "originals_unchanged": report.get("originals_unchanged"),
                      "failure_type": report.get("failure_type"), "cleanup_incomplete": report.get("cleanup_incomplete", False)}))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approved-sha256")
    parser.add_argument("--remaining-only", action="store_true",
                        help="Check memory first, then orchestrator only if memory passes")
    parser.add_argument("--allow-blocked-local-probe", action="store_true",
                        help="Opt in to the reviewed, source-pinned blocked localhost probe contract")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"state": "INCOMPLETE", "inert": True}))
        return
    result = run(Path(__file__).resolve().parents[2], args.output, args.approved_sha256,
                 remaining_only=args.remaining_only, allow_blocked_local_probe=args.allow_blocked_local_probe)
    if result["state"] != "READY_FOR_INDEPENDENT_REVIEW":
        raise RuntimeError("installed_import_proof_incomplete")


if __name__ == "__main__":
    main()
