"""Pure V2 packet proposal for accepted v6c IDs; no policy or runtime authority."""
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = str(HERE.relative_to(ROOT))
PRIOR = BASE + "/runtime_packet_v6b_launcher"
PINS = {
    "manifest": (BASE + "/fresh_preparation_v6c/reviewed_preparation_manifest.json", "e20775accd2ea02ac16d258ead2fb58e5ba1b6d26ff003ba10492dc6d442b6b9"),
    "evidence": (BASE + "/actual_c/preparation_evidence.json", "9f52a511c6b86f3009712f88515087cf20bd117534877e71ec5ebeae6b80dfb9"),
    "id_review": (BASE + "/actual_c/actual_id_review.json", "f2b926136e5503d9310ec88b0f881c82c8292a92dc4ffcb5e78c97cfac54946e"),
    "actual_review": (BASE + "/actual_c/independent_review.json", "2bec57b4fdb612dc3f75627071c0beaf3274670bc3a648d2e16a8231f70dc092"),
    "metadata": (BASE + "/actual_c/staged_metadata.json", "c44711bf215f395fca2483fade7af43ae4075e2823faed057110adbd76282704"),
    "postcheck": (BASE + "/actual_c/postcheck.json", "33c14d296ba35227d4ed3299f7a4f1731394b0c72332b1aaefaa7efc0aa7108e"),
    "correction": (BASE + "/active_network_correction/independent_review.json", "0484cdde9dec89b2a22f91aa4082cbe2782caa10318b5ad027363a6feac9bacc"),
    "prior_runtime": (PRIOR + "/accepted_policy_records/runtime_review.json", "47dbeebdbdbd3cd978156f9a25d8b07027f34023ab6b0ff541f2d05cfc1ca3e6"),
    "prior_scope": (PRIOR + "/accepted_policy_records/scope_review.json", "d32f3589c9156844f9a4211a3cec289c36c5260536e82c82be38f947d3ff4054"),
    "topical": (PRIOR + "/topical_approvals.json", "f4de03c65058769eb434e5931065deaeb5795087983a92a3b2f54dacd8feff45"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, expected):
    raw = (ROOT / path).read_bytes()
    if digest(raw) != expected:
        raise ValueError("v6c_packet_input_changed")
    return raw


def snapshot(row, bindings):
    configured, networks, evidence = network.project(row, bindings)
    return install.Snapshot(row["name"].removeprefix("/"), row["id"], row["image"], row["state"],
        row["started"], row["restarts"], row["restart_policy"], adapter.preservation_digest(row),
        adapter.preservation_digest({**row, "networks": {}}),
        tuple(sorted(n["NetworkID"] for n in row["networks"].values())), row.get("attempt") or "",
        configured, networks, evidence)


def derive():
    raw = {name: checked(*pin) for name, pin in PINS.items()}
    data = {name: json.loads(value) for name, value in raw.items()}
    plan = preparation._manifest(ROOT / PINS["manifest"][0], PINS["manifest"][1])
    prepared = staged.ReviewedPreparation.load(raw["evidence"], raw["id_review"], PINS["id_review"][1], plan)
    review, correction, prior, scope = (data[k] for k in ("actual_review", "correction", "prior_runtime", "prior_scope"))
    if any(r.get("decision") != "ACCEPTED_WITH_RISK" or r.get("blocking_findings", [])
           for r in (review, correction, prior, scope)):
        raise ValueError("v6c_packet_review_unaccepted")
    consumers = review["consumer_sha256"]
    for path, expected in consumers.items():
        checked(path, expected)
    if tuple(s["name"] for s in prior["subjects"]) != core.TARGETS:
        raise ValueError("v6c_packet_prior_subjects_changed")
    for subject in prior["subjects"]:
        child = json.loads(checked(PRIOR + "/accepted_policy_records/" + subject["name"] + ".json",
                                   prior["dependency_reviews"][subject["image_id"]]))
        if child["subjects"] != [subject]:
            raise ValueError("v6c_packet_prior_subjects_changed")
    rows, observed = data["metadata"]["rows"], data["postcheck"]
    if (len(rows) != 4 or len(observed["before"]) != 11 or observed["before"] != observed["after"]
            or rows != observed["before"][7:]):
        raise ValueError("v6c_packet_observation_changed")
    bindings = dict(plan.network_bindings)
    if tuple(snapshot(r, bindings) for r in observed["before"][:7]) != plan.baseline:
        raise ValueError("v6c_packet_originals_changed")
    witnesses = observed["source_files"]
    index = {(w["name"], w["path"]): w for w in witnesses}
    if len(witnesses) != 43 or len(index) != 43:
        raise ValueError("v6c_packet_witness_count")
    subjects, deltas = [], []
    for before, subject in zip(plan.baseline[:3], prior["subjects"][:3]):
        if (before.id, before.image, before.metadata) != (subject["container_id"], subject["image_id"], subject["preservation_sha256"]):
            raise ValueError("v6c_packet_storage_changed")
        subjects.append(deepcopy(subject))
    for app, actual, row, previous in zip(plan.applications, prepared.replacements, rows, prior["subjects"][3:]):
        if (snapshot(row, bindings) != actual or previous["name"] != app["name"]
                or previous["image_id"] != actual.image or row["command"] != app["command"]
                or app["network_options"][::2] != ["--alias"] * (len(app["network_options"]) // 2)):
            raise ValueError("v6c_packet_stage_changed")
        for source in app["sources"]:
            witness = index[(app["name"], source["destination"])]
            if ((witness["container_id"], witness["image"], witness["sha256"], witness["matches_frozen_source"])
                    != (actual.id, actual.image, source["sha256"], True)
                    or previous["sources"].get(source["destination"]) != source["sha256"]):
                raise ValueError("v6c_packet_source_changed")
            checked(source["local"], source["sha256"])
        candidate = network.final_subject({**previous, "container_id": actual.id}, row, bindings,
                                          app["network_options"][1::2])
        if candidate["preservation_sha256"] != app["replacement_configured_metadata"]:
            raise ValueError("v6c_packet_final_projection_changed")
        subjects.append(candidate)
        deltas.append({"name": app["name"], "prior_container_id": previous["container_id"],
            "container_id": actual.id, "image_changed": False, "sources_changed": False,
            "preservation_contract": network.CONTRACT, "final_configuration_evidence": "MODELLED"})
    topical = data["topical"]
    targets = tuple(adapter.TargetPin(s["name"], s["container_id"], s["image_id"], s["preservation_sha256"],
                                      tuple(sorted(s["sources"].items()))) for s in subjects)
    validator = adapter.PinnedRuntimeAdapter(None, adapter.ReviewedPins(targets, "0" * 64, (), tuple(topical), b"", ()))
    try:
        if not validator._source_coverage(validator._pins()) or not validator._topical_contract():
            raise ValueError("v6c_packet_structural_failure")
    finally:
        validator.close()
    artifacts, dependencies = {}, {}
    for subject in subjects:
        draft = {"schema": "companion-installed-policy-review-v1", "decision": "INCOMPLETE", "reviewer": "",
                 "image_id": subject["image_id"], "subjects": [subject],
                 "policies": dict.fromkeys(scope["policy_meanings"], "UNVERIFIED")}
        artifacts[subject["name"] + ".draft.json"] = draft
        dependencies[subject["image_id"]] = digest(install.canonical(draft))
    artifacts["runtime_review.draft.json"] = {"schema": "companion-runtime-pins-v2", "decision": "INCOMPLETE",
        "reviewer": "", "subjects": subjects, "dependency_reviews": dependencies,
        "topical_approvals_sha256": digest(install.canonical(topical)),
        "network_configuration": {"contract": network.CONTRACT, "bindings": bindings}}
    artifacts.update({"subjects.draft.json": subjects, "staged_metadata.derived.json": {"rows": rows},
        "topical_approvals.json": topical,
        "provenance.json": {"schema": "companion-v6c-runtime-packet-proposal-v1", "state": "READY_FOR_INDEPENDENT_REVIEW",
            "attempt": plan.attempt, "input_sha256": {p: h for p, h in PINS.values()}, "consumer_sha256": consumers,
            "prior_dependency_reviews": prior["dependency_reviews"], "subject_delta": deltas,
            "direct_application_source_witnesses": 43, "inherited_same_image_or_storage_pins": 89,
            "total_source_pins": sum(len(s["sources"]) for s in subjects),
            "source_provenance": "43 actual-v6c application witnesses; other 89 pins including four Uvicorn launchers inherited from prior exact-image/storage records, not recaptured",
            "preserved_policy_meanings": scope["policy_meanings"], "preserved_limits": scope["preserved_limits"],
            "final_configuration_evidence": "MODELLED", "runtime_state": "INCOMPLETE",
            "native_operations": False, "credential_access": False, "policy_approval_created": False,
            "cutover_authorized": False}})
    return artifacts


if __name__ == "__main__":
    artifacts = derive()
    output = HERE / "runtime_packet_v6c"
    output.mkdir(mode=0o700)
    for name, value in artifacts.items():
        with (output / name).open("xb") as stream:
            stream.write(install.canonical(value))
    print(json.dumps({"state": "READY_FOR_INDEPENDENT_REVIEW", "artifacts": len(artifacts), "source_pins": 132,
                      "native_operations": False, "policy_approval_created": False}))
