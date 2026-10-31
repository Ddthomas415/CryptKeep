"""Add four reviewed launcher pins offline; preserve prior artifacts and authority."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from scripts.research import companion_installer as install
from scripts.research import companion_runtime_adapter as adapter
from scripts.research.companion_docker_transport import _path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = "/usr/local/lib/python3.11/site-packages/uvicorn/__main__.py"
SOURCE_SHA = "0d08b3cba9ca3f4cb084fa6708782644360831f72a64a544ccd2164198eab554"
TRANSPORT = "scripts/research/companion_docker_transport.py"
OLD_TRANSPORT = "817c378c289093a7f7c5395f3eb28291e5af1c3a7ae8b09eed2bde5868d2ecc5"
NEW_TRANSPORT = "5cbdf417a6b180bdd6e77cf7c9b85eba6649ebd15212f0836725f13301edcd81"
PINS = {
    "draft_review": ("runtime_packet_v6b/independent_review.json", "b8e72a553264b02357b6ccd569b82551fd016b0c4d3e1c151259bfe3be78e33a"),
    "capture": ("launcher_capture/report.json", "5e1f397376c0e2f4ff1617b5881accb70baf5202ef35bfe2b7bfdf2e58d36d32"),
    "capture_review": ("launcher_capture/independent_review.json", "03a3e5fc9687cb190bc0a099fa984d050a8578fec6a82d1ee790b5371effaab1"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, expected):
    raw = path.read_bytes()
    if digest(raw) != expected:
        raise ValueError("launcher_packet_input_changed: " + str(path.relative_to(ROOT)))
    return raw


def validate_subjects(subjects, previous):
    if len(subjects) != 7 or subjects[:3] != previous[:3]:
        raise ValueError("launcher_packet_subjects_changed")
    for old, new in zip(previous[3:], subjects[3:]):
        expected = deepcopy(old)
        expected["sources"][SOURCE] = SOURCE_SHA
        if new != expected or SOURCE in old["sources"]:
            raise ValueError("launcher_pin_missing_or_changed")
        _path(SOURCE)
    if sum(len(s["sources"]) for s in subjects) != 132:
        raise ValueError("launcher_packet_pin_count_changed")


def derive():
    values = {key: json.loads(checked(HERE / path, sha)) for key, (path, sha) in PINS.items()}
    review, capture, accepted = (values[k] for k in ("draft_review", "capture", "capture_review"))
    if (review["derivation_decision"] != "ACCEPTED"
            or accepted["capture_evidence_decision"] != "ACCEPTED_WITH_RISK"
            or accepted["R1_source_and_static_bridge_decision"] != "ACCEPTED_WITH_RISK"
            or not accepted["R1_resolution"]["narrow_R1_source_evidence_gap_closed"]):
        raise ValueError("launcher_support_review_not_accepted")
    artifacts = {Path(p).name: json.loads(checked(ROOT / p, sha))
                 for p, sha in review["hashes"]["draft_outputs"].items()}
    previous = artifacts["subjects.draft.json"]
    prior_proof = artifacts["provenance.json"]
    consumers = dict(prior_proof["consumer_sha256"])
    if consumers[TRANSPORT] != OLD_TRANSPORT:
        raise ValueError("launcher_prior_consumer_changed")
    raw = checked(ROOT / TRANSPORT, NEW_TRANSPORT)
    addition = ('                    "' + SOURCE + '",\n').encode()
    if raw.count(addition) != 1 or digest(raw.replace(addition, b"")) != OLD_TRANSPORT:
        raise ValueError("launcher_transport_delta_exceeds_one_path")
    consumers[TRANSPORT] = NEW_TRANSPORT
    for path, sha in consumers.items():
        checked(ROOT / path, sha)
    if (capture["before"] != capture["after"] or capture["source_path"] != SOURCE
            or capture["commands_completed"] != 6 or len(capture["files"]) != 4):
        raise ValueError("launcher_capture_changed")
    witnesses = {item["name"]: item for item in capture["files"]}
    if len(witnesses) != 4 or set(witnesses) != {s["name"] for s in previous[3:]}:
        raise ValueError("launcher_witness_subjects_changed")
    subjects = deepcopy(previous)
    for subject in subjects[3:]:
        witness = witnesses[subject["name"]]
        if ((witness["container_id"], witness["image_id"], witness["path"], witness["sha256"], witness["size_bytes"])
                != (subject["container_id"], subject["image_id"], SOURCE, SOURCE_SHA, 62)
                or witness["saved_file"] != subject["name"] + ".__main__.py.source.txt"):
            raise ValueError("launcher_witness_binding_changed")
        checked(HERE / "launcher_capture" / witness["saved_file"], SOURCE_SHA)
        subject["sources"][SOURCE] = SOURCE_SHA
    validate_subjects(subjects, previous)
    targets = tuple(adapter.TargetPin(s["name"], s["container_id"], s["image_id"],
        s["preservation_sha256"], tuple(sorted(s["sources"].items()))) for s in subjects)
    validator = adapter.PinnedRuntimeAdapter(None, adapter.ReviewedPins(targets, "0" * 64,
        (), tuple(artifacts["topical_approvals.json"]), b"", ()))
    try:
        if not validator._source_coverage(validator._pins()) or not validator._topical_contract():
            raise ValueError("launcher_packet_structure_failed")
    finally:
        validator.close()
    out = {k: deepcopy(artifacts[k]) for k in ("staged_metadata.derived.json", "topical_approvals.json")}
    out["subjects.draft.json"] = subjects
    dependencies = {}
    for subject in subjects:
        record = deepcopy(artifacts[subject["name"] + ".draft.json"])
        if record["decision"] != "INCOMPLETE" or record["reviewer"]:
            raise ValueError("launcher_proposal_not_unapproved")
        record["subjects"] = [subject]
        out[subject["name"] + ".draft.json"] = record
        dependencies[subject["image_id"]] = digest(install.canonical(record))
    runtime = deepcopy(artifacts["runtime_review.draft.json"])
    runtime.update(subjects=subjects, dependency_reviews=dependencies)
    out["runtime_review.draft.json"] = runtime
    out["provenance.json"] = {
        "schema": "companion-v6b-launcher-pin-proposal-v1", "state": "READY_FOR_INDEPENDENT_REVIEW",
        "inputs_sha256": {str((HERE / p).relative_to(ROOT)): h for p, h in PINS.values()},
        "prior_outputs_sha256": review["hashes"]["draft_outputs"], "consumer_sha256": consumers,
        "consumer_changes": [{"path": TRANSPORT, "before": OLD_TRANSPORT, "after": NEW_TRANSPORT}],
        "source_additions": [{"name": s["name"], "container_id": s["container_id"], "image_id": s["image_id"],
            "path": SOURCE, "sha256": SOURCE_SHA} for s in subjects[3:]],
        "total_source_pins": 132, "previous_source_pins": 128, "source_removals": [],
        "inherited_provenance": prior_proof, "final_configuration_evidence": "MODELLED",
        "policy_approval_created": False, "native_operations": False, "credential_access": False,
        "runtime_state": "INCOMPLETE", "cutover_authorized": False}
    return out


if __name__ == "__main__":
    artifacts = derive()
    output = HERE / "runtime_packet_v6b_launcher"
    output.mkdir()
    for name, value in artifacts.items():
        with (output / name).open("xb") as stream:
            stream.write(install.canonical(value))
    print(json.dumps({"state": "READY_FOR_INDEPENDENT_REVIEW", "artifacts": len(artifacts),
        "source_pins": 132, "native_operations": False, "policy_approval_created": False}))
