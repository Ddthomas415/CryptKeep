from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.ai_copilot.policy import report_root
from services.admin.config_editor import load_user_yaml
from services.analytics.paper_strategy_evidence_service import load_runtime_status as load_campaign_runtime_status
from services.os.app_paths import config_dir, ensure_dirs, runtime_dir
from storage.paper_trading_sqlite import PaperTradingSQLite
from storage.trade_journal_sqlite import TradeJournalSQLite

logger = logging.getLogger(__name__)

MONITOR_NAME = "paper_sim_monitor"
WATCH_TRIGGERS = {
    "new_fill",
    "position_opened",
    "position_closed",
    "campaign_completed",
    "recommendation_investigate",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _flags_dir() -> Path:
    return runtime_dir() / "flags"


def _health_dir() -> Path:
    return runtime_dir() / "health"


def stop_file() -> Path:
    return _flags_dir() / f"{MONITOR_NAME}.stop"


def status_file() -> Path:
    return _health_dir() / f"{MONITOR_NAME}.json"


def pid_file() -> Path:
    return _health_dir() / f"{MONITOR_NAME}.pid.json"


def history_file() -> Path:
    return _health_dir() / f"{MONITOR_NAME}.history.jsonl"


def watches_file() -> Path:
    return config_dir() / f"{MONITOR_NAME}.watches.json"


def _write_status(obj: dict[str, Any]) -> None:
    ensure_dirs()
    _health_dir().mkdir(parents=True, exist_ok=True)
    status_file().write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_pid_state(obj: dict[str, Any]) -> None:
    ensure_dirs()
    _health_dir().mkdir(parents=True, exist_ok=True)
    pid_file().write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_history(obj: dict[str, Any]) -> None:
    ensure_dirs()
    _health_dir().mkdir(parents=True, exist_ok=True)
    with history_file().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, sort_keys=True, default=str) + "\n")


def _load_json(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")) or {})


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return []
    out: list[dict[str, Any]] = []
    for item in payload:
        if isinstance(item, dict):
            out.append(dict(item))
    return out


def _clear_pid_state() -> None:
    try:
        if pid_file().exists():
            pid_file().unlink()
    except Exception as exc:
        logger.warning(
            "paper_sim_monitor_pid_clear_failed",
            extra={"path": str(pid_file()), "error_type": type(exc).__name__},
        )


def _process_alive(pid: int) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return _load_json(path)
    except Exception:
        return {}


def _strategy_runner_status() -> dict[str, Any]:
    return _read_json_if_exists(runtime_dir() / "flags" / "strategy_runner.status.json")


def _paper_engine_status() -> dict[str, Any]:
    return _read_json_if_exists(runtime_dir() / "flags" / "paper_engine.status.json")


def _load_watches() -> list[dict[str, Any]]:
    if not watches_file().exists():
        return []
    try:
        rows = _read_json_list(watches_file())
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for row in rows:
        name = str(row.get("name") or "").strip()
        trigger = str(row.get("trigger") or "").strip()
        if not name or trigger not in WATCH_TRIGGERS:
            continue
        out.append(
            {
                "name": name,
                "trigger": trigger,
                "active": bool(row.get("active", True)),
                "created_at": str(row.get("created_at") or ""),
                "last_fired_at": str(row.get("last_fired_at") or ""),
                "last_event_key": str(row.get("last_event_key") or ""),
                "last_report_stem": str(row.get("last_report_stem") or ""),
            }
        )
    return out


def _save_watches(rows: list[dict[str, Any]]) -> None:
    ensure_dirs()
    config_dir().mkdir(parents=True, exist_ok=True)
    watches_file().write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def list_watches() -> list[dict[str, Any]]:
    return _load_watches()


def register_watch(*, name: str, trigger: str) -> dict[str, Any]:
    watch_name = str(name or "").strip()
    watch_trigger = str(trigger or "").strip()
    if not watch_name:
        return {"ok": False, "reason": "watch_name_required"}
    if watch_trigger not in WATCH_TRIGGERS:
        return {"ok": False, "reason": "invalid_trigger", "valid_triggers": sorted(WATCH_TRIGGERS)}
    rows = _load_watches()
    updated = False
    for row in rows:
        if str(row.get("name") or "").strip() == watch_name:
            row["trigger"] = watch_trigger
            row["active"] = True
            updated = True
            break
    if not updated:
        rows.append(
            {
                "name": watch_name,
                "trigger": watch_trigger,
                "active": True,
                "created_at": _now_iso(),
                "last_fired_at": "",
                "last_event_key": "",
                "last_report_stem": "",
            }
        )
    _save_watches(rows)
    return {
        "ok": True,
        "name": watch_name,
        "trigger": watch_trigger,
        "watch_count": len(rows),
        "watches_path": str(watches_file()),
    }


def delete_watch(*, name: str) -> dict[str, Any]:
    watch_name = str(name or "").strip()
    if not watch_name:
        return {"ok": False, "reason": "watch_name_required"}
    rows = _load_watches()
    kept = [row for row in rows if str(row.get("name") or "").strip() != watch_name]
    if len(kept) == len(rows):
        return {"ok": False, "reason": "watch_not_found", "name": watch_name}
    _save_watches(kept)
    return {"ok": True, "name": watch_name, "watch_count": len(kept), "watches_path": str(watches_file())}


def _configured_strategy_runner() -> dict[str, Any]:
    cfg = dict(load_user_yaml() or {})
    strategy_runner = dict(cfg.get("strategy_runner") or {})
    strategy = dict(strategy_runner.get("strategy") or {})
    raw_symbols = list(strategy_runner.get("symbols") or [])
    symbols = [str(item).strip() for item in raw_symbols if str(item).strip()]
    primary_symbol = str(strategy_runner.get("symbol") or "").strip()
    if primary_symbol and primary_symbol not in symbols:
        symbols.insert(0, primary_symbol)
    return {
        "strategy": str(strategy.get("name") or "").strip(),
        "symbols": symbols,
        "primary_symbol": symbols[0] if symbols else primary_symbol,
        "signal_source": str(strategy_runner.get("signal_source") or "").strip(),
        "venue": str(strategy_runner.get("venue") or "").strip(),
    }


def _paper_state_snapshot(symbol: str) -> dict[str, Any]:
    return _paper_state_snapshot_window(symbol, since_ts="")


def _iso_epoch(value: Any) -> float:
    raw = str(value or "").strip()
    if not raw:
        return 0.0
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _row_meets_since(row: dict[str, Any], *, since_epoch: float, keys: list[str]) -> bool:
    if since_epoch <= 0.0:
        return True
    for key in keys:
        value = _iso_epoch(row.get(key))
        if value > 0.0:
            return value >= since_epoch
    return False


def _paper_state_snapshot_window(symbol: str, *, since_ts: str = "") -> dict[str, Any]:
    store = PaperTradingSQLite()
    position = store.get_position(symbol) if symbol else None
    if position is None and not symbol:
        positions = list(store.list_positions(limit=1) or [])
        position = dict(positions[0]) if positions else {}
    since_epoch = _iso_epoch(since_ts)
    latest_order_rows = [
        dict(row)
        for row in list(store.list_orders(limit=500) or [])
        if not symbol or str(row.get("symbol") or "").strip() == str(symbol).strip()
        if _row_meets_since(row, since_epoch=since_epoch, keys=["created_ts", "ts"])
    ]
    latest_order = dict(latest_order_rows[0]) if latest_order_rows else {}
    latest_paper_fill: dict[str, Any] = {}
    for row in latest_order_rows:
        fills_for_order = list(store.list_fills_for_order(str(row.get("order_id") or ""), limit=2000) or [])
        matching_fills = [
            dict(fill)
            for fill in fills_for_order
            if _row_meets_since(dict(fill), since_epoch=since_epoch, keys=["ts"])
        ]
        if matching_fills:
            latest_paper_fill = dict(matching_fills[-1])
            break
    latest_equity_rows = list(store.list_equity(limit=1) or [])
    return {
        "position": dict(position or {}),
        "latest_order": latest_order,
        "latest_paper_fill": latest_paper_fill,
        "latest_equity": dict(latest_equity_rows[0]) if latest_equity_rows else {},
    }


def _trade_journal_snapshot(symbol: str, *, since_ts: str = "") -> dict[str, Any]:
    store = TradeJournalSQLite()
    since_epoch = _iso_epoch(since_ts)
    rows = list(store.list_fills(limit=1000) or [])
    for row in rows:
        if (
            (not symbol or str(row.get("symbol") or "").strip() == str(symbol).strip())
            and _row_meets_since(dict(row), since_epoch=since_epoch, keys=["fill_ts", "journal_ts"])
        ):
            return dict(row)
    return {}


def _latest_result(payload: dict[str, Any]) -> dict[str, Any]:
    rows = list(payload.get("results") or [])
    for item in reversed(rows):
        if isinstance(item, dict):
            return dict(item)
    return {}


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _result_fill_count(result: dict[str, Any]) -> int:
    if "fills_delta" in result:
        return _safe_int(result.get("fills_delta"))
    return _safe_int(result.get("fills_total"))


def _result_round_trip_count(result: dict[str, Any]) -> int:
    if "closed_trades_delta" in result:
        return _safe_int(result.get("closed_trades_delta"))
    return _safe_int(result.get("closed_trades_total"))


def _result_realized_pnl(result: dict[str, Any], position: dict[str, Any], equity: dict[str, Any]) -> float:
    if "net_realized_pnl_delta" in result:
        return _safe_float(result.get("net_realized_pnl_delta"))
    if "net_realized_pnl_total" in result:
        return _safe_float(result.get("net_realized_pnl_total"))
    if "realized_pnl" in position:
        return _safe_float(position.get("realized_pnl"))
    return _safe_float(equity.get("realized_pnl"))


def _recommendation(
    *,
    cfg: "PaperSimMonitorCfg",
    campaign: dict[str, Any],
    runner: dict[str, Any],
    paper_engine: dict[str, Any],
    result: dict[str, Any],
    position: dict[str, Any],
    latest_fill: dict[str, Any],
) -> tuple[str, str]:
    campaign_status = str(campaign.get("status") or "not_started").strip().lower()
    runner_status = str(runner.get("status") or "").strip().lower()
    paper_engine_status = str(paper_engine.get("status") or "").strip().lower()
    runner_note = str(result.get("runner_note") or runner.get("note") or "").strip().lower()
    round_trips = _result_round_trip_count(result)
    fills = _result_fill_count(result)
    pos_qty = _safe_float(position.get("qty"))
    latest_fill_id = str(latest_fill.get("fill_id") or "").strip()
    enqueued_total = _safe_int(result.get("enqueued_total") or runner.get("enqueued_total"))

    if campaign_status in {"failed", "dead"}:
        return "investigate", f"campaign_{campaign_status}"
    if runner_note.startswith("no_public_ohlcv") or runner_note.startswith("no_fresh_tick"):
        return "investigate", "market_data_blocked"
    if "error" in runner_note or "failed" in runner_note:
        return "investigate", "runner_note_error"
    if campaign_status == "running" and runner_status in {"dead", "failed"}:
        return "investigate", "runner_not_healthy"
    if campaign_status == "running" and paper_engine_status in {"dead", "failed"}:
        return "investigate", "paper_engine_not_healthy"
    if campaign_status == "completed":
        if round_trips >= int(cfg.min_closed_trades_for_enough_evidence):
            return "enough_evidence", "closed_trade_threshold_met"
        if fills > 0 or latest_fill_id:
            return "continue", "completed_with_partial_trade_evidence"
        return "investigate", "completed_without_trade_evidence"
    if campaign_status in {"running", "starting"}:
        if pos_qty != 0.0 or latest_fill_id or enqueued_total > 0:
            return "continue", "campaign_progress_visible"
        return "continue", "awaiting_first_trade"
    return "continue", "monitor_idle"


def _summary_text(
    *,
    strategy_label: str,
    symbol: str,
    campaign_status: str,
    position: dict[str, Any],
    latest_fill: dict[str, Any],
    round_trips: int,
    fills: int,
    current_window_realized_pnl: float,
    recommendation: str,
) -> str:
    qty = _safe_float(position.get("qty"))
    latest_fill_side = str(latest_fill.get("side") or "").strip()
    latest_fill_ts = str(latest_fill.get("fill_ts") or latest_fill.get("ts") or "").strip()
    latest_fill_part = "no fill yet"
    if latest_fill_side:
        latest_fill_part = f"latest_fill={latest_fill_side}@{latest_fill_ts or 'unknown_ts'}"
    position_part = "flat" if qty == 0.0 else f"open qty={qty}"
    return (
        f"Paper sim monitor sees {strategy_label or 'unknown_strategy'} on {symbol or 'unknown_symbol'} "
        f"with campaign {campaign_status or 'unknown'}; {position_part}; fills={fills}; "
        f"round_trips={round_trips}; current_window_realized_pnl={current_window_realized_pnl:.4f}; {latest_fill_part}; "
        f"recommendation={recommendation}."
    )


@dataclass(frozen=True)
class PaperSimMonitorCfg:
    poll_interval_sec: float = 300.0
    min_closed_trades_for_enough_evidence: int = 1
    desktop_notify: bool = True


def collect_once(cfg: PaperSimMonitorCfg) -> dict[str, Any]:
    ts = _now_iso()
    configured = _configured_strategy_runner()
    campaign = dict(load_campaign_runtime_status() or {})
    runner = _strategy_runner_status()
    paper_engine = _paper_engine_status()
    result = _latest_result(campaign)
    symbol = str(campaign.get("symbol") or configured.get("primary_symbol") or "").strip()
    venue = str(campaign.get("venue") or configured.get("venue") or "").strip()
    window_started_ts = str(result.get("started_ts") or campaign.get("started_ts") or "").strip()
    paper_state = _paper_state_snapshot_window(symbol, since_ts=window_started_ts)
    position = dict(paper_state.get("position") or {})
    latest_order = dict(paper_state.get("latest_order") or {})
    latest_paper_fill = dict(paper_state.get("latest_paper_fill") or {})
    latest_equity = dict(paper_state.get("latest_equity") or {})
    latest_journal_fill = _trade_journal_snapshot(symbol, since_ts=window_started_ts)
    strategy_name = str(
        campaign.get("current_strategy")
        or result.get("strategy")
        or runner.get("strategy_id")
        or configured.get("strategy")
        or ""
    ).strip()
    strategy_preset = str(
        campaign.get("current_strategy_preset")
        or result.get("strategy_preset")
        or runner.get("strategy_preset")
        or ""
    ).strip()
    strategy_label = strategy_preset or strategy_name
    round_trips = _result_round_trip_count(result)
    fills = _result_fill_count(result)
    current_window_realized_pnl = _result_realized_pnl(result, position, latest_equity)
    position_realized_pnl_total = _safe_float(position.get("realized_pnl"))
    equity_realized_pnl_total = _safe_float(latest_equity.get("realized_pnl"))
    unrealized_pnl = _safe_float(latest_equity.get("unrealized_pnl"))
    recommendation, recommendation_reason = _recommendation(
        cfg=cfg,
        campaign=campaign,
        runner=runner,
        paper_engine=paper_engine,
        result=result,
        position=position,
        latest_fill=latest_journal_fill or latest_paper_fill,
    )
    latest_fill = latest_journal_fill or latest_paper_fill
    return {
        "ok": True,
        "ts": ts,
        "monitor_name": MONITOR_NAME,
        "campaign_status": str(campaign.get("status") or "not_started"),
        "campaign_reason": str(campaign.get("reason") or ""),
        "recommendation": recommendation,
        "recommendation_reason": recommendation_reason,
        "configured_strategy": str(configured.get("strategy") or ""),
        "configured_symbols": list(configured.get("symbols") or []),
        "configured_signal_source": str(configured.get("signal_source") or ""),
        "current_strategy": strategy_name,
        "current_strategy_preset": strategy_preset,
        "strategy_label": strategy_label,
        "symbol": symbol,
        "venue": venue,
        "fills_observed": fills,
        "round_trips_observed": round_trips,
        "current_window_realized_pnl": current_window_realized_pnl,
        "position_realized_pnl_total": position_realized_pnl_total,
        "equity_realized_pnl_total": equity_realized_pnl_total,
        "unrealized_pnl": unrealized_pnl,
        "paper_position": position,
        "latest_order": latest_order,
        "latest_paper_fill": latest_paper_fill,
        "latest_journal_fill": latest_journal_fill,
        "latest_equity": latest_equity,
        "campaign_result": result,
        "collector": campaign,
        "strategy_runner": runner,
        "paper_engine": paper_engine,
        "summary_text": _summary_text(
            strategy_label=strategy_label,
            symbol=symbol,
            campaign_status=str(campaign.get("status") or "not_started"),
            position=position,
            latest_fill=latest_fill,
            round_trips=round_trips,
            fills=fills,
            current_window_realized_pnl=current_window_realized_pnl,
            recommendation=recommendation,
        ),
    }


def request_stop() -> dict[str, Any]:
    ensure_dirs()
    _flags_dir().mkdir(parents=True, exist_ok=True)
    stop_file().write_text(_now_iso() + "\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(stop_file())}


def _report_severity(recommendation: str) -> str:
    rec = str(recommendation or "").strip().lower()
    return "warn" if rec == "investigate" else "info"


def _osascript_escape(text: str) -> str:
    return str(text or "").replace("\\", "\\\\").replace('"', '\\"')


def _notify_local_desktop(payload: dict[str, Any]) -> dict[str, Any]:
    if sys.platform != "darwin":
        return {"attempted": False, "sent": False, "reason": "unsupported_platform"}
    binary = shutil.which("osascript")
    if not binary:
        return {"attempted": False, "sent": False, "reason": "osascript_missing"}

    watch_name = str(payload.get("watch_name") or "paper_sim_watch").strip()
    strategy_label = str(payload.get("strategy_label") or "unknown_strategy").strip()
    symbol = str(payload.get("symbol") or "unknown_symbol").strip()
    recommendation = str(payload.get("recommendation") or "continue").strip()
    message = (str(payload.get("summary") or "").strip() or f"{strategy_label} on {symbol}")[:220]
    title = f"CryptKeep: {watch_name}"
    subtitle = f"{strategy_label} · {symbol} · {recommendation}"
    script = (
        f'display notification "{_osascript_escape(message)}" '
        f'with title "{_osascript_escape(title)}" '
        f'subtitle "{_osascript_escape(subtitle)}"'
    )
    try:
        proc = subprocess.run(
            [binary, "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            timeout=5.0,
            check=False,
        )
    except Exception as exc:
        return {"attempted": True, "sent": False, "reason": f"notify_failed:{type(exc).__name__}"}
    if int(proc.returncode or 0) != 0:
        return {"attempted": True, "sent": False, "reason": f"notify_exit:{int(proc.returncode or 0)}"}
    return {"attempted": True, "sent": True, "reason": "notified"}


def _watch_event_key(previous: dict[str, Any] | None, current: dict[str, Any], watch: dict[str, Any]) -> str:
    if previous is None:
        return ""
    trigger = str(watch.get("trigger") or "")
    current_fill = dict(current.get("latest_journal_fill") or current.get("latest_paper_fill") or {})
    previous_fill = dict((previous or {}).get("latest_journal_fill") or (previous or {}).get("latest_paper_fill") or {})
    current_position = dict(current.get("paper_position") or {})
    previous_position = dict((previous or {}).get("paper_position") or {})
    current_campaign_status = str(current.get("campaign_status") or "").strip().lower()
    previous_campaign_status = str((previous or {}).get("campaign_status") or "").strip().lower()
    current_recommendation = str(current.get("recommendation") or "").strip().lower()
    previous_recommendation = str((previous or {}).get("recommendation") or "").strip().lower()
    current_fill_id = str(current_fill.get("fill_id") or "").strip()
    previous_fill_id = str(previous_fill.get("fill_id") or "").strip()
    current_qty = _safe_float(current_position.get("qty"))
    previous_qty = _safe_float(previous_position.get("qty"))

    if trigger == "new_fill" and current_fill_id and current_fill_id != previous_fill_id:
        return current_fill_id
    if trigger == "position_opened" and previous_qty == 0.0 and current_qty != 0.0:
        return str(current_fill_id or current.get("ts") or "")
    if trigger == "position_closed" and previous_qty != 0.0 and current_qty == 0.0:
        return str(current_fill_id or current.get("ts") or "")
    if trigger == "campaign_completed" and current_campaign_status == "completed" and previous_campaign_status != "completed":
        return str(current.get("ts") or "")
    if trigger == "recommendation_investigate" and current_recommendation == "investigate" and previous_recommendation != "investigate":
        return f"{current.get('recommendation_reason') or ''}:{current.get('ts') or ''}"
    return ""


def render_watch_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Paper Sim Monitor Watch `{payload.get('watch_name')}`",
        "",
        f"- Generated: {payload.get('generated_at')}",
        f"- Trigger: `{payload.get('trigger')}`",
        f"- Severity: `{payload.get('severity')}`",
        f"- Summary: {payload.get('summary')}",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Strategy: `{payload.get('strategy_label')}`",
        f"- Symbol: `{payload.get('symbol')}`",
        "",
        "## Snapshot",
        "```json",
        json.dumps(payload.get("snapshot") or {}, indent=2, sort_keys=True),
        "```",
    ]
    return "\n".join(lines) + "\n"


def _write_watch_report(payload: dict[str, Any], *, stem: str) -> dict[str, str]:
    root = report_root()
    json_path = root / f"{stem}.json"
    markdown_path = root / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_watch_markdown(payload), encoding="utf-8")
    return {"json_path": str(json_path), "markdown_path": str(markdown_path)}


def _recent_watch_reports(*, limit: int = 5) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(report_root().glob(f"{MONITOR_NAME}_watch_*.json"), reverse=True)[: max(1, int(limit or 5))]:
        try:
            payload = _load_json(path)
        except Exception:
            continue
        rows.append(
            {
                "stem": path.stem,
                "generated_at": str(payload.get("generated_at") or ""),
                "watch_name": str(payload.get("watch_name") or ""),
                "trigger": str(payload.get("trigger") or ""),
                "summary": str(payload.get("summary") or ""),
                "severity": str(payload.get("severity") or ""),
                "json_path": str(path),
                "markdown_path": str(path.with_suffix(".md")),
            }
        )
    return rows


def _fire_watch_reports(
    *,
    previous_snapshot: dict[str, Any] | None,
    current_snapshot: dict[str, Any],
    watches: list[dict[str, Any]],
    desktop_notify: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fired: list[dict[str, Any]] = []
    updated_watches: list[dict[str, Any]] = []
    for watch in watches:
        row = dict(watch)
        event_key = _watch_event_key(previous_snapshot, current_snapshot, row)
        if event_key and event_key != str(row.get("last_event_key") or ""):
            stem = f"{MONITOR_NAME}_watch_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{row['name']}"
            summary = (
                f"Watch `{row['name']}` fired on `{row['trigger']}` for "
                f"{current_snapshot.get('strategy_label') or 'unknown_strategy'} on {current_snapshot.get('symbol') or 'unknown_symbol'}."
            )
            payload = {
                "generated_at": _now_iso(),
                "monitor_name": MONITOR_NAME,
                "watch_name": str(row.get("name") or ""),
                "trigger": str(row.get("trigger") or ""),
                "severity": _report_severity(str(current_snapshot.get("recommendation") or "")),
                "summary": summary,
                "recommendation": str(current_snapshot.get("recommendation") or ""),
                "recommendation_reason": str(current_snapshot.get("recommendation_reason") or ""),
                "strategy_label": str(current_snapshot.get("strategy_label") or ""),
                "symbol": str(current_snapshot.get("symbol") or ""),
                "venue": str(current_snapshot.get("venue") or ""),
                "event_key": event_key,
                "snapshot": current_snapshot,
            }
            notify_result = (
                _notify_local_desktop(payload)
                if bool(desktop_notify)
                else {"attempted": False, "sent": False, "reason": "disabled"}
            )
            payload["desktop_notification"] = notify_result
            paths = _write_watch_report(payload, stem=stem)
            fired.append(
                {
                    "watch_name": str(row.get("name") or ""),
                    "trigger": str(row.get("trigger") or ""),
                    "report_stem": stem,
                    "summary": summary,
                    "severity": payload["severity"],
                    "json_path": paths["json_path"],
                    "markdown_path": paths["markdown_path"],
                    "event_key": event_key,
                    "desktop_notification": notify_result,
                }
            )
            row["last_fired_at"] = str(payload.get("generated_at") or "")
            row["last_event_key"] = event_key
            row["last_report_stem"] = stem
        updated_watches.append(row)
    return updated_watches, fired


def _signature_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    latest_fill = dict(snapshot.get("latest_journal_fill") or snapshot.get("latest_paper_fill") or {})
    latest_order = dict(snapshot.get("latest_order") or {})
    position = dict(snapshot.get("paper_position") or {})
    return {
        "campaign_status": str(snapshot.get("campaign_status") or ""),
        "recommendation": str(snapshot.get("recommendation") or ""),
        "strategy_label": str(snapshot.get("strategy_label") or ""),
        "symbol": str(snapshot.get("symbol") or ""),
        "position_qty": _safe_float(position.get("qty")),
        "latest_fill_id": str(latest_fill.get("fill_id") or ""),
        "latest_order_id": str(latest_order.get("order_id") or ""),
        "latest_order_status": str(latest_order.get("status") or ""),
        "round_trips_observed": _safe_int(snapshot.get("round_trips_observed")),
        "fills_observed": _safe_int(snapshot.get("fills_observed")),
        "current_window_realized_pnl": round(_safe_float(snapshot.get("current_window_realized_pnl")), 8),
        "unrealized_pnl": round(_safe_float(snapshot.get("unrealized_pnl")), 8),
    }


def _change_reasons(previous: dict[str, Any] | None, current: dict[str, Any]) -> list[str]:
    if not previous:
        return ["initial_snapshot"]
    labels = {
        "campaign_status": "campaign_status_changed",
        "recommendation": "recommendation_changed",
        "strategy_label": "strategy_changed",
        "symbol": "symbol_changed",
        "position_qty": "position_changed",
        "latest_fill_id": "latest_fill_changed",
        "latest_order_id": "latest_order_changed",
        "latest_order_status": "order_status_changed",
        "round_trips_observed": "round_trip_count_changed",
        "fills_observed": "fill_count_changed",
        "current_window_realized_pnl": "realized_pnl_changed",
        "unrealized_pnl": "unrealized_pnl_changed",
    }
    reasons = [label for key, label in labels.items() if previous.get(key) != current.get(key)]
    return reasons or ["heartbeat_only"]


def load_runtime_status() -> dict[str, Any]:
    payload: dict[str, Any]
    if status_file().exists():
        try:
            payload = _load_json(status_file())
        except Exception as exc:
            return {
                "ok": False,
                "has_status": False,
                "reason": f"status_read_failed:{type(exc).__name__}",
                "summary_text": "Paper sim monitor status is unavailable.",
            }
    else:
        payload = {
            "ok": True,
            "has_status": False,
            "status": "not_started",
            "reason": "status_missing",
            "summary_text": "Paper sim monitor has not written runtime status yet.",
        }

    pid_state: dict[str, Any] = {}
    if pid_file().exists():
        try:
            pid_state = _load_json(pid_file())
        except Exception as exc:
            payload["pid_reason"] = f"pid_read_failed:{type(exc).__name__}"

    status_pid = _safe_int(payload.get("pid"))
    pid = _safe_int(pid_state.get("pid"))
    if status_pid > 0 and (pid <= 0 or payload.get("status") == "running"):
        pid = status_pid
    pid_alive = _process_alive(pid) if pid > 0 else False

    payload["ok"] = bool(payload.get("ok", True))
    payload["has_status"] = bool(payload.get("has_status")) if "has_status" in payload else True
    payload["pid"] = pid or None
    payload["pid_alive"] = pid_alive
    payload["has_pid_file"] = bool(pid_state)
    payload["started_ts"] = str(pid_state.get("started_ts") or "")
    payload["poll_interval_sec"] = float(pid_state.get("poll_interval_sec") or payload.get("poll_interval_sec") or 0.0)
    payload["min_closed_trades_for_enough_evidence"] = int(
        pid_state.get("min_closed_trades_for_enough_evidence")
        or payload.get("min_closed_trades_for_enough_evidence")
        or 0
    )
    payload["desktop_notify"] = bool(
        pid_state.get("desktop_notify", payload.get("desktop_notify", True))
    )
    payload["history_path"] = str(history_file())
    payload["watches_path"] = str(watches_file())
    payload["watches"] = list_watches()
    payload["recent_watch_reports"] = _recent_watch_reports(limit=3)

    if pid_state and payload.get("status") == "running" and not pid_alive:
        payload["status"] = "dead"
        payload["reason"] = "process_not_running"
        payload["last_reason"] = str(payload.get("last_reason") or payload.get("reason") or "process_not_running")
    elif pid_state and not payload.get("has_status") and pid_alive:
        payload["status"] = "starting"
        payload["reason"] = "pid_alive_waiting_for_status"
        payload["has_status"] = True

    return payload


def run_forever(cfg: PaperSimMonitorCfg, *, max_loops: int | None = None) -> dict[str, Any]:
    ensure_dirs()
    _flags_dir().mkdir(parents=True, exist_ok=True)
    current_pid = int(os.getpid())
    existing = load_runtime_status()
    if bool(existing.get("pid_alive")) and _safe_int(existing.get("pid")) not in {0, current_pid}:
        return {
            "ok": True,
            "status": "running",
            "reason": "already_running",
            "pid": _safe_int(existing.get("pid")),
            "poll_interval_sec": float(existing.get("poll_interval_sec") or cfg.poll_interval_sec),
            "min_closed_trades_for_enough_evidence": int(
                existing.get("min_closed_trades_for_enough_evidence") or cfg.min_closed_trades_for_enough_evidence
            ),
            "desktop_notify": bool(existing.get("desktop_notify", cfg.desktop_notify)),
        }
    try:
        if stop_file().exists():
            stop_file().unlink()
    except Exception as exc:
        logger.warning(
            "paper_sim_monitor_stop_file_clear_failed",
            extra={"path": str(stop_file()), "error_type": type(exc).__name__},
        )

    _write_pid_state(
        {
            "pid": current_pid,
            "started_ts": _now_iso(),
            "poll_interval_sec": float(cfg.poll_interval_sec),
            "min_closed_trades_for_enough_evidence": int(cfg.min_closed_trades_for_enough_evidence),
            "desktop_notify": bool(cfg.desktop_notify),
        }
    )

    loops = 0
    changes_written = 0
    last_snapshot: dict[str, Any] = {}
    previous_signature: dict[str, Any] | None = None
    previous_snapshot: dict[str, Any] | None = None
    _write_status(
        {
            "ok": True,
            "has_status": True,
            "status": "running",
            "reason": "starting",
            "ts": _now_iso(),
            "loops": 0,
            "changes_written": 0,
            "pid": current_pid,
            "poll_interval_sec": float(cfg.poll_interval_sec),
            "min_closed_trades_for_enough_evidence": int(cfg.min_closed_trades_for_enough_evidence),
            "desktop_notify": bool(cfg.desktop_notify),
            "history_path": str(history_file()),
            "watches_path": str(watches_file()),
            "watches": list_watches(),
            "recent_watch_reports": _recent_watch_reports(limit=3),
            "summary_text": "Paper sim monitor is starting.",
        }
    )

    while True:
        if stop_file().exists():
            final_watch_reports: list[dict[str, Any]] = []
            final_trigger_reasons = ["stop_requested"]
            final_watches = list_watches()
            if previous_signature is not None or previous_snapshot is not None:
                try:
                    final_snapshot = collect_once(cfg)
                    final_signature = _signature_payload(final_snapshot)
                    final_trigger_reasons = _change_reasons(previous_signature, final_signature) + ["stop_requested"]
                    updated_watches, final_watch_reports = _fire_watch_reports(
                        previous_snapshot=previous_snapshot,
                        current_snapshot=final_snapshot,
                        watches=final_watches,
                        desktop_notify=bool(cfg.desktop_notify),
                    )
                    if updated_watches != final_watches:
                        _save_watches(updated_watches)
                    final_watches = updated_watches
                    if previous_signature is None or final_signature != previous_signature:
                        changes_written += 1
                        _append_history(
                            {
                                "ts": final_snapshot.get("ts") or _now_iso(),
                                "trigger_reasons": final_trigger_reasons,
                                "watch_reports_written": final_watch_reports,
                                **final_snapshot,
                            }
                        )
                        previous_signature = final_signature
                    elif final_watch_reports:
                        _append_history(
                            {
                                "ts": final_snapshot.get("ts") or _now_iso(),
                                "trigger_reasons": ["watch_report_written", "stop_requested"],
                                "watch_reports_written": final_watch_reports,
                                **final_snapshot,
                            }
                        )
                    last_snapshot = dict(final_snapshot)
                    previous_snapshot = dict(final_snapshot)
                except Exception as exc:
                    logger.warning(
                        "paper_sim_monitor_final_snapshot_failed",
                        extra={"error_type": type(exc).__name__},
                    )
            out = {
                "ok": True,
                "has_status": True,
                "status": "stopped",
                "reason": "stop_requested",
                "ts": _now_iso(),
                "loops": loops,
                "changes_written": changes_written,
                "pid": current_pid,
                "poll_interval_sec": float(cfg.poll_interval_sec),
                "min_closed_trades_for_enough_evidence": int(cfg.min_closed_trades_for_enough_evidence),
                "desktop_notify": bool(cfg.desktop_notify),
                "history_path": str(history_file()),
                "watches_path": str(watches_file()),
                "watches": final_watches,
                "recent_watch_reports": _recent_watch_reports(limit=3),
                "last_watch_reports_written": final_watch_reports,
                "trigger_reasons": final_trigger_reasons,
                **last_snapshot,
            }
            _write_status(out)
            _clear_pid_state()
            return out

        loops += 1
        snapshot = collect_once(cfg)
        current_signature = _signature_payload(snapshot)
        change_reasons = _change_reasons(previous_signature, current_signature)
        watches = list_watches()
        updated_watches, fired_watch_reports = _fire_watch_reports(
            previous_snapshot=previous_snapshot,
            current_snapshot=snapshot,
            watches=watches,
            desktop_notify=bool(cfg.desktop_notify),
        )
        if updated_watches != watches:
            _save_watches(updated_watches)
        if previous_signature is None or current_signature != previous_signature:
            changes_written += 1
            _append_history(
                {
                    "ts": snapshot.get("ts") or _now_iso(),
                    "trigger_reasons": change_reasons,
                    "watch_reports_written": fired_watch_reports,
                    **snapshot,
                }
            )
            previous_signature = current_signature
        elif fired_watch_reports:
            _append_history(
                {
                    "ts": snapshot.get("ts") or _now_iso(),
                    "trigger_reasons": ["watch_report_written"],
                    "watch_reports_written": fired_watch_reports,
                    **snapshot,
                }
            )
        last_snapshot = dict(snapshot)
        previous_snapshot = dict(snapshot)
        out = {
            "ok": True,
            "has_status": True,
            "status": "running",
            "reason": "monitoring",
            "ts": _now_iso(),
            "loops": loops,
            "changes_written": changes_written,
            "pid": current_pid,
            "poll_interval_sec": float(cfg.poll_interval_sec),
            "min_closed_trades_for_enough_evidence": int(cfg.min_closed_trades_for_enough_evidence),
            "desktop_notify": bool(cfg.desktop_notify),
            "history_path": str(history_file()),
            "watches_path": str(watches_file()),
            "watches": updated_watches,
            "recent_watch_reports": _recent_watch_reports(limit=3),
            "last_watch_reports_written": fired_watch_reports,
            "trigger_reasons": change_reasons,
            **snapshot,
        }
        _write_status(out)

        if max_loops is not None and loops >= int(max_loops):
            out["status"] = "stopped"
            out["reason"] = "max_loops"
            out["ts"] = _now_iso()
            _write_status(out)
            _clear_pid_state()
            return out

        time.sleep(max(0.1, float(cfg.poll_interval_sec)))
