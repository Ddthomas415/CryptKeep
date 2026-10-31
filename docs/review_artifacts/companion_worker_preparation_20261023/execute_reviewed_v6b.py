"""Fixed v6b handoff. Default is inert; execution requires separate authorization."""
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
PACKET = HERE / "runtime_packet_v6b_launcher"
RECEIPT_SHA = "aebbeb6384465e01fff7d2354b4e654619af5d57d566d304607d35619aabe0af"
REVIEW_SHA = "607dbae7221bbb51738b82f3c28e2961adb6f993c47b2cc092017cbbec360835"
SCOPE_SHA = "d32f3589c9156844f9a4211a3cec289c36c5260536e82c82be38f947d3ff4054"
RUNTIME_SHA = "47dbeebdbdbd3cd978156f9a25d8b07027f34023ab6b0ff541f2d05cfc1ca3e6"
ATTEMPT = "workerprep20261023v6b"


def helpers():
    raw = OLD_HELPER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != HELPER_SHA:
        raise ValueError("reviewed_helper_changed")
    module = types.ModuleType("reviewed_v6b_private_pipe_helpers")
    module.__file__ = str(OLD_HELPER)
    exec(compile(raw, str(OLD_HELPER), "exec"), module.__dict__)
    return module


def validated():
    common = helpers()
    receipt = common.checked_json(PACKET / "inert_validation_receipt.json", RECEIPT_SHA)
    review = common.checked_json(PACKET / "independent_review.json", REVIEW_SHA)
    scope = common.checked_json(PACKET / "accepted_policy_records/scope_review.json", SCOPE_SHA)
    runtime = common.checked_json(PACKET / "accepted_policy_records/runtime_review.json", RUNTIME_SHA)
    if (review.get("decision") != "ACCEPTED_WITH_RISK"
            or scope.get("decision") != "ACCEPTED_WITH_RISK"
            or scope.get("runtime_execution_authorized") is not False
            or review.get("accepted_runtime_review_sha256") != RUNTIME_SHA
            or runtime.get("subjects") != scope.get("exact_subjects")):
        raise ValueError("reviewed_v6b_scope_invalid")
    for name, expected in scope["consumer_sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError("reviewed_consumer_changed")
    command = receipt["command"]
    prefix = ["./.venv/bin/python", "-B", "-m", "scripts.research.companion_cutover"]
    if (type(command) is not list or command[:4] != prefix
            or any(type(arg) is not str for arg in command)
            or any(arg in command for arg in ("--execute-cutover", "--token-fd",
                "--continuation-review", "--reviewed-continuation-review-sha256"))):
        raise ValueError("unexpected_recorded_command")
    argv = command[4:]
    args = common.parse_inputs(argv)
    from scripts.research import companion_cutover as cutover
    plan, prepared, pins = cutover.load_inputs(args)
    if (plan.attempt != ATTEMPT or not plan.worker_shutdown or plan.cli_sha256 != common.CLI_SHA
            or args.reviewed_runtime_review_sha256 != RUNTIME_SHA
            or len(pins.targets) != 7 or sum(len(p.source_sha256) for p in pins.targets) != 132):
        raise ValueError("reviewed_v6b_binding_invalid")
    for record in (runtime, *(json.loads(raw) for raw in pins.dependency_review_records)):
        if "scope-review-sha256=" + SCOPE_SHA not in record["reviewer"]:
            raise ValueError("reviewed_v6b_scope_detached")
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
            raise ValueError("v6b_execution_already_reserved")
        source = next(s for s in plan.baseline if s.name == "phase1-orchestrator")
        with tempfile.TemporaryDirectory(prefix="cryptkeep-v6b-token-source-") as temporary:
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
        print(json.dumps({"state": "INCOMPLETE", "reason": "reviewed_v6b_handoff_failed",
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
