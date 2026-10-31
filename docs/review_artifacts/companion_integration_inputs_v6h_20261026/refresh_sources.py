"""Offline V6h source proposal, not a preparation manifest or operation grant."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PRIOR = "docs/review_artifacts/companion_integration_inputs_v6g_20261025"
REPAIR = "docs/review_artifacts/companion_verifier_diagnostics_20261026"
PROPOSED = "workerprep20261026v6h"
PINS = {
    "sources": (PRIOR + "/source_refresh.json", "3fd7e028d7bba8b9b012404f1eac0f91d3c7fa0016cc8d5cedffb604aa4882e1"),
    "manifest": (PRIOR + "/reviewed_preparation_manifest.json", "33e6633229e9399ec695be2f8e743930212b9ed926277235fd071e675fcf2e26"),
    "diagnostics_review": (REPAIR + "/independent_review_v2.json", "ca5664535df5109539a51747ebf10683d939e2adaa0d7ae147f991f9d350b35b"),
    "diagnostics_report": (REPAIR + "/report.json", "cd71d127bcc9a6cd2880017892524d348a735130a6cf4c894ec5a64efa37b317"),
    "failure_outcome": (PRIOR + "/actual_runtime_v6g/outcome.json", "b2c851460445678ccd97ca6ee2ab1794d935d134d4b943645ceef0615fbbbe4b"),
    "failure_receipt": (PRIOR + "/actual_runtime_v6g/receipt.jsonl", "eb2ebdd2013f73d6649885b8714281f91585cedab479d2e2bbc75942d25fdfbc"),
}
HISTORICAL_CHECKPOINT = "docs/checkpoints/companion_verifier_diagnostics_20261026.md"
CHANGED = frozenset("scripts/research/" + name + ".py" for name in (
    "companion_evidence_checks", "companion_installer", "companion_runtime_adapter"))


def checked(path, expected):
    raw = (ROOT / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("source_refresh_drift:" + path)
    return raw


def refresh():
    values = {key: json.loads(checked(path, sha)) for key, (path, sha) in PINS.items()
              if key != "failure_receipt"}
    checked(*PINS["failure_receipt"])
    review, report = values["diagnostics_review"], values["diagnostics_report"]
    if (review["decision"] != "ACCEPTED_WITH_RISK" or review["blocking_findings"]
            or review["runtime_execution_authorized"] is not False):
        raise ValueError("diagnostics_not_reviewed")
    for path, sha in review["hashes"].items():
        if path != HISTORICAL_CHECKPOINT:
            checked(path, sha)
    prior, manifest = values["sources"], values["manifest"]
    applications = deepcopy(manifest["applications"])
    sources = [s for app in applications for s in app["sources"]]
    preparation = deepcopy(prior["consumer_sha256"])
    runtime = deepcopy(prior["runtime_consumer_sha256"])
    if (len(sources) != 43 or len(preparation) != 13 or len(runtime) != 20
            or applications != prior["applications"]):
        raise ValueError("source_inventory_changed")
    deltas = []
    for path in sorted(CHANGED):
        before = report["pre_change_source_sha256"][path]
        after = review["hashes"][path]
        lanes = []
        for label, group in (("preparation", preparation), ("runtime", runtime)):
            if path in group:
                if group[path] != before or before == after:
                    raise ValueError("unexpected_source_delta")
                group[path] = after
                lanes.append(label)
        if not lanes:
            raise ValueError("source_not_in_consumers")
        deltas.append({"path": path, "before": before, "after": after, "lanes": lanes})
    for source in sources:
        checked(source["local"], source["sha256"])
    for group in (preparation, runtime):
        for path, sha in group.items():
            checked(path, sha)
    failure = values["failure_outcome"]
    if (failure["query_passed"] is not False or failure["preparation_consumed"] is not True
            or failure["prepared_ids_preserved"] is not False):
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
        "source_deltas": deltas,
        "input_sha256": {**{p: sha for p, sha in PINS.values()},
            str(Path(__file__).relative_to(ROOT)): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "historical_checkpoint_binding": {"path": HISTORICAL_CHECKPOINT,
            "pre_closeout_sha256": review["hashes"][HISTORICAL_CHECKPOINT],
            "current_equality_claimed": False},
        "baseline": None, "baseline_status": "MISSING_POST_V6G_ROLLBACK_PAIRED_CAPTURE",
        "new_container_ids": None, "new_image_ids": None,
        "expected_original_targets": [{"name": row["name"], "id": row["id"]} for row in manifest["baseline"]],
        "preparation_authorized": False, "startup_authorized": False,
        "cutover_authorized": False, "query_authorized": False,
        "scope": "Source-only proposal, not a Plan or approval. Original targets and image/source maps are historical constraints, not current observations. No current health, installed-file, namespace, recipient or SDK equivalence is inferred.",
    }


if __name__ == "__main__":
    print(json.dumps(refresh(), indent=2, sort_keys=True))
