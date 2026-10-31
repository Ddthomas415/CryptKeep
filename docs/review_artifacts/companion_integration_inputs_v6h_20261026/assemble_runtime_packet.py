"""Offline V6h proposal: actual IDs, modelled configuration, no approvals/actions."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

from scripts.research import companion_existing_controller as core
from scripts.research import companion_installer as install
from scripts.research import companion_network_configuration as network
from scripts.research import companion_prepare as preparation
from scripts.research import companion_runtime_adapter as adapter
from scripts.research import companion_staged_update as staged
from docs.review_artifacts.companion_integration_inputs_v6f_20261025.assemble_runtime_packet import snapshot


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = str(HERE.relative_to(ROOT))
PRIOR = "docs/review_artifacts/companion_integration_inputs_v6g_20261025/runtime_packet_v6g"
GUARD = "dashboard/services/views/_shared_signals.py"
CHANGED = frozenset("scripts/research/" + name + ".py" for name in (
    "companion_evidence_checks", "companion_installer", "companion_runtime_adapter"))
PINS = {
    "manifest": (BASE + "/reviewed_preparation_manifest.json", "d11fccb5e4f7c46e7d726704c9b75c400a1482eab5d1b840027d876a5837f047"),
    "evidence": (BASE + "/actual_preparation/preparation_evidence.json", "950b09d049a7f6a01f91352cb8ff12e1edecedfcf523c13fc75d39e9f25b805d"),
    "id_review": (BASE + "/actual_preparation/actual_id_review.json", "fc18b363eb94a324e3d91500b967a7709ad70fa6635a100b2ab2bb1fda30a79f"),
    "actual_review": (BASE + "/actual_preparation/independent_review.json", "e3c97007d3ea3bd1fb6d2363c4989f226604b01457660c93e6da7e3c448dd9ca"),
    "provenance": (BASE + "/provenance.json", "e60cbfad2f7af46acdf47c018cb345621fa9304a4cf97a6b12fcce5bf36a0ef0"),
    "prior_runtime": (PRIOR + "/accepted_policy_records/runtime_review.json", "df2ec5e24ebe4e4d6acc605056ec49d3821c535199cea489417a75c46f52be60"),
    "prior_scope": (PRIOR + "/accepted_policy_records/scope_review.json", "f01d70a7f459a1a2d4f34b32af1f688ac94d3b153a5c9b0fd641fefa9632612d"),
    "prior_models": (PRIOR + "/staged_metadata.derived.json", "7b22b5af03146c99e7628e2c3a054fa7f07615448219e90b1ec9892498ee0a93"),
    "prior_provenance": (PRIOR + "/provenance.json", "ef824d5ba5a98af870d9ae369cae4331a5f2fd888589e2e62af8bbe17d51c4da"),
    "diagnostics_review": ("docs/review_artifacts/companion_verifier_diagnostics_20261026/independent_review_v2.json", "ca5664535df5109539a51747ebf10683d939e2adaa0d7ae147f991f9d350b35b"),
    "topical": (PRIOR + "/topical_approvals.json", "dc3f5678277fb14afb523d54acfc3ef9303627fb810ad075228702054d18505a"),
    "snapshot_helper": ("docs/review_artifacts/companion_integration_inputs_v6f_20261025/assemble_runtime_packet.py", "16c8616f9152fec3e004ad54e1bd81795323cb88827ff6ccaf2f3933a8d36453"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, sha):
    raw = (ROOT / path).read_bytes()
    if digest(raw) != sha:
        raise ValueError("v6h_packet_input_changed:" + path)
    return raw


def require(condition, label):
    if not condition:
        raise ValueError("v6h_packet_" + label)


def derive():
    raw = {key: checked(*pin) for key, pin in PINS.items()}
    data = {key: json.loads(value) for key, value in raw.items() if key != "snapshot_helper"}
    plan = preparation._manifest(ROOT / PINS["manifest"][0], PINS["manifest"][1])
    prepared = staged.ReviewedPreparation.load(raw["evidence"], raw["id_review"], PINS["id_review"][1], plan)
    prior, scope, proof = data["prior_runtime"], data["prior_scope"], data["provenance"]
    require(data["prior_provenance"]["inherited_exact_prior_image_or_storage_pins"] == 89
            and data["prior_provenance"]["historical_pin_basis"] == {
                "prior_exact_image_or_storage": 52, "prior_common_parent_memory_library": 37}
            and data["prior_provenance"]["total_source_pins"] == 132, "historical_pin_basis")
    for name in ("actual_review", "prior_runtime", "prior_scope", "diagnostics_review"):
        require(data[name]["decision"] == "ACCEPTED_WITH_RISK" and not data[name].get("blocking_findings")
                and not data[name].get("blockers"), "review_unaccepted")
    require(plan.attempt == "workerprep20261026v6h", "attempt")
    for group, expected in (("companion_preparations", True), ("companion_cutovers", False)):
        require(os.path.lexists(ROOT / ".cbp_state/runtime" / group / plan.attempt) is expected, "attempt_state")
    consumers = dict(proof["runtime_consumer_sha256"])
    require(set(consumers) == set(scope["consumer_sha256"]) and len(consumers) == 20, "consumer_inventory")
    require({p for p in consumers if consumers[p] != scope["consumer_sha256"][p]} == CHANGED, "consumer_delta")
    require(all(consumers[p] == data["diagnostics_review"]["hashes"][p] for p in CHANGED), "diagnostics_lineage")
    for path, sha in consumers.items():
        checked(path, sha)
    require(len(proof["consumer_sha256"]) == 13 and all(consumers[p] == h for p, h in proof["consumer_sha256"].items()), "tools")
    require(tuple(s["name"] for s in prior["subjects"]) == core.TARGETS, "subjects")
    for subject in prior["subjects"]:
        child = json.loads(checked(PRIOR + "/accepted_policy_records/" + subject["name"] + ".json",
                                   prior["dependency_reviews"][subject["image_id"]]))
        require(child["subjects"] == [subject], "prior_child")
    require([(r.id, r.image) for r in prepared.replacements]
            == [(r["id"], r["image"]) for r in data["actual_review"]["actual_replacements"]], "actual_review_identity")
    subjects, models, changes = [], [], []
    bindings = dict(plan.network_bindings)
    for before, subject in zip(plan.baseline[:3], prior["subjects"][:3]):
        require((before.id, before.image, before.metadata) == (subject["container_id"], subject["image_id"], subject["preservation_sha256"]), "storage")
        subjects.append(deepcopy(subject))
    require(len(data["prior_models"]["rows"]) == 4 and sum(len(a["sources"]) for a in plan.applications) == 43, "counts")
    for app, actual, previous, template in zip(plan.applications, prepared.replacements, prior["subjects"][3:], data["prior_models"]["rows"]):
        require(previous["name"] == app["name"] and previous["image_id"] == actual.image, "same_image")
        expected = {s["destination"]: s["sha256"] for s in app["sources"]}
        require(expected == {p: h for p, h in previous["sources"].items() if p.startswith("/app/")}, "app_sources")
        for source in app["sources"]:
            checked(source["local"], source["sha256"])
        row = deepcopy(template)
        require(row["id"] == previous["container_id"] and row["image"] == actual.image and row["command"] == app["command"], "model_template")
        row.update(id=actual.id, name="/" + actual.name, hostname=actual.id[:12], attempt=plan.attempt)
        for attachment in row["networks"].values():
            require(attachment["Aliases"] == [template["name"].removeprefix("/")], "temporary_alias")
            attachment["Aliases"] = [actual.name]
        require(snapshot(row, bindings) == actual, "model_attestation_mismatch")
        require(app["network_options"][::2] == ["--alias"] * (len(app["network_options"]) // 2), "network_options")
        subject = network.final_subject({**previous, "container_id": actual.id}, row, bindings, app["network_options"][1::2])
        require(subject["preservation_sha256"] == app["replacement_configured_metadata"], "final_model")
        subjects.append(subject)
        models.append(row)
        changes.append({"name": app["name"], "prior_container_id": previous["container_id"], "container_id": actual.id,
                        "image_id": actual.image, "changed_source_paths": [], "configuration_evidence": "MODELLED"})
    topical = data["topical"]
    require(digest(install.canonical(topical)) == prior["topical_approvals_sha256"], "topical_changed")
    targets = tuple(adapter.TargetPin(s["name"], s["container_id"], s["image_id"], s["preservation_sha256"], tuple(sorted(s["sources"].items()))) for s in subjects)
    validator = adapter.PinnedRuntimeAdapter(None, adapter.ReviewedPins(targets, "0" * 64, (), tuple(topical), b"", ()))
    try:
        require(validator._source_coverage(validator._pins()) and validator._topical_contract(), "structural_contract")
    finally:
        validator.close()
    artifacts, dependencies = {}, {}
    for subject in subjects:
        draft = {"schema": "companion-installed-policy-review-v1", "decision": "INCOMPLETE", "reviewer": "",
                 "image_id": subject["image_id"], "subjects": [subject], "policies": dict.fromkeys(scope["policy_meanings"], "UNVERIFIED")}
        artifacts[subject["name"] + ".draft.json"] = draft
        dependencies[subject["image_id"]] = digest(install.canonical(draft))
    artifacts["runtime_review.draft.json"] = {"schema": "companion-runtime-pins-v2", "decision": "INCOMPLETE", "reviewer": "",
        "subjects": subjects, "dependency_reviews": dependencies, "topical_approvals_sha256": digest(install.canonical(topical)),
        "network_configuration": {"contract": network.CONTRACT, "bindings": bindings}}
    artifacts.update({"subjects.draft.json": subjects, "topical_approvals.json": topical,
        "staged_metadata.derived.json": {"rows": models, "evidence_lane": "MODELLED_TEMPLATE_MATCHED_TO_CONTROLLER_ATTESTATION", "raw_v6h_capture": False},
        "provenance.json": {"schema": "companion-v6h-runtime-packet-proposal-v1", "state": "READY_FOR_INDEPENDENT_REVIEW",
            "attempt": plan.attempt, "input_sha256": {**{p: h for p, h in PINS.values()}, str(Path(__file__).relative_to(ROOT)): digest(Path(__file__).read_bytes())},
            "consumer_sha256": consumers, "subject_delta": changes, "total_source_pins": sum(len(s["sources"]) for s in subjects),
            "application_entries_controller_attested": 43, "direct_file_streams_recaptured": 0,
            "inherited_exact_prior_image_or_storage_pins": 89,
            "historical_pin_basis": {"prior_exact_image_or_storage": 52, "prior_common_parent_memory_library": 37},
            "historical_pin_provenance": {"path": PINS["prior_provenance"][0], "sha256": PINS["prior_provenance"][1],
                "limit": "37 memory-library pins retain their historical common-original-parent/source-only-overlay origin; equality to the prior runtime image is not a fresh capture."},
            "preserved_policy_meanings": scope["policy_meanings"], "preserved_limits": scope["preserved_limits"],
            "configuration_evidence": "MODELLED", "native_operations": False, "credential_access": False,
            "policy_approval_created": False, "cutover_authorized": False, "runtime_state": "INCOMPLETE"}})
    require(artifacts["provenance.json"]["total_source_pins"] == 132, "source_pin_count")
    return artifacts


if __name__ == "__main__":
    artifacts = derive()
    output = HERE / "runtime_packet_v6h"
    output.mkdir(exist_ok=False)
    for name, value in artifacts.items():
        with (output / name).open("xb") as stream:
            stream.write(install.canonical(value))
