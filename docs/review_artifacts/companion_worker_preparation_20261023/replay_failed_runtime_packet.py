"""Offline post-attempt comparison and fingerprint replay; no native operations."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from scripts.research import companion_installer as install
from scripts.research import companion_network_configuration as network
from scripts.research import companion_runtime_adapter as adapter

HERE = Path(__file__).resolve().parent
PINS = {
    "manifest": ("refresh_inputs/reviewed_preparation_manifest.json", "67e29202a3bcd78f050f94b42bc87f91c7a50be90d3485ebd1fc0cfac0b7485e"),
    "before": ("actual_b/post_inventory.json", "7d4a164c4e2638492f04d83e4aa70287e9801bf298cda0c489c2a7e8037f01f5"),
    "post": ("runtime_attempt_v6b/post_inventory.json", "44602ff88a1d978fe5b6ae50d47becb71f6d135de32a526feda930a837cc4d40"),
    "stages": ("runtime_packet_v6b_launcher/staged_metadata.derived.json", "ca7101c34446f7b04cc0e1c08dcfcba2026e197d3cecbedb8de13e3cf70118e8"),
    "subjects": ("runtime_packet_v6b_launcher/subjects.draft.json", "0e6cfcc5bdf823659cf6d1f17aab0a961267d9d881e317b62dfa280141402107"),
    "receipt": ("runtime_attempt_v6b/receipt.jsonl", "63003bed13993c1d5d044ba16c271b4cd51d16209ebcb206dec16b4be2315d5a"),
}


def derive():
    raw = {}
    for key, (name, expected) in PINS.items():
        data = (HERE / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("runtime_replay_input_changed")
        raw[key] = data
    values = {k: json.loads(v) for k, v in raw.items() if k != "receipt"}
    events = [json.loads(line) for line in raw["receipt"].splitlines()]
    plan = install.Plan.load(raw["manifest"], PINS["manifest"][1])
    bindings = dict(plan.network_bindings)
    old, post = values["before"]["rows"], values["post"]["rows"]
    by_id = {r["id"]: r for r in post}
    comparison = []
    for prior in old[:11]:
        current = by_id[prior["id"]]
        comparison.append({
            "name": prior["name"], "id": prior["id"],
            "same_id_image_name": all(prior[k] == current[k] for k in ("id", "image", "name")),
            "running": current["state"] == "running",
            "configured_metadata_matches": network.project(prior, bindings)[0] == network.project(current, bindings)[0],
            "shared_fields_changed": sorted(k for k in set(prior) & set(current) if prior[k] != current[k]),
            "fields_not_recaptured": sorted(set(prior) - set(current)),
        })
    models = []
    for app, row, pin in zip(plan.applications, values["stages"]["rows"], values["subjects"][3:]):
        final = deepcopy(row)
        for attachment in final["networks"].values():
            attachment["Aliases"] = app["network_options"][1::2]
        bound = deepcopy(final)
        for name, attachment in bound["networks"].items():
            attachment["NetworkID"] = bindings[name]
        models.append({
            "name": app["name"], "accepted_pin": pin["preservation_sha256"],
            "saved_model_network_ids": [r["NetworkID"] for r in final["networks"].values()],
            "accepted_pin_matches_saved_raw_model": adapter.preservation_digest(final) == pin["preservation_sha256"],
            "known_network_binding_changes_preservation_digest": adapter.preservation_digest(final) != adapter.preservation_digest(bound),
            "bound_network_model_digest": adapter.preservation_digest(bound),
            "configured_projection_unchanged": network.project(final, bindings)[0] == network.project(bound, bindings)[0],
        })
    return {
        "schema": "companion-v6b-failed-runtime-offline-replay-v1",
        "state": "READY_FOR_INDEPENDENT_REVIEW",
        "inputs_sha256": {name: sha for name, sha in PINS.values()},
        "original_and_older_stage_comparisons": comparison,
        "all_originals_running_same_ids_images_names": all(r["running"] and r["same_id_image_name"] for r in comparison[:7]),
        "all_eleven_configured_projections_match": all(r["configured_metadata_matches"] for r in comparison),
        "old_four_stages_shared_fields_unchanged": all(not r["shared_fields_changed"] for r in comparison[7:]),
        "initial_postcheck_false_flags_explained": "Full-row equality compares unequal capture schemas (five extra historical fields were not recaptured). Raw preservation hashes also distinguish null and empty-object IPAMConfig on three reconnected originals. Compare only captured fields and the existing configured-network projection; do not overwrite the raw report or claim byte-exact restoration.",
        "quiesce_confirmed_targets": [r["target"] for r in events if r["phase"] == "quiesce_confirmed"],
        "replacement_start_intents": sum(r["phase"] == "replacement_start_intended" for r in events),
        "query_intents": sum(r["phase"] == "query_intended" for r in events),
        "last_runtime_operation": [r["installation_evidence"]["operation"] for r in events if r["phase"] == "runtime_operation_intended"][-1],
        "fingerprint_replay": models,
        "shown_defect": "Accepted final runtime pins reproduce raw staged metadata with blank network IDs. Substituting the already-reviewed immutable network binding changes all four preservation digests despite an unchanged configured-network projection. This is a packet-model/adapter representation mismatch.",
        "inference": "The modeled blank network identity is a concrete candidate explanation for configured_compatibility refusing after activation. The exact failing predicate/exception and activated replacement raw rows were not retained, so this replay is not an observed per-predicate failure trace.",
        "limits": ["No activated-replacement raw capture, no replacement startup or query, no post-rollback health or volume-content checks.",
                   "Known final IPAM/default alias representation must be tested before any corrected packet is proposed; this NetworkID-only replay is not a complete approved replacement fingerprint.",
                   "The four v6b replacements were removed and the attempt is consumed; old reviewed IDs/packets cannot be re-executed."],
        "native_operations": 0, "credential_access": False, "runtime_authorized": False,
    }


if __name__ == "__main__":
    result = derive()
    destination = HERE / "runtime_attempt_v6b/offline_replay.json"
    with destination.open("xb") as stream:
        stream.write(install.canonical(result))
    print(json.dumps({"state": result["state"],
        "all_originals_running_same_ids_images_names": result["all_originals_running_same_ids_images_names"],
        "all_eleven_configured_projections_match": result["all_eleven_configured_projections_match"],
        "old_four_stages_shared_fields_unchanged": result["old_four_stages_shared_fields_unchanged"],
        "replacement_start_intents": result["replacement_start_intents"], "query_intents": result["query_intents"],
        "network_model_mismatches": sum(r["known_network_binding_changes_preservation_digest"] for r in result["fingerprint_replay"]),
        "offline_replay_sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}))
