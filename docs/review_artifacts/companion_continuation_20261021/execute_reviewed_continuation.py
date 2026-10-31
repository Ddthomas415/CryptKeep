"""Fixed reviewed continuation handoff; inert unless separately authorized to execute."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shlex
import tempfile
import time
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HELPER_SHA = "5c319350681e2fb4fdac363e29b829947e0348678fdcc8ecabc84820713adf12"
IMPLEMENTATION_REVIEW_SHA = "dfeaf12e2b2f2ff7f38e7954fc21f818cdd878c733c5aac8dc90f83ae9e45ded"
CONTINUATION_SHA = "56c03c4cf249ceef01ce5aaace1b7bd1e512b73c4771952f0ad84e27388b1ccc"
CONTINUATION_SCOPE_SHA = "2ae3cc1ee7c0dca885b57e65acfd428f61b4378179b8995a2d1310288157e649"


def helpers():
    path = HERE / "execute_reviewed_cutover.py"
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != HELPER_SHA:
        raise ValueError("reviewed_helper_changed")
    module = types.ModuleType("reviewed_original_handoff")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def validated():
    common = helpers()
    packet = HERE / "runtime_packet"
    receipt = common.checked_json(packet / "inert_validation_receipt.json", common.RECEIPT_SHA)
    common.checked_json(packet / "accepted_policy_records/scope_review.json", common.SCOPE_SHA)
    common.checked_json(packet / "accepted_policy_records/runtime_review.json", common.RUNTIME_SHA)
    review = common.checked_json(packet / "prestart_continuation_implementation_review.json", IMPLEMENTATION_REVIEW_SHA)
    record = common.checked_json(packet / "reviewed_continuation.json", CONTINUATION_SHA)
    scope = common.checked_json(packet / "reviewed_continuation_scope.json", CONTINUATION_SCOPE_SHA)
    if (review.get("decision") not in {"ACCEPTED", "ACCEPTED_WITH_RISK"}
            or scope.get("decision") not in {"ACCEPTED", "ACCEPTED_WITH_RISK"}
            or scope.get("continuation_record_sha256") != CONTINUATION_SHA
            or scope.get("operational_authorized") is not False):
        raise ValueError("continuation_scope_invalid")
    for name, expected in record["consumer_sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError("reviewed_consumer_changed")
    tokens = shlex.split(receipt["command"].replace("\\\n", " "))
    prefix = ["env", "-i", "PATH=/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE=1",
              "./.venv/bin/python", "-B", "-m", "scripts.research.companion_cutover"]
    if tokens[:8] != prefix or any(t in tokens for t in ("--execute-cutover", "--token-fd")):
        raise ValueError("unexpected_recorded_command")
    args = common.parse_inputs(tokens[8:])
    args.continuation_review = packet / "reviewed_continuation.json"
    args.reviewed_continuation_review_sha256 = CONTINUATION_SHA
    from scripts.research import companion_cutover as cutover
    plan, prepared, pins = cutover.load_inputs(args)
    continued = cutover.continuation.load(args, plan, prepared, ROOT, cutover.STATE_PARTS, cutover._read)
    if continued is None:
        raise ValueError("continuation_missing")
    argv = [*tokens[8:], "--continuation-review", str(args.continuation_review),
            "--reviewed-continuation-review-sha256", CONTINUATION_SHA]
    return common, argv, plan, continued


def execute():
    token = raw = None
    entered = False
    try:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        os.chdir(ROOT)
        common, argv, plan, continued = validated()
        from scripts.research import companion_cutover as cutover
        from scripts.research import companion_docker_transport as transport
        destination = ROOT.joinpath(*cutover.STATE_PARTS, continued.execution_id)
        if os.path.lexists(destination):
            raise ValueError("continuation_execution_already_reserved")
        source = next(s for s in plan.baseline if s.name == "phase1-orchestrator")
        with tempfile.TemporaryDirectory(prefix="cryptkeep-token-source-") as temporary:
            config = Path(temporary).resolve(strict=True)
            native = transport.DockerTransport(common.CLI_SHA, config, authorized=True)
            if not native._verify_cli(time.monotonic() + 10):
                raise ValueError("token_source_cli_unverified")
            raw = transport._run((str(transport.CLI), "--host", transport.ENDPOINT, "--config", str(config),
                "container", "inspect", "--format", common.source_format(source), source.id),
                timeout=10, input_bytes=None, limit=8192, env=dict(transport.ENV))
            token = common.parse_token(raw)
            raw = None
        entered = True
        return common.handoff(token, argv, cutover.main)
    except Exception:
        print(json.dumps({"state": "INCOMPLETE", "reason": "reviewed_continuation_handoff_failed",
                          "entrypoint_handoff_entered": entered}))
        return 1
    finally:
        token = raw = None


def validate_only():
    _, argv, plan, continued = validated()
    from scripts.research import companion_cutover as cutover
    return cutover.main(argv)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-once", action="store_true")
    args = parser.parse_args()
    raise SystemExit(execute() if args.execute_once else validate_only())
