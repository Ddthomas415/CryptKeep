"""Prospective offline input refresh for the one-line template repair; no retry."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

from scripts.research import companion_installer as install

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ATTEMPT = "workerprep20261023v6b"
PINS = {
    "manifest": ("inputs/reviewed_preparation_manifest.json", "35032e02db1bf1d569d7918ef9127562abc205154d68908455c3ec5bf3201d42"),
    "review": ("inputs/preparation_plan_review.json", "a97d3f2226ac7ff3d99131e22afa5714c65b8430cd06d4745c80aa6975cd0cd6"),
    "receipt": ("actual/preparation_receipt.jsonl", "cdd014f97777e42b7251fc4d8f1b899a368764ff843602160da3906f3889c3d5"),
    "outcome": ("actual/operation_outcome.json", "150ccdde9fa78e9a340966e9f0ab1f7d7665544f48299c08cf6dba1b153f51f9"),
    "before": ("actual/before_inventory.json", "f494a090ed856dcded0f97d2d969f831de1d081e73724a0402fede15b20d67e3"),
    "after": ("actual/post_inventory.json", "2db7e158c5ba7e51e8102fae38d816aeef90158b94830694866cde5affbfc8f3"),
    "diagnosis": ("actual/readonly_diagnosis.json", "e8839d41019b3fdc7d8f0171ee9828f86bcfc3476324ff2e5bd0620ed612c01d"),
}
BACKEND = "scripts/research/companion_install_docker.py"
OLD_BACKEND = "470783aa8f126bb5c73b0dc8f7373a00069050ceb89ec08bc95cd66c15199f84"
NEW_BACKEND = "fbe5c0abe9be35cd0765d98b6d31b29f0e075cf7ece2e4d541283bce2755b28c"


def derive():
    values = {}
    for key, (path, expected) in PINS.items():
        raw = (HERE / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("template_refresh_input_changed")
        values[key] = [json.loads(line) for line in raw.splitlines()] if key == "receipt" else json.loads(raw)
    old, review = values["manifest"], values["review"]
    if (values["outcome"]["stdout"]["attempt_reserved"] is not True
            or values["outcome"]["stdout"]["cleanup_verified"] is not True
            or values["after"]["rows"] != values["before"]["rows"]
            or values["after"]["attempt_named_stages"]):
        raise ValueError("template_refresh_failure_evidence_invalid")
    raw = (ROOT / BACKEND).read_bytes()
    new, previous = b'not (index .Config "Entrypoint")', b'not .Config.Entrypoint'
    if (hashlib.sha256(raw).hexdigest() != NEW_BACKEND or raw.count(new) != 1
            or hashlib.sha256(raw.replace(new, previous)).hexdigest() != OLD_BACKEND):
        raise ValueError("template_refresh_exceeds_single_expression")
    consumers = dict(review["support_sha256"])
    if consumers[BACKEND] != OLD_BACKEND:
        raise ValueError("template_refresh_prior_binding_invalid")
    consumers[BACKEND] = NEW_BACKEND
    for path, expected in consumers.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError("template_refresh_other_consumer_changed")
    for app in old["applications"]:
        for source in app["sources"]:
            if hashlib.sha256((ROOT / source["local"]).read_bytes()).hexdigest() != source["sha256"]:
                raise ValueError("template_refresh_application_changed")
    for part in ("companion_preparations", "companion_cutovers"):
        if os.path.lexists(ROOT / ".cbp_state/runtime" / part / ATTEMPT):
            raise ValueError("template_refresh_attempt_occupied")
    candidate = deepcopy(old)
    candidate.update(attempt=ATTEMPT, decision="INCOMPLETE", reviewer="")
    provenance = {
        "schema": "companion-worker-template-refresh-proposal-v1", "state": "READY_FOR_INDEPENDENT_REVIEW",
        "previous_attempt": old["attempt"], "proposed_attempt": ATTEMPT,
        "inputs_sha256": {str((HERE / path).relative_to(ROOT)): digest for path, digest in PINS.values()},
        "consumer_sha256": consumers,
        "consumer_changes": [{"path": BACKEND, "before": OLD_BACKEND, "after": NEW_BACKEND}],
        "changed_manifest_fields": ["attempt", "decision", "reviewer"],
        "candidate_manifest_sha256": hashlib.sha256(install.canonical(candidate)).hexdigest(),
        "application_source_changes": [], "predicted_metadata_changes": [],
        "prediction_evidence_label": "MODELLED", "new_container_ids": None, "new_image_ids": None,
        "failed_attempt_preserved": True, "template_fix_and_inputs_require_independent_review": True,
        "native_operations": False, "preparation_authorized": False, "startup_authorized": False,
        "cutover_authorized": False,
    }
    return candidate, provenance


def main():
    candidate, provenance = derive()
    output = HERE / "refresh_inputs"
    output.mkdir(mode=0o700)
    for name, value in (("candidate_manifest.json", candidate), ("provenance.json", provenance)):
        with (output / name).open("xb") as stream:
            stream.write(install.canonical(value))
    print(json.dumps({"state": provenance["state"], "attempt": ATTEMPT,
                      "candidate_sha256": provenance["candidate_manifest_sha256"], "native_operations": False}))


if __name__ == "__main__":
    main()
