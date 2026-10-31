"""Offline V6i proposal: actual IDs, modelled configuration, no approvals/actions."""
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
PRIOR = "docs/review_artifacts/companion_integration_inputs_v6h_20261026/runtime_packet_v6h"
GUARD = "dashboard/services/views/_shared_signals.py"
CHANGED = frozenset({"scripts/research/companion_evidence_checks.py"})
MAIN = "/app/memory_retrieval/main.py"
PINS = {
    "manifest": (BASE + "/reviewed_preparation_manifest.json", "3c8066b43cf924374f2338907f306aadec25fdb599a2ef28a068ab0a21632a33"),
    "evidence": (BASE + "/actual_preparation/preparation_evidence.json", "6b307618be50d7e6179106fbcfc837ac5ec0695a12aaa9888b34fed54e8d2fcf"),
    "id_review": (BASE + "/actual_preparation/actual_id_review.json", "f50dc3ecdd7a6271138640c9ac7d873c20377edc0b98311fc63324d70d13efbb"),
    "actual_review": (BASE + "/actual_preparation/independent_review.json", "609100b858e95dafcc6953141790c17f700fc2e5519877f6ef639be92b764e7a"),
    "provenance": (BASE + "/provenance.json", "a3555d20e26d2fd885b852373ce6a25705caf84f5c6839f337e30973ea45356b"),
    "prior_runtime": (PRIOR + "/accepted_policy_records/runtime_review.json", "ed4b60bf40c7d55fe8f603a4d92c3211902b6f47340403211b0c04cfb63d2f1c"),
    "prior_scope": (PRIOR + "/accepted_policy_records/scope_review.json", "1ede90d017d8f59b99497073610c3161365652f52bbb9d79633a37617ca29aa2"),
    "prior_models": (PRIOR + "/staged_metadata.derived.json", "ed24d414eb8a12afce0d4756686dbf40d8baa649672fbcc5dfc3cdb29a4909d7"),
    "prior_provenance": (PRIOR + "/provenance.json", "6645cef0b870325a30668c8018761beac5ec5c30f06d99b5ed14455539103dfc"),
    "repair_review": ("docs/review_artifacts/companion_archival_market_exclusion_20261026/independent_review.json", "167cfa9ca11965368faa054e1a3ad050bd41b05049f6ea202a4da2cde12c763d"),
    "repair_report": ("docs/review_artifacts/companion_archival_market_exclusion_20261026/report.json", "71868bd2fa6632448eb1eb930f12b5afde1c6cfa3e68ef27e0912369d1a845eb"),
    "memory_review": (BASE + "/memory_image_capture/independent_review.json", "9f33a094c632497a115d236861805ddef116f404115663a65bb410e590af2bb6"),
    "memory_capture": (BASE + "/memory_image_capture/report.json", "578cdb75388031bfc2c7c60a293e11131f9dafe0f87cebfed1116a5510b92001"),
    "topical": (PRIOR + "/topical_approvals.json", "dc3f5678277fb14afb523d54acfc3ef9303627fb810ad075228702054d18505a"),
    "snapshot_helper": ("docs/review_artifacts/companion_integration_inputs_v6f_20261025/assemble_runtime_packet.py", "16c8616f9152fec3e004ad54e1bd81795323cb88827ff6ccaf2f3933a8d36453"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, sha):
    raw = (ROOT / path).read_bytes()
    if digest(raw) != sha:
        raise ValueError("v6i_packet_input_changed:" + path)
    return raw


def require(condition, label):
    if not condition:
        raise ValueError("v6i_packet_" + label)


def memory_sources(data, plan, prepared, prior, scope):
    review, capture = data["memory_review"], data["memory_capture"]
    applicability = review["conditional_applicability"]
    require(applicability["decision"] == "ACCEPTED_WITH_RISK"
            and applicability["policy_meanings"] == scope["policy_meanings"]
            and applicability["changed_main_repair_review_sha256"] == PINS["repair_review"][1]
            and review["operations_authorized"] is False
            and review["final_subject_policy_record_issued"] is False, "memory_applicability")
    actual = next(r for r in prepared.replacements if r.name == plan.staged_name("phase1-memory"))
    original = next(r for r in plan.baseline if r.name == "phase1-memory")
    before, after = capture["before"], capture["after"]
    require(capture["state"] == "READY_FOR_INDEPENDENT_REVIEW" and before == after
            and before == review["selected_targets"] and len(before) == 2
            and before[0]["id"] == original.id and before[0]["image"] == original.image
            and before[1]["id"] == actual.id and before[1]["image"] == actual.image
            and before[1]["state"] == "created" and before[1]["restarts"] == 0
            and before[1]["started"] in core.NEVER_STARTED, "memory_identity")
    folder = BASE + "/memory_image_capture/"
    hashes = review["hashes"]["reviewed_inputs"]
    for key in ("before", "after", "images"):
        path = folder + key + ".jsonl"
        rows = [json.loads(line) for line in checked(path, hashes[path]).splitlines()]
        require(rows == capture[key], "memory_raw_metadata")
    images = capture["images"]
    require(len(images) == 2 and [r["id"] for r in images] == [original.image, actual.image]
            and all(r["onbuild_empty"] is True for r in images)
            and len(images[0]["layers"]) > 0
            and images[1]["layers"][:len(images[0]["layers"])] == images[0]["layers"]
            and len(images[1]["layers"]) == len(images[0]["layers"]) + 11, "memory_lineage")
    previous = next(s for s in prior["subjects"] if s["name"] == "phase1-memory")
    expected = dict(previous["sources"])
    app = next(a for a in plan.applications if a["name"] == "phase1-memory")
    expected.update({s["destination"]: s["sha256"] for s in app["sources"]})
    require(len(expected) == 48 and len(app["sources"]) == 11
            and {p for p in expected if expected[p] != previous["sources"][p]} == {MAIN}
            and expected[MAIN] == data["repair_review"]["hashes"]["phase1_research_copilot/memory_retrieval/main.py"]
            and expected == review["source_evidence"]["source_path_sha256"], "memory_source_delta")
    files = capture["files"]
    require(len(files) == 48 and {f["path"] for f in files} == set(expected), "memory_file_set")
    for index, file in enumerate(files):
        require(file["saved_file"] == str(index) + ".source.txt"
                and file["container_id"] == actual.id and file["image_id"] == actual.image
                and file["sha256"] == expected[file["path"]]
                and file["matches_expected"] is True, "memory_file_binding")
        path = folder + file["saved_file"]
        payload = checked(path, hashes[path])
        require(digest(payload) == expected[file["path"]] and len(payload) == file["bytes"], "memory_file_bytes")
    return expected


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
    for name in ("actual_review", "prior_runtime", "prior_scope", "repair_review", "memory_review"):
        require(data[name]["decision"] == "ACCEPTED_WITH_RISK" and not data[name].get("blocking_findings")
                and not data[name].get("blockers"), "review_unaccepted")
    require(plan.attempt == "workerprep20261027v6i", "attempt")
    for group, expected in (("companion_preparations", True), ("companion_cutovers", False)):
        require(os.path.lexists(ROOT / ".cbp_state/runtime" / group / plan.attempt) is expected, "attempt_state")
    consumers = dict(proof["runtime_consumer_sha256"])
    require(set(consumers) == set(scope["consumer_sha256"]) and len(consumers) == 20, "consumer_inventory")
    require({p for p in consumers if consumers[p] != scope["consumer_sha256"][p]} == CHANGED, "consumer_delta")
    require(all(consumers[p] == data["repair_review"]["hashes"][p]
                and scope["consumer_sha256"][p] == data["repair_report"]["before_sha256"][p]
                for p in CHANGED), "repair_lineage")
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
    captured_sources = memory_sources(data, plan, prepared, prior, scope)
    subjects, models, changes = [], [], []
    bindings = dict(plan.network_bindings)
    for before, subject in zip(plan.baseline[:3], prior["subjects"][:3]):
        require((before.id, before.image, before.metadata) == (subject["container_id"], subject["image_id"], subject["preservation_sha256"]), "storage")
        subjects.append(deepcopy(subject))
    require(len(data["prior_models"]["rows"]) == 4 and sum(len(a["sources"]) for a in plan.applications) == 43, "counts")
    for app, actual, previous, template in zip(plan.applications, prepared.replacements, prior["subjects"][3:], data["prior_models"]["rows"]):
        require(previous["name"] == app["name"], "application_name")
        source_subject = deepcopy(previous)
        if app["name"] == "phase1-memory":
            source_subject.update(image_id=actual.image, sources=captured_sources)
        else:
            require(previous["image_id"] == actual.image, "same_image")
        expected = {s["destination"]: s["sha256"] for s in app["sources"]}
        require(expected == {p: h for p, h in source_subject["sources"].items() if p.startswith("/app/")}, "app_sources")
        for source in app["sources"]:
            checked(source["local"], source["sha256"])
        row = deepcopy(template)
        require(row["id"] == previous["container_id"] and row["image"] == previous["image_id"] and row["command"] == app["command"], "model_template")
        row.update(id=actual.id, image=actual.image, name="/" + actual.name, hostname=actual.id[:12], attempt=plan.attempt)
        for attachment in row["networks"].values():
            require(attachment["Aliases"] == [template["name"].removeprefix("/")], "temporary_alias")
            attachment["Aliases"] = [actual.name]
        require(snapshot(row, bindings) == actual, "model_attestation_mismatch")
        require(app["network_options"][::2] == ["--alias"] * (len(app["network_options"]) // 2), "network_options")
        subject = network.final_subject({**source_subject, "container_id": actual.id}, row, bindings, app["network_options"][1::2])
        require(subject["preservation_sha256"] == app["replacement_configured_metadata"], "final_model")
        subjects.append(subject)
        models.append(row)
        changes.append({"name": app["name"], "prior_container_id": previous["container_id"], "container_id": actual.id,
                        "image_id": actual.image, "changed_source_paths": [p for p in previous["sources"] if previous["sources"][p] != source_subject["sources"][p]], "configuration_evidence": "MODELLED"})
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
        "staged_metadata.derived.json": {"rows": models, "evidence_lane": "MODELLED_TEMPLATE_MATCHED_TO_CONTROLLER_ATTESTATION", "raw_v6i_capture": False},
        "provenance.json": {"schema": "companion-v6i-runtime-packet-proposal-v1", "state": "READY_FOR_INDEPENDENT_REVIEW",
            "attempt": plan.attempt, "input_sha256": {**{p: h for p, h in PINS.values()}, str(Path(__file__).relative_to(ROOT)): digest(Path(__file__).read_bytes())},
            "consumer_sha256": consumers, "subject_delta": changes, "total_source_pins": sum(len(s["sources"]) for s in subjects),
            "application_entries_controller_attested": 43, "direct_file_streams_recaptured": 48,
            "inherited_exact_prior_image_or_storage_pins": 52,
            "source_evidence_partition": {"direct_memory_streams": 48, "other_controller_attested_app_entries": 32, "prior_exact_image_or_storage_pins": 52},
            "historical_pin_basis": deepcopy(data["prior_provenance"]["historical_pin_basis"]),
            "historical_pin_provenance": {"path": PINS["prior_provenance"][0], "sha256": PINS["prior_provenance"][1],
                "limit": "Prior 52/37 origin is historical only. All 48 memory files now have reviewed direct capture streams; other subjects are not upgraded by that capture."},
            "preserved_policy_meanings": scope["policy_meanings"], "preserved_limits": scope["preserved_limits"],
            "memory_applicability_review": {"path": PINS["memory_review"][0], "sha256": PINS["memory_review"][1], "scope": "conditional source applicability; final subjects still require independent policy review"},
            "configuration_evidence": "MODELLED", "native_operations": False, "credential_access": False,
            "policy_approval_created": False, "cutover_authorized": False, "runtime_state": "INCOMPLETE"}})
    require(artifacts["provenance.json"]["total_source_pins"] == 132, "source_pin_count")
    return artifacts


if __name__ == "__main__":
    artifacts = derive()
    output = HERE / "runtime_packet_v6i"
    output.mkdir(exist_ok=False)
    for name, value in artifacts.items():
        with (output / name).open("xb") as stream:
            stream.write(install.canonical(value))
