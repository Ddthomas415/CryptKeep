"""Offline v6 preparation-input derivation; never approve or operate services."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

from scripts.research import companion_installer as install
from scripts.research import companion_network_configuration as network
from scripts.research import companion_runtime_adapter as adapter
from scripts.research.companion_worker_shutdown import replacement_command

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OLD = "docs/review_artifacts/companion_continuation_20261021/"
ATTEMPT = "workerprep20261023v6a"
PINS = {
    "manifest": (OLD + "s3_source_refresh_plan/reviewed_preparation_manifest.json", "dd7b537aa39d2f5cbccebf41a20fadc7e2ae8e22ebe20063daf7417286dddb6d"),
    "models": (OLD + "runtime_packet/staged_metadata.derived.json", "98c186a31d78686bf7702eb46685c87a2d6487a680cad0e702a35244c7eed118"),
    "inventory": (OLD + "runtime_packet/continuation_post_attempt_inventory.json", "b80c453502c678ad3e558149fd4f6042e0a807259989623cb970dc4e9ac0d55b"),
    "implementation_review": (OLD + "runtime_packet/worker_shutdown_repair_review.json", "4386b6debb2e50fc2936d46ab9553ae92640bcba94c6aad19851c41ad5a7daab"),
    "capability_review": (OLD + "runtime_packet/worker_capabilities_review.json", "5fead98b283c16a936f0094f52a846b1e86f6f690e81c630dd1e4fbb6e0f1920"),
    "capabilities": (OLD + "runtime_packet/worker_capabilities_observation.json", "3d2e9f7556208861f2a419bdc2216dbf0acf6a09455da2a23e16d5bd21cf217a"),
}
PREPARATION_CONSUMERS = {
    "scripts/research/companion_prepare.py": "89b60b67a6204a83ad045edc91874b9e828c023fe0d094cda6d7c61c56e7bfd1",
    "scripts/research/companion_runtime_adapter.py": "e7315cd9047f656afca0b3845be54629c46c80c9a20065d8646978dce20fce38",
    "scripts/research/companion_network_configuration.py": "c3824743fb08098a35af6966ee9e3345a63e6500f18a5fdd84a02d1114bf39d7",
    "scripts/research/companion_staged_update.py": "f6a6878d8de760caaee757ed5ef570872c67efb74106fe2d6b0f8090ab697d18",
    "scripts/research/companion_install_env.py": "845bf702766525a3afa2397e76dcff4ff1c784b8ec549ace658b5c2f0001b38b",
    "scripts/research/companion_docker_transport.py": "817c378c289093a7f7c5395f3eb28291e5af1c3a7ae8b09eed2bde5868d2ecc5",
    "scripts/research/companion_existing_controller.py": "a3c67719299513cccd99a9303938b128362c29a9ed911b14e164d779403626a3",
}


def checked(path, expected):
    raw = (ROOT / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("worker_preparation_input_changed")
    return raw


def derive():
    data = {key: json.loads(checked(*pin)) for key, pin in PINS.items()}
    old = data["manifest"]
    install.Plan.load(install.canonical(old), hashlib.sha256(install.canonical(old)).hexdigest())
    for review_name, binding_key in (("implementation_review", "source_sha256"),
                                     ("capability_review", "reviewed_artifact_sha256")):
        review = data[review_name]
        if review["decision"] not in {"ACCEPTED", "ACCEPTED_WITH_RISK"}:
            raise ValueError("worker_preparation_review_unaccepted")
        for path, expected in review[binding_key].items():
            checked(path, expected)
    consumers = {**PREPARATION_CONSUMERS, **data["implementation_review"]["source_sha256"]}
    for path, expected in consumers.items():
        checked(path, expected)
    for part in ("companion_preparations", "companion_cutovers"):
        if os.path.lexists(ROOT / ".cbp_state/runtime" / part / ATTEMPT):
            raise ValueError("worker_preparation_attempt_already_used")
    observation = data["capabilities"]
    if (tuple(r["name"] for r in observation["results"]) != install.APPS
            or any(not r["exact_worker_validation_passed"] or r["signals_sent"]
                   for r in observation["results"])):
        raise ValueError("worker_preparation_capability_binding_invalid")
    bindings = old["network_contract"]["bindings"]
    saved = data["inventory"]["rows"]
    by_id = {row["id"]: row for row in saved}
    if len(by_id) != len(saved):
        raise ValueError("worker_preparation_duplicate_inventory")
    for before in old["baseline"]:
        raw = by_id[before["id"]]
        projected, nets, evidence = network.project(raw, bindings)
        restored = install.Snapshot(raw["name"].removeprefix("/"), raw["id"], raw["image"],
            raw["state"], raw["started"], raw["restarts"], raw["restart_policy"],
            adapter.preservation_digest(raw), adapter.preservation_digest({**raw, "networks": {}}),
            tuple(sorted(n["NetworkID"] for n in raw["networks"].values())), "", projected, nets, evidence)
        if restored != install.Snapshot.from_record(before):
            raise ValueError("worker_preparation_saved_baseline_mismatch")
    expected = [(r["id"], "/" + r["name"], r["image"], r["started"], r["restarts"])
                for r in old["baseline"]]
    observed = [(r["id"], r["name"], r["image"], r["started"], r["restarts"])
                for r in observation["originals"] if r["running"] is True]
    if observed != expected:
        raise ValueError("worker_preparation_current_selected_baseline_mismatch")
    candidate = deepcopy(old)
    candidate.update(schema="companion-worker-staged-update-v6", attempt=ATTEMPT,
                     decision="INCOMPLETE", reviewer="")
    predictions = []
    models = data["models"]["rows"]
    if len(models) != 4:
        raise ValueError("worker_preparation_saved_models_mismatch")
    sources = []
    for previous, app, saved_model in zip(old["applications"], candidate["applications"], models):
        if (saved_model["name"] != "/" + app["name"] + "-staged-" + old["attempt"]
                or saved_model["attempt"] != old["attempt"] or saved_model["state"] != "created"
                or app["network_options"][::2] != ["--alias"] * (len(app["network_options"]) // 2)):
            raise ValueError("worker_preparation_model_identity_mismatch")
        model = deepcopy(saved_model)
        for net in model["networks"].values():
            net["Aliases"] = app["network_options"][1::2]
        if network.project(model, bindings)[0] != previous["replacement_configured_metadata"]:
            raise ValueError("worker_preparation_old_prediction_mismatch")
        app["command"] = replacement_command(app["name"])
        model["command"] = app["command"]
        app["replacement_configured_metadata"] = network.project(model, bindings)[0]
        predictions.append({"name": app["name"], "historical_basis_id": saved_model["id"],
            "historical_basis_removed": True, "command": app["command"],
            "previous_prediction": previous["replacement_configured_metadata"],
            "predicted_final_metadata": app["replacement_configured_metadata"],
            "evidence_label": "MODELLED", "new_container_id": None, "new_image_id": None})
        for source in app["sources"]:
            checked(source["local"], source["sha256"])
            sources.append({"name": app["name"], **source})
    provenance = {
        "schema": "companion-worker-preparation-inputs-v1", "state": "READY_FOR_INDEPENDENT_REVIEW",
        "inputs_sha256": {path: digest for path, digest in PINS.values()},
        "consumer_sha256": consumers, "previous_attempt": old["attempt"], "proposed_attempt": ATTEMPT,
        "candidate_manifest_sha256": hashlib.sha256(install.canonical(candidate)).hexdigest(),
        "changed_manifest_fields": ["schema", "attempt", "decision", "reviewer"] +
            ["applications[%d].%s" % (i, field) for i in range(4)
             for field in ("command", "replacement_configured_metadata")],
        "source_entries": sources, "source_changes": [], "predictions": predictions,
        "full_baseline_saved_at_utc": data["inventory"]["observed_utc"],
        "selected_baseline_observed_at_utc": observation["observed_at_utc"],
        "baseline_is_live_inventory": False,
        "preserve_old_stages_as_of_saved_inventory": [
            {key: r[key] for key in ("id", "name", "image", "state")}
            for r in saved if "-staged-" in r["name"]],
        "new_container_ids": None, "new_image_ids": None, "native_operations": False,
        "preparation_authorized": False, "startup_authorized": False, "cutover_authorized": False,
    }
    return candidate, provenance


def main():
    candidate, provenance = derive()
    output = HERE / "inputs"
    output.mkdir(mode=0o700)
    for name, value in (("candidate_manifest.json", candidate), ("provenance.json", provenance)):
        with (output / name).open("xb") as stream:
            stream.write(install.canonical(value))
    print(json.dumps({"state": provenance["state"], "candidate_sha256": provenance["candidate_manifest_sha256"],
                      "source_entries": len(provenance["source_entries"]), "source_changes": 0,
                      "modeled_metadata_changes": len(provenance["predictions"]), "native_operations": False}))


if __name__ == "__main__":
    main()
