"""Retain synthetic handoff regressions; adapt only labels and receipt schema."""
import hashlib
from pathlib import Path

_source = Path(__file__).with_name("test_companion_v6c_handoff.py")
_raw = _source.read_bytes()
assert hashlib.sha256(_raw).hexdigest() == "81785505e39f40c9b36fa7c98ebc0bbafcd3957b0516387ca7f72d9e7defe958"
_adapted = (_raw.replace(b"companion_worker_preparation_20261023", b"companion_integration_inputs_v6h_20261026")
    .replace(b"workerprep20261023v6c", b"workerprep20261026v6h")
    .replace(b"v6c", b"v6h").replace(b"V6c", b"V6h")
    .replace(b'value["stdout"]', b'value["response"]'))
exec(compile(_adapted, str(__file__), "exec"), globals())


def test_exact_delta_from_reviewed_v6g_launcher():
    prior = handoff.ROOT / "docs/review_artifacts/companion_integration_inputs_v6g_20261025/execute_reviewed_v6g.py"
    raw = prior.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "f07d6bc90f0d2d2e578da1f03d8d73ee2dac0cdc465e7535491ad29afe4554f4"
    expected = raw.decode().replace("v6g", "v6h").replace("V6g", "V6h")
    expected = expected.replace("workerprep20261025v6h", "workerprep20261026v6h")
    for key in ("RECEIPT_SHA", "REVIEW_SHA", "SCOPE_SHA", "RUNTIME_SHA"):
        old = next(line for line in expected.splitlines() if line.startswith(key + " = "))
        expected = expected.replace(old, key + ' = "' + getattr(handoff, key) + '"')
    assert Path(handoff.__file__).read_text() == expected


@pytest.mark.parametrize("name", ["_shared_signals.py", "companion_evidence_checks.py", "companion_installer.py", "companion_runtime_adapter.py"])
def test_current_guard_verifier_or_installer_drift_refuses(monkeypatch, name):
    read = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: b"changed" if p.name == name else read(p))
    with pytest.raises(ValueError, match="reviewed_consumer_changed"):
        handoff.validated()


@pytest.mark.parametrize("name", ["scope", "runtime"])
def test_new_published_output_binding_mismatch_refuses(monkeypatch, name):
    common = handoff.helpers()
    original = common.checked_json

    def changed(path, sha):
        value = original(path, sha)
        if path.name == "independent_review.json":
            value["hashes"]["published_outputs"][str((handoff.PACKET / ("accepted_policy_records/" + name + "_review.json")).relative_to(handoff.ROOT))] = "0" * 64
        return value

    monkeypatch.setattr(common, "checked_json", changed)
    monkeypatch.setattr(handoff, "helpers", lambda: common)
    with pytest.raises(ValueError, match="reviewed_v6h_scope_invalid"):
        handoff.validated()


@pytest.mark.parametrize("key,value", [("attempt", "wrong"), ("manifest_sha256", "0" * 64)])
def test_actual_receipt_plan_binding_mismatch_refuses(monkeypatch, key, value):
    common = handoff.helpers()
    original = common.checked_json

    def changed(path, sha):
        result = original(path, sha)
        if path.name == "inert_validation_receipt.json":
            result["response"][key] = value
        return result

    monkeypatch.setattr(common, "checked_json", changed)
    monkeypatch.setattr(handoff, "helpers", lambda: common)
    with pytest.raises(ValueError, match="reviewed_v6h_binding_invalid"):
        handoff.validated()
