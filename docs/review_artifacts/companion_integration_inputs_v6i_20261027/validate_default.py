"""Run actual default preparation validation with external-operation tripwires."""
from contextlib import ExitStack, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
from unittest.mock import patch

from scripts.research import companion_prepare as prepare
from . import refresh_sources as sources


HERE = Path(__file__).resolve().parent


def validate():
    manifest = HERE / "reviewed_preparation_manifest.json"
    sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
    markers = [sources.ROOT / ".cbp_state/runtime" / group / sources.PROPOSED
               for group in ("companion_preparations", "companion_cutovers")]
    before = [os.path.lexists(p) for p in markers]
    assert before == [False, False]
    calls, reads = [], []
    original_open = os.open

    def forbidden(*_args, **_kwargs):
        calls.append("external_operation")
        raise AssertionError("default validation crossed boundary")

    def readonly(path, flags, *args, **kwargs):
        assert Path(path).resolve() == manifest.resolve()
        assert not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        reads.append(str(path))
        return original_open(path, flags, *args, **kwargs)

    stdout = io.StringIO()
    with ExitStack() as stack:
        for target in (
            "scripts.research.companion_prepare.DockerInstallBackend",
            "scripts.research.companion_prepare.PreparationReceipt",
            "scripts.research.companion_prepare._reserve", "fcntl.flock",
            "socket.socket", "socket.create_connection", "socket.getaddrinfo",
            "subprocess.Popen", "subprocess.run", "os.pipe",
        ):
            stack.enter_context(patch(target, forbidden))
        stack.enter_context(patch("os.open", readonly))
        with redirect_stdout(stdout):
            result = prepare.main(["--manifest", str(manifest), "--reviewed-manifest-sha256", sha])
    response = json.loads(stdout.getvalue())
    after = [os.path.lexists(p) for p in markers]
    assert result == 0 and not calls and len(reads) == 1 and before == after
    assert response["actions_executed"] is False and response["startup_authorized"] is False
    assert response["attempt"] == sources.PROPOSED
    return {"exit_code": result, "response": response, "tripwire_calls": calls,
            "readonly_manifest_opens": reads, "markers_before": before, "markers_after": after,
            "manifest_sha256": sha, "runtime_state": "INCOMPLETE"}


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
