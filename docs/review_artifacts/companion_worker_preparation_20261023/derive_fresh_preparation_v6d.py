"""Fixed offline v6d proposal using the reviewed recipe; never prepares services."""
import hashlib
import json
from pathlib import Path
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ATTEMPT = "workerprep20261023v6d"
HELPER = "derive_fresh_preparation.py"
HELPER_SHA = "bb5854132df93d2e055a98358e581fc4a8ab7c16db2f98e7048e51a29d63544e"
PINS = {
    "manifest": ("fresh_preparation_v6c/reviewed_preparation_manifest.json", "e20775accd2ea02ac16d258ead2fb58e5ba1b6d26ff003ba10492dc6d442b6b9"),
    "observation": ("fresh_baseline_v6d_native/observation.json", "735f82278f43416a62adbc7a5d23b1f37decbb96bd557a1d34a50d8c9ebc8321"),
    "correction": ("nonrecipient_configuration_review_20261023.json", "ced40c1af138f586af0878182ab462ff6bbc5e7ab17870815f8783ad2a1bbb69"),
    "consumers": ("fresh_preparation_v6c/provenance.json", "b2d6496eff557543b3b7464bb0d0ebc044a502445a80c1d585f5e1c1e871ef1b"),
    "models": ("runtime_packet_v6c/staged_metadata.derived.json", "c44711bf215f395fca2483fade7af43ae4075e2823faed057110adbd76282704"),
}
LINEAGE = {
    "prior_review": ("fresh_preparation_v6c/independent_review.json", "6bcf752e347ecae8ebfa42f8863701195025a9bed0e7e2ffadae04e4d64584ad"),
    "failed_outcome": ("runtime_attempt_v6c/independent_review.json", "ef02af1091292fb1d1158951d2f5afff5a302e83645d643f052efe3a0582f134"),
    "current_predicate": ("corrected_recipient_observation_20261024T030934746449Z.json", "8c993731264bdc61f79a87b78b0d63aa4c38f9f858385e83e772be3ea2daae33"),
}


def checked(name, expected):
    raw = (HERE / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("v6d_input_changed")
    return raw


def recipe():
    raw = checked(HELPER, HELPER_SHA)
    module = types.ModuleType("reviewed_v6d_offline_recipe")
    module.__file__ = str(HERE / HELPER)
    exec(compile(raw, module.__file__, "exec"), module.__dict__)
    module.ATTEMPT, module.PINS = ATTEMPT, dict(PINS)
    return module


def derive():
    lineage = {key: json.loads(checked(name, sha)) for key, (name, sha) in LINEAGE.items()}
    prior = lineage["prior_review"]
    if (prior["decision"] != "ACCEPTED_WITH_RISK" or prior["blocking_findings"]
            or prior["accepted_derivative"]["sha256"] != PINS["manifest"][1]
            or lineage["failed_outcome"]["runtime_status"] != "INCOMPLETE"
            or lineage["failed_outcome"]["retry_authorized"] is not False
            or lineage["current_predicate"]["recipient_binding_passed"] is not True):
        raise ValueError("v6d_lineage_changed")
    worker = recipe()
    candidate, proof = worker.derive()
    if (candidate["attempt"] != ATTEMPT or candidate["decision"] != "INCOMPLETE"
            or candidate["reviewer"] != "" or len(proof["consumer_sha256"]) != 13
            or proof["new_container_ids"] is not None or proof["new_image_ids"] is not None):
        raise ValueError("v6d_proposal_contract_changed")
    proof["input_sha256"][str((HERE / HELPER).relative_to(ROOT))] = HELPER_SHA
    proof["input_sha256"].update({str((HERE / name).relative_to(ROOT)): sha
                                  for name, sha in LINEAGE.values()})
    proof.update(recipe_reuse="Exact reviewed recipe bytes, non-main import; only five fixed inputs and unused attempt changed",
                 historical_v6c_cause="UNVERIFIED", runtime_status="INCOMPLETE",
                 prior_prepared_ids="Historical model inputs only, not new identities or reusable stages",
                 policy_limit="Preparation inputs only; current recipient review does not grant runtime policy or operation",
                 authorization="No container creation, build, environment copy, startup, cutover, query or reservation")
    return candidate, proof


if __name__ == "__main__":
    candidate, proof = derive()
    output = HERE / "fresh_preparation_v6d"
    output.mkdir(mode=0o700)
    for name, value in (("candidate_manifest.json", candidate), ("provenance.json", proof)):
        with (output / name).open("xb") as stream:
            stream.write(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())
    print(json.dumps({"state": "READY_FOR_INDEPENDENT_REVIEW", "attempt": ATTEMPT,
                      "candidate_sha256": proof["candidate_sha256"], "native_operations": False}))
