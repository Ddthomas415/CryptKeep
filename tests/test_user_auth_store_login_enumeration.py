from services.security import user_auth_store as auth

def test_verify_login_unknown_user_returns_invalid_credentials() -> None:
    out = auth.verify_login(username="missing-user", password="x")
    assert out["ok"] is False
    assert out["reason"] == "invalid_credentials"
