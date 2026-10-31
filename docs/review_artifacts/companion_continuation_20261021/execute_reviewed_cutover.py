"""One authorized handoff to the existing cutover, with no credential fallback."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shlex
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RECEIPT_SHA = "a269cfdd5307724af5b67c414f4ad1d6e4e9009c1bbb2a3e1f0df47ff6b67f36"
SCOPE_SHA = "271c1c2c204f1493fd36caf0db57b5af464aba4c920526e2e77fd019ce24790d"
RUNTIME_SHA = "64127a85c985be4e09c0c6df24f5a688d5faae5a38077a3ccd20af7e82d7d43b"
CLI_SHA = "678271184175b40dfc4bd6f4582be00ae1538b0d1e031181f52ceedfae9af5fb"


def checked_json(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("reviewed_input_changed")
    return json.loads(raw)


def inputs():
    receipt = checked_json(HERE / "runtime_packet/inert_validation_receipt.json", RECEIPT_SHA)
    scope = checked_json(HERE / "runtime_packet/accepted_policy_records/scope_review.json", SCOPE_SHA)
    checked_json(HERE / "runtime_packet/accepted_policy_records/runtime_review.json", RUNTIME_SHA)
    for name, expected in scope["reviewed_sha256"].items():
        if name.startswith("scripts/research/") and hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError("reviewed_consumer_changed")
    tokens = shlex.split(receipt["command"].replace("\\\n", " "))
    prefix = ["env", "-i", "PATH=/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE=1",
              "./.venv/bin/python", "-B", "-m", "scripts.research.companion_cutover"]
    if tokens[:8] != prefix or any(t in tokens for t in ("--execute-cutover", "--token-fd")):
        raise ValueError("unexpected_recorded_command")
    return tokens[8:]


def parse_inputs(argv):
    parser = argparse.ArgumentParser(add_help=False)
    for key in ("manifest", "preparation-evidence", "preparation-review", "staged-metadata",
                "runtime-review", "topical-approvals"):
        parser.add_argument("--" + key, type=Path, required=True)
    for key in ("manifest", "preparation-review", "runtime-review"):
        parser.add_argument("--reviewed-" + key + "-sha256", required=True)
    parser.add_argument("--dependency-review", type=Path, action="append", required=True)
    return parser.parse_args(argv)


def source_format(source):
    # Only this exact existing internal service token may reach the private pipe.
    identity = json.dumps(source.id)
    image = json.dumps(source.image)
    return ('{{if and (eq .Id ' + identity + ') (eq .Image ' + image + ') '
        '(eq .State.Status "running")}}{{range .Config.Env}}'
        '{{if eq (index (split . "=") 0) "SERVICE_TOKEN"}}{{json .}}{{println}}{{end}}'
        '{{end}}{{end}}')


def parse_token(raw):
    if type(raw) is not bytes or len(raw) > 8192:
        raise ValueError("token_source_invalid")
    rows = [line for line in raw.splitlines() if line]
    if len(rows) != 1:
        raise ValueError("token_source_invalid")
    value = json.loads(rows[0])
    prefix = "SERVICE_TOKEN="
    if type(value) is not str or not value.startswith(prefix):
        raise ValueError("token_source_invalid")
    token = value[len(prefix):]
    if not 1 <= len(token) <= 4096 or any(not 33 <= ord(c) <= 126 for c in token):
        raise ValueError("token_source_invalid")
    return token


def handoff(token, argv, invoke):
    read_fd = write_fd = None
    payload = None
    try:
        read_fd, write_fd = os.pipe()
        if read_fd <= 2:
            raise ValueError("token_pipe_descriptor_unavailable")
        os.set_blocking(write_fd, False)
        payload = token.encode("ascii")
        if os.write(write_fd, payload) != len(payload):
            raise ValueError("token_pipe_incomplete")
        os.close(write_fd)
        write_fd = None
        token = payload = None
        channel, read_fd = read_fd, None  # Existing entrypoint takes descriptor ownership.
        return invoke([*argv, "--execute-cutover", "--token-fd", str(channel)])
    finally:
        token = payload = None
        for fd in (read_fd, write_fd):
            if fd is not None:
                os.close(fd)


def execute():
    token = raw = None
    entered = False
    try:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        os.chdir(ROOT)
        argv = inputs()
        from scripts.research import companion_cutover as cutover
        from scripts.research import companion_docker_transport as transport
        plan, prepared, pins = cutover.load_inputs(parse_inputs(argv))
        source = next(s for s in plan.baseline if s.name == "phase1-orchestrator")
        with tempfile.TemporaryDirectory(prefix="cryptkeep-token-source-") as temporary:
            native = transport.DockerTransport(CLI_SHA, Path(temporary).resolve(), authorized=True)
            if not native._verify_cli(time.monotonic() + 10):
                raise ValueError("token_source_cli_unverified")
            raw = transport._run((str(transport.CLI), "--host", transport.ENDPOINT, "--config", temporary,
                "container", "inspect", "--format", source_format(source), source.id),
                timeout=10, input_bytes=None, limit=8192, env=dict(transport.ENV))
            token = parse_token(raw)
            raw = None
        entered = True
        return handoff(token, argv, cutover.main)
    except Exception:
        # Never print source output, exception payload, token length/hash or traceback.
        print(json.dumps({"state": "INCOMPLETE", "reason": "reviewed_handoff_failed",
                          "entrypoint_handoff_entered": entered}))
        return 1
    finally:
        token = raw = None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-once", action="store_true")
    args = parser.parse_args()
    if args.execute_once:
        raise SystemExit(execute())
    print(json.dumps({"actions_executed": False, "native_operations": False,
                      "existing_inputs_loaded": len(inputs()) > 0}))
