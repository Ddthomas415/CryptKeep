"""Fixed V6g handoff; default inert, execution needs separate operator approval."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import tempfile
import time
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD_HELPER = ROOT / "docs/review_artifacts/companion_continuation_20261021/execute_reviewed_cutover.py"
HELPER_SHA = "5c319350681e2fb4fdac363e29b829947e0348678fdcc8ecabc84820713adf12"
PACKET = HERE / "runtime_packet_v6g"
RECEIPT_SHA = "f93389b2f86f495af748e839112d5935e7bfd6e8d1f91a1eeb0243a1f7873f9d"
REVIEW_SHA = "5d729d529c7c39d339e01d50d76f0baee5a4f4d93768dbda71493d96c6b54b17"
SCOPE_SHA = "f01d70a7f459a1a2d4f34b32af1f688ac94d3b153a5c9b0fd641fefa9632612d"
RUNTIME_SHA = "df2ec5e24ebe4e4d6acc605056ec49d3821c535199cea489417a75c46f52be60"
ATTEMPT = "workerprep20261025v6g"


def helpers():
    raw = OLD_HELPER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != HELPER_SHA:
        raise ValueError("reviewed_helper_changed")
    module = types.ModuleType("reviewed_v6g_private_pipe_helpers")
    module.__file__ = str(OLD_HELPER)
    exec(compile(raw, str(OLD_HELPER), "exec"), module.__dict__)
    return module


def validated():
    common = helpers()
    receipt = common.checked_json(PACKET / "inert_validation_receipt.json", RECEIPT_SHA)
    review = common.checked_json(PACKET / "independent_review.json", REVIEW_SHA)
    scope = common.checked_json(PACKET / "accepted_policy_records/scope_review.json", SCOPE_SHA)
    runtime = common.checked_json(PACKET / "accepted_policy_records/runtime_review.json", RUNTIME_SHA)
    subjects = common.checked_json(ROOT / scope["exact_subjects"]["path"], scope["exact_subjects"]["sha256"])
    if (review.get("decision") != "ACCEPTED_WITH_RISK" or review.get("blocking_findings") != []
            or scope.get("decision") != "ACCEPTED_WITH_RISK"
            or scope.get("runtime_execution_authorized") is not False
            or review["hashes"]["published_outputs"].get(str((PACKET / "accepted_policy_records/runtime_review.json").relative_to(ROOT))) != RUNTIME_SHA
            or review["hashes"]["published_outputs"].get(str((PACKET / "accepted_policy_records/scope_review.json").relative_to(ROOT))) != SCOPE_SHA
            or receipt.get("exit_code") != 0
            or receipt["response"].get("input_bindings_validated") is not True
            or receipt["response"].get("actions_executed") is not False
            or receipt["response"].get("startup_authorized") is not False
            or runtime.get("schema") != "companion-runtime-pins-v2" or runtime.get("subjects") != subjects
            or runtime.get("network_configuration") != scope.get("network_configuration")):
        raise ValueError("reviewed_v6g_scope_invalid")
    for name, expected in scope["consumer_sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError("reviewed_consumer_changed")
    argv = receipt["argv"]
    if (type(argv) is not list or not argv or any(type(arg) is not str for arg in argv)
            or any(arg in argv for arg in ("--execute-cutover", "--token-fd",
                "--continuation-review", "--reviewed-continuation-review-sha256"))):
        raise ValueError("unexpected_recorded_command")
    args = common.parse_inputs(argv)
    from scripts.research import companion_cutover as cutover
    plan, prepared, pins = cutover.load_inputs(args)
    if (plan.attempt != ATTEMPT or not plan.worker_shutdown or plan.cli_sha256 != common.CLI_SHA
            or args.reviewed_runtime_review_sha256 != RUNTIME_SHA
            or len(pins.targets) != 7 or sum(len(p.source_sha256) for p in pins.targets) != 132
            or runtime["network_configuration"]["bindings"] != dict(plan.network_bindings)
            or receipt["response"].get("attempt") != plan.attempt
            or receipt["response"].get("manifest_sha256") != plan.manifest_sha256):
        raise ValueError("reviewed_v6g_binding_invalid")
    for record in (runtime, *(json.loads(raw) for raw in pins.dependency_review_records)):
        if "scope-review-sha256=" + SCOPE_SHA not in record["reviewer"]:
            raise ValueError("reviewed_v6g_scope_detached")
    return common, argv, plan


def execute():
    token = raw = None
    entered = False
    try:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        os.chdir(ROOT)
        common, argv, plan = validated()
        from scripts.research import companion_cutover as cutover
        from scripts.research import companion_docker_transport as transport
        if os.path.lexists(ROOT.joinpath(*cutover.STATE_PARTS, plan.attempt)):
            raise ValueError("v6g_execution_already_reserved")
        source = next(s for s in plan.baseline if s.name == "phase1-orchestrator")
        with tempfile.TemporaryDirectory(prefix="cryptkeep-v6g-token-source-") as temporary:
            native = transport.DockerTransport(common.CLI_SHA, Path(temporary).resolve(), authorized=True)
            if not native._verify_cli(time.monotonic() + 10):
                raise ValueError("token_source_cli_unverified")
            raw = transport._run((str(transport.CLI), "--host", transport.ENDPOINT,
                "--config", temporary, "container", "inspect", "--format",
                common.source_format(source), source.id),
                timeout=10, input_bytes=None, limit=8192, env=dict(transport.ENV))
            token = common.parse_token(raw)
            raw = None
        entered = True
        return common.handoff(token, argv, cutover.main)
    except Exception:
        print(json.dumps({"state": "INCOMPLETE", "reason": "reviewed_v6g_handoff_failed",
                          "entrypoint_handoff_entered": entered}))
        return 1
    finally:
        token = raw = None


def validate_only():
    os.chdir(ROOT)
    _, argv, _ = validated()
    from scripts.research import companion_cutover as cutover
    return cutover.main(argv)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-once", action="store_true")
    args = parser.parse_args()
    raise SystemExit(execute() if args.execute_once else validate_only())
