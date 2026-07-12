from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.edge_cadence import check_edge_cadence
from services.analytics.paper_campaign_recovery import load_campaign_specs
from services.execution.ohlcv_preflight import check_ohlcv_reachable
from services.os.app_paths import code_root, data_dir
from services.os.file_utils import atomic_write
from services.strategies.config_tools import apply_preset_and_validate, supported_strategies
from services.strategies.crypto_edge_context import funding_context_from_crypto_edge_store
from services.strategies.presets import PRESETS
from services.strategies.strategy_registry import SUPPORTED as REGISTRY_SUPPORTED

REPORT_TYPE = "funding_stage0_readiness"
STRATEGY = "funding_extreme"
SESSION_STRATEGY_ID = "funding_extreme_default"
SYMBOL = "BTC/USDT"
VENUE = "coinbase"
SIGNAL_SOURCE = "public_ohlcv_5m"
CONTEXT_SYMBOL = "BTC/USDT:USDT"
CONTEXT_VENUE = "okx"
CONTEXT_SOURCE = "live_public"
RUNTIME_SEC = 900
STRATEGY_DRAIN_SEC = 2
STATE_DIR_REL = ".cbp_state_challengers/funding_extreme_default"
DEFAULT_LAPTOP_MANIFEST = code_root() / "configs" / "paper_evidence_campaigns.laptop.json"
DEFAULT_HETZNER_MANIFEST = code_root() / "configs" / "paper_evidence_campaigns.hetzner.example.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_stamp() -> str:
    return _now_iso().replace(":", "").replace("+", "Z")


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _check(name: str, ok: bool, detail: str, *, required: bool = True) -> dict[str, Any]:
    return {
        "name": name,
        "ok": bool(ok),
        "required": bool(required),
        "detail": detail,
    }


def _proof_argv(
    *,
    status: bool = False,
    symbol: str = SYMBOL,
    venue: str = VENUE,
    signal_source: str = SIGNAL_SOURCE,
    context_symbol: str = CONTEXT_SYMBOL,
    context_venue: str = CONTEXT_VENUE,
) -> list[str]:
    argv = ["./.venv/bin/python", "scripts/run_paper_strategy_evidence_collector.py"]
    if status:
        return [*argv, "--status"]
    return [
        *argv,
        "--strategies",
        STRATEGY,
        "--session-strategy-id",
        SESSION_STRATEGY_ID,
        "--symbol",
        symbol,
        "--venue",
        venue,
        "--signal-source",
        signal_source,
        "--strategy-context-symbol",
        context_symbol,
        "--strategy-context-venue",
        context_venue,
        "--runtime-sec",
        str(RUNTIME_SEC),
        "--strategy-drain-sec",
        str(STRATEGY_DRAIN_SEC),
    ]


def _shell(argv: list[str]) -> str:
    return f'CBP_STATE_DIR="$PWD/{STATE_DIR_REL}" ' + " ".join(argv)


def _manifest_rows(*, root: Path, manifests: dict[str, Path]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for host, manifest_path in manifests.items():
        if not manifest_path.exists():
            errors.append(
                {
                    "type": "missing_manifest",
                    "host_owner": host,
                    "manifest_path": _rel(manifest_path, root),
                }
            )
            continue
        try:
            specs = load_campaign_specs(manifest_path, repo_root=root)
        except Exception as exc:
            errors.append(
                {
                    "type": "invalid_manifest",
                    "host_owner": host,
                    "manifest_path": _rel(manifest_path, root),
                    "reason": f"{type(exc).__name__}:{exc}",
                }
            )
            continue
        for spec in specs:
            rows.append(
                {
                    "host_owner": host,
                    "manifest_path": _rel(manifest_path, root),
                    "name": spec.name,
                    "state_dir": _rel(spec.state_dir, root),
                    "strategy": spec.strategy,
                    "session_strategy_id": spec.session_strategy_id,
                    "symbol": spec.symbol,
                    "venue": spec.venue,
                    "signal_source": spec.signal_source,
                }
            )
    return rows, errors


def _campaign_conflicts(
    rows: list[dict[str, Any]],
    *,
    symbol: str = SYMBOL,
    venue: str = VENUE,
) -> list[dict[str, str]]:
    conflicts: list[dict[str, str]] = []
    planned_owner = (STRATEGY, SESSION_STRATEGY_ID, str(symbol or "").upper(), str(venue or "").lower())
    for row in rows:
        row_owner = (
            str(row.get("strategy") or ""),
            str(row.get("session_strategy_id") or ""),
            str(row.get("symbol") or "").upper(),
            str(row.get("venue") or "").lower(),
        )
        if str(row.get("name") or "") == SESSION_STRATEGY_ID:
            conflicts.append({"type": "campaign_name_conflict", "campaign": str(row.get("name") or "")})
        if str(row.get("session_strategy_id") or "") == SESSION_STRATEGY_ID:
            conflicts.append({"type": "session_strategy_id_conflict", "campaign": str(row.get("name") or "")})
        if str(row.get("state_dir") or "") == STATE_DIR_REL:
            conflicts.append({"type": "state_dir_conflict", "campaign": str(row.get("name") or "")})
        if row_owner == planned_owner:
            conflicts.append(
                {
                    "type": "strategy_session_symbol_venue_conflict",
                    "campaign": str(row.get("name") or ""),
                }
            )
    return conflicts


def _collector_explicit_session_id_ok() -> tuple[bool, str]:
    try:
        from scripts import run_paper_strategy_evidence_collector as collector

        actual = collector._session_strategy_id(strategies=(STRATEGY,), override=SESSION_STRATEGY_ID)
    except Exception as exc:
        return False, f"collector_session_lookup_failed:{type(exc).__name__}:{exc}"
    return actual == SESSION_STRATEGY_ID, f"expected={SESSION_STRATEGY_ID} actual={actual}"


def build_funding_stage0_readiness(
    *,
    repo_root: Path | None = None,
    laptop_manifest: Path = DEFAULT_LAPTOP_MANIFEST,
    hetzner_manifest: Path = DEFAULT_HETZNER_MANIFEST,
    run_ohlcv_preflight: bool = True,
    symbol: str = SYMBOL,
    venue: str = VENUE,
    signal_source: str = SIGNAL_SOURCE,
    context_symbol: str = CONTEXT_SYMBOL,
    context_venue: str = CONTEXT_VENUE,
    context_source: str = CONTEXT_SOURCE,
) -> dict[str, Any]:
    root = (repo_root or code_root()).resolve()
    symbol = str(symbol or SYMBOL).strip() or SYMBOL
    venue = str(venue or VENUE).strip() or VENUE
    signal_source = str(signal_source or SIGNAL_SOURCE).strip() or SIGNAL_SOURCE
    context_symbol = str(context_symbol or CONTEXT_SYMBOL).strip() or CONTEXT_SYMBOL
    context_venue = str(context_venue or CONTEXT_VENUE).strip() or CONTEXT_VENUE
    context_source = str(context_source or CONTEXT_SOURCE).strip() or CONTEXT_SOURCE
    state_dir = (root / STATE_DIR_REL).resolve()
    canonical_state_dir = (root / ".cbp_state").resolve()
    manifests = {
        "laptop": Path(laptop_manifest),
        "hetzner": Path(hetzner_manifest),
    }
    configured, validation = apply_preset_and_validate({}, SESSION_STRATEGY_ID)
    manifest_rows, manifest_errors = _manifest_rows(root=root, manifests=manifests)
    conflicts = _campaign_conflicts(manifest_rows, symbol=symbol, venue=venue)
    collector_ok, collector_detail = _collector_explicit_session_id_ok()
    proof_argv = _proof_argv(
        symbol=symbol,
        venue=venue,
        signal_source=signal_source,
        context_symbol=context_symbol,
        context_venue=context_venue,
    )
    status_argv = _proof_argv(status=True)
    ohlcv = (
        check_ohlcv_reachable(
            venue=venue,
            symbol=symbol,
            signal_source=signal_source,
            probe_limit=5,
            attempts=3,
        )
        if run_ohlcv_preflight
        else {"ok": True, "status": "skipped", "reason": "run_ohlcv_preflight=false"}
    )
    edge_cadence = check_edge_cadence()
    funding_context = funding_context_from_crypto_edge_store(
        symbol=context_symbol,
        venue=context_venue,
        source=context_source,
    )

    checks = [
        _check(
            "strategy_module_exists",
            (root / "services" / "strategies" / "funding_extreme.py").exists(),
            "services/strategies/funding_extreme.py",
        ),
        _check("strategy_supported_by_config_tools", STRATEGY in supported_strategies(), STRATEGY),
        _check("strategy_supported_by_registry", STRATEGY in REGISTRY_SUPPORTED, STRATEGY),
        _check("preset_exists", SESSION_STRATEGY_ID in PRESETS, SESSION_STRATEGY_ID),
        _check("preset_validates", bool(validation.get("ok")), json.dumps(validation, sort_keys=True)),
        _check(
            "preset_resolves_strategy_name",
            configured.get("strategy", {}).get("name") == STRATEGY,
            STRATEGY,
        ),
        _check("collector_explicit_session_strategy_id", collector_ok, collector_detail),
        _check(
            "collector_script_exists",
            (root / "scripts" / "run_paper_strategy_evidence_collector.py").exists(),
            "scripts/run_paper_strategy_evidence_collector.py",
        ),
        _check(
            "stage0_command_is_one_shot",
            "--daily-loop" not in proof_argv and "--detach" not in proof_argv,
            "no daily-loop/detach flags",
        ),
        _check("state_dir_is_repo_relative", not Path(STATE_DIR_REL).is_absolute(), STATE_DIR_REL),
        _check(
            "state_dir_is_challenger_scoped",
            STATE_DIR_REL.startswith(".cbp_state_challengers/"),
            STATE_DIR_REL,
        ),
        _check("state_dir_is_not_canonical", state_dir != canonical_state_dir, _rel(state_dir, root)),
        _check("campaign_manifests_loaded", not manifest_errors, json.dumps(manifest_errors, sort_keys=True)),
        _check("campaign_manifests_do_not_own_stage0", not conflicts, json.dumps(conflicts, sort_keys=True)),
        _check("public_ohlcv_reachable", bool(ohlcv.get("ok")), json.dumps(ohlcv, sort_keys=True)),
        _check("edge_cadence_ready", bool(edge_cadence.get("ok")), json.dumps(edge_cadence, sort_keys=True)),
        _check(
            "funding_context_ready",
            bool(funding_context.get("ok")),
            json.dumps(funding_context, sort_keys=True, default=str),
        ),
    ]
    blocking = [check for check in checks if bool(check["required"]) and not bool(check["ok"])]
    return {
        "report_type": REPORT_TYPE,
        "generated_at": _now_iso(),
        "status": "ready_for_operator_stage0" if not blocking else "blocked",
        "ready": not blocking,
        "read_only": True,
        "strategy": STRATEGY,
        "session_strategy_id": SESSION_STRATEGY_ID,
        "symbol": symbol,
        "venue": venue,
        "signal_source": signal_source,
        "strategy_context_symbol": context_symbol,
        "strategy_context_venue": context_venue,
        "strategy_context_source": context_source,
        "runtime_sec": RUNTIME_SEC,
        "strategy_drain_sec": STRATEGY_DRAIN_SEC,
        "state_dir": STATE_DIR_REL,
        "state_dir_exists": state_dir.exists(),
        "ohlcv_preflight": ohlcv,
        "edge_cadence": edge_cadence,
        "funding_context": funding_context,
        "proof_command": {
            "environment": {"CBP_STATE_DIR": f"$PWD/{STATE_DIR_REL}"},
            "argv": proof_argv,
            "shell": _shell(proof_argv),
        },
        "status_command": {
            "environment": {"CBP_STATE_DIR": f"$PWD/{STATE_DIR_REL}"},
            "argv": status_argv,
            "shell": _shell(status_argv),
        },
        "checks": checks,
        "blocking_checks": blocking,
        "manifest_rows": manifest_rows,
        "manifest_errors": manifest_errors,
        "manifest_conflicts": conflicts,
        "safety": {
            "campaigns_started": False,
            "campaigns_stopped": False,
            "restore_invoked": False,
            "collector_invoked": False,
            "manifest_files_written": False,
            "state_dirs_created": False,
            "orders_routed": False,
            "live_trading_enabled": False,
        },
        "operator_next_step": "Run proof_command.shell only when ready for the 15-minute Stage 0 proof.",
    }


def _markdown(report: dict[str, Any]) -> str:
    checks = "\n".join(
        f"- [{'x' if bool(check.get('ok')) else ' '}] {check.get('name')}: {check.get('detail')}"
        for check in report.get("checks", [])
        if isinstance(check, dict)
    )
    return "\n".join(
        [
            "# Funding Extreme Stage 0 Readiness",
            "",
            f"- Generated: `{report.get('generated_at')}`",
            f"- Status: `{report.get('status')}`",
            f"- Read-only: `{bool(report.get('read_only'))}`",
            f"- Strategy: `{report.get('strategy')}`",
            f"- Evidence strategy ID: `{report.get('session_strategy_id')}`",
            f"- State dir: `{report.get('state_dir')}`",
            "",
            "## Checks",
            "",
            checks,
            "",
            "## Stage 0 Proof Command",
            "",
            "```bash",
            str(report.get("proof_command", {}).get("shell") or ""),
            "```",
            "",
            "## Status Command",
            "",
            "```bash",
            str(report.get("status_command", {}).get("shell") or ""),
            "```",
            "",
            "## Safety",
            "",
            "This report does not start collectors, stop collectors, restore campaigns, "
            "write manifests, create state directories, route orders, or enable live trading.",
            "",
        ]
    )


def write_funding_stage0_readiness(report: dict[str, Any]) -> dict[str, str]:
    out_dir = data_dir() / "funding_stage0_readiness"
    latest_json = out_dir / "funding_stage0_readiness.latest.json"
    latest_markdown = out_dir / "funding_stage0_readiness.latest.md"
    stamped_json = out_dir / f"funding_stage0_readiness.{_safe_stamp()}.json"
    stamped_markdown = out_dir / f"funding_stage0_readiness.{_safe_stamp()}.md"
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    md = _markdown(report)
    for path, content in (
        (latest_json, text),
        (stamped_json, text),
        (latest_markdown, md),
        (stamped_markdown, md),
    ):
        atomic_write(path, content)
    return {
        "latest_json": str(latest_json),
        "latest_markdown": str(latest_markdown),
        "stamped_json": str(stamped_json),
        "stamped_markdown": str(stamped_markdown),
    }
