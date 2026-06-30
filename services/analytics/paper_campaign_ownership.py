from __future__ import annotations

from pathlib import Path
from typing import Any

from services.analytics.paper_campaign_recovery import PaperCampaignSpec, load_campaign_specs
from services.os.app_paths import code_root

DEFAULT_LAPTOP_CONFIG = code_root() / "configs" / "paper_evidence_campaigns.laptop.json"
DEFAULT_HETZNER_CONFIG = code_root() / "configs" / "paper_evidence_campaigns.hetzner.example.json"

DEFAULT_EXPECTED_OWNERS = {
    "es_daily_trend_v1": "laptop",
    "breakout_default": "laptop",
    "ema_cross_default": "hetzner",
}


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def _load_manifest(
    *,
    host: str,
    config_path: Path,
    repo_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    try:
        specs = load_campaign_specs(config_path, repo_root=repo_root)
    except Exception as exc:
        return [], {
            "host": host,
            "config_path": str(config_path),
            "reason": f"invalid_manifest:{type(exc).__name__}",
        }
    rows = [
        _campaign_row(host=host, spec=spec, repo_root=repo_root, config_path=config_path)
        for spec in specs
    ]
    return rows, None


def _campaign_row(
    *,
    host: str,
    spec: PaperCampaignSpec,
    repo_root: Path,
    config_path: Path,
) -> dict[str, Any]:
    return {
        "host": host,
        "config_path": str(config_path),
        "name": spec.name,
        "strategy": spec.strategy,
        "session_strategy_id": spec.session_strategy_id,
        "symbol": spec.symbol,
        "venue": spec.venue,
        "signal_source": spec.signal_source,
        "state_dir": _rel(spec.state_dir, repo_root),
        "runtime_sec": float(spec.runtime_sec),
        "poll_interval_sec": float(spec.poll_interval_sec),
        "max_daily_attempts": int(spec.max_daily_attempts),
        "desktop_notify": bool(spec.desktop_notify),
    }


def _duplicates(
    rows: list[dict[str, Any]],
    *,
    field: str,
) -> list[dict[str, Any]]:
    seen: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        value = str(row.get(field) or "").strip()
        if not value:
            continue
        seen.setdefault(value, []).append(
            {
                "host": str(row.get("host") or ""),
                "campaign": str(row.get("name") or ""),
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
    by_name: dict[str, list[str]] = {}
    for row in rows:
        by_name.setdefault(str(row.get("name") or ""), []).append(str(row.get("host") or ""))

    mismatches: list[dict[str, Any]] = []
    for campaign, expected_host in sorted(expected_owners.items()):
        hosts = sorted({host for host in by_name.get(campaign, []) if host})
        if not hosts:
            mismatches.append(
                {
                    "campaign": campaign,
                    "expected_host": expected_host,
                    "actual_hosts": [],
                    "reason": "expected_campaign_missing",
                }
            )
        elif hosts != [expected_host]:
            mismatches.append(
                {
                    "campaign": campaign,
                    "expected_host": expected_host,
                    "actual_hosts": hosts,
                    "reason": "unexpected_owner",
                }
            )
    return mismatches


def _headless_hetzner_violations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "host": str(row.get("host") or ""),
            "campaign": str(row.get("name") or ""),
            "reason": "hetzner_desktop_notify_enabled",
        }
        for row in rows
        if str(row.get("host") or "") == "hetzner" and bool(row.get("desktop_notify"))
    ]


def build_paper_campaign_ownership_report(
    *,
    laptop_config: str | Path = DEFAULT_LAPTOP_CONFIG,
    hetzner_config: str | Path = DEFAULT_HETZNER_CONFIG,
    repo_root: str | Path | None = None,
    expected_owners: dict[str, str] | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).expanduser().resolve() if repo_root else code_root().resolve()
    manifests = {
        "laptop": Path(laptop_config).expanduser().resolve(),
        "hetzner": Path(hetzner_config).expanduser().resolve(),
    }
    expected = dict(expected_owners or DEFAULT_EXPECTED_OWNERS)

    rows: list[dict[str, Any]] = []
    manifest_errors: list[dict[str, Any]] = []
    for host, config_path in manifests.items():
        loaded, error = _load_manifest(host=host, config_path=config_path, repo_root=root)
        rows.extend(loaded)
        if error:
            manifest_errors.append(error)

    conflicts = (
        _duplicates(rows, field="name")
        + _duplicates(rows, field="session_strategy_id")
        + _duplicates(rows, field="state_dir")
    )
    expected_mismatches = _expected_owner_checks(rows, expected)
    headless_violations = _headless_hetzner_violations(rows)
    blockers = [
        *[f"{item['host']} manifest invalid: {item['reason']}" for item in manifest_errors],
        *[
            f"Duplicate {item['field']} `{item['value']}` across campaign manifests."
            for item in conflicts
        ],
        *[
            f"Campaign `{item['campaign']}` owner mismatch: expected "
            f"{item['expected_host']}, got {item['actual_hosts']}."
            for item in expected_mismatches
        ],
        *[
            f"Hetzner campaign `{item['campaign']}` has desktop notifications enabled."
            for item in headless_violations
        ],
    ]
    ok = not blockers
    return {
        "ok": ok,
        "status": "single_owner_ready" if ok else "single_owner_blocked",
        "read_only": True,
        "restore_invoked": False,
        "ssh_invoked": False,
        "repo_root": str(root),
        "manifests": {host: str(path) for host, path in manifests.items()},
        "expected_owners": expected,
        "campaigns": rows,
        "conflicts": conflicts,
        "expected_owner_mismatches": expected_mismatches,
        "headless_violations": headless_violations,
        "blockers": blockers,
        "recommendations": _recommendations(ok),
    }


def _recommendations(ok: bool) -> list[str]:
    if ok:
        return [
            "Use this as manifest-level single-owner proof only.",
            "Still verify running processes before any stop-copy-verify-start operation.",
            "Do not migrate canonical .cbp_state until backup restore proof is accepted.",
        ]
    return [
        "Fix manifest ownership conflicts before restore or state transfer.",
        "Do not run laptop and Hetzner collectors for the same campaign state.",
    ]
