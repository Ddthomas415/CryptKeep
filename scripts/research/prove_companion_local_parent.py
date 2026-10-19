"""One explicit image/cache-only proof; never install, start or read credentials."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import time

CLI = Path("/Applications/Docker.app/Contents/Resources/bin/docker")
ENDPOINT = "unix:///Users/baitus/.docker/run/docker.sock"
CLI_HASH = "31ae2d64e51d9dfc728a2934941615cdd92f31279ed6d5c1fb2bfc0a44637a8f"
BASELINE = "docs/review_artifacts/companion_compatibility_20261016.json"
BASELINE_HASH = "85d226fc1e347ecd4187877f6c60a51f53fb75428f89f00d82854dbc5e764d69"
REVIEWED_ENGINE = {"version": "29.8.2", "commit": "8af9fe3"}
ENGINE_FORMAT = '{"version":{{json .Server.Version}},"commit":{{json .Server.GitCommit}}}'
IMAGE_FORMAT = '{"id":{{json .Id}},"layers":{{json .RootFS.Layers}},"onbuild":{{json (index .Config "OnBuild")}}}'
FIELDS = {"id": ".Id", "image": ".Image", "state": ".State.Status", "started": ".State.StartedAt",
          "restarts": ".RestartCount", "restart_policy": ".HostConfig.RestartPolicy.Name",
          "mounts": ".Mounts", "networks": ".NetworkSettings.Networks", "ports": ".HostConfig.PortBindings"}
INSPECT_FORMAT = "{" + ",".join(json.dumps(key) + ":{{json " + value + "}}" for key, value in FIELDS.items()) + "}"
SOURCE = "phase1_research_copilot/shared/probe.py"
SOURCE_HASH = "9f9251260009a63be1dc02918c5dd70b671e6a4428678ec4f55d75b7923e0228"
MISSING = hashlib.sha256(b"cryptkeep-local-parent-negative-20261017").hexdigest()
IMAGE = re.compile(r"sha256:[0-9a-f]{64}\Z")


def context(parent, source):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w") as archive:
        for name, raw in (("Dockerfile", f"FROM {parent}\nCOPY app/shared/probe.py /app/shared/probe.py\n".encode()),
                          ("app/shared/probe.py", source)):
            member = tarfile.TarInfo(name)
            member.size, member.mode, member.mtime = len(raw), 0o644, 0
            archive.addfile(member, io.BytesIO(raw))
    return output.getvalue()


def run(root, output, approved_sha256, *, runner=subprocess.run):
    """The caller authorizes one attempt; a matching hash is not authorization."""
    own_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if approved_sha256 != own_hash or hashlib.sha256(CLI.read_bytes()).hexdigest() != CLI_HASH:
        raise ValueError("identity_changed_no_commands_run")
    root = root.resolve()
    source_path = root / SOURCE
    if source_path.is_symlink() or source_path.resolve(strict=True) != source_path:
        raise ValueError("source_path_refused")
    source = source_path.read_bytes()
    if len(source) > 65_536 or hashlib.sha256(source).hexdigest() != SOURCE_HASH:
        raise ValueError("source_identity_changed_no_commands_run")
    baseline_bytes = (root / BASELINE).read_bytes()
    if hashlib.sha256(baseline_bytes).hexdigest() != BASELINE_HASH:
        raise ValueError("baseline_identity_changed_no_commands_run")
    baseline = json.loads(baseline_bytes)["targets"]
    if len(baseline) != 7 or not IMAGE.fullmatch(baseline[3]["image_id"]):
        raise ValueError("baseline_refused")
    output.mkdir(parents=True, exist_ok=False)
    end = time.monotonic() + 120
    report = {"state": "INCOMPLETE", "scope": "One present-parent and one missing-parent build; image/cache only",
              "runner_sha256": own_hash, "cli_sha256": CLI_HASH, "source_sha256": SOURCE_HASH,
              "baseline_sha256": BASELINE_HASH,
              "observed_utc": datetime.now(timezone.utc).isoformat(), "commands": [],
              "build_requests": 0, "runtime_state": "INCOMPLETE", "network_trace_collected": False}

    def save():
        (output / "receipt.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    with tempfile.TemporaryDirectory(prefix="cki-local-parent-") as config:
        def call(args, *, payload=None, timeout=10, allow_failure=False):
            remaining = end - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("overall_deadline")
            report["commands"].append(list(args))
            save()
            result = runner((str(CLI), "--config", config, "--host", ENDPOINT, *args),
                            input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=min(timeout, remaining), close_fds=True,
                            env={"PATH": "/usr/bin:/bin", "DOCKER_BUILDKIT": "0"})
            if len(result.stdout) + len(result.stderr) > 2_000_000:
                raise RuntimeError("output_limit")
            if result.returncode and not allow_failure:
                raise RuntimeError("command_failed")
            return result

        def inventory():
            return [json.loads(line) for line in call(("container", "inspect", "--format", INSPECT_FORMAT,
                    *[r["id"] for r in baseline])).stdout.splitlines()]

        def image(identity):
            return json.loads(call(("image", "inspect", "--format", IMAGE_FORMAT, identity)).stdout)

        verified = False
        try:
            report["engine"] = json.loads(call(("version", "--format", ENGINE_FORMAT)).stdout)
            if report["engine"] != REVIEWED_ENGINE:
                raise RuntimeError("unreviewed_engine")
            report["before"] = inventory()
            rows = report["before"]
            if ([(r["id"], r["image"], r["state"]) for r in rows]
                    != [(r["id"], r["image_id"], "exited") for r in baseline]
                    or any(r.get("restarts") != 0 or r.get("restart_policy") != "no" for r in rows)):
                raise RuntimeError("baseline_changed")
            parent = image(baseline[3]["image_id"])
            if parent["id"] != baseline[3]["image_id"] or parent["onbuild"] or not parent["layers"]:
                raise RuntimeError("parent_refused")
            report["parent"] = parent
            missing = call(("image", "inspect", "--format", "{{json .Id}}", "sha256:" + MISSING), allow_failure=True)
            if (missing.returncode != 1 or b"no such image" not in missing.stderr.lower()):
                raise RuntimeError("missing_parent_not_confirmed")
            report["missing_parent"] = "sha256:" + MISSING
            for label, parent_id in (("present", parent["id"].removeprefix("sha256:")), ("missing", MISSING)):
                payload = context(parent_id, source)
                (output / (label + "_context.tar")).write_bytes(payload)
                report[label + "_context_sha256"] = hashlib.sha256(payload).hexdigest()
                report["build_requests"] += 1
                result = call(("build", "--quiet", "--pull=false", "--network=none", "-"),
                              payload=payload, timeout=45 if label == "present" else 15, allow_failure=True)
                if label == "present":
                    identity = result.stdout.decode("ascii").strip()
                    if result.returncode or not IMAGE.fullmatch(identity) or identity == parent["id"]:
                        raise RuntimeError("positive_build_failed")
                    report["built"] = image(identity)
                    if (report["built"]["id"] != identity or report["built"]["onbuild"]
                            or report["built"]["layers"][:-1] != parent["layers"]
                            or len(report["built"]["layers"]) != len(parent["layers"]) + 1):
                        raise RuntimeError("positive_lineage_failed")
                else:
                    marker = b"cannot specify 64-byte hexadecimal strings"
                    if result.returncode != 1 or marker not in result.stdout + result.stderr:
                        raise RuntimeError("negative_parser_refusal_not_shown")
                    report["negative_returncode"] = result.returncode
                    report["negative_parser_refusal"] = True
            verified = True
        except Exception as error:
            # Only fixed categories, never subprocess stderr or arbitrary exception text.
            report["failure_type"] = type(error).__name__
            if isinstance(error, RuntimeError) and str(error) in {
                    "unreviewed_engine", "baseline_changed", "parent_refused", "missing_parent_not_confirmed",
                    "positive_build_failed", "positive_lineage_failed", "negative_parser_refusal_not_shown",
                    "overall_deadline", "output_limit", "command_failed"}:
                report["failure_category"] = str(error)
        finally:
            if "before" in report:
                try:
                    report["after"] = inventory()
                    report["originals_unchanged"] = report["after"] == report["before"]
                except Exception as error:
                    report["final_check_failure_type"] = type(error).__name__
            if verified and report.get("originals_unchanged") is True:
                report["state"] = "READY_FOR_INDEPENDENT_REVIEW"
            save()
    print(json.dumps({key: report.get(key) for key in ("state", "build_requests", "originals_unchanged",
                                                     "negative_parser_refusal", "failure_category")}))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approved-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"state": "INCOMPLETE", "inert": True, "authorization_required": True}))
        return
    result = run(Path(__file__).resolve().parents[2], args.output, args.approved_sha256)
    if result["state"] != "READY_FOR_INDEPENDENT_REVIEW":
        raise RuntimeError("proof_incomplete")


if __name__ == "__main__":
    main()
