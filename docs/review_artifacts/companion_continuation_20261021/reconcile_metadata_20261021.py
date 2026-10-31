"""Offline draft correction only; never approve, operate or rewrite old evidence."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from scripts.research import companion_installer as install
from scripts.research import companion_network_configuration as network
from scripts.research import companion_staged_update as staged

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
INPUTS = {
    "manifest": ("docs/review_artifacts/companion_continuation_20261020/reviewed_preparation_manifest.json",
                 "3b6f785ca1dd732e307aa83b30dcea2a5d2d9379d57af06a4afaa3774df94635"),
    "evidence": ("docs/review_artifacts/companion_continuation_20261021/prepared_evidence_public_copy.json",
                 "78726c0b834778934368713e55a7496a91249d17323e3d43c9052895a5e4d8de"),
    "diagnostic": ("docs/review_artifacts/companion_continuation_20261021/staged_metadata_diagnostic.json",
                   "03ffaa2dd4e4ee3c6d42383c41df4e04c3e797382416699134aa9661e3bf748e"),
}


def inputs():
    raw = {}
    for key, (path, expected) in INPUTS.items():
        raw[key] = (ROOT / path).read_bytes()
        if hashlib.sha256(raw[key]).hexdigest() != expected:
            raise ValueError("reconciliation_input_changed")
    return raw


def derive(raw):
    if (set(raw) != set(INPUTS)
            or any(hashlib.sha256(raw[key]).hexdigest() != pin for key, (_, pin) in INPUTS.items())):
        raise ValueError("reconciliation_input_changed")
    plan = install.Plan.load(raw["manifest"], INPUTS["manifest"][1])
    evidence = json.loads(raw["evidence"])
    saved = staged._rows(plan, evidence)
    diagnostic = json.loads(raw["diagnostic"])
    if (diagnostic["manifest_sha256"] != plan.manifest_sha256
            or diagnostic["evidence_sha256"] != INPUTS["evidence"][1]
            or len(diagnostic["rows"]) != len(saved)):
        raise ValueError("reconciliation_binding_changed")
    draft = json.loads(raw["manifest"])
    changes = []
    for app, actual, snapshot, proposed in zip(plan.applications, diagnostic["rows"], saved, draft["applications"]):
        if (actual["id"] != snapshot.id or actual["name"] != "/" + snapshot.name
                or actual["image"] != snapshot.image or actual["attempt"] != plan.attempt
                or actual["state"] != "created" or actual["started"] not in install.core.NEVER_STARTED
                or actual["restart_policy"] != "no" or actual["restarts"] != 0
                or network.project(actual, dict(plan.network_bindings))[0] != snapshot.configured_metadata
                or actual["dns"] is not None or actual["extra_hosts"] is not None
                or app["network_options"][::2] != ["--alias"] * (len(app["network_options"]) // 2)):
            raise ValueError("reconciliation_observation_changed")
        final_model = deepcopy(actual)
        for net in final_model["networks"].values():
            net["Aliases"] = app["network_options"][1::2]
        previous_model = deepcopy(final_model)
        previous_model["dns"] = previous_model["extra_hosts"] = []
        if network.project(previous_model, dict(plan.network_bindings))[0] != app["replacement_configured_metadata"]:
            raise ValueError("reconciliation_exceeds_confirmed_fields")
        corrected = network.project(final_model, dict(plan.network_bindings))[0]
        proposed["replacement_configured_metadata"] = corrected
        changes.append({"name": app["name"], "staged_id": snapshot.id,
                        "previous_prediction": app["replacement_configured_metadata"],
                        "corrected_prediction": corrected})
    draft.update(decision="INCOMPLETE", reviewer="")
    provenance = {"schema": "companion-metadata-reconciliation-v1",
                  "state": "READY_FOR_INDEPENDENT_REVIEW", "inputs": INPUTS,
                  "original_evidence": {"path": ".cbp_state/runtime/companion_preparations/f4e189b78ccc48acb8b92f20c4627f51/evidence.json",
                                        "sha256": INPUTS["evidence"][1], "public_copy_byte_identical": True},
                  "changes": changes, "native_operations": False,
                  "history_rewritten": False, "preparation_repeated": False,
                  "scope": "Correct final modeled DNS/ExtraHosts representation, preserve actual rows and all strict gates"}
    return draft, provenance


def main():
    draft, provenance = derive(inputs())
    raw = install.canonical(draft)
    provenance["draft_sha256"] = hashlib.sha256(raw).hexdigest()
    for name, content in (("metadata_corrected_draft_r2.json", raw),
                          ("metadata_reconciliation_proposal_r2.json", install.canonical(provenance))):
        with (HERE / name).open("xb") as stream:
            stream.write(content)
    print(json.dumps({"state": provenance["state"], "draft_sha256": provenance["draft_sha256"],
                      "corrected_predictions": len(provenance["changes"]), "actions_executed": False}))


if __name__ == "__main__":
    main()
