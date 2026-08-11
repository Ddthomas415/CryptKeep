from __future__ import annotations

import json

from services.security import credential_source_posture as posture


def test_credential_source_posture_reports_keyring_without_values(monkeypatch):
    monkeypatch.setattr(posture, "load_user_yaml", lambda: {"exchanges": {"coinbase": {}}})
    monkeypatch.setattr(
        posture,
        "load_exchange_credentials",
        lambda venue: {
            "source": "keyring",
            "api_key_present": True,
            "secret_present": True,
            "password_present": False,
            "apiKey": "SHOULD_NOT_APPEAR",
            "secret": "SHOULD_NOT_APPEAR",
        },
    )

    report = posture.credential_source_posture()

    assert report["ok"] is True
    assert report["status"] == "ok"
    assert report["venues"][0]["source"] == "keyring"
    assert report["credential_values_logged"] is False
    assert "SHOULD_NOT_APPEAR" not in json.dumps(report)


def test_credential_source_posture_surfaces_env_credentials(monkeypatch):
    monkeypatch.setattr(
        posture,
        "load_exchange_credentials",
        lambda venue: {
            "source": "env",
            "api_key_present": True,
            "secret_present": True,
            "password_present": True,
            "api_env": "CB_API_KEY",
            "secret_env": "CB_API_SECRET",
            "password_env": "CB_API_PASSPHRASE",
            "apiKey": "ENV_KEY",
            "secret": "ENV_SECRET",
            "password": "ENV_PASS",
        },
    )

    report = posture.credential_source_posture(venues=["coinbase"])

    assert report["ok"] is True
    assert report["status"] == "env_credentials_active"
    assert report["env_credential_venues"] == ["coinbase"]
    assert report["venues"][0]["api_env"] == "CB_API_KEY"
    assert "ENV_KEY" not in json.dumps(report)
    assert "ENV_SECRET" not in json.dumps(report)
    assert "ENV_PASS" not in json.dumps(report)


def test_credential_source_posture_cli_fail_on_env(monkeypatch, capsys):
    from scripts import check_credential_source_posture as cli

    monkeypatch.setattr(
        cli,
        "credential_source_posture",
        lambda venues=None: {
            "ok": True,
            "status": "env_credentials_active",
            "read_only": True,
            "venues": [{"venue": "coinbase", "source": "env", "api_key_present": True, "secret_present": True}],
            "env_credential_venues": ["coinbase"],
            "missing_credential_venues": [],
            "credential_values_logged": False,
        },
    )

    assert cli.main(["--json", "--fail-on-env", "--venue", "coinbase"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is False
    assert report["status"] == "env_credentials_active"
