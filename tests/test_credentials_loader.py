from __future__ import annotations

from services.security import credentials_loader as loader


def test_load_exchange_credentials_prefers_keyring(monkeypatch):
    monkeypatch.setattr(
        loader,
        "load_user_yaml",
        lambda: {
            "exchanges": {
                "coinbase": {
                    "api_key_env": "CB_API_KEY",
                    "secret_env": "CB_API_SECRET",
                    "password_env": "CB_API_PASSPHRASE",
                }
            }
        },
    )
    monkeypatch.setattr(
        loader,
        "get_exchange_credentials",
        lambda venue: {"apiKey": "keyring-key", "secret": "keyring-secret", "passphrase": "keyring-pass"},
    )
    monkeypatch.setenv("CB_API_KEY", "env-key")
    monkeypatch.setenv("CB_API_SECRET", "env-secret")
    monkeypatch.setenv("CB_API_PASSPHRASE", "env-pass")

    out = loader.load_exchange_credentials("coinbase")

    assert out["source"] == "keyring"
    assert out["apiKey"] == "keyring-key"
    assert out["secret"] == "keyring-secret"
    assert out["password"] == "keyring-pass"
    assert out["password_present"] is True
    assert out["api_env"] == "CB_API_KEY"
    assert out["secret_env"] == "CB_API_SECRET"


def test_load_exchange_credentials_falls_back_to_env(monkeypatch):
    monkeypatch.setattr(loader, "load_user_yaml", lambda: {"exchanges": {"coinbase": {}}})
    monkeypatch.setattr(loader, "get_exchange_credentials", lambda venue: None)
    monkeypatch.setenv("COINBASE_API_KEY", "env-key")
    monkeypatch.setenv("COINBASE_API_SECRET", "env-secret")

    out = loader.load_exchange_credentials("coinbase")

    assert out["source"] == "env"
    assert out["apiKey"] == "env-key"
    assert out["secret"] == "env-secret"
    assert out["password"] is None
    assert out["api_key_present"] is True
    assert out["secret_present"] is True
