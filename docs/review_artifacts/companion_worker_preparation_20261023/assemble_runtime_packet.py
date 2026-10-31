"""Offline v6b packet derivation; policy drafts grant no operational authority."""
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
OLD = "docs/review_artifacts/companion_continuation_20261021/runtime_packet"
BASE = str(HERE.relative_to(ROOT))
PINS = {
    "manifest": (BASE + "/refresh_inputs/reviewed_preparation_manifest.json", "67e29202a3bcd78f050f94b42bc87f91c7a50be90d3485ebd1fc0cfac0b7485e"),
    "preparation": (BASE + "/actual_b/preparation_evidence.json", "da7ee2de44a4e98990cceb6b4c53edc530fc717cc45c7c94d6b65994edfa35ef"),
    "id_review": (BASE + "/actual_b/actual_id_review.json", "c8fd96dd96b12576a82494d079022f6571ef52dd8bbdade7a154a70d826bce96"),
    "metadata": (BASE + "/actual_b/staged_metadata.json", "28256b005e8414a542f3f894cff1cc285b095d2b42cf9398980e8496f847d198"),
    "before": (BASE + "/actual_b/before_inventory.json", "ae05c9e33fe708c14d89afc9bfa9a56896c55e5e00a45c2338bac792b4889d5f"),
    "after": (BASE + "/actual_b/post_inventory.json", "7d4a164c4e2638492f04d83e4aa70287e9801bf298cda0c489c2a7e8037f01f5"),
    "sources": (BASE + "/actual_b/source_postcheck.json", "bd95a3481795597412d9214a574520812c350243e1aa0126b29232dc07f2e90f"),
    "consumers": (BASE + "/refresh_inputs/provenance.json", "c4bd70588ee5d695cd76fdec3f9380814edc2e833979f67418e60c5964a190ce"),
    "prior_runtime": (OLD + "/accepted_policy_records/runtime_review.json", "64127a85c985be4e09c0c6df24f5a688d5faae5a38077a3ccd20af7e82d7d43b"),
    "prior_scope": (OLD + "/accepted_policy_records/scope_review.json", "271c1c2c204f1493fd36caf0db57b5af464aba4c920526e2e77fd019ce24790d"),
    "topical": (OLD + "/topical_approvals.json", "f4de03c65058769eb434e5931065deaeb5795087983a92a3b2f54dacd8feff45"),
}
CUTOVER = "scripts/research/companion_cutover.py"
CUTOVER_SHA = "8740d65d31eade3d94cd849710aa2b1cf00a67ca560e385fd5a54ff4a20aaf4e"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, expected):
    raw = (ROOT / path).read_bytes()
    if digest(raw) != expected:
        raise ValueError("packet_input_changed: " + path)
    return raw


def derive():
    raw = {key: checked(*pin) for key, pin in PINS.items()}
    values = {key: json.loads(value) for key, value in raw.items()}
    plan = preparation._manifest(ROOT / PINS["manifest"][0], PINS["manifest"][1])
    prepared = staged.ReviewedPreparation.load(raw["preparation"], raw["id_review"], PINS["id_review"][1], plan)
    consumers = {p: h for p, h in values["consumers"]["consumer_sha256"].items()
                 if p.startswith("scripts/research/")}
    consumers[CUTOVER] = CUTOVER_SHA
    for path, expected in consumers.items():
        checked(path, expected)
    prior = values["prior_runtime"]
    if (prior["decision"] != "ACCEPTED_WITH_RISK"
            or values["prior_scope"]["decision"] != "ACCEPTED_WITH_RISK"
            or tuple(s["name"] for s in prior["subjects"]) != core.TARGETS):
        raise ValueError("prior_policy_scope_invalid")
    for subject in prior["subjects"]:
        child = checked(OLD + "/accepted_policy_records/" + subject["name"] + ".json",
                        prior["dependency_reviews"][subject["image_id"]])
        if json.loads(child)["subjects"] != [subject]:
            raise ValueError("prior_policy_subject_changed")
    before, after = values["before"]["rows"], values["after"]["rows"]
    if len(before) != 11 or len(after) != 15 or after[:11] != before:
        raise ValueError("saved_original_inventory_changed")
    witnessed = values["sources"]["source_files"]
    witnesses = {(w["name"], w["path"]): w for w in witnessed}
    if len(witnessed) != 43 or len(witnesses) != 43:
        raise ValueError("source_witness_count_invalid")
    metadata, subjects, deltas = [], [], []
    for baseline, previous in zip(plan.baseline[:3], prior["subjects"][:3]):
        row = next(r for r in before if r["id"] == baseline.id)
        if (previous["container_id"], previous["image_id"], previous["preservation_sha256"]) != (
                baseline.id, baseline.image, adapter.preservation_digest(row)):
            raise ValueError("storage_binding_changed")
        subjects.append(deepcopy(previous))
    for app, actual, saved, previous in zip(plan.applications, prepared.replacements,
                                          values["metadata"]["rows"], prior["subjects"][3:]):
        row = deepcopy(saved)
        if row not in after or previous["name"] != app["name"] or previous["image_id"] != actual.image:
            raise ValueError("image_lineage_changed")
        # The attempt label comes from accepted controller evidence, not raw inspect.
        row["attempt"] = actual.attempt
        configured, ids, evidence = network.project(row, dict(plan.network_bindings))
        snapshot = install.Snapshot(row["name"].removeprefix("/"), row["id"], row["image"],
            row["state"], row["started"], row["restarts"], row["restart_policy"],
            adapter.preservation_digest(row), adapter.preservation_digest({**row, "networks": {}}),
            tuple(sorted(n["NetworkID"] for n in row["networks"].values())), row["attempt"], configured, ids, evidence)
        if snapshot != actual:
            raise ValueError("staged_snapshot_changed")
        for source in app["sources"]:
            witness = witnesses[(app["name"], source["destination"])]
            if (witness["container_id"], witness["image"], witness["sha256"], witness["matches_frozen_source"]) != (
                    actual.id, actual.image, source["sha256"], True):
                raise ValueError("source_witness_changed")
            checked(source["local"], source["sha256"])
            if previous["sources"].get(source["destination"]) != source["sha256"]:
                raise ValueError("prior_application_source_changed")
        metadata.append(row)
        final = deepcopy(row)
        for attachment in final["networks"].values():
            attachment["Aliases"] = app["network_options"][1::2]
        if network.project(final, dict(plan.network_bindings))[0] != app["replacement_configured_metadata"]:
            raise ValueError("final_projection_changed")
        subject = dict(previous, container_id=actual.id, preservation_sha256=adapter.preservation_digest(final))
        subjects.append(subject)
        deltas.append({"name": app["name"], "previous_container_id": previous["container_id"],
            "container_id": actual.id, "source_changes": [], "image_changed": False,
            "final_configuration_evidence": "MODELLED", "command": row["command"]})
    topical = values["topical"]
    targets = tuple(adapter.TargetPin(s["name"], s["container_id"], s["image_id"],
        s["preservation_sha256"], tuple(sorted(s["sources"].items()))) for s in subjects)
    validator = adapter.PinnedRuntimeAdapter(None, adapter.ReviewedPins(targets, "0" * 64, (), tuple(topical), b"", ()))
    try:
        if not validator._source_coverage(validator._pins()) or not validator._topical_contract():
            raise ValueError("packet_structural_validation_failed")
    finally:
        validator.close()
    proposals = {}
    dependencies = {}
    for subject in subjects:
        proposal = {"schema": "companion-installed-policy-review-v1", "decision": "INCOMPLETE",
            "reviewer": "", "image_id": subject["image_id"], "subjects": [subject],
            "policies": {p: "UNVERIFIED" for p in values["prior_scope"]["policy_meanings"]}}
        proposals[subject["name"] + ".draft.json"] = proposal
        dependencies[subject["image_id"]] = digest(install.canonical(proposal))
    proposals["runtime_review.draft.json"] = {"schema": "companion-runtime-pins-v1", "decision": "INCOMPLETE",
        "reviewer": "", "subjects": subjects, "dependency_reviews": dependencies,
        "topical_approvals_sha256": digest(install.canonical(topical))}
    return {"staged_metadata.derived.json": {"rows": metadata}, "subjects.draft.json": subjects,
        "topical_approvals.json": topical, **proposals,
        "provenance.json": {"schema": "companion-v6b-runtime-packet-proposal-v1",
            "state": "READY_FOR_INDEPENDENT_REVIEW", "attempt": plan.attempt,
            "input_sha256": {p: h for p, h in PINS.values()}, "consumer_sha256": consumers,
            "prior_dependency_reviews": prior["dependency_reviews"], "subject_delta": deltas,
            "direct_application_source_witnesses": 43, "total_source_pins": sum(len(s["sources"]) for s in subjects),
            "source_provenance": "43 direct v6b source witnesses; other pins inherited from unchanged-image accepted records, not recaptured",
            "attempt_provenance": "accepted controller evidence, not independently captured raw label",
            "final_alias_projection": "MODELLED only; blank raw network IDs retained",
            "policy_review_required": "Assess applicability to new IDs and direct python -m uvicorn command; no policy approval is copied",
            "preserved_policy_meanings": values["prior_scope"]["policy_meanings"],
            "preserved_limits": values["prior_scope"]["preserved_limits"],
            "runtime_state": "INCOMPLETE", "policy_approval_created": False,
            "native_operations": False, "credential_access": False, "cutover_authorized": False}}


if __name__ == "__main__":
    artifacts = derive()
    output = HERE / "runtime_packet_v6b"
    output.mkdir()
    for name, value in artifacts.items():
        with (output / name).open("xb") as stream:
            stream.write(install.canonical(value))
    print(json.dumps({"state": "READY_FOR_INDEPENDENT_REVIEW", "artifacts": len(artifacts),
        "subjects": 7, "source_pins": 128, "native_operations": False, "policy_approval_created": False}))
