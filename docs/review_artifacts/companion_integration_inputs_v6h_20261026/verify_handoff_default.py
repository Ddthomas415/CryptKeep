"""Verify actual handoff default with no real token, native call or writes."""
from contextlib import ExitStack, redirect_stdout, redirect_stderr
import builtins
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import sys
from unittest.mock import patch

from scripts.research import companion_cutover as entry


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODULE = "docs.review_artifacts.companion_integration_inputs_v6h_20261026.execute_reviewed_v6h"


def verify():
    packet = HERE / "runtime_packet_v6h"
    receipt_path = packet / "inert_validation_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    scope_path = packet / "accepted_policy_records/scope_review.json"
    scope = json.loads(scope_path.read_text())
    args = receipt["argv"]
    allowed = {Path(args[index + 1]).resolve() for index, value in enumerate(args)
               if value in {"--manifest", "--preparation-evidence", "--preparation-review",
                            "--staged-metadata", "--runtime-review", "--topical-approvals", "--dependency-review"}}
    allowed.update((ROOT / p).resolve() for p in scope["consumer_sha256"])
    allowed.update({receipt_path.resolve(), scope_path.resolve(),
                    (packet / "independent_review.json").resolve(),
                    (ROOT / scope["exact_subjects"]["path"]).resolve(),
                    (ROOT / "docs/review_artifacts/companion_continuation_20261021/execute_reviewed_cutover.py").resolve(),
                    (HERE / "execute_reviewed_v6h.py").resolve()})
    marker = ROOT / ".cbp_state/runtime/companion_cutovers/workerprep20261026v6h"
    assert not os.path.lexists(marker)
    calls, readonly_paths, fds = [], [], set()
    old_os_open, old_io_open = os.open, io.open

    def forbidden(*_args, **_kwargs):
        calls.append("external_operation")
        raise AssertionError("actual default crossed operation boundary")

    def readonly_os(path, flags, *a, **kw):
        assert Path(path).resolve() in allowed
        assert not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        fd = old_os_open(path, flags, *a, **kw)
        fds.add(fd)
        readonly_paths.append(str(path))
        return fd

    def readonly_io(path, mode="r", *a, **kw):
        assert not any(flag in mode for flag in "wax+")
        assert (path in fds) if type(path) is int else (Path(path).resolve() in allowed)
        return old_io_open(path, mode, *a, **kw)

    stdout, stderr = io.StringIO(), io.StringIO()
    with ExitStack() as stack:
        for target in ("scripts.research.companion_docker_transport._run",
                       "scripts.research.companion_docker_transport.DockerTransport",
                       "scripts.research.companion_cutover.DockerInstallBackend",
                       "scripts.research.companion_cutover._reserve",
                       "scripts.research.companion_runtime_adapter.token_from_pipe",
                       "socket.socket", "socket.create_connection", "socket.getaddrinfo",
                       "subprocess.Popen", "subprocess.run", "fcntl.flock", "os.pipe",
                       "tempfile.TemporaryDirectory", "resource.setrlimit"):
            stack.enter_context(patch(target, forbidden))
        stack.enter_context(patch("os.open", readonly_os))
        stack.enter_context(patch("io.open", readonly_io))
        stack.enter_context(patch.object(builtins, "open", readonly_io))
        stack.enter_context(patch.object(sys, "argv", [MODULE]))
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                runpy.run_module(MODULE, run_name="__main__")
            except SystemExit as error:
                code = error.code
            else:
                raise AssertionError("actual module omitted exit status")
    response = json.loads(stdout.getvalue())
    assert code == 0 and response == receipt["response"] and stderr.getvalue() == ""
    assert not calls and not os.path.lexists(marker)
    return {"exit_code": code, "response": response, "stderr_empty": True,
            "tripwire_calls": calls, "readonly_os_opens": readonly_paths,
            "cutover_marker_absent_before_after": True,
            "source_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
            "module_sha256": hashlib.sha256((HERE / "execute_reviewed_v6h.py").read_bytes()).hexdigest(),
            "proof_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "runtime_state": "INCOMPLETE"}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
