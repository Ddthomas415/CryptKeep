from __future__ import annotations

import json
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
