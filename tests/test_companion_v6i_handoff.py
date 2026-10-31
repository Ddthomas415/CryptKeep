"""Retain synthetic handoff regressions; adapt only labels and receipt schema."""
import hashlib
from pathlib import Path

_source = Path(__file__).with_name("test_companion_v6c_handoff.py")
_raw = _source.read_bytes()
assert hashlib.sha256(_raw).hexdigest() == "81785505e39f40c9b36fa7c98ebc0bbafcd3957b0516387ca7f72d9e7defe958"
_adapted = (_raw.replace(b"companion_worker_preparation_20261023", b"companion_integration_inputs_v6i_20261027")
    .replace(b"workerprep20261023v6c", b"workerprep20261027v6i")
    .replace(b"v6c", b"v6i").replace(b"V6c", b"V6i")
    .replace(b'value["stdout"]', b'value["response"]'))
exec(compile(_adapted, str(__file__), "exec"), globals())


def test_exact_delta_from_reviewed_v6h_launcher():
    prior = handoff.ROOT / "docs/review_artifacts/companion_integration_inputs_v6h_20261026/execute_reviewed_v6h.py"
    raw = prior.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "e0ecdd3f791507f6b930104dd46ee11dd79115424be7606f4fe4f46bb2f9eaa2"
    expected = raw.decode().replace("v6h", "v6i").replace("V6h", "V6i")
    expected = expected.replace("workerprep20261026v6i", "workerprep20261027v6i")
    for key in ("RECEIPT_SHA", "REVIEW_SHA", "SCOPE_SHA", "RUNTIME_SHA"):
        old = next(line for line in expected.splitlines() if line.startswith(key + " = "))
        expected = expected.replace(old, key + ' = "' + getattr(handoff, key) + '"')
    expected = expected.replace(
        '    subjects = common.checked_json(ROOT / scope["exact_subjects"]["path"], scope["exact_subjects"]["sha256"])',
        '    subject_path = PACKET / "subjects.draft.json"\n'
        '    subject_sha = scope["input_sha256"].get(str(subject_path.relative_to(ROOT)))\n'
        '    subjects = common.checked_json(subject_path, subject_sha)')
    expected = expected.replace(
        '            or runtime.get("schema") != "companion-runtime-pins-v2" or runtime.get("subjects") != subjects',
        '            or scope.get("exact_subjects") != subjects\n'
        '            or runtime.get("schema") != "companion-runtime-pins-v2" or runtime.get("subjects") != subjects')
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
    with pytest.raises(ValueError, match="reviewed_v6i_scope_invalid"):
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
    with pytest.raises(ValueError, match="reviewed_v6i_binding_invalid"):
        handoff.validated()


@pytest.mark.parametrize("change", ["inline_subject", "subject_file_hash", "missing_subject_pin", "legacy_shape"])
def test_inline_subjects_require_exact_hash_bound_file(monkeypatch, change):
    common = handoff.helpers()
    original = common.checked_json

    def changed(path, sha):
        value = original(path, sha)
        if path.name == "scope_review.json":
            key = str((handoff.PACKET / "subjects.draft.json").relative_to(handoff.ROOT))
            if change == "inline_subject":
                value["exact_subjects"][3]["container_id"] = "0" * 64
            elif change == "subject_file_hash":
                value["input_sha256"][key] = "0" * 64
            elif change == "missing_subject_pin":
                del value["input_sha256"][key]
            else:
                value["exact_subjects"] = {"path": key, "sha256": value["input_sha256"][key]}
        return value

    monkeypatch.setattr(common, "checked_json", changed)
    monkeypatch.setattr(handoff, "helpers", lambda: common)
    with pytest.raises(ValueError):
        handoff.validated()
