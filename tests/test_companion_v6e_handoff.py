"""Reuse reviewed handoff cases, plus exact-delta and added-client guards."""
import hashlib
from pathlib import Path

_source = Path(__file__).with_name("test_companion_v6c_handoff.py")
_raw = _source.read_bytes()
assert hashlib.sha256(_raw).hexdigest() == "81785505e39f40c9b36fa7c98ebc0bbafcd3957b0516387ca7f72d9e7defe958"
_adapted = (_raw.replace(b"companion_worker_preparation_20261023", b"companion_reconnection_plan_20261024")
    .replace(b"workerprep20261023v6c", b"workerprep20261024v6e")
    .replace(b"v6c", b"v6e").replace(b"V6c", b"V6e"))
exec(compile(_adapted, str(__file__), "exec"), globals())


def test_exact_delta_from_prior_reviewed_handoff():
    prior = handoff.ROOT / "docs/review_artifacts/companion_worker_preparation_20261023/execute_reviewed_v6d.py"
    raw = prior.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "0d942f6d41d6e93d07e8129358f20d369b91e2a2f66c607fb157c912ac727959"
    expected = (raw.decode().replace("v6d", "v6e").replace("V6d", "V6e")
        .replace("workerprep20261023v6e", "workerprep20261024v6e"))
    for key in ("RECEIPT_SHA", "REVIEW_SHA", "SCOPE_SHA", "RUNTIME_SHA"):
        old = next(line for line in expected.splitlines() if line.startswith(key + " = "))
        expected = expected.replace(old, key + ' = "' + getattr(handoff, key) + '"')
    assert Path(handoff.__file__).read_text() == expected


@pytest.mark.parametrize("name", ["_shared_signals.py", "companion_evidence_checks.py"])
def test_new_host_guard_or_verifier_drift_refuses(monkeypatch, name):
    read = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: b"changed" if p.name == name else read(p))
    with pytest.raises(ValueError, match="reviewed_consumer_changed"):
        handoff.validated()
