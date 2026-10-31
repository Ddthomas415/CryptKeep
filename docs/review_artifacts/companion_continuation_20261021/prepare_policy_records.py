"""Prepare unapproved existing-schema records; never grant policy acceptance."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SUBJECTS_SHA = "b99ccc38ce8942bd2bdfd601f30d3d734d1a7c1fed3037870199151a6fc673bc"
EVIDENCE = (
    "s3_source_refresh_plan/actual_id_review.json",
    "installed_facts_capture_result_review.json",
    "companion_s3_single_attempt_review_20261021.json",
    "missing_runtime_sources_authorized/capture_review.json",
    "missing_runtime_sources_authorized/source_policy_assessment.json",
    "missing_runtime_sources_authorized/compatibility_review.json",
    "startup_profile/independent_review.json",
    "topical_witness_review.json",
)
CONSUMERS = ("companion_cutover", "companion_runtime_adapter", "companion_docker_transport",
    "companion_installer", "companion_staged_update", "companion_prepare", "companion_install_docker")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def derive():
    raw = (HERE / "runtime_packet/subjects.sources_v2.draft.json").read_bytes()
    if digest(raw) != SUBJECTS_SHA:
        raise ValueError("policy_subjects_changed")
    subjects = json.loads(raw)
    if len(subjects) != 7 or len({s["image_id"] for s in subjects}) != 7:
        raise ValueError("policy_subjects_invalid")
    evidence_hashes = {}
    for name in EVIDENCE:
        evidence_raw = (HERE / name).read_bytes()
        if json.loads(evidence_raw).get("decision") != "ACCEPTED_WITH_RISK":
            raise ValueError("supporting_review_not_accepted")
        evidence_hashes[name] = digest(evidence_raw)
    topical = json.loads((HERE / "runtime_packet/topical_approvals.json").read_bytes())
    scope = {
        "state": "READY_FOR_INDEPENDENT_REVIEW", "author_role": "ENGINEER",
        "classification": "CLAIMED proposed policy mapping; not seven-image acceptance",
        "profile": "single-cited-query-v1; existing running-storage application cutover",
        "subjects_sha256": SUBJECTS_SHA, "supporting_reviews_sha256": evidence_hashes,
        "consumer_sources_sha256": {"scripts/research/" + name + ".py":
            digest((ROOT / "scripts/research" / (name + ".py")).read_bytes()) for name in CONSUMERS},
        "policy_meanings": {
            "zero_retries": "Original fixed-loopback HTTP transport and restricted application-call controls, not one physical socket or DNS/address result. Existing separate planned health/read operations are not retries of each other.",
            "no_proxy_redirect": "Reviewed fixed-recipient HTTP clients in the restricted profile, not every unrestricted image operation or daemon behavior.",
            "entrypoint_side_effects": "Characterized permitted startup effects, not effect-free startup. Only four applications start; three existing storage daemons remain running."},
        "subject_mapping": {
            "phase1-timescaledb": "No daemon startup. Existing owned local-socket readiness/schema checks; read-only SQL. PG_VERSION16 and existing namespaces already evidenced. No HTTP client is invoked inside this subject by these planned checks.",
            "phase1-qdrant": "No daemon startup. Existing fixed-loopback controller health/collection reads use reviewed HTTP transport. No whole-daemon implementation or background-effect assertion.",
            "phase1-minio": "No daemon startup. Fixed-loopback readiness plus reviewed owned curl/bashing HeadBucket path, explicit no-proxy/no-redirect/no-retry flags. Credentials remain in owning container under separately authorized runtime checks.",
            "phase1-audit-log": "Source-reviewed single-worker default startup, config/stdout logging and lazy Database construction; planned health SELECT and authenticated audit inserts. SQL connection address fallback is not SQL resubmission.",
            "phase1-risk-stub": "Source-reviewed single-worker startup. Strict-profile audit HTTP is fresh-client retries0/trust_envFalse/follow_redirectsFalse; risk routes remain no-trading.",
            "phase1-memory": "Source-reviewed single-worker read-only startup refuses missing stores. Reviewed restricted Qdrant/S3 controls and accepted per-client S3 retry-event suppression. Planned storage reads, retrieval and audit effects remain disclosed.",
            "phase1-orchestrator": "Source-reviewed single-worker startup and repository import path. Strict probe uses fixed tool recipients, no HTTP retry/proxy/redirect, lazy model wrapper not called, deterministic archived evidence and planned audit insert."},
        "limits": [
            "Source-reviewed/configured evidence is not observed SDK initialization, actual startup or a successful citation.",
            "HTTPcore pool reassignment and Psycopg multiple address attempts remain disclosed; no duplicate business execution was observed or certified absent at all layers.",
            "Storage scope is planned client operations against already-running subjects, not daemon-wide no-retry or effect-free behavior.",
            "The future fresh identity/configuration/source/namespace/recipient checks are not waived.",
            "No general model-backed explanation, current-market causation, profitability or trading readiness is accepted."],
        "runtime_authorized": False, "native_operations": False,
    }
    records, dependencies = {}, {}
    for subject in subjects:
        name = subject["name"] + ".draft.json"
        record = {"schema": "companion-installed-policy-review-v1", "decision": "INCOMPLETE",
            "reviewer": "", "image_id": subject["image_id"], "subjects": [subject],
            "policies": {key: "UNVERIFIED" for key in scope["policy_meanings"]}}
        records[name] = record
        dependencies[subject["image_id"]] = digest(canonical(record))
    records["runtime_review.draft.json"] = {"schema": "companion-runtime-pins-v1",
        "decision": "INCOMPLETE", "reviewer": "", "subjects": subjects,
        "dependency_reviews": dependencies, "topical_approvals_sha256": digest(canonical(topical))}
    records["scope.proposed.json"] = scope
    return records


if __name__ == "__main__":
    records = derive()
    output = HERE / "runtime_packet/policy_record_proposals"
    output.mkdir()
    for name, record in records.items():
        with (output / name).open("xb") as stream:
            stream.write(canonical(record))
    print(json.dumps({"state": "READY_FOR_INDEPENDENT_REVIEW", "draft_records": 8,
        "policy_approvals": 0, "native_operations": False}))
