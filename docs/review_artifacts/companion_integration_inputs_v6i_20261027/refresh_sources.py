"""Offline V6i source proposal; never an installed-image or operation approval."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PRIOR = "docs/review_artifacts/companion_integration_inputs_v6h_20261026"
REPAIR = "docs/review_artifacts/companion_archival_market_exclusion_20261026"
PROPOSED = "workerprep20261027v6i"
MEMORY = "phase1_research_copilot/memory_retrieval/main.py"
VERIFIER = "scripts/research/companion_evidence_checks.py"
CHANGED = frozenset({MEMORY, VERIFIER})
HISTORICAL_CHECKPOINT = "docs/checkpoints/companion_archival_market_exclusion_20261026.md"
PINS = {
    "manifest": (PRIOR + "/reviewed_preparation_manifest.json", "d11fccb5e4f7c46e7d726704c9b75c400a1482eab5d1b840027d876a5837f047"),
    "sources": (PRIOR + "/provenance.json", "e60cbfad2f7af46acdf47c018cb345621fa9304a4cf97a6b12fcce5bf36a0ef0"),
    "repair_review": (REPAIR + "/independent_review.json", "167cfa9ca11965368faa054e1a3ad050bd41b05049f6ea202a4da2cde12c763d"),
    "repair_report": (REPAIR + "/report.json", "71868bd2fa6632448eb1eb930f12b5afde1c6cfa3e68ef27e0912369d1a845eb"),
    "failure_outcome": (PRIOR + "/actual_runtime_v6h/outcome.json", "22b048282b1e974358251ec1486b8c496b1fdc146677eef5ddc28f56f8d19243"),
    "failure_receipt": (PRIOR + "/actual_runtime_v6h/receipt.jsonl", "ab587bb2fa1a56818b2c70f45cafc29b543e4ae3efba83c006ac696021d91b4a"),
    "failure_review": (PRIOR + "/actual_runtime_v6h/independent_review.json", "a79199bed7c7fbd3212313d98055e4154d2faf73c424ca3dc9d291df9e649df9"),
}


def checked(path, expected):
    raw = (ROOT / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("source_refresh_drift:" + path)
    return raw


def refresh():
    values = {key: json.loads(checked(path, sha)) for key, (path, sha) in PINS.items()
              if key != "failure_receipt"}
    checked(*PINS["failure_receipt"])
    review, report = values["repair_review"], values["repair_report"]
    if (review["decision"] != "ACCEPTED_WITH_RISK" or review["blocking_findings"]
            or review["operations_authorized"] is not False
            or set(report["production_paths"]) != CHANGED):
        raise ValueError("repair_not_reviewed")
    for path, sha in review["hashes"].items():
        if path != HISTORICAL_CHECKPOINT:
            checked(path, sha)
    manifest, prior = values["manifest"], values["sources"]
    applications = deepcopy(manifest["applications"])
    preparation = deepcopy(prior["consumer_sha256"])
    runtime = deepcopy(prior["runtime_consumer_sha256"])
    if (sum(len(a["sources"]) for a in applications) != 43
            or len(preparation) != 13 or len(runtime) != 20
            or VERIFIER in preparation or MEMORY in runtime or MEMORY in preparation):
        raise ValueError("source_inventory_changed")
    changes = []
    for app in applications:
        for source in app["sources"]:
            if source["local"] == MEMORY:
                before, after = source["sha256"], review["hashes"][MEMORY]
                if (app["name"] != "phase1-memory" or before != report["before_sha256"][MEMORY]
                        or before == after):
                    raise ValueError("unexpected_application_delta")
                source["sha256"] = after
                changes.append({"path": MEMORY, "before": before, "after": after,
                    "lanes": ["application"], "application": app["name"], "destination": source["destination"]})
    if len(changes) != 1 or runtime[VERIFIER] != report["before_sha256"][VERIFIER]:
        raise ValueError("unexpected_source_delta")
    before, after = runtime[VERIFIER], review["hashes"][VERIFIER]
    if before == after:
        raise ValueError("missing_verifier_delta")
    runtime[VERIFIER] = after
    changes.append({"path": VERIFIER, "before": before, "after": after, "lanes": ["runtime"]})
    for app in applications:
        for source in app["sources"]:
            checked(source["local"], source["sha256"])
    for group in (preparation, runtime):
        for path, sha in group.items():
            checked(path, sha)
    failure, failure_review = values["failure_outcome"], values["failure_review"]
    if (failure["query_passed"] is not False or failure["preparation_consumed"] is not True
            or failure["prepared_ids_preserved"] is not False
            or failure_review["decision"] != "ACCEPTED_WITH_RISK" or failure_review["blocking_findings"]):
        raise ValueError("unexpected_prior_outcome")
    for lane in ("companion_preparations", "companion_cutovers"):
        base = ROOT / ".cbp_state/runtime" / lane
        if not os.path.lexists(base / manifest["attempt"]):
            raise ValueError("prior_consumption_missing")
        if os.path.lexists(base / PROPOSED):
            raise ValueError("proposed_label_consumed")
    return {
        "schema": "companion-source-refresh-only-v1", "decision": "INCOMPLETE", "reviewer": "",
        "proposed_attempt": PROPOSED, "applications": applications,
        "consumer_sha256": preparation, "runtime_consumer_sha256": runtime,
        "source_deltas": changes,
        "input_sha256": {**{p: sha for p, sha in PINS.values()},
            str(Path(__file__).relative_to(ROOT)): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "historical_checkpoint_binding": {"path": HISTORICAL_CHECKPOINT,
            "pre_closeout_sha256": review["hashes"][HISTORICAL_CHECKPOINT], "current_equality_claimed": False},
        "baseline": None, "baseline_status": "MISSING_POST_V6H_ROLLBACK_PAIRED_CAPTURE",
        "new_container_ids": None, "new_image_ids": None,
        "expected_original_targets": [{"name": row["name"], "id": row["id"]} for row in manifest["baseline"]],
        "changed_memory_image_policy": "UNVERIFIED: new source overlay requires actual image/parent/layer/source evidence and independent applicability review; prior SDK acceptance is not automatically transferred.",
        "preparation_authorized": False, "startup_authorized": False,
        "cutover_authorized": False, "query_authorized": False,
        "scope": "Source-only proposal, not a Plan or approval. Original IDs and recipes are historical constraints, not current observations. No current health, new image identity, installed-source, namespace, recipient or SDK equivalence inferred.",
    }


if __name__ == "__main__":
    print(json.dumps(refresh(), indent=2, sort_keys=True))
