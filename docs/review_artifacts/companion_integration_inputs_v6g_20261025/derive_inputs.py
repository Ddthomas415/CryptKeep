"""Hash-bound current-input proposal; no approval, reservation or native calls."""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
import hashlib
import json
from pathlib import Path

from scripts.research import companion_installer as install
from scripts.research import companion_network_configuration as network
from scripts.research import companion_runtime_adapter as adapter
from . import refresh_sources as sources


HERE = Path(__file__).resolve().parent
SOURCE_REVIEW = "docs/review_artifacts/companion_integration_inputs_v6g_20261025/independent_review.json"
SOURCE_REVIEW_SHA = "0e284e50121f41a274694173d7dd4f5ef916cceb5e884714c504b5cb15665cc2"
MODELS = "docs/review_artifacts/companion_reconnection_plan_20261024/runtime_packet_v6e/staged_metadata.derived.json"
MODELS_SHA = "bee8dccb784344ae8627040b86d076ee26f0c9911312b0f34e8549a3bd8fc2cd"


def derive(observation_path, observation_sha):
    refresh = sources.refresh()
    review = json.loads(sources.checked(SOURCE_REVIEW, SOURCE_REVIEW_SHA))
    if review["decision"] != "ACCEPTED_WITH_RISK" or review["blocking_implementation_findings"]:
        raise ValueError("source_refresh_not_reviewed")
    for path in (str(HERE.relative_to(sources.ROOT) / "refresh_sources.py"),
                 str(HERE.relative_to(sources.ROOT) / "source_refresh.json")):
        sources.checked(path, review["hashes"][path])
    manifest = json.loads(sources.checked(*sources.PINS["manifest"]))
    old_bytes = install.canonical(manifest)
    old = install.Plan.load(old_bytes, hashlib.sha256(old_bytes).hexdigest())
    path = Path(observation_path)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != observation_sha:
        raise ValueError("observation_hash_mismatch")
    observed = json.loads(raw)
    pair = observed.get("observations")
    if (observed.get("state") != "READY_FOR_INDEPENDENT_REVIEW"
            or observed.get("native_inspections") != 2
            or type(pair) is not list or len(pair) != 2 or pair[0] != pair[1] or len(pair[0]) != 7
            or observed.get("selected_observations_equal") is not True
            or observed.get("metadata_complete_for_selected_fields") is not True
            or observed.get("cli_sha256") != old.cli_sha256
            or observed.get("source_refresh_sha256") != review["hashes"][str(HERE.relative_to(sources.ROOT) / "source_refresh.json")]):
        raise ValueError("baseline_incomplete")
    for number in (1, 2):
        payload = (path.parent / f"capture_{number}.jsonl").read_bytes()
        if (hashlib.sha256(payload).hexdigest() != observed["raw_sha256"][number - 1]
                or [json.loads(line) for line in payload.splitlines()] != pair[number - 1]):
            raise ValueError("raw_observation_mismatch")
    start, end = (datetime.fromisoformat(observed[k]) for k in ("observed_start_utc", "observed_end_utc"))
    if (start.tzinfo is None or end.tzinfo is None or not 0 <= (end - start).total_seconds() <= 30
            or type(observed["elapsed_seconds"]) not in (int, float)
            or not 0 <= observed["elapsed_seconds"] <= 30):
        raise ValueError("capture_budget_invalid")
    bindings, baseline, changes = dict(old.network_bindings), [], []
    for before, row in zip(old.baseline, pair[0]):
        configured, nets, evidence = network.project(row, bindings)
        foundation = adapter.preservation_digest({**row, "networks": {}})
        if (row["name"] != "/" + before.name or row["id"] != before.id or row["image"] != before.image
                or row["state"] != "running" or row["restart_policy"] != "no"
                or type(row["restarts"]) is not int or row["restarts"] != before.restarts
                or foundation != before.foundation or configured != before.configured_metadata):
            raise ValueError("original_drift")
        current = asdict(install.Snapshot(before.name, row["id"], row["image"], row["state"], row["started"],
            row["restarts"], row["restart_policy"], adapter.preservation_digest(row), foundation,
            tuple(sorted(n["NetworkID"] for n in row["networks"].values())), "", configured, nets, evidence))
        delta = [key for key, value in asdict(before).items()
                 if install.canonical(value) != install.canonical(current[key])]
        if (before.name in {"phase1-timescaledb", "phase1-qdrant", "phase1-minio"} and delta
                or set(delta) - {"started"}):
            raise ValueError("unreviewed_baseline_delta")
        baseline.append(current)
        changes.append({"name": before.name, "changed_fields": delta})
    models = json.loads(sources.checked(MODELS, MODELS_SHA))["rows"]
    if len(models) != 4 or len(refresh["applications"]) != 4:
        raise ValueError("model_count_invalid")
    for app, model in zip(refresh["applications"], models):
        if app["network_options"][::2] != ["--alias"] * (len(app["network_options"]) // 2):
            raise ValueError("network_options_changed")
        final = network.final_model(model, bindings, app["network_options"][1::2])
        if network.project(final, bindings)[0] != app["replacement_configured_metadata"]:
            raise ValueError("model_changed")
    candidate = deepcopy(manifest)
    candidate.update(attempt=sources.PROPOSED, decision="INCOMPLETE", reviewer="",
                     baseline=baseline, applications=refresh["applications"])
    return candidate, {
        "schema": "companion-current-inputs-v6g-v1", "state": "READY_FOR_INDEPENDENT_REVIEW",
        "baseline_deltas": changes, "source_deltas": refresh["source_deltas"],
        "consumer_sha256": refresh["consumer_sha256"],
        "runtime_consumer_sha256": refresh["runtime_consumer_sha256"],
        "input_sha256": {**refresh["input_sha256"], SOURCE_REVIEW: SOURCE_REVIEW_SHA,
            MODELS: MODELS_SHA, str(path.relative_to(sources.ROOT)): observation_sha,
            str(Path(__file__).relative_to(sources.ROOT)): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "candidate_sha256": hashlib.sha256(install.canonical(candidate)).hexdigest(),
        "new_container_ids": None, "new_image_ids": None,
        "preparation_authorized": False, "startup_authorized": False, "query_authorized": False,
        "limits": "Saved selected metadata only; sequential, not atomic. No health, connectivity, installed source or volume-byte proof. Historical model IDs are references, not adopted replacements.",
    }
