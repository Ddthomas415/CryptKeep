"""
services/strategies/evidence_logger.py

Evidence logger for es_daily_trend_v1.

Writes structured JSONL logs for every signal, order, fill, session, and drawdown
event. These logs are the primary input to check_promotion_gates.py.

Log schema matches configs/strategies/es_daily_trend_v1.yaml evidence section.

Usage:
    logger = EvidenceLogger("es_daily_trend_v1")
    logger.log_signal(timestamp=..., price=..., sma_200=..., ...)
    logger.log_session(regime_at_open=..., halts_triggered=..., ...)
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir
from services.os.file_utils import atomic_write
from services.logging.app_logger import get_logger

_LOG = get_logger("strategy.evidence_logger")


def _trace_enabled() -> bool:
    raw = str(os.environ.get("CBP_DEBUG_CHILD_IO") or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _version_stamp(strategy_id: str, stage: str | None = None) -> dict:
    """Return version identity fields for every evidence record."""
    try:
        from services.control.deployment_stage import get_current_stage
        _stage = stage or get_current_stage(strategy_id).value
    except Exception:
        _stage = stage or "unknown"

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).parents[2],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        commit = "unknown"

    return {
        "_strategy_id": strategy_id,
        "_stage":       _stage,
        "_commit":      commit,
    }


class EvidenceLogger:
    """Writes structured evidence logs for one strategy."""

    def __init__(self, strategy_id: str, log_dir: Path | None = None) -> None:
        self.strategy_id = strategy_id
        self.log_dir = log_dir or (data_dir() / "evidence" / strategy_id)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _log_dir_for(self, record_type: str) -> Path:
        return self.log_dir

    def _append(self, record_type: str, record: dict) -> None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = self.log_dir / f"{record_type}_{date}.jsonl"
        record.setdefault("_logged_at", _now_iso())
        record.setdefault("strategy_id", self.strategy_id)
        # Stamp with version identity so every record is attributable
        stamp = _version_stamp(self.strategy_id)
        for k, v in stamp.items():
            record.setdefault(k, v)
        try:
            existing = path.read_text(encoding="utf-8") if path.exists() else ""
            atomic_write(path, existing + json.dumps(record) + "\n")
            if record_type == "signal" and _trace_enabled():
                _LOG.debug("evidence_logger signal write path=%s", path)
        except Exception as e:
            _LOG.error("evidence_logger write failed type=%s err=%s", record_type, e)
            if record_type == "signal" and _trace_enabled():
                _LOG.debug("evidence_logger signal write failed path=%s err=%s", path, e)

    # ------------------------------------------------------------------
    # Signal log — one record per bar evaluated
    # ------------------------------------------------------------------

    def log_signal(
        self,
        *,
        timestamp: str,
        price: float,
        sma_200: float | None,
        atr_ratio: float | None,
        signal_direction: str,       # "long" | "flat"
        regime_flag: str,            # "trending" | "chop" | "high_vol" | "borderline"
        kernel_action: str | None = None,
        entry_allowed: bool | None = None,
        extra: dict | None = None,
    ) -> None:
        record: dict[str, Any] = {
            "record_type":      "signal",
            "timestamp":        timestamp,
            "price":            price,
            "sma_200":          sma_200,
            "atr_ratio":        atr_ratio,
            "signal_direction": signal_direction,
            "regime_flag":      regime_flag,
            "kernel_action":    kernel_action,
            "entry_allowed":    entry_allowed,
        }
        if extra:
            record.update(extra)
        self._append("signal", record)

    # ------------------------------------------------------------------
    # Order log — one record per order sent
    # ------------------------------------------------------------------

    def log_order(
        self,
        *,
        timestamp: str,
        order_type: str,             # "market" | "limit"
        size: float,
        intended_price: float,
        stop_level: float,
        capital_at_risk_usd: float,
        side: str = "buy",
        order_id: str | None = None,
        extra: dict | None = None,
    ) -> None:
        record: dict[str, Any] = {
            "record_type":        "order",
            "timestamp":          timestamp,
            "order_type":         order_type,
            "side":               side,
            "size":               size,
            "intended_price":     intended_price,
            "stop_level":         stop_level,
            "capital_at_risk_usd": capital_at_risk_usd,
            "order_id":           order_id,
        }
        if extra:
            record.update(extra)
        self._append("order", record)

    # ------------------------------------------------------------------
    # Fill log — one record per confirmed fill
    # ------------------------------------------------------------------

    def log_fill(
        self,
        *,
        timestamp: str,
        fill_price: float,
        slippage_points: float,
        slippage_pct: float,
        fees_paid: float,
        side: str = "buy",
        size: float | None = None,
        pnl_usd: float | None = None,
        order_id: str | None = None,
        extra: dict | None = None,
    ) -> None:
        record: dict[str, Any] = {
            "record_type":      "fill",
            "timestamp":        timestamp,
            "side":             side,
            "size":             size,
            "fill_price":       fill_price,
            "slippage_points":  slippage_points,
            "slippage_pct":     slippage_pct,
            "fees_paid":        fees_paid,
            "pnl_usd":          pnl_usd,
            "order_id":         order_id,
        }
        if extra:
            record.update(extra)
        self._append("fill", record)

    # ------------------------------------------------------------------
    # Session log — one record per trading session (daily)
    # ------------------------------------------------------------------

    def log_session(
        self,
        *,
        regime_at_open: str,
        halts_triggered: list[str],
        manual_overrides: list[str],
        reconciliation_result: str,   # "pass" | "mismatch:..."
        drawdown_from_peak: float,
        kill_switch_tested: bool = False,
        recovery_tested: bool = False,
        ops_checks_passed: bool = True,
        infra_halt: bool = False,
        critical_error: bool = False,
        session_start: str | None = None,
        extra: dict | None = None,
    ) -> None:
        record: dict[str, Any] = {
            "record_type":           "session",
            "timestamp":             session_start or _now_iso(),
            "regime_at_open":        regime_at_open,
            "halts_triggered":       halts_triggered,
            "manual_overrides":      manual_overrides,
            "reconciliation_result": reconciliation_result,
            "drawdown_from_peak":    drawdown_from_peak,
            "kill_switch_tested":    kill_switch_tested,
            "recovery_tested":       recovery_tested,
            "ops_checks_passed":     ops_checks_passed,
            "infra_halt":            infra_halt,
            "critical_error":        critical_error,
        }
        if extra:
            record.update(extra)
        self._append("session", record)

    # ------------------------------------------------------------------
    # Drawdown log — one record per drawdown event
    # ------------------------------------------------------------------

    def log_drawdown(
        self,
        *,
        peak_equity: float,
        trough_equity: float,
        duration_days: int,
        action_taken: str,           # "held" | "halved" | "paused"
        recovery_date: str | None = None,
        drawdown_pct: float | None = None,
        extra: dict | None = None,
    ) -> None:
        dd_pct = drawdown_pct
        if dd_pct is None and peak_equity > 0:
            dd_pct = (peak_equity - trough_equity) / peak_equity * 100
        record: dict[str, Any] = {
            "record_type":   "drawdown",
            "timestamp":     _now_iso(),
            "peak_equity":   peak_equity,
            "trough_equity": trough_equity,
            "drawdown_pct":  dd_pct,
            "duration_days": duration_days,
            "action_taken":  action_taken,
            "recovery_date": recovery_date,
        }
        if extra:
            record.update(extra)
        self._append("drawdown", record)
