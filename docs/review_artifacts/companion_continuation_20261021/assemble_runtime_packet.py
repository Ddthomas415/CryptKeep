"""Derive offline pin evidence, never policy acceptance or runtime permission."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from scripts.research import companion_existing_controller as core
from scripts.research import companion_installer as install
from scripts.research import companion_network_configuration as network
from scripts.research import companion_prepare as preparation
from scripts.research import companion_runtime_adapter as adapter
from scripts.research import companion_staged_update as staged
from scripts.research.companion_docker_transport import _path

HERE = Path(__file__).resolve().parent
PLAN = HERE / "s3_source_refresh_plan"
PINS = {
    "s3_source_refresh_plan/reviewed_preparation_manifest.json": "dd7b537aa39d2f5cbccebf41a20fadc7e2ae8e22ebe20063daf7417286dddb6d",
    "s3_source_refresh_plan/actual_preparation_evidence.json": "fe3569d39351d72766136aae7c58ae24f52f7b3a627edf760d999874f06c2f96",
    "s3_source_refresh_plan/actual_preparation_postcheck.json": "c505e4c6c3b2be5cd1054ac976fd69a503d0fcf2b2304cc6e6583ef1b1decb06",
    "s3_source_refresh_plan/actual_id_review.json": "b9723bdd60158e9f5f354eee34db097af6d6949a3bb113d8dd16a5c6980b931c",
    "installed_facts_capture/report.json": "7dbda2c14b68b58d372508eda0d34e232bc9e6548bd0b7ff5327b027abbdad2b",
    "topical_witness_candidate.json": "56aee572ae72837a859c81f0c5fa70d35ab9ac5dd71128754d57c1df98762cd1",
    "topical_witness_review.json": "2f787ebafbe0d435f4b528ae173d748e40f08fe82237a9cce12d5a0779936c45",
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def derive():
    inputs = {}
    for name, expected in PINS.items():
        raw = (HERE / name).read_bytes()
        if digest(raw) != expected:
            raise ValueError("packet_input_changed: " + name)
        inputs[name] = json.loads(raw)
    plan = preparation._manifest(PLAN / "reviewed_preparation_manifest.json",
        PINS["s3_source_refresh_plan/reviewed_preparation_manifest.json"])
    prepared = staged.ReviewedPreparation.load(
        (PLAN / "actual_preparation_evidence.json").read_bytes(),
        (PLAN / "actual_id_review.json").read_bytes(),
        PINS["s3_source_refresh_plan/actual_id_review.json"], plan)
    postcheck = inputs["s3_source_refresh_plan/actual_preparation_postcheck.json"]
    capture = inputs["installed_facts_capture/report.json"]
    if postcheck["before"] != postcheck["after"] or capture["before"] != capture["after"]:
        raise ValueError("saved_inventory_changed")
    rows = {r["id"]: r for r in postcheck["after"]}
    sources, provenance, excluded = {}, [], []
    for item in capture["files"]:
        raw = (HERE / "installed_facts_capture" / item["saved_file"]).read_bytes()
        if item["status"] != "CAPTURED" or digest(raw) != item["sha256"]:
            raise ValueError("saved_source_changed")
        try:
            _path(item["path"])
        except Exception:
            excluded.append({"path": item["path"], "sha256": item["sha256"],
                "reason": "not a runtime source-pin path; archive has separate verification"})
            continue
        logical = item["name"].split("-staged-", 1)[0]
        sources.setdefault(logical, {})[item["path"]] = item["sha256"]
        provenance.append({**item, "logical_name": logical,
            "binding": "saved capture; identical image or inherited dependency, not new capture"})
    memory_raw = (PLAN / "actual_memory_main.py.source.txt").read_bytes()
    if digest(memory_raw) != postcheck["main_sha256"]:
        raise ValueError("new_memory_source_changed")
    sources["phase1-memory"]["/app/memory_retrieval/main.py"] = digest(memory_raw)
    for item in provenance:
        if item["logical_name"] == "phase1-memory" and item["path"] == "/app/memory_retrieval/main.py":
            item["binding"] = "superseded historical source, not selected for new memory pin"
    provenance.append({"logical_name": "phase1-memory", "path": "/app/memory_retrieval/main.py",
        "sha256": digest(memory_raw), "container_id": postcheck["main_container_id"],
        "image_id": postcheck["main_image_id"], "binding": "direct new-ID source capture"})
    metadata, subjects = [], []
    for old in plan.baseline[:3]:
        row = rows[old.id]
        if row["image"] != old.image or adapter.preservation_digest(row) != old.metadata:
            raise ValueError("storage_binding_changed")
        subjects.append({"name": old.name, "container_id": old.id, "image_id": old.image,
            "preservation_sha256": old.metadata, "sources": sources.get(old.name, {})})
    for app, actual in zip(plan.applications, prepared.replacements):
        row = deepcopy(rows[actual.id])
        # Attempt was independently accepted as backend-attested, not captured here.
        row["attempt"] = actual.attempt
        configured, ids, evidence = network.project(row, dict(plan.network_bindings))
        snapshot = install.Snapshot(row["name"].removeprefix("/"), row["id"], row["image"],
            row["state"], row["started"], row["restarts"], row["restart_policy"],
            adapter.preservation_digest(row), adapter.preservation_digest({**row, "networks": {}}),
            tuple(sorted(n["NetworkID"] for n in row["networks"].values())), actual.attempt,
            configured, ids, evidence)
        if snapshot != actual:
            raise ValueError("staged_binding_changed")
        metadata.append(row)
        final = deepcopy(row)
        for attachment in final["networks"].values():
            attachment["Aliases"] = app["network_options"][1::2]
        if network.project(final, dict(plan.network_bindings))[0] != app["replacement_configured_metadata"]:
            raise ValueError("final_projection_changed")
        if any(sources[app["name"]].get(s["destination"]) != s["sha256"] for s in app["sources"]):
            raise ValueError("app_source_binding_changed")
        subjects.append({"name": app["name"], "container_id": actual.id, "image_id": actual.image,
            "preservation_sha256": adapter.preservation_digest(final), "sources": sources[app["name"]]})
    targets = tuple(adapter.TargetPin(s["name"], s["container_id"], s["image_id"],
        s["preservation_sha256"], tuple(sorted(s["sources"].items()))) for s in subjects)
    topical = inputs["topical_witness_candidate.json"]
    pins = adapter.ReviewedPins(targets, "0" * 64, (), tuple(topical), b"", ())
    validator = adapter.PinnedRuntimeAdapter(None, pins)
    try:
        if tuple(s["name"] for s in subjects) != core.TARGETS or not validator._source_coverage(validator._pins()):
            raise ValueError("source_coverage_failed")
        if not validator._topical_contract():
            raise ValueError("topical_contract_failed")
    finally:
        validator.close()
    return {
        "staged_metadata.derived.json": {"rows": metadata},
        "subjects.draft.json": subjects,
        "topical_approvals.json": topical,
        "provenance.json": {"schema": "companion-runtime-packet-draft-v1", "state": "INCOMPLETE",
            "inputs_sha256": PINS, "source_records": provenance, "excluded_source_paths": excluded,
            "attempt_provenance": "derived from accepted preparation evidence; not an independently captured label",
            "new_memory_sdk_provenance": "inherited source-only image lineage, not directly recaptured",
            "raw_final_network_ids": "blank IDs retained; only aliases modeled; no live attachment claim",
            "source_coverage_validated": True, "policy_approval_created": False,
            "runtime_authorized": False, "native_operations": False},
    }


if __name__ == "__main__":
    artifacts = derive()
    output = HERE / "runtime_packet"
    output.mkdir()
    for name, value in artifacts.items():
        with (output / name).open("xb") as stream:
            stream.write(canonical(value))
    print(json.dumps({"state": "INCOMPLETE", "subjects": len(artifacts["subjects.draft.json"]),
        "source_coverage_validated": True, "native_operations": False,
        "artifacts_sha256": {k: digest(canonical(v)) for k, v in artifacts.items()}}))
