"""Source-bound preparation proposal only; no native work or approval authority."""
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
ATTEMPT = "workerprep20261025v6f"
PRIOR = "docs/review_artifacts/companion_reconnection_plan_20261024"
REPAIR = "docs/review_artifacts/companion_archive_scope_repair_20261025"
PINS = {
    "manifest": (PRIOR + "/fresh_inputs/reviewed_preparation_manifest.json", "2075f3b98abc53be9e8336d425dd8d158aca4b1934a1b9da46c2ae9d3cd562d4"),
    "consumers": (PRIOR + "/fresh_inputs/provenance.json", "9407ddedf5b573286af1de56c7c867fe5a09d3e8bfa31bf6f4e14fc0a7f31fed"),
    "models": (PRIOR + "/runtime_packet_v6e/staged_metadata.derived.json", "bee8dccb784344ae8627040b86d076ee26f0c9911312b0f34e8549a3bd8fc2cd"),
    "repair": (REPAIR + "/report.json", "7ff14e8f8f46ee30aa17d526fe670c01bd952dd54155fdc517447d05207dfd6d"),
    "review": (REPAIR + "/independent_review.json", "4747ffdc6f86e549bdc703dd5ee017456ae221ad456b7b97d84828d11dbe5f35"),
}
CHANGED = frozenset({"phase1_research_copilot/memory_retrieval/article_view.py",
    "phase1_research_copilot/memory_retrieval/main.py", "scripts/research/companion_installer.py"})


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, expected):
    raw = Path(path).read_bytes()
    if digest(raw) != expected:
        raise ValueError("integration_input_changed:" + str(path))
    return raw


def source_inputs():
    values = {key: json.loads(checked(ROOT / p, sha)) for key, (p, sha) in PINS.items()}
    review, repair = values["review"], values["repair"]
    if (review["decision"] != "ACCEPTED_WITH_RISK" or review["blocking_findings"]
            or review["integrity"]["artifacts"][PINS["repair"][0]] != PINS["repair"][1]):
        raise ValueError("integration_repair_not_reviewed")
    for path, sha in repair["source_and_input_sha256"].items():
        checked(ROOT / path, sha)
    previous = values["manifest"]
    old = install.Plan.load(install.canonical(previous), digest(install.canonical(previous)))
    applications = deepcopy(previous["applications"])
    consumers = dict(values["consumers"]["consumer_sha256"])
    deltas = []
    def refresh(path, before):
        after = repair["source_and_input_sha256"].get(path) if path in CHANGED else before
        if path in CHANGED and repair["pre_change_source_sha256"].get(path) != before:
            raise ValueError("integration_prior_source_mismatch")
        checked(ROOT / path, after)
        if after != before:
            deltas.append({"path": path, "before": before, "after": after})
        return after
    for app in applications:
        for source in app["sources"]:
            source["sha256"] = refresh(source["local"], source["sha256"])
    for path, sha in list(consumers.items()):
        consumers[path] = refresh(path, sha)
    if (len(consumers) != 13 or sum(len(a["sources"]) for a in applications) != 43
            or {d["path"] for d in deltas} != CHANGED or len(deltas) != 3):
        raise ValueError("integration_source_delta_invalid")
    return values, old, applications, consumers, deltas


def derive(observation_path, observation_sha256):
    values, old, applications, consumers, deltas = source_inputs()
    for group in ("companion_preparations", "companion_cutovers"):
        if not os.path.lexists(ROOT / ".cbp_state/runtime" / group / "workerprep20261024v6e"):
            raise ValueError("integration_prior_consumption_missing")
        if os.path.lexists(ROOT / ".cbp_state/runtime" / group / ATTEMPT):
            raise ValueError("integration_attempt_consumed")
    observed = json.loads(checked(observation_path, observation_sha256))
    pair = observed.get("observations")
    if (type(pair) is not list or len(pair) != 2 or pair[0] != pair[1]
            or len(pair[0]) != 7 or observed.get("selected_observations_equal") is not True
            or observed.get("metadata_complete_for_selected_fields") is not True
            or observed.get("cli_sha256") != old.cli_sha256):
        raise ValueError("integration_baseline_incomplete")
    bindings, baseline, baseline_deltas = dict(old.network_bindings), [], []
    for before, row in zip(old.baseline, pair[0]):
        configured, nets, evidence = network.project(row, bindings)
        foundation = adapter.preservation_digest({**row, "networks": {}})
        if (row["name"] != "/" + before.name or row["id"] != before.id or row["image"] != before.image
                or row["state"] != "running" or row["restart_policy"] != "no"
                or type(row["restarts"]) is not int or row["restarts"] != before.restarts
                or foundation != before.foundation or configured != before.configured_metadata):
            raise ValueError("integration_original_drift")
        current = asdict(install.Snapshot(before.name, row["id"], row["image"], row["state"], row["started"],
            row["restarts"], row["restart_policy"], adapter.preservation_digest(row), foundation,
            tuple(sorted(n["NetworkID"] for n in row["networks"].values())), "", configured, nets, evidence))
        baseline.append(current)
        baseline_deltas.append({"name": before.name, "changed_fields": [k for k,v in asdict(before).items()
            if install.canonical(v) != install.canonical(current[k])]})
    models = values["models"]["rows"]
    if len(models) != 4:
        raise ValueError("integration_model_count")
    for app, model in zip(applications, models):
        if app["network_options"][::2] != ["--alias"] * (len(app["network_options"]) // 2):
            raise ValueError("integration_options_changed")
        final = network.final_model(model, bindings, app["network_options"][1::2])
        if network.project(final, bindings)[0] != app["replacement_configured_metadata"]:
            raise ValueError("integration_model_changed")
    candidate = deepcopy(values["manifest"])
    candidate.update(attempt=ATTEMPT, decision="INCOMPLETE", reviewer="", baseline=baseline, applications=applications)
    proof = {"schema": "companion-integration-inputs-v6f-v1", "state": "READY_FOR_INDEPENDENT_REVIEW",
        "input_sha256": {**{p: sha for p, sha in PINS.values()},
            str(Path(__file__).relative_to(ROOT)): digest(Path(__file__).read_bytes())}, "consumer_sha256": consumers,
        "source_deltas": deltas, "baseline_deltas": baseline_deltas,
        "observation": {"path": str(Path(observation_path).resolve()), "sha256": observation_sha256,
                        "observed_end_utc": observed["observed_end_utc"]},
        "candidate_sha256": digest(install.canonical(candidate)), "attempt": ATTEMPT,
        "new_container_ids": None, "new_image_ids": None, "prediction_evidence": "MODELLED",
        "native_operations_by_derivation": False, "preparation_authorized": False,
        "startup_authorized": False, "cutover_authorized": False,
        "limits": "Fresh source-bound proposal only. Historical models are not reusable IDs; no current installed-source, namespace, health, connectivity or cited-query proof."}
    return candidate, proof
