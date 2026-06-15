from __future__ import annotations

import io
import json
import urllib.error
import urllib.parse

import pytest

from scripts import hetzner_account_status as status_script
from scripts import set_hetzner_api_token as token_script
from services.ops import hetzner_cloud
from services.security import hetzner_token_store


class _Response:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def read(self) -> bytes:
        return self._body


class _Keyring:
    def __init__(self) -> None:
        self.value: str | None = None

    def get_password(self, service: str, account: str) -> str | None:
        assert service == "crypto-bot-pro"
        assert account == "hetzner_cloud:readonly"
        return self.value

    def set_password(self, service: str, account: str, value: str) -> None:
        assert service == "crypto-bot-pro"
        assert account == "hetzner_cloud:readonly"
        self.value = value

    def delete_password(self, service: str, account: str) -> None:
        assert service == "crypto-bot-pro"
        assert account == "hetzner_cloud:readonly"
        if self.value is None:
            raise RuntimeError("missing")
        self.value = None


def test_token_store_never_returns_secret_in_status(monkeypatch) -> None:
    keyring = _Keyring()
    monkeypatch.setattr(hetzner_token_store, "_require_keyring", lambda: keyring)

    result = hetzner_token_store.set_hetzner_api_token("secret-token")
    status = hetzner_token_store.hetzner_api_token_status()

    assert result == {
        "ok": True,
        "stored_in": "os_keyring",
        "account": "hetzner_cloud:readonly",
    }
    assert status["present"] is True
    assert "secret-token" not in json.dumps([result, status])


def test_interactive_setter_does_not_echo_token(monkeypatch, capsys) -> None:
    values = iter(["secret-token", "secret-token"])
    monkeypatch.setattr(token_script.getpass, "getpass", lambda _prompt: next(values))
    monkeypatch.setattr(
        token_script,
        "set_hetzner_api_token",
        lambda token: {"ok": token == "secret-token", "stored_in": "os_keyring"},
    )

    assert token_script.main([]) == 0
    assert "secret-token" not in capsys.readouterr().out


def test_token_store_sanitizes_keyring_write_failure(monkeypatch) -> None:
    class _BrokenKeyring:
        def set_password(self, _service: str, _account: str, _value: str) -> None:
            raise RuntimeError("secret-token")

    monkeypatch.setattr(
        hetzner_token_store,
        "_require_keyring",
        lambda: _BrokenKeyring(),
    )

    result = hetzner_token_store.set_hetzner_api_token("secret-token")

    assert result == {
        "ok": False,
        "reason": "keyring_write_failed:RuntimeError",
    }
    assert "secret-token" not in json.dumps(result)


def test_read_project_inventory_uses_only_get_and_sanitizes_output() -> None:
    seen = []

    def _open(request, *, timeout):
        seen.append((request, timeout))
        name = urllib.parse.urlsplit(request.full_url).path.rsplit("/", 1)[-1]
        if name == "servers":
            return _Response(
                {
                    "servers": [
                        {
                            "id": 7,
                            "name": "paper-host",
                            "status": "running",
                            "server_type": {"name": "cx22"},
                            "datacenter": {"location": {"name": "ash"}},
                        }
                    ]
                }
            )
        return _Response({name: []})

    result = hetzner_cloud.read_project_inventory("secret-token", open_url=_open)

    assert result["ok"] is True
    assert result["resource_counts"]["servers"] == 1
    assert result["servers"][0]["name"] == "paper-host"
    assert len(seen) == len(hetzner_cloud.RESOURCE_PATHS)
    assert all(request.method == "GET" for request, _timeout in seen)
    assert "secret-token" not in json.dumps(result)


def test_read_project_inventory_follows_pagination() -> None:
    def _open(request, *, timeout):
        parsed = urllib.parse.urlsplit(request.full_url)
        name = parsed.path.rsplit("/", 1)[-1]
        page = int(urllib.parse.parse_qs(parsed.query)["page"][0])
        if name != "servers":
            return _Response({name: []})
        if page == 1:
            return _Response(
                {
                    "servers": [{"id": 1, "name": "first"}],
                    "meta": {"pagination": {"next_page": 2}},
                }
            )
        return _Response(
            {
                "servers": [{"id": 2, "name": "second"}],
                "meta": {"pagination": {"next_page": None}},
            }
        )

    result = hetzner_cloud.read_project_inventory("secret-token", open_url=_open)

    assert result["resource_counts"]["servers"] == 2
    assert [row["name"] for row in result["servers"]] == ["first", "second"]


def test_read_project_inventory_sanitizes_http_errors() -> None:
    def _open(_request, *, timeout):
        raise urllib.error.HTTPError(
            url="https://api.hetzner.cloud/v1/servers",
            code=401,
            msg="Unauthorized secret-token",
            hdrs=None,
            fp=io.BytesIO(),
        )

    with pytest.raises(
        hetzner_cloud.HetznerCloudError,
        match="^hetzner_http_error:401$",
    ):
        hetzner_cloud.read_project_inventory("secret-token", open_url=_open)


def test_account_status_requires_keyring_token(monkeypatch, capsys) -> None:
    monkeypatch.setattr(status_script, "get_hetzner_api_token", lambda: None)

    assert status_script.main() == 1
    result = json.loads(capsys.readouterr().out)
    assert result == {"ok": False, "reason": "hetzner_token_not_configured"}
