"""Add exact captured-source hashes to a preserved, unapproved subject draft."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from scripts.research.companion_docker_transport import _path
from scripts.research import companion_runtime_adapter as adapter

HERE = Path(__file__).resolve().parent
INPUTS = {
    "runtime_packet/subjects.draft.json": "6215685a6dcd6fc35e3acf87fbb595acf995758ff4013c3c551919692a2c72e6",
    "missing_runtime_sources_authorized/report.json": "7e0445af269135ea252e69da471098e884d71cb967ce261761f7c9c37cb44363",
    "missing_psycopg_attempt_sources/report.json": "d68eb1714c13b5379ad0904f46b83c800fa668530dd497945f17100854cc77fd",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def derive():
    inputs = {}
    for name, expected in INPUTS.items():
        raw = (HERE / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("augmentation_input_changed")
        inputs[name] = json.loads(raw)
    subjects = deepcopy(inputs["runtime_packet/subjects.draft.json"])
    by_id = {s["container_id"]: s for s in subjects[3:]}
    added = []
    for name in tuple(INPUTS)[1:]:
        report = inputs[name]
        if (report["state"] != "READY_FOR_INDEPENDENT_REVIEW" or report["before"] != report["after"]
                or {r["id"] for r in report["before"]} != set(by_id)):
            raise ValueError("augmentation_capture_incomplete")
        for item in report["files"]:
            subject = by_id[item["container_id"]]
            raw = (HERE / Path(name).parent / item["saved_file"]).read_bytes()
            if (item["image_id"] != subject["image_id"] or len(raw) != item["bytes"]
                    or hashlib.sha256(raw).hexdigest() != item["sha256"]):
                raise ValueError("augmentation_source_changed")
            _path(item["path"])
            if item["path"] in subject["sources"]:
                raise ValueError("augmentation_source_duplicate")
            subject["sources"][item["path"]] = item["sha256"]
            added.append({"container_id": item["container_id"], "path": item["path"],
                "sha256": item["sha256"], "capture_report": name})
    if len(added) != 40 or sum(len(s["sources"]) for s in subjects) != 128:
        raise ValueError("augmentation_scope_changed")
    targets = tuple(adapter.TargetPin(s["name"], s["container_id"], s["image_id"],
        s["preservation_sha256"], tuple(sorted(s["sources"].items()))) for s in subjects)
    verifier = adapter.PinnedRuntimeAdapter(None, adapter.ReviewedPins(targets, "0" * 64, (), (), b"", ()))
    try:
        if not verifier._source_coverage(verifier._pins()):
            raise ValueError("augmentation_coverage_failed")
    finally:
        verifier.close()
    return subjects, {"state": "READY_FOR_INDEPENDENT_REVIEW", "inputs_sha256": INPUTS,
        "added_sources": added, "source_entries": 128, "subject_identities_changed": False,
        "policy_approval_created": False, "native_operations": False, "runtime_authorized": False}


if __name__ == "__main__":
    subjects, provenance = derive()
    for name, value in (("subjects.sources_v2.draft.json", subjects), ("source_augmentation.json", provenance)):
        with (HERE / "runtime_packet" / name).open("xb") as stream:
            stream.write(canonical(value))
    print(json.dumps({"state": provenance["state"], "added_sources": 40,
        "source_entries": 128, "native_operations": False}))
