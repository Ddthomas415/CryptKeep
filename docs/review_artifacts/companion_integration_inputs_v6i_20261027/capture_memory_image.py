"""Separately authorized fixed memory-image facts; no startup or execution."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import time

from scripts.research import companion_docker_transport as transport
from scripts.research import companion_installer as install
from scripts.research.companion_staged_update import ReviewedPreparation
from docs.review_artifacts.companion_continuation_20261021.capture_installed_facts import regular_member

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = str(HERE.relative_to(ROOT))
POLICY = "docs/review_artifacts/companion_integration_inputs_v6h_20261026/runtime_packet_v6h/accepted_policy_records/phase1-memory.json"
PINS = {
    BASE + "/reviewed_preparation_manifest.json": "3c8066b43cf924374f2338907f306aadec25fdb599a2ef28a068ab0a21632a33",
    BASE + "/provenance.json": "a3555d20e26d2fd885b852373ce6a25705caf84f5c6839f337e30973ea45356b",
    BASE + "/actual_preparation/preparation_evidence.json": "6b307618be50d7e6179106fbcfc837ac5ec0695a12aaa9888b34fed54e8d2fcf",
    BASE + "/actual_preparation/actual_id_review.json": "f50dc3ecdd7a6271138640c9ac7d873c20377edc0b98311fc63324d70d13efbb",
    BASE + "/actual_preparation/independent_review.json": "609100b858e95dafcc6953141790c17f700fc2e5519877f6ef639be92b764e7a",
    POLICY: "1b007132b549c1fa97e6cea57f3f5980fc3b1dbcb1368ba6f56844538faf1d00",
    "scripts/research/companion_docker_transport.py": "5cbdf417a6b180bdd6e77cf7c9b85eba6649ebd15212f0836725f13301edcd81",
    "docs/review_artifacts/companion_continuation_20261021/capture_installed_facts.py": "a553e37e9bac1b5f6827fa8fe9ff40d520e7dc6005df4fc81064d03b6259eb76",
}
FORMAT = ('{"id":{{json .Id}},"name":{{json .Name}},"image":{{json .Image}},'
          '"state":{{json .State.Status}},"started":{{json .State.StartedAt}},'
          '"restarts":{{json .RestartCount}},"policy":{{json .HostConfig.RestartPolicy.Name}}}')
IMAGE_FORMAT = ('{"id":{{json .Id}},"layers":{{json .RootFS.Layers}},'
                '"onbuild_empty":{{not (index .Config "OnBuild")}}}')
FILE_BUDGET = 8 << 20
PER_FILE = 1 << 20


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def inputs():
    raw = {}
    for path, sha in PINS.items():
        raw[path] = (ROOT / path).read_bytes()
        if digest(raw[path]) != sha:
            raise ValueError("input_changed")
    plan = install.Plan.load(raw[BASE + "/reviewed_preparation_manifest.json"],
                             PINS[BASE + "/reviewed_preparation_manifest.json"])
    reviewed = ReviewedPreparation.load(raw[BASE + "/actual_preparation/preparation_evidence.json"],
        raw[BASE + "/actual_preparation/actual_id_review.json"],
        PINS[BASE + "/actual_preparation/actual_id_review.json"], plan)
    proof = json.loads(raw[BASE + "/provenance.json"])
    for group in (proof["consumer_sha256"], proof["runtime_consumer_sha256"]):
        for path, sha in group.items():
            if digest((ROOT / path).read_bytes()) != sha:
                raise ValueError("consumer_changed")
    original = next(r for r in plan.baseline if r.name == "phase1-memory")
    replacement = next(r for r in reviewed.replacements if r.name == plan.staged_name(original.name))
    app = next(a for a in plan.applications if a["name"] == original.name)
    policy = json.loads(raw[POLICY])
    if policy["decision"] != "ACCEPTED_WITH_RISK" or len(policy["subjects"]) != 1:
        raise ValueError("prior_policy_invalid")
    selected = dict(policy["subjects"][0]["sources"])
    if len(selected) != 48 or len(app["sources"]) != 11:
        raise ValueError("selection_changed")
    for source in app["sources"]:
        if source["destination"] not in selected or digest((ROOT / source["local"]).read_bytes()) != source["sha256"]:
            raise ValueError("application_changed")
        selected[source["destination"]] = source["sha256"]
    if {p for p in selected if selected[p] != policy["subjects"][0]["sources"][p]} != {"/app/memory_retrieval/main.py"}:
        raise ValueError("unexpected_policy_delta")
    for path in selected:
        transport._path(path)
    expected = [{k: getattr(r, k) for k in ("id", "name", "image", "state", "started", "restarts", "policy")}
                for r in (original, replacement)]
    for row in expected:
        row["name"] = "/" + row["name"]
    return plan, expected, selected, len(app["sources"])


def capture():
    began = time.monotonic()
    plan, expected, selected, extra_layers = inputs()
    output = HERE / "memory_image_capture"
    output.mkdir(mode=0o700)
    report = {"schema": "companion-v6i-memory-image-capture-v1", "state": "INCOMPLETE",
        "observed_start_utc": datetime.now(timezone.utc).isoformat(), "inputs_sha256": PINS,
        "source_sha256": digest(Path(__file__).read_bytes()), "files": [], "commands_attempted": 0,
        "file_transfer_bytes_charged": 0, "before": None, "after": None, "images": None,
        "source_policy_accepted": False, "runtime_authorized": False}
    deadline = began + 120
    stage = "before_inventory"
    with tempfile.TemporaryDirectory(prefix="ck-v6i-memory-read-") as config:
        guard = transport.DockerTransport(plan.cli_sha256, Path(config).resolve())

        def command(args, limit, *, final=False):
            command_deadline = deadline - (0 if final else 10)
            remaining = command_deadline - time.monotonic()
            if report["commands_attempted"] >= 51 or remaining <= 0 or not guard._verify_cli(command_deadline):
                raise ValueError("capture_budget_or_cli")
            remaining = command_deadline - time.monotonic()
            if remaining <= 0:
                raise ValueError("capture_deadline")
            report["commands_attempted"] += 1
            return transport._run((str(transport.CLI), "--config", config, "--host", transport.ENDPOINT, *args),
                timeout=min(10, remaining), input_bytes=None, limit=limit, env=dict(transport.ENV))

        def inventory(label, final=False):
            raw = command(("container", "inspect", "--format", FORMAT, *(r["id"] for r in expected)), 65536, final=final)
            (output / (label + ".jsonl")).write_bytes(raw)
            rows = [json.loads(line) for line in raw.splitlines()]
            if rows != expected:
                raise ValueError("identity_or_state_changed")
            return rows

        try:
            report["before"] = inventory("before")
            stage = "image_lineage"
            raw = command(("image", "inspect", "--format", IMAGE_FORMAT, *(r["image"] for r in expected)), 65536)
            (output / "images.jsonl").write_bytes(raw)
            images = report["images"] = [json.loads(line) for line in raw.splitlines()]
            if (len(images) != 2 or [r["id"] for r in images] != [r["image"] for r in expected]
                    or any(r["onbuild_empty"] is not True or not r["layers"] for r in images)
                    or images[1]["layers"][:len(images[0]["layers"])] != images[0]["layers"]
                    or len(images[1]["layers"]) != len(images[0]["layers"]) + extra_layers):
                raise ValueError("image_lineage_changed")
            stage = "selected_files"
            for path, sha in selected.items():
                remaining = FILE_BUDGET - report["file_transfer_bytes_charged"]
                limit = min(PER_FILE + 10240, remaining - 1)
                if limit <= 10240:
                    raise ValueError("file_budget")
                try:
                    raw = command(("container", "cp", expected[1]["id"] + ":" + path, "-"), limit)
                except Exception:
                    report["file_transfer_bytes_charged"] += limit + 1
                    raise
                report["file_transfer_bytes_charged"] += len(raw)
                content = regular_member(raw, path, min(PER_FILE, limit - 10240))
                saved = str(len(report["files"])) + ".source.txt"
                (output / saved).write_bytes(content)
                row = {"path": path, "container_id": expected[1]["id"], "image_id": expected[1]["image"],
                       "saved_file": saved, "sha256": digest(content), "bytes": len(content), "matches_expected": digest(content) == sha}
                report["files"].append(row)
                if not row["matches_expected"]:
                    raise ValueError("file_hash_changed")
        except Exception as error:
            report["failure_stage"], report["failure_class"] = stage, type(error).__name__
        finally:
            try:
                report["after"] = inventory("after", final=True)
            except Exception as error:
                report["final_failure_class"] = type(error).__name__
            if ("failure_class" not in report and "final_failure_class" not in report
                    and report["before"] == report["after"] and len(report["files"]) == 48):
                report["state"] = "READY_FOR_INDEPENDENT_REVIEW"
            report["observed_end_utc"] = datetime.now(timezone.utc).isoformat()
            report["elapsed_seconds"] = time.monotonic() - began
            (output / "report.json").write_bytes(install.canonical(report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-capture", action="store_true")
    parser.add_argument("--approved-sha256")
    args = parser.parse_args(argv)
    if not args.execute_capture:
        print(json.dumps({"native_operations": False, "runtime_authorized": False}))
        return 0
    if args.approved_sha256 != digest(Path(__file__).read_bytes()):
        raise ValueError("source_not_approved")
    result = capture()
    print(json.dumps({k: result[k] for k in ("state", "commands_attempted", "elapsed_seconds")}))
    return 0 if result["state"] == "READY_FOR_INDEPENDENT_REVIEW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
