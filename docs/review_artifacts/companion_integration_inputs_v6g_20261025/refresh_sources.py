"""Offline source-only refresh. Never a preparation manifest or operation grant."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PRIOR = "docs/review_artifacts/companion_integration_inputs_v6f_20261025"
REPAIR = "docs/review_artifacts/companion_cited_precedent_repair_20261025"
GUARD = "dashboard/services/views/_shared_signals.py"
PROPOSED = "workerprep20261025v6g"
PINS = {
    "manifest": (PRIOR + "/reviewed_preparation_manifest.json", "a7854b1660ae2c321f8edb62d3ac2b7ab60350deb62df91bdde774e8c2ea1588"),
    "preparation_sources": (PRIOR + "/provenance.json", "b8c685aac89efc0661a2635e97855b997e8fc77cbd9ab2b029b667f4da3377a7"),
    "runtime_scope": (PRIOR + "/runtime_packet_v6f/accepted_policy_records/scope_review.json", "a165d3db68fe6dd139e44d5052049b162bbc7214d8df0d213974f2d4e2e58ef7"),
    "guard_review": (REPAIR + "/independent_review_v2.json", "bebb73297e47f784a1d43ff9ab1a2755cef6ad29348716145ea0bd4688259732"),
    "failure_outcome": (PRIOR + "/actual_runtime_v6f/outcome.json", "c074d27caa3a16f94fc6bf28a2875d8640ac30d6a6f5ae9dda1a7d85caf4e267"),
    "failure_receipt": (PRIOR + "/actual_runtime_v6f/receipt.jsonl", "9fdc6a9823d45777e591a25b108be4da7bfeadea296daeb50492481cb3acf555"),
}
HISTORICAL_CHECKPOINT = "docs/checkpoints/companion_cited_precedent_repair_20261025.md"


def checked(path, expected):
    raw = (ROOT / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("source_refresh_drift:" + path)
    return raw


def refresh():
    values = {key: json.loads(checked(path, sha)) for key, (path, sha) in PINS.items()
              if key != "failure_receipt"}
    checked(*PINS["failure_receipt"])
    review = values["guard_review"]
    if review["decision"] != "ACCEPTED_WITH_RISK" or review["blocking_findings"]:
        raise ValueError("guard_not_reviewed")
    # The accepted review binds pre-closeout checkpoint text. That historical
    # document is not a code/runtime input and was explicitly updated afterward.
    for path, sha in review["hashes"].items():
        if path != HISTORICAL_CHECKPOINT:
            checked(path, sha)
    manifest = values["manifest"]
    applications = deepcopy(manifest["applications"])
    sources = [s for app in applications for s in app["sources"]]
    tools = values["preparation_sources"]["consumer_sha256"]
    runtime = deepcopy(values["runtime_scope"]["consumer_sha256"])
    if len(sources) != 43 or len(tools) != 13 or len(runtime) != 20:
        raise ValueError("source_inventory_changed")
    for source in sources:
        checked(source["local"], source["sha256"])
    for path, sha in tools.items():
        checked(path, sha)
    before = runtime[GUARD]
    runtime[GUARD] = review["hashes"][GUARD]
    for path, sha in runtime.items():
        checked(path, sha)
    if before == runtime[GUARD]:
        raise ValueError("missing_guard_delta")
    failure = values["failure_outcome"]
    if (failure["query_passed"] is not False or failure["preparation_consumed"] is not True
            or failure["prepared_ids_preserved"] is not False):
        raise ValueError("unexpected_prior_outcome")
    for group in ("companion_preparations", "companion_cutovers"):
        base = ROOT / ".cbp_state/runtime" / group
        if not os.path.lexists(base / manifest["attempt"]):
            raise ValueError("prior_consumption_missing")
        if os.path.lexists(base / PROPOSED):
            raise ValueError("proposed_label_consumed")
    return {
        "schema": "companion-source-refresh-only-v1", "decision": "INCOMPLETE", "reviewer": "",
        "proposed_attempt": PROPOSED,
        "applications": applications, "consumer_sha256": tools,
        "runtime_consumer_sha256": runtime,
        "source_deltas": [{"path": GUARD, "before": before, "after": runtime[GUARD],
                           "lane": "host_runtime_consumer_only"}],
        "input_sha256": {**{p: sha for p, sha in PINS.values()},
                         str(Path(__file__).relative_to(ROOT)): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "historical_checkpoint_binding": {"path": HISTORICAL_CHECKPOINT,
            "pre_closeout_sha256": review["hashes"][HISTORICAL_CHECKPOINT],
            "current_equality_claimed": False},
        "baseline": None, "baseline_status": "MISSING_POST_V6F_ROLLBACK_PAIRED_CAPTURE",
        "new_container_ids": None, "new_image_ids": None,
        "expected_original_targets": [{"name": row["name"], "id": row["id"]} for row in manifest["baseline"]],
        "preparation_authorized": False, "startup_authorized": False,
        "cutover_authorized": False, "query_authorized": False,
        "scope": "Source-only refresh, not a Plan or an approval. Original targets are historical constraints, not current observations. No source, identity, model, installed-code or current health equivalence is inferred.",
    }


if __name__ == "__main__":
    print(json.dumps(refresh(), indent=2, sort_keys=True))
