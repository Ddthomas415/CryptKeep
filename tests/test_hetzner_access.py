from __future__ import annotations

import io
import json
import ssl
import urllib.error
import urllib.parse

import pytest

from scripts import hetzner_account_status as status_script
from scripts import hetzner_cloud_safeguards as safeguards_script
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

    def _open(request, *, timeout, context):
        seen.append((request, timeout, context))
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
    assert all(request.method == "GET" for request, _timeout, _context in seen)
    assert all(
        isinstance(context, ssl.SSLContext)
        for _request, _timeout, context in seen
    )
    assert all(context.check_hostname for _request, _timeout, context in seen)
    assert all(
        context.verify_mode == ssl.CERT_REQUIRED
        for _request, _timeout, context in seen
    )
    assert "secret-token" not in json.dumps(result)


def test_read_project_inventory_follows_pagination() -> None:
    def _open(request, *, timeout, context):
        assert isinstance(context, ssl.SSLContext)
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
    def _open(_request, *, timeout, context):
        assert isinstance(context, ssl.SSLContext)
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


def test_cloud_safeguard_plan_requires_restrictive_ssh_source_before_network() -> None:
    def _open(_request, *, timeout, context):  # pragma: no cover - must not call
        raise AssertionError("network should not be called without SSH source CIDR")

    result = hetzner_cloud.plan_cloud_safeguards(
        "secret-token",
        server_id=7,
        open_url=_open,
    )

    assert result == {
        "ok": False,
        "ready_to_apply": False,
        "reason": "ssh_source_cidr_required",
        "changes": [],
    }


def test_cloud_safeguard_plan_rejects_broad_ssh_source_before_network() -> None:
    def _open(_request, *, timeout, context):  # pragma: no cover - must not call
        raise AssertionError("network should not be called for unsafe CIDR")

    with pytest.raises(
        hetzner_cloud.HetznerCloudError,
        match="^ssh_source_cidr_too_broad$",
    ):
        hetzner_cloud.plan_cloud_safeguards(
            "secret-token",
            server_id=7,
            ssh_source_cidrs=["0.0.0.0/0"],
            open_url=_open,
        )


def test_cloud_safeguard_plan_tailscale_only_does_not_require_ssh_source() -> None:
    seen = []

    def _open(request, *, timeout, context):
        seen.append((request.method, urllib.parse.urlsplit(request.full_url).path))
        path = urllib.parse.urlsplit(request.full_url).path
        if path.endswith("/servers/7"):
            return _Response(
                {
                    "server": {
                        "id": 7,
                        "name": "paper-host",
                        "status": "running",
                        "server_type": {"name": "cax11"},
                        "datacenter": {"location": {"name": "nbg1"}},
                        "backup_window": None,
                        "protection": {"delete": False, "rebuild": False},
                    }
                }
            )
        if path.endswith("/firewalls"):
            return _Response({"firewalls": []})
        raise AssertionError(path)

    result = hetzner_cloud.plan_cloud_safeguards(
        "secret-token",
        server_id=7,
        access_mode=hetzner_cloud.ACCESS_MODE_TAILSCALE_ONLY,
        open_url=_open,
    )

    assert result["ok"] is True
    assert result["ready_to_apply"] is True
    assert result["access_mode"] == hetzner_cloud.ACCESS_MODE_TAILSCALE_ONLY
    assert result["firewall_name"] == hetzner_cloud.TAILSCALE_ONLY_FIREWALL_NAME
    assert result["ssh_source_cidrs"] == []
    assert [row["id"] for row in result["changes_needed"]] == [
        "create_tailscale_only_firewall",
        "enable_delete_rebuild_protection",
        "enable_backups",
    ]
    assert all(method == "GET" for method, _path in seen)
    assert "secret-token" not in json.dumps(result)


def test_cloud_safeguard_plan_tailscale_only_rejects_ssh_source_before_network() -> None:
    def _open(_request, *, timeout, context):  # pragma: no cover - must not call
        raise AssertionError("network should not be called for mixed access modes")

    with pytest.raises(
        hetzner_cloud.HetznerCloudError,
        match="^ssh_source_cidr_not_allowed_for_tailscale_only$",
    ):
        hetzner_cloud.plan_cloud_safeguards(
            "secret-token",
            server_id=7,
            ssh_source_cidrs=["198.51.100.7/32"],
            access_mode=hetzner_cloud.ACCESS_MODE_TAILSCALE_ONLY,
            open_url=_open,
        )


def test_cloud_safeguard_plan_reports_needed_cloud_changes() -> None:
    seen = []

    def _open(request, *, timeout, context):
        seen.append((request.method, urllib.parse.urlsplit(request.full_url).path))
        path = urllib.parse.urlsplit(request.full_url).path
        if path.endswith("/servers/7"):
            return _Response(
                {
                    "server": {
                        "id": 7,
                        "name": "paper-host",
                        "status": "running",
                        "server_type": {"name": "cax11"},
                        "datacenter": {"location": {"name": "nbg1"}},
                        "backup_window": None,
                        "protection": {"delete": False, "rebuild": False},
                    }
                }
            )
        if path.endswith("/firewalls"):
            return _Response({"firewalls": []})
        raise AssertionError(path)

    result = hetzner_cloud.plan_cloud_safeguards(
        "secret-token",
        server_id=7,
        ssh_source_cidrs=["198.51.100.7/32"],
        open_url=_open,
    )

    assert result["ok"] is True
    assert result["ready_to_apply"] is True
    assert result["server"]["name"] == "paper-host"
    assert result["ssh_source_cidrs"] == ["198.51.100.7/32"]
    assert [row["id"] for row in result["changes_needed"]] == [
        "create_ssh_firewall",
        "enable_delete_rebuild_protection",
        "enable_backups",
    ]
    assert all(method == "GET" for method, _path in seen)
    assert "secret-token" not in json.dumps(result)


def test_cloud_safeguard_apply_tailscale_only_uses_no_inbound_rules() -> None:
    seen = []

    def _open(request, *, timeout, context):
        parsed = urllib.parse.urlsplit(request.full_url)
        body = json.loads(request.data.decode("utf-8")) if request.data else None
        seen.append((request.method, parsed.path, body))
        if parsed.path.endswith("/servers/7") and request.method == "GET":
            return _Response(
                {
                    "server": {
                        "id": 7,
                        "name": "paper-host",
                        "status": "running",
                        "server_type": {"name": "cax11"},
                        "datacenter": {"location": {"name": "nbg1"}},
                        "backup_window": None,
                        "protection": {"delete": False, "rebuild": False},
                    }
                }
            )
        if parsed.path.endswith("/firewalls") and request.method == "GET":
            return _Response({"firewalls": []})
        if parsed.path.endswith("/firewalls") and request.method == "POST":
            assert body == {
                "apply_to": [{"type": "server", "server": {"id": 7}}],
                "name": hetzner_cloud.TAILSCALE_ONLY_FIREWALL_NAME,
                "rules": [],
            }
            return _Response({"firewall": {"id": 41}, "action": {"id": 101}})
        if parsed.path.endswith("/servers/7/actions/change_protection"):
            assert body == {"delete": True, "rebuild": True}
            return _Response({"action": {"id": 102}})
        if parsed.path.endswith("/servers/7/actions/enable_backup"):
            assert body == {}
            return _Response({"action": {"id": 103}})
        raise AssertionError((request.method, parsed.path, body))

    result = hetzner_cloud.apply_cloud_safeguards(
        "secret-token",
        server_id=7,
        confirm_server_id=7,
        access_mode=hetzner_cloud.ACCESS_MODE_TAILSCALE_ONLY,
        open_url=_open,
    )

    assert result == {
        "ok": True,
        "server_id": 7,
        "applied": [
            {
                "id": "create_tailscale_only_firewall",
                "firewall_id": 41,
                "action_ids": [101],
            },
            {"id": "enable_delete_rebuild_protection", "action_ids": [102]},
            {"id": "enable_backups", "action_ids": [103]},
        ],
        "applied_count": 3,
    }
    assert [method for method, _path, _body in seen] == [
        "GET",
        "GET",
        "POST",
        "POST",
        "POST",
    ]
    assert "secret-token" not in json.dumps(result)


def test_cloud_safeguard_apply_requires_matching_confirm_server_id() -> None:
    with pytest.raises(
        hetzner_cloud.HetznerCloudError,
        match="^confirm_server_id_mismatch$",
    ):
        hetzner_cloud.apply_cloud_safeguards(
            "secret-token",
            server_id=7,
            confirm_server_id=8,
            ssh_source_cidrs=["198.51.100.7/32"],
        )


def test_cloud_safeguard_apply_uses_guarded_post_sequence() -> None:
    seen = []

    def _open(request, *, timeout, context):
        parsed = urllib.parse.urlsplit(request.full_url)
        body = json.loads(request.data.decode("utf-8")) if request.data else None
        seen.append((request.method, parsed.path, body))
        if parsed.path.endswith("/servers/7") and request.method == "GET":
            return _Response(
                {
                    "server": {
                        "id": 7,
                        "name": "paper-host",
                        "status": "running",
                        "server_type": {"name": "cax11"},
                        "datacenter": {"location": {"name": "nbg1"}},
                        "backup_window": None,
                        "protection": {"delete": False, "rebuild": False},
                    }
                }
            )
        if parsed.path.endswith("/firewalls") and request.method == "GET":
            return _Response({"firewalls": []})
        if parsed.path.endswith("/firewalls") and request.method == "POST":
            assert body["name"] == hetzner_cloud.SSH_FIREWALL_NAME
            assert body["rules"][0]["source_ips"] == ["198.51.100.7/32"]
            assert body["apply_to"] == [{"type": "server", "server": {"id": 7}}]
            return _Response({"firewall": {"id": 41}, "action": {"id": 101}})
        if parsed.path.endswith("/servers/7/actions/change_protection"):
            assert body == {"delete": True, "rebuild": True}
            return _Response({"action": {"id": 102}})
        if parsed.path.endswith("/servers/7/actions/enable_backup"):
            assert body == {}
            return _Response({"action": {"id": 103}})
        raise AssertionError((request.method, parsed.path, body))

    result = hetzner_cloud.apply_cloud_safeguards(
        "secret-token",
        server_id=7,
        confirm_server_id=7,
        ssh_source_cidrs=["198.51.100.7/32"],
        open_url=_open,
    )

    assert result == {
        "ok": True,
        "server_id": 7,
        "applied": [
            {"id": "create_ssh_firewall", "firewall_id": 41, "action_ids": [101]},
            {"id": "enable_delete_rebuild_protection", "action_ids": [102]},
            {"id": "enable_backups", "action_ids": [103]},
        ],
        "applied_count": 3,
    }
    assert [method for method, _path, _body in seen] == [
        "GET",
        "GET",
        "POST",
        "POST",
        "POST",
    ]
    assert "secret-token" not in json.dumps(result)


def test_cloud_safeguard_apply_tailscale_only_corrects_rule_drift() -> None:
    seen_posts = []

    def _open(request, *, timeout, context):
        parsed = urllib.parse.urlsplit(request.full_url)
        body = json.loads(request.data.decode("utf-8")) if request.data else None
        if parsed.path.endswith("/servers/7") and request.method == "GET":
            return _Response(
                {
                    "server": {
                        "id": 7,
                        "name": "paper-host",
                        "status": "running",
                        "backup_window": "22-02",
                        "protection": {"delete": True, "rebuild": True},
                    }
                }
            )
        if parsed.path.endswith("/firewalls") and request.method == "GET":
            return _Response(
                {
                    "firewalls": [
                        {
                            "id": 41,
                            "name": hetzner_cloud.TAILSCALE_ONLY_FIREWALL_NAME,
                            "rules": [
                                {
                                    "direction": "in",
                                    "protocol": "tcp",
                                    "port": "22",
                                    "source_ips": ["203.0.113.5/32"],
                                }
                            ],
                            "applied_to": [
                                {"type": "server", "server": {"id": 7}},
                            ],
                        }
                    ]
                }
            )
        if parsed.path.endswith("/firewalls/41/actions/set_rules"):
            seen_posts.append((parsed.path, body))
            return _Response({"action": {"id": 201}})
        raise AssertionError((request.method, parsed.path, body))

    result = hetzner_cloud.apply_cloud_safeguards(
        "secret-token",
        server_id=7,
        confirm_server_id=7,
        access_mode=hetzner_cloud.ACCESS_MODE_TAILSCALE_ONLY,
        open_url=_open,
    )

    assert result["applied"] == [
        {"id": "set_tailscale_only_firewall_rules", "action_ids": [201]},
    ]
    assert seen_posts == [
        (
            "/v1/firewalls/41/actions/set_rules",
            {"rules": []},
        )
    ]


def test_cloud_safeguard_apply_corrects_existing_named_firewall_rules() -> None:
    seen_posts = []

    def _open(request, *, timeout, context):
        parsed = urllib.parse.urlsplit(request.full_url)
        body = json.loads(request.data.decode("utf-8")) if request.data else None
        if parsed.path.endswith("/servers/7") and request.method == "GET":
            return _Response(
                {
                    "server": {
                        "id": 7,
                        "name": "paper-host",
                        "status": "running",
                        "backup_window": "22-02",
                        "protection": {"delete": True, "rebuild": True},
                    }
                }
            )
        if parsed.path.endswith("/firewalls") and request.method == "GET":
            return _Response(
                {
                    "firewalls": [
                        {
                            "id": 41,
                            "name": hetzner_cloud.SSH_FIREWALL_NAME,
                            "rules": [
                                {
                                    "direction": "in",
                                    "protocol": "tcp",
                                    "port": "22",
                                    "source_ips": ["203.0.113.5/32"],
                                }
                            ],
                            "applied_to": [
                                {"type": "server", "server": {"id": 7}},
                            ],
                        }
                    ]
                }
            )
        if parsed.path.endswith("/firewalls/41/actions/set_rules"):
            seen_posts.append((parsed.path, body))
            return _Response({"action": {"id": 201}})
        raise AssertionError((request.method, parsed.path, body))

    result = hetzner_cloud.apply_cloud_safeguards(
        "secret-token",
        server_id=7,
        confirm_server_id=7,
        ssh_source_cidrs=["198.51.100.7/32"],
        open_url=_open,
    )

    assert result["applied"] == [
        {"id": "set_ssh_firewall_rules", "action_ids": [201]},
    ]
    assert seen_posts == [
        (
            "/v1/firewalls/41/actions/set_rules",
            {
                "rules": [
                    {
                        "description": "CryptKeep SSH administration",
                        "direction": "in",
                        "port": "22",
                        "protocol": "tcp",
                        "source_ips": ["198.51.100.7/32"],
                    }
                ]
            },
        )
    ]


def test_cloud_safeguard_cli_apply_requires_confirmation(monkeypatch, capsys) -> None:
    monkeypatch.setattr(safeguards_script, "get_hetzner_api_token", lambda: "token")

    code = safeguards_script.main(
        ["--server-id", "7", "--ssh-source-cidr", "198.51.100.7/32", "--apply"]
    )

    assert code == 1
    assert json.loads(capsys.readouterr().out) == {
        "ok": False,
        "reason": "confirm_server_id_required",
    }
