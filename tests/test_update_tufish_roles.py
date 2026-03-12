from __future__ import annotations

from services.update import tufish


def test_verify_role_threshold_requires_unique_signers(monkeypatch):
    role = {
        "threshold": 2,
        "keys": {"k1": "pem1", "k2": "pem2", "k3": "pem3"},
        "meta": {"version": 1},
        "signatures": [
            {"keyid": "k1", "sig_b64": "sig-ok-1"},
            {"keyid": "k2", "sig_b64": "sig-ok-2"},
            {"keyid": "k1", "sig_b64": "sig-ok-1-dup"},
        ],
    }

    monkeypatch.setattr(
        tufish,
        "verify_ed25519_key",
        lambda pem, payload, sig_b64: str(sig_b64).startswith("sig-ok"),
    )

    out = tufish.verify_role_threshold(role)
    assert out["ok"] is True
    assert out["threshold"] == 2
    assert out["valid_signatures"] == 2
    assert sorted(out["unique_valid_signers"]) == ["k1", "k2"]


def test_verify_role_threshold_fails_when_threshold_not_met(monkeypatch):
    role = {
        "threshold": 2,
        "keys": {"k1": "pem1"},
        "meta": {"version": 1},
        "signatures": [
            {"keyid": "k1", "sig_b64": "sig-ok"},
            {"keyid": "kX", "sig_b64": "sig-ok"},
        ],
    }
    monkeypatch.setattr(tufish, "verify_ed25519_key", lambda pem, payload, sig_b64: True)

    out = tufish.verify_role_threshold(role)
    assert out["ok"] is False
    assert out["valid_signatures"] == 1
    assert out["missing_keys"] == ["kX"]


def test_verify_roles_metadata_with_required_roles_and_policy(monkeypatch):
    monkeypatch.setattr(tufish, "verify_ed25519_key", lambda pem, payload, sig_b64: True)
    role_template = {
        "threshold": 1,
        "keys": {"k1": "pem1"},
        "meta": {"version": 1},
        "signatures": [{"keyid": "k1", "sig_b64": "sig-any"}],
    }
    manifest = {
        "roles": {
            "root": dict(role_template, rotation_policy={"min_signatures": 1, "max_key_age_days": 365, "revoked_keyids": []}),
            "targets": dict(role_template),
            "timestamp": dict(role_template),
            "snapshot": dict(role_template),
        }
    }
    out = tufish.verify_roles_metadata(
        manifest,
        require_roles=True,
        require_role_signatures=True,
        require_rotation_policy=True,
    )
    assert out["ok"] is True
    assert out["missing_roles"] == []
    assert out["rotation_policy"]["ok"] is True


def test_verify_roles_metadata_reports_missing_required_roles():
    manifest = {"roles": {"root": {"threshold": 1, "keys": {"k1": "pem1"}, "signatures": []}}}
    out = tufish.verify_roles_metadata(
        manifest,
        require_roles=True,
        require_role_signatures=False,
        require_rotation_policy=False,
    )
    assert out["ok"] is False
    assert "targets" in out["missing_roles"]
    assert "timestamp" in out["missing_roles"]
    assert "snapshot" in out["missing_roles"]
