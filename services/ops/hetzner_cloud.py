from __future__ import annotations

import json
import ipaddress
import ssl
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

import certifi

API_BASE = "https://api.hetzner.cloud/v1"
RESOURCE_PATHS = {
    "servers": "/servers",
    "firewalls": "/firewalls",
    "networks": "/networks",
    "primary_ips": "/primary_ips",
    "ssh_keys": "/ssh_keys",
    "volumes": "/volumes",
}

OpenUrl = Callable[..., Any]
SSH_FIREWALL_NAME = "cryptkeep-paper-ssh-only"
TAILSCALE_ONLY_FIREWALL_NAME = "cryptkeep-tailscale-only"
ACCESS_MODE_CIDR_SSH = "cidr_ssh"
ACCESS_MODE_TAILSCALE_ONLY = "tailscale_only"
ACCESS_MODES = {ACCESS_MODE_CIDR_SSH, ACCESS_MODE_TAILSCALE_ONLY}


class HetznerCloudError(RuntimeError):
    pass


def _tls_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def _get_json(
    path: str,
    *,
    token: str,
    open_url: OpenUrl = urllib.request.urlopen,
    timeout_sec: float = 15.0,
) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{API_BASE}{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "CryptKeep-Hetzner-Audit/1.0",
        },
        method="GET",
    )
    try:
        with open_url(
            request,
            timeout=float(timeout_sec),
            context=_tls_context(),
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise HetznerCloudError(f"hetzner_http_error:{int(exc.code)}") from None
    except urllib.error.URLError:
        raise HetznerCloudError("hetzner_network_error") from None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise HetznerCloudError("hetzner_response_invalid") from None
    if not isinstance(payload, dict):
        raise HetznerCloudError("hetzner_response_not_object")
    return payload


def _request_json(
    method: str,
    path: str,
    *,
    token: str,
    body: dict[str, Any] | None = None,
    open_url: OpenUrl = urllib.request.urlopen,
    timeout_sec: float = 15.0,
) -> dict[str, Any]:
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "CryptKeep-Hetzner-Audit/1.0",
    }
    if body is not None:
        data = json.dumps(body, sort_keys=True).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers=headers,
        method=str(method).upper(),
    )
    try:
        with open_url(
            request,
            timeout=float(timeout_sec),
            context=_tls_context(),
        ) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        raise HetznerCloudError(f"hetzner_http_error:{int(exc.code)}") from None
    except urllib.error.URLError:
        raise HetznerCloudError("hetzner_network_error") from None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise HetznerCloudError("hetzner_response_invalid") from None
    if not isinstance(payload, dict):
        raise HetznerCloudError("hetzner_response_not_object")
    return payload


def _server_summary(server: dict[str, Any]) -> dict[str, object]:
    server_type = server.get("server_type")
    datacenter = server.get("datacenter")
    location = datacenter.get("location") if isinstance(datacenter, dict) else None
    return {
        "id": server.get("id"),
        "name": str(server.get("name") or ""),
        "status": str(server.get("status") or "unknown"),
        "server_type": (
            str(server_type.get("name") or "")
            if isinstance(server_type, dict)
            else ""
        ),
        "location": (
            str(location.get("name") or "") if isinstance(location, dict) else ""
        ),
    }


def _server_id(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value or "").strip())
    except ValueError:
        return None


def _server_detail(server: dict[str, Any]) -> dict[str, object]:
    protection = server.get("protection")
    if not isinstance(protection, dict):
        protection = {}
    return {
        **_server_summary(server),
        "backup_window": server.get("backup_window"),
        "protection": {
            "delete": bool(protection.get("delete")),
            "rebuild": bool(protection.get("rebuild")),
        },
    }


def _normalize_ssh_source_cidrs(source_cidrs: list[str] | None) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for item in source_cidrs or []:
        text = str(item).strip()
        if not text:
            continue
        try:
            network = ipaddress.ip_network(text, strict=False)
        except ValueError:
            raise HetznerCloudError("ssh_source_cidr_invalid") from None
        if network.prefixlen == 0:
            raise HetznerCloudError("ssh_source_cidr_too_broad")
        normalized = str(network)
        if normalized not in seen:
            values.append(normalized)
            seen.add(normalized)
    return values


def _normalize_access_mode(value: str | None) -> str:
    mode = str(value or ACCESS_MODE_CIDR_SSH).strip().lower().replace("-", "_")
    if mode not in ACCESS_MODES:
        raise HetznerCloudError("hetzner_access_mode_invalid")
    return mode


def _ssh_firewall_rules(source_cidrs: list[str]) -> list[dict[str, Any]]:
    cidrs = _normalize_ssh_source_cidrs(source_cidrs)
    return [
        {
            "direction": "in",
            "protocol": "tcp",
            "port": "22",
            "source_ips": cidrs,
            "description": "CryptKeep SSH administration",
        }
    ]


def _ssh_firewall_rules_match(
    firewall: dict[str, Any],
    source_cidrs: list[str],
) -> bool:
    expected = _ssh_firewall_rules(source_cidrs)
    rules = firewall.get("rules")
    if not isinstance(rules, list) or len(rules) != len(expected):
        return False
    rule = rules[0]
    if not isinstance(rule, dict):
        return False
    expected_rule = expected[0]
    return (
        rule.get("direction") == expected_rule["direction"]
        and rule.get("protocol") == expected_rule["protocol"]
        and str(rule.get("port") or "") == expected_rule["port"]
        and set(rule.get("source_ips") or []) == set(expected_rule["source_ips"])
    )


def _tailscale_only_firewall_rules_match(firewall: dict[str, Any]) -> bool:
    rules = firewall.get("rules")
    return isinstance(rules, list) and len(rules) == 0


def _is_firewall_attached_to_server(firewall: dict[str, Any], server_id: int) -> bool:
    applied_to = firewall.get("applied_to")
    if not isinstance(applied_to, list):
        return False
    for item in applied_to:
        if not isinstance(item, dict) or item.get("type") != "server":
            continue
        server = item.get("server")
        if isinstance(server, dict) and _server_id(server.get("id")) == server_id:
            return True
    return False


def _get_collection(
    name: str,
    path: str,
    *,
    token: str,
    open_url: OpenUrl,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    page = 1
    while True:
        separator = "&" if "?" in path else "?"
        payload = _get_json(
            f"{path}{separator}page={page}&per_page=50",
            token=token,
            open_url=open_url,
        )
        current = payload.get(name)
        if not isinstance(current, list):
            raise HetznerCloudError(f"hetzner_{name}_response_invalid")
        rows.extend(row for row in current if isinstance(row, dict))

        meta = payload.get("meta")
        pagination = meta.get("pagination") if isinstance(meta, dict) else None
        next_page = (
            pagination.get("next_page") if isinstance(pagination, dict) else None
        )
        if next_page is None:
            return rows
        if (
            isinstance(next_page, bool)
            or not isinstance(next_page, int)
            or next_page <= page
            or next_page > 1000
        ):
            raise HetznerCloudError(f"hetzner_{name}_pagination_invalid")
        page = next_page


def read_project_inventory(
    token: str,
    *,
    open_url: OpenUrl = urllib.request.urlopen,
) -> dict[str, Any]:
    value = str(token or "").strip()
    if not value:
        raise HetznerCloudError("hetzner_token_missing")

    resources: dict[str, list[dict[str, Any]]] = {}
    for name, path in RESOURCE_PATHS.items():
        resources[name] = _get_collection(
            name,
            path,
            token=value,
            open_url=open_url,
        )

    return {
        "ok": True,
        "access_mode": "read_only_operations",
        "resource_counts": {
            name: len(rows) for name, rows in sorted(resources.items())
        },
        "servers": [_server_summary(row) for row in resources["servers"]],
    }


def plan_cloud_safeguards(
    token: str,
    *,
    server_id: int,
    ssh_source_cidrs: list[str] | None = None,
    access_mode: str = ACCESS_MODE_CIDR_SSH,
    open_url: OpenUrl = urllib.request.urlopen,
) -> dict[str, Any]:
    value = str(token or "").strip()
    if not value:
        raise HetznerCloudError("hetzner_token_missing")
    if not isinstance(server_id, int) or server_id <= 0:
        raise HetznerCloudError("hetzner_server_id_invalid")
    mode = _normalize_access_mode(access_mode)
    cidrs = _normalize_ssh_source_cidrs(ssh_source_cidrs)
    if mode == ACCESS_MODE_CIDR_SSH and not cidrs:
        return {
            "ok": False,
            "ready_to_apply": False,
            "reason": "ssh_source_cidr_required",
            "changes": [],
        }
    if mode == ACCESS_MODE_TAILSCALE_ONLY and cidrs:
        raise HetznerCloudError("ssh_source_cidr_not_allowed_for_tailscale_only")

    server_payload = _get_json(f"/servers/{server_id}", token=value, open_url=open_url)
    server = server_payload.get("server")
    if not isinstance(server, dict):
        raise HetznerCloudError("hetzner_server_response_invalid")
    firewalls = _get_collection(
        "firewalls",
        "/firewalls",
        token=value,
        open_url=open_url,
    )
    firewall_name = (
        TAILSCALE_ONLY_FIREWALL_NAME
        if mode == ACCESS_MODE_TAILSCALE_ONLY
        else SSH_FIREWALL_NAME
    )
    named_firewall = next(
        (
            firewall
            for firewall in firewalls
            if str(firewall.get("name") or "") == firewall_name
        ),
        None,
    )
    protection = _server_detail(server)["protection"]
    backup_window = server.get("backup_window")
    firewall_attached = (
        _is_firewall_attached_to_server(named_firewall, server_id)
        if isinstance(named_firewall, dict)
        else False
    )

    changes: list[dict[str, Any]] = []
    if named_firewall is None:
        if mode == ACCESS_MODE_TAILSCALE_ONLY:
            changes.append(
                {
                    "id": "create_tailscale_only_firewall",
                    "method": "POST",
                    "path": "/firewalls",
                    "needed": True,
                    "name": TAILSCALE_ONLY_FIREWALL_NAME,
                    "rules": [],
                    "attach_to_server_id": server_id,
                }
            )
        else:
            changes.append(
                {
                    "id": "create_ssh_firewall",
                    "method": "POST",
                    "path": "/firewalls",
                    "needed": True,
                    "name": SSH_FIREWALL_NAME,
                    "source_ips": cidrs,
                    "attach_to_server_id": server_id,
                }
            )
    else:
        if mode == ACCESS_MODE_TAILSCALE_ONLY:
            rules_match = _tailscale_only_firewall_rules_match(named_firewall)
            drift_id = "set_tailscale_only_firewall_rules"
            current_id = "tailscale_only_firewall_rules_current"
        else:
            rules_match = _ssh_firewall_rules_match(named_firewall, cidrs)
            drift_id = "set_ssh_firewall_rules"
            current_id = "ssh_firewall_rules_current"
        if not rules_match:
            change: dict[str, Any] = {
                "id": drift_id,
                "method": "POST",
                "path": f"/firewalls/{named_firewall.get('id')}/actions/set_rules",
                "needed": True,
                "firewall_id": named_firewall.get("id"),
            }
            if mode == ACCESS_MODE_TAILSCALE_ONLY:
                change["rules"] = []
            else:
                change["source_ips"] = cidrs
            changes.append(
                change
            )
        else:
            changes.append({"id": current_id, "needed": False})

    if named_firewall is not None and not firewall_attached:
        attach_id = (
            "attach_tailscale_only_firewall"
            if mode == ACCESS_MODE_TAILSCALE_ONLY
            else "attach_ssh_firewall"
        )
        changes.append(
            {
                "id": attach_id,
                "method": "POST",
                "path": f"/firewalls/{named_firewall.get('id')}/actions/apply_to_resources",
                "needed": True,
                "firewall_id": named_firewall.get("id"),
                "attach_to_server_id": server_id,
            }
        )
    elif named_firewall is not None:
        attached_id = (
            "tailscale_only_firewall_attached"
            if mode == ACCESS_MODE_TAILSCALE_ONLY
            else "ssh_firewall_attached"
        )
        changes.append({"id": attached_id, "needed": False})

    if not (
        isinstance(protection, dict)
        and bool(protection.get("delete"))
        and bool(protection.get("rebuild"))
    ):
        changes.append(
            {
                "id": "enable_delete_rebuild_protection",
                "method": "POST",
                "path": f"/servers/{server_id}/actions/change_protection",
                "needed": True,
            }
        )
    else:
        changes.append({"id": "delete_rebuild_protection_enabled", "needed": False})

    if not backup_window:
        changes.append(
            {
                "id": "enable_backups",
                "method": "POST",
                "path": f"/servers/{server_id}/actions/enable_backup",
                "needed": True,
            }
        )
    else:
        changes.append({"id": "backups_enabled", "needed": False})

    return {
        "ok": True,
        "server": _server_detail(server),
        "ready_to_apply": True,
        "access_mode": mode,
        "firewall_name": firewall_name,
        "ssh_source_cidrs": cidrs,
        "changes": changes,
        "changes_needed": [row for row in changes if bool(row.get("needed"))],
    }


def apply_cloud_safeguards(
    token: str,
    *,
    server_id: int,
    confirm_server_id: int,
    ssh_source_cidrs: list[str] | None = None,
    access_mode: str = ACCESS_MODE_CIDR_SSH,
    open_url: OpenUrl = urllib.request.urlopen,
) -> dict[str, Any]:
    if confirm_server_id != server_id:
        raise HetznerCloudError("confirm_server_id_mismatch")
    plan = plan_cloud_safeguards(
        token,
        server_id=server_id,
        ssh_source_cidrs=ssh_source_cidrs,
        access_mode=access_mode,
        open_url=open_url,
    )
    if not bool(plan.get("ok")):
        return plan

    cidrs = _normalize_ssh_source_cidrs(
        [str(item) for item in plan.get("ssh_source_cidrs", [])]
    )
    applied: list[dict[str, Any]] = []
    for change in plan.get("changes_needed", []):
        change_id = str(change.get("id") or "")
        if change_id == "create_ssh_firewall":
            response = _request_json(
                "POST",
                "/firewalls",
                token=token,
                body={
                    "name": SSH_FIREWALL_NAME,
                    "rules": _ssh_firewall_rules(cidrs),
                    "apply_to": [
                        {"type": "server", "server": {"id": server_id}},
                    ],
                },
                open_url=open_url,
            )
            firewall = response.get("firewall")
            applied.append(
                {
                    "id": change_id,
                    "firewall_id": (
                        firewall.get("id") if isinstance(firewall, dict) else None
                    ),
                    "action_ids": _action_ids(response),
                }
            )
        elif change_id == "create_tailscale_only_firewall":
            response = _request_json(
                "POST",
                "/firewalls",
                token=token,
                body={
                    "name": TAILSCALE_ONLY_FIREWALL_NAME,
                    "rules": [],
                    "apply_to": [
                        {"type": "server", "server": {"id": server_id}},
                    ],
                },
                open_url=open_url,
            )
            firewall = response.get("firewall")
            applied.append(
                {
                    "id": change_id,
                    "firewall_id": (
                        firewall.get("id") if isinstance(firewall, dict) else None
                    ),
                    "action_ids": _action_ids(response),
                }
            )
        elif change_id == "set_ssh_firewall_rules":
            firewall_id = _server_id(change.get("firewall_id"))
            if firewall_id is None:
                raise HetznerCloudError("hetzner_firewall_id_invalid")
            response = _request_json(
                "POST",
                f"/firewalls/{firewall_id}/actions/set_rules",
                token=token,
                body={"rules": _ssh_firewall_rules(cidrs)},
                open_url=open_url,
            )
            applied.append({"id": change_id, "action_ids": _action_ids(response)})
        elif change_id == "set_tailscale_only_firewall_rules":
            firewall_id = _server_id(change.get("firewall_id"))
            if firewall_id is None:
                raise HetznerCloudError("hetzner_firewall_id_invalid")
            response = _request_json(
                "POST",
                f"/firewalls/{firewall_id}/actions/set_rules",
                token=token,
                body={"rules": []},
                open_url=open_url,
            )
            applied.append({"id": change_id, "action_ids": _action_ids(response)})
        elif change_id == "attach_ssh_firewall":
            firewall_id = _server_id(change.get("firewall_id"))
            if firewall_id is None:
                raise HetznerCloudError("hetzner_firewall_id_invalid")
            response = _request_json(
                "POST",
                f"/firewalls/{firewall_id}/actions/apply_to_resources",
                token=token,
                body={
                    "apply_to": [
                        {"type": "server", "server": {"id": server_id}},
                    ],
                },
                open_url=open_url,
            )
            applied.append({"id": change_id, "action_ids": _action_ids(response)})
        elif change_id == "attach_tailscale_only_firewall":
            firewall_id = _server_id(change.get("firewall_id"))
            if firewall_id is None:
                raise HetznerCloudError("hetzner_firewall_id_invalid")
            response = _request_json(
                "POST",
                f"/firewalls/{firewall_id}/actions/apply_to_resources",
                token=token,
                body={
                    "apply_to": [
                        {"type": "server", "server": {"id": server_id}},
                    ],
                },
                open_url=open_url,
            )
            applied.append({"id": change_id, "action_ids": _action_ids(response)})
        elif change_id == "enable_delete_rebuild_protection":
            response = _request_json(
                "POST",
                f"/servers/{server_id}/actions/change_protection",
                token=token,
                body={"delete": True, "rebuild": True},
                open_url=open_url,
            )
            applied.append({"id": change_id, "action_ids": _action_ids(response)})
        elif change_id == "enable_backups":
            response = _request_json(
                "POST",
                f"/servers/{server_id}/actions/enable_backup",
                token=token,
                body={},
                open_url=open_url,
            )
            applied.append({"id": change_id, "action_ids": _action_ids(response)})
        else:
            raise HetznerCloudError(f"unsupported_change:{change_id}")

    return {
        "ok": True,
        "server_id": server_id,
        "applied": applied,
        "applied_count": len(applied),
    }


def _action_ids(response: dict[str, Any]) -> list[int]:
    values: list[int] = []
    action = response.get("action")
    if isinstance(action, dict):
        action_id = _server_id(action.get("id"))
        if action_id is not None:
            values.append(action_id)
    actions = response.get("actions")
    if isinstance(actions, list):
        for item in actions:
            if isinstance(item, dict):
                action_id = _server_id(item.get("id"))
                if action_id is not None:
                    values.append(action_id)
    return values
