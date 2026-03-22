from services.security import user_auth_store as auth

def test_bootstrap_user_from_env_requires_dev_opt_in(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("CBP_ALLOW_BOOTSTRAP_USER", raising=False)
    monkeypatch.setenv("CBP_AUTH_BOOTSTRAP_USER", "bootstrap-admin")
    monkeypatch.setenv("CBP_AUTH_BOOTSTRAP_PASSWORD", "bootstrap-pass")
    out = auth.ensure_bootstrap_user_from_env()
    assert out["ok"] is True
    assert out["skipped"] is True
    assert out["reason"] == "bootstrap_not_allowed"
