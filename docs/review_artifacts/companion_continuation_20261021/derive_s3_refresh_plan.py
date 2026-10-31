"""Offline source-binding draft; cannot approve or execute preparation."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ATTEMPT = "s3refresh20261021c1eaae5a"
NEW_MAIN = "c1eaae5a5e1712ad926f556fdaf3195442a2b6e354059542748a429945a36228"
OLD_MAIN = "35fc51165e44dba1ab8d28e783285f51f392b01f814096f3950ce720995504a3"
PINS = {
    "preparation_reconciled_manifest.json": "b9594f55b7d409d5815ea318de68c0391943dcafe919326ebedb143821627b11",
    "installed_facts_capture/report.json": "7dbda2c14b68b58d372508eda0d34e232bc9e6548bd0b7ff5327b027abbdad2b",
    "companion_s3_single_attempt_review_20261021.json": "8668bc8bfcfa16eb559c60bc20550838ab308d89e6240ddd4f056f6794308252",
    "installed_facts_capture_result_review.json": "22f6acc80b6c5457549bb49549121df7620129578e154850ac6ce6a76dfba87a",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def derive():
    inputs = {}
    for name, expected in PINS.items():
        raw = (HERE / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("refresh_input_changed")
        inputs[name] = json.loads(raw)
    source = inputs["preparation_reconciled_manifest.json"]
    capture = inputs["installed_facts_capture/report.json"]
    review = inputs["companion_s3_single_attempt_review_20261021.json"]
    if (review["decision"] != "ACCEPTED_WITH_RISK"
            or review["reviewed_sha256"]["phase1_research_copilot/memory_retrieval/main.py"] != NEW_MAIN
            or capture["inventory_preserved"] is not True or capture["before"] != capture["after"]
            or capture["error"] is not None):
        raise ValueError("refresh_evidence_invalid")
    candidate = deepcopy(source)
    candidate.update(attempt=ATTEMPT, decision="INCOMPLETE", reviewer="")
    changes = []
    current = []
    for app in candidate["applications"]:
        for entry in app["sources"]:
            actual = hashlib.sha256((ROOT / entry["local"]).read_bytes()).hexdigest()
            if entry["local"] == "phase1_research_copilot/memory_retrieval/main.py":
                if app["name"] != "phase1-memory" or entry["sha256"] != OLD_MAIN or actual != NEW_MAIN:
                    raise ValueError("refresh_repair_binding_invalid")
                changes.append({"name": app["name"], "local": entry["local"],
                                "previous_sha256": entry["sha256"], "new_sha256": actual})
                entry["sha256"] = actual
            elif actual != entry["sha256"]:
                raise ValueError("unrelated_source_change")
            current.append({"name": app["name"], **entry})
    if len(current) != 43 or len(changes) != 1 or ATTEMPT == source["attempt"]:
        raise ValueError("refresh_scope_invalid")
    originals = {r["name"].removeprefix("/"): r for r in capture["after"]}
    for row in candidate["baseline"]:
        observed = originals[row["name"]]
        if (observed["id"] != row["id"] or observed["image"] != row["image"]
                or observed["state"] != row["state"]):
            raise ValueError("refresh_baseline_binding_invalid")
    consumed = ROOT / ".cbp_state/runtime/companion_preparations" / ATTEMPT
    if consumed.exists():
        raise ValueError("refresh_attempt_already_exists")
    provenance = {
        "schema": "companion-s3-source-refresh-proposal-v1", "state": "READY_FOR_INDEPENDENT_REVIEW",
        "inputs_sha256": PINS, "previous_attempt": source["attempt"], "proposed_attempt": ATTEMPT,
        "baseline_observed_utc": capture["recorded_utc"], "baseline_is_live_inventory": False,
        "source_entries": current, "source_changes": changes,
        "changed_manifest_fields": ["attempt", "decision", "reviewer", "applications[2].sources[2].sha256"],
        "unchanged_applications": [a["name"] for a in candidate["applications"] if a["name"] != "phase1-memory"],
        "preserve_old_prepared_subjects": [
            {k: r[k] for k in ("id", "name", "image", "state")}
            for r in capture["after"] if "-staged-" in r["name"]],
        "new_container_ids": None, "native_operations": False, "preparation_authorized": False,
        "startup_authorized": False, "cutover_authorized": False,
        "candidate_manifest_sha256": hashlib.sha256(canonical(candidate)).hexdigest(),
    }
    return candidate, provenance


def main():
    candidate, provenance = derive()
    output = HERE / "s3_source_refresh_plan"
    output.mkdir(mode=0o700)
    for name, value in (("candidate_manifest.json", candidate), ("provenance.json", provenance)):
        with (output / name).open("xb") as stream:
            stream.write(canonical(value))
    print(json.dumps({"state": provenance["state"], "candidate_sha256": provenance["candidate_manifest_sha256"],
                      "source_changes": len(provenance["source_changes"]), "native_operations": False}))


if __name__ == "__main__":
    main()
