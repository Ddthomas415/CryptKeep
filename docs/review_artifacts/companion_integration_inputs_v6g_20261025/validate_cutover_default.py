"""Actual default CLI validation only, with external-operation tripwires."""
from contextlib import ExitStack, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
from unittest.mock import patch

from scripts.research import companion_cutover as entry
from scripts.research import companion_existing_controller as core


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def validate():
    packet = HERE / "runtime_packet_v6g"
    records = packet / "accepted_policy_records"
    review = json.loads((packet / "independent_review.json").read_text())
    assert review["decision"] == "ACCEPTED_WITH_RISK" and not review["blocking_findings"]
    for path, sha in review["hashes"]["published_outputs"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha
    files = {"manifest": HERE / "reviewed_preparation_manifest.json",
             "preparation-evidence": HERE / "actual_preparation/preparation_evidence.json",
             "preparation-review": HERE / "actual_preparation/actual_id_review.json",
             "staged-metadata": packet / "staged_metadata.derived.json",
             "runtime-review": records / "runtime_review.json",
             "topical-approvals": packet / "topical_approvals.json"}
    argv = [a for key, path in files.items() for a in ("--" + key, str(path))]
    for key in ("manifest", "preparation-review", "runtime-review"):
        argv += ["--reviewed-" + key + "-sha256", hashlib.sha256(files[key].read_bytes()).hexdigest()]
    children = [records / (name + ".json") for name in core.TARGETS]
    for child in children:
        argv += ["--dependency-review", str(child)]
    allowed = {p.resolve() for p in [*files.values(), *children]}
    marker = ROOT / ".cbp_state/runtime/companion_cutovers/workerprep20261025v6g"
    assert not os.path.lexists(marker)
    opened, calls = [], []
    original_open = os.open

    def forbidden(*_args, **_kwargs):
        calls.append("external_operation")
        raise AssertionError("default CLI crossed operation boundary")

    def readonly(path, flags, *args, **kwargs):
        assert Path(path).resolve() in allowed
        assert not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        opened.append(str(path))
        return original_open(path, flags, *args, **kwargs)

    stdout = io.StringIO()
    with ExitStack() as stack:
        for target in ("scripts.research.companion_cutover.DockerInstallBackend",
                       "scripts.research.companion_cutover._reserve",
                       "scripts.research.companion_runtime_adapter.token_from_pipe",
                       "socket.socket", "socket.create_connection", "socket.getaddrinfo",
                       "subprocess.Popen", "subprocess.run", "fcntl.flock", "os.pipe"):
            stack.enter_context(patch(target, forbidden))
        stack.enter_context(patch("os.open", readonly))
        with redirect_stdout(stdout):
            result = entry.main(argv)
    response = json.loads(stdout.getvalue())
    assert result == 0 and not calls and len(opened) == len(allowed) == 13
    assert response["input_bindings_validated"] is True and response["actions_executed"] is False
    assert response["startup_authorized"] is False and not os.path.lexists(marker)
    return {"exit_code": result, "argv": argv, "response": response,
            "allowlisted_readonly_opens": opened, "tripwire_calls": calls,
            "cutover_marker_absent_before_after": True, "runtime_state": "INCOMPLETE"}


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
