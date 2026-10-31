"""Pure fresh-baseline preparation proposal; no acceptance or native work."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path

from scripts.research import companion_installer as install
from scripts.research import companion_network_configuration as network
from scripts.research import companion_runtime_adapter as adapter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ATTEMPT = "workerprep20261023v6c"
PINS = {
    "manifest": ("refresh_inputs/reviewed_preparation_manifest.json", "67e29202a3bcd78f050f94b42bc87f91c7a50be90d3485ebd1fc0cfac0b7485e"),
    "observation": ("fresh_baseline_v6c_native/observation.json", "61ebef99a9053815450d1b2eab5e6f751b89c2a1f8d762f8210fe1b8ee8087b6"),
    "correction": ("active_network_correction/independent_review.json", "0484cdde9dec89b2a22f91aa4082cbe2782caa10318b5ad027363a6feac9bacc"),
    "consumers": ("runtime_packet_v6b_launcher/provenance.json", "6438a9aa91a1cdc5dafcd266a0f66e00cd1ce08a401a23d63e955c3ee56852f9"),
    "models": ("runtime_packet_v6b_launcher/staged_metadata.derived.json", "ca7101c34446f7b04cc0e1c08dcfcba2026e197d3cecbedb8de13e3cf70118e8"),
}


def checked(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("fresh_preparation_input_changed")
    return raw


def derive():
    values = {key: json.loads(checked(HERE / path, sha)) for key, (path, sha) in PINS.items()}
    previous, observed, review = (values[k] for k in ("manifest", "observation", "correction"))
    old = install.Plan.load(install.canonical(previous), hashlib.sha256(install.canonical(previous)).hexdigest())
    if review["decision"] != "ACCEPTED_WITH_RISK" or review["blocking_findings"]:
        raise ValueError("fresh_preparation_unaccepted_correction")
    consumers = dict(values["consumers"]["consumer_sha256"])
    for path, sha in review["source_and_artifact_sha256"].items():
        checked(ROOT / path, sha)
        if path in consumers:
            consumers[path] = sha
    for path, sha in consumers.items():
        checked(ROOT / path, sha)
    for part in ("companion_preparations", "companion_cutovers"):
        if os.path.lexists(ROOT / ".cbp_state/runtime" / part / ATTEMPT):
            raise ValueError("fresh_preparation_attempt_consumed")
    rows = observed.get("observations")
    if (observed.get("metadata_complete_for_selected_fields") is not True
            or observed.get("final_observations_match") is not True
            or type(rows) is not list or len(rows) != 7
            or rows != observed.get("final_observations")
            or observed.get("cli_sha256") != old.cli_sha256):
        raise ValueError("fresh_preparation_capture_incomplete")
    bindings = dict(old.network_bindings)
    baseline, deltas = [], []
    for before, row in zip(old.baseline, rows):
        configured, nets, evidence = network.project(row, bindings)
        foundation = adapter.preservation_digest({**row, "networks": {}})
        if (row["name"] != "/" + before.name or row["id"] != before.id or row["image"] != before.image
                or row["state"] != "running" or row["restart_policy"] != "no"
                or type(row["restarts"]) is not int or row["restarts"] != before.restarts
                or foundation != before.foundation or configured != before.configured_metadata):
            raise ValueError("fresh_preparation_original_drift")
        snapshot = install.Snapshot(before.name, row["id"], row["image"], row["state"], row["started"],
            row["restarts"], row["restart_policy"], adapter.preservation_digest(row), foundation,
            tuple(sorted(n["NetworkID"] for n in row["networks"].values())), "", configured, nets, evidence)
        baseline.append(asdict(snapshot))
        deltas.append({"name": before.name, "changed_fields": [key for key in asdict(before)
                        if install.canonical(asdict(before)[key]) != install.canonical(asdict(snapshot)[key])]})
    models = values["models"]["rows"]
    if len(models) != 4:
        raise ValueError("fresh_preparation_model_count")
    for app, model in zip(old.applications, models):
        if app["network_options"][::2] != ["--alias"] * (len(app["network_options"]) // 2):
            raise ValueError("fresh_preparation_options_changed")
        final = network.final_model(model, bindings, app["network_options"][1::2])
        if network.project(final, bindings)[0] != app["replacement_configured_metadata"]:
            raise ValueError("fresh_preparation_prediction_changed")
        for source in app["sources"]:
            checked(ROOT / source["local"], source["sha256"])
    candidate = deepcopy(previous)
    candidate.update(attempt=ATTEMPT, decision="INCOMPLETE", reviewer="", baseline=baseline)
    provenance = {"schema": "companion-fresh-preparation-proposal-v1", "state": "READY_FOR_INDEPENDENT_REVIEW",
        "input_sha256": {str((HERE / p).relative_to(ROOT)): h for p, h in PINS.values()},
        "consumer_sha256": consumers, "baseline_deltas": deltas,
        "observed_utc": observed["observed_utc"], "candidate_sha256": hashlib.sha256(install.canonical(candidate)).hexdigest(),
        "changed_manifest_fields": ["attempt", "decision", "reviewer", "baseline"],
        "applications_unchanged": candidate["applications"] == previous["applications"],
        "prediction_evidence": "MODELLED", "new_container_ids": None, "new_image_ids": None,
        "legacy_capture_status": observed["state"],
        "legacy_capture_limit": "Expected exited state is obsolete; fresh running baseline independently checked here",
        "native_operations_by_derivation": False, "preparation_authorized": False,
        "startup_authorized": False, "cutover_authorized": False}
    return candidate, provenance


if __name__ == "__main__":
    candidate, provenance = derive()
    output = HERE / "fresh_preparation_v6c"
    output.mkdir(mode=0o700)
    for name, value in (("candidate_manifest.json", candidate), ("provenance.json", provenance)):
        with (output / name).open("xb") as stream:
            stream.write(install.canonical(value))
    print(json.dumps({"state": "READY_FOR_INDEPENDENT_REVIEW", "attempt": ATTEMPT,
                      "candidate_sha256": provenance["candidate_sha256"], "native_operations": False}))
