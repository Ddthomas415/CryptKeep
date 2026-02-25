from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml
from services.os.app_paths import data_dir, ensure_dirs


def _default_exec_db_path() -> str:
    ensure_dirs()
    return str(data_dir() / "execution.sqlite")

DEFAULT_CFG = {
    "symbols": ["BTC/USD"],
    "pipeline": {
        "exchange_id": "coinbase",
        "strategy": "ema",          # ema | mean_reversion
        "timeframe": "5m",
        "poll_sec": 10,
        "only_on_new_bar": True,

        # EMA
        "ema_fast": 12,
        "ema_slow": 26,

        # Mean reversion (BB)
        "bb_window": 20,
        "bb_k": 2.0,

        # sizing (choose one)
        "fixed_qty": 0.0,
        "quote_notional": 0.0,
    },
    "execution": {
        "db_path": _default_exec_db_path(),
        "executor_mode": "paper",     # paper|live
        "executor_poll_sec": 1.5,
        "executor_max_per_cycle": 10,
        "paper_fee_bps": 7.0,
        "paper_slippage_bps": 2.0,

        # live must be explicitly enabled
        "live_enabled": False,
        "require_keys_for_live": True,

        # live reconciliation knobs (read-only recovery)
        "live_reconcile_lookback_ms": 21600000,
        "live_reconcile_limit_trades": 200,
        "live_reconcile_max_intents": 20,
    },
    "ai_engine": {
        "enabled": False,
        "strict": False,
        "model_path": "",
        "buy_threshold": 0.55,
        "sell_threshold": 0.45,
    },
    "risk": {
        "exchange_allowlist": [],
        "symbol_allowlist": [],
        "min_qty": 0.0,
        "max_qty": 0.0,
        "min_notional": 0.0,
        "max_notional": 0.0,
        "max_intents_per_day": 0,
        "max_live_intents_per_day": 0,
        "price_exchange_id": "coinbase",
        "price_default_type": "spot",
        "price_sandbox": False,
        "max_daily_loss_quote": 0.0,
        "max_position_notional_per_symbol": 0.0,
        "max_total_notional": 0.0,
        "reject_if_price_unknown_for_exposure": True,
    }
}

def deep_merge(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(dst)
    for k, v in (src or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out

@dataclass
class ConfigManager:
    cfg_path: str = "config/trading.yaml"

    def exists(self) -> bool:
        return Path(self.cfg_path).exists()

    def load(self) -> Dict[str, Any]:
        p = Path(self.cfg_path)
        if not p.exists():
            return dict(DEFAULT_CFG)
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        # ensure defaults present
        return deep_merge(DEFAULT_CFG, data)

    def save(self, cfg: Dict[str, Any]) -> None:
        p = Path(self.cfg_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

    def ensure(self) -> Dict[str, Any]:
        cfg = self.load()
        if not self.exists():
            self.save(cfg)
        return cfg

def apply_risk_preset(cfg: Dict[str, Any], preset: str) -> Dict[str, Any]:
    preset = (preset or "").lower().strip()
    risk = dict(cfg.get("risk") or {})
    exe = dict(cfg.get("execution") or {})
    pipe = dict(cfg.get("pipeline") or {})

    # Always safe: live disabled unless user enables explicitly
    if preset == "safe_paper":
        exe["executor_mode"] = "paper"
        exe["live_enabled"] = False
        risk.update({
            "exchange_allowlist": [pipe.get("exchange_id","coinbase")],
            "symbol_allowlist": cfg.get("symbols") or ["BTC/USD"],
            "min_notional": 5.0,
            "max_notional": 50.0,
            "max_intents_per_day": 50,
            "max_daily_loss_quote": 25.0,
            "max_position_notional_per_symbol": 100.0,
            "max_total_notional": 250.0,
        })
    elif preset == "paper_relaxed":
        exe["executor_mode"] = "paper"
        exe["live_enabled"] = False
        risk.update({
            "min_notional": 0.0,
            "max_notional": 0.0,
            "max_intents_per_day": 0,
            "max_daily_loss_quote": 0.0,
            "max_position_notional_per_symbol": 0.0,
            "max_total_notional": 0.0,
        })
    elif preset == "live_locked":
        # still locked unless live_enabled set true by user in wizard
        exe["executor_mode"] = "live"
        risk.update({
            "exchange_allowlist": [pipe.get("exchange_id","coinbase")],
            "symbol_allowlist": cfg.get("symbols") or ["BTC/USD"],
            "min_notional": 10.0,
            "max_notional": 100.0,
            "max_live_intents_per_day": 10,
            "max_daily_loss_quote": 50.0,
            "max_position_notional_per_symbol": 200.0,
            "max_total_notional": 400.0,
            "reject_if_price_unknown_for_exposure": True,
        })

    cfg["risk"] = risk
    cfg["execution"] = exe
    cfg["pipeline"] = pipe
    return cfg
