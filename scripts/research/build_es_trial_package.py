"""Render an uninstalled Hetzner user-service package; never launch a process."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

ROOT = "/srv/cryptkeep/app"
STATE = ROOT + "/.cbp_state_challengers/es_corrected_prospective_v1"
NAME = "cbp-es-corrected-prospective"


def utc(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() != timedelta(0):
        raise ValueError("explicit UTC timestamp required")
    return result.astimezone(timezone.utc)


def before_deadline(value: str, now: datetime) -> bool:
    return now < utc(value)


def render(start: str, now: datetime) -> dict[str, str]:
    first = utc(start)
    if first.hour or first.minute or first.second or first.microsecond:
        raise ValueError("evaluation start must be UTC midnight")
    if not now < first <= now + timedelta(days=1):
        raise ValueError("start must be the next UTC midnight")
    end = first + timedelta(days=30)
    deadline = end.isoformat()
    # JSON is also valid YAML, consumed by the existing state-local loader.
    config = {
        "strategy_runner": {
            "strategy": {"name": "sma_200_trend", "sma_period": 200,
                         "atr_period": 20, "trade_enabled": True},
            "strategy_preset": "es_daily_trend_v1", "qty": 0.001,
            "symbol": "BTC/USDT", "venue": "coinbase",
            "signal_source": "public_ohlcv_1d", "min_bars": 210, "max_bars": 400,
            "risk": {"stop_loss_pct": 0, "take_profit_pct": 0,
                     "trailing_stop_pct": 0, "max_bars_hold": 0},
        },
        "paper_trading": {"enabled": True, "quote_currency": "USDT",
                          "starting_cash_quote": 10000, "fee_bps": 7.5,
                          "slippage_bps": 5},
    }
    config_text = json.dumps(config, indent=2, sort_keys=True) + "\n"
    service = f"""[Unit]
Description=Isolated corrected ES prospective paper trial
Requires={NAME}-deadline.timer
After={NAME}-deadline.timer network-online.target

[Service]
Type=exec
WorkingDirectory={ROOT}
Environment=CBP_STATE_DIR={STATE}
ExecCondition={ROOT}/.venv/bin/python scripts/research/build_es_trial_package.py --check-deadline {deadline}
ExecStart={ROOT}/.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --strategies sma_200_trend --session-strategy-id es_corrected_prospective_v1 --symbol BTC/USDT --venue coinbase --signal-source public_ohlcv_1d --runtime-sec 20 --strategy-drain-sec 2 --poll-interval-sec 300 --max-daily-attempts 2 --daily-loop --no-desktop-notify
Restart=no
RuntimeMaxSec=31d
TimeoutStopSec=30
KillMode=control-group
SendSIGKILL=yes
"""
    timer = f"""[Unit]
Description=Absolute deadline for corrected ES trial

[Timer]
OnCalendar={end.strftime('%Y-%m-%d %H:%M:%S')} UTC
Persistent=true
AccuracySec=1s
Unit={NAME}-stop.service
"""
    stop = f"""[Unit]
Description=Stop corrected ES trial at fixed deadline

[Service]
Type=oneshot
ExecStart=/usr/bin/systemctl --user --no-block stop {NAME}.service
"""
    return {
        f"{NAME}.service": service,
        f"{NAME}-deadline.timer": timer,
        f"{NAME}-stop.service": stop,
        "user.yaml": config_text,
        "evaluation.json": json.dumps({
            "research_only": True, "installed": False, "launched": False,
            "evaluation_start_utc": first.isoformat(), "stop_at_utc": deadline,
            "operational_review_utc": (first+timedelta(days=7)).isoformat(),
            "state_dir": STATE, "config_sha256": hashlib.sha256(config_text.encode()).hexdigest(),
            "note": "Host config/commit/preflight proof required before installation; pre-start rows excluded."
        }, indent=2) + "\n",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-deadline")
    parser.add_argument("--evaluation-start")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    if args.check_deadline:
        try:
            return 0 if before_deadline(args.check_deadline, now) else 1
        except ValueError:
            return 1
    if not args.evaluation_start or args.output is None:
        parser.error("--evaluation-start and --output required")
    files = render(args.evaluation_start, now)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in files.items():
        (args.output / name).write_text(value, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
