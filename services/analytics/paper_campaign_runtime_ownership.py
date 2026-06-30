from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.analytics.paper_campaign_ownership import DEFAULT_EXPECTED_OWNERS

HOSTS = ("laptop", "hetzner")


def load_status_payload(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("paper campaign status payload must be an object")
    return payload


def _normalize_state_dir(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.startswith(".cbp_state"):
        return raw
    marker = "/.cbp_state"
    idx = raw.find(marker)
    if idx >= 0:
        return raw[idx + 1 :]
    return raw


def _as_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number or None


def _status_rows(
    *,
    host: str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in list(payload.get("campaigns") or []):
        if not isinstance(raw, dict):
            continue
        state_dir = str(raw.get("state_dir") or "").strip()
        rows.append(
            {
                "host": host,
                "name": str(raw.get("name") or "").strip(),
                "strategy": str(raw.get("strategy") or "").strip(),
                "session_strategy_id": str(raw.get("session_strategy_id") or "").strip(),
                "state_dir": state_dir,
                "normalized_state_dir": _normalize_state_dir(state_dir),
                "running": bool(raw.get("running")),
                "ok": bool(raw.get("ok")),
                "status": str(raw.get("status") or "unknown"),
                "reason": str(raw.get("reason") or ""),
                "pid": _as_int(raw.get("pid")),
                "last_completed_day": raw.get("last_completed_day"),
            }
        )
    return rows


def _duplicates(
    rows: list[dict[str, Any]],
    *,
    field: str,
) -> list[dict[str, Any]]:
    seen: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        value = str(row.get(field) or "").strip()
        if not value:
            continue
        seen.setdefault(value, []).append(
            {
                "host": row.get("host"),
                "campaign": row.get("name"),
                "pid": row.get("pid"),
                "state_dir": row.get("state_dir"),
            }
        )
    return [
        {
            "field": field,
            "value": value,
            "owners": owners,
        }
        for value, owners in sorted(seen.items())
        if len(owners) > 1
    ]


def _expected_owner_checks(
    rows: list[dict[str, Any]],
    expected_owners: dict[str, str],
) -> list[dict[str, Any]]:
    running_by_name: dict[str, list[str]] = {}
    for row in rows:
        if not bool(row.get("running")):
            continue
        name = str(row.get("name") or "").strip()
        host = str(row.get("host") or "").strip()
        if name and host:
            running_by_name.setdefault(name, []).append(host)

    mismatches: list[dict[str, Any]] = []
    for campaign, expected_host in sorted(expected_owners.items()):
        actual_hosts = sorted(set(running_by_name.get(campaign, [])))
        if not actual_hosts:
            mismatches.append(
                {
                    "campaign": campaign,
                    "expected_host": expected_host,
                    "actual_hosts": [],
                    "reason": "expected_campaign_not_running",
                }
            )
        elif actual_hosts != [expected_host]:
            mismatches.append(
                {
                    "campaign": campaign,
                    "expected_host": expected_host,
                    "actual_hosts": actual_hosts,
                    "reason": "unexpected_runtime_owner",
                }
            )
    return mismatches


def build_paper_campaign_runtime_ownership_report(
    *,
    laptop_status: dict[str, Any],
    hetzner_status: dict[str, Any],
    expected_owners: dict[str, str] | None = None,
) -> dict[str, Any]:
    expected = dict(expected_owners or DEFAULT_EXPECTED_OWNERS)
    host_payloads = {
        "laptop": dict(laptop_status),
        "hetzner": dict(hetzner_status),
    }
    rows = [
        row
        for host, payload in host_payloads.items()
        for row in _status_rows(host=host, payload=payload)
    ]
    running_rows = [row for row in rows if bool(row.get("running"))]

    host_blockers = [
        f"{host} status payload is not ok."
        for host, payload in host_payloads.items()
        if not bool(payload.get("ok"))
    ]
    conflicts = (
        _duplicates(running_rows, field="name")
        + _duplicates(running_rows, field="session_strategy_id")
        + _duplicates(running_rows, field="normalized_state_dir")
    )
    owner_mismatches = _expected_owner_checks(running_rows, expected)
    blockers = [
        *host_blockers,
        *[
            f"Duplicate running {item['field']} `{item['value']}` across hosts."
            for item in conflicts
        ],
        *[
            f"Campaign `{item['campaign']}` runtime owner mismatch: expected "
            f"{item['expected_host']}, got {item['actual_hosts']}."
            for item in owner_mismatches
        ],
    ]
    ok = not blockers
    return {
        "ok": ok,
        "status": "runtime_single_owner_ready" if ok else "runtime_single_owner_blocked",
        "read_only": True,
        "restore_invoked": False,
        "ssh_invoked": False,
        "status_payload_only": True,
        "expected_owners": expected,
        "hosts": {
            host: {
                "ok": bool(payload.get("ok")),
                "all_running": bool(payload.get("all_running")),
                "campaign_count": int(payload.get("campaign_count") or 0),
                "running_count": int(payload.get("running_count") or 0),
            }
            for host, payload in host_payloads.items()
        },
        "campaigns": rows,
        "running_campaigns": running_rows,
        "conflicts": conflicts,
        "expected_owner_mismatches": owner_mismatches,
        "blockers": blockers,
        "recommendations": _recommendations(ok),
    }


def _recommendations(ok: bool) -> list[str]:
    if ok:
        return [
            "Use this as runtime duplicate-process proof for captured status payloads.",
            "Still collect fresh laptop and Hetzner status immediately before migration.",
            "Do not start copied state on another host until this report stays ok.",
        ]
    return [
        "Stop state-transfer planning until runtime ownership blockers are resolved.",
        "Do not run laptop and Hetzner collectors for the same campaign state.",
    ]
