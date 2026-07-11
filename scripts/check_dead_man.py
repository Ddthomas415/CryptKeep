from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

_REPO = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json
import math
import os
import time

from services.process.heartbeat import named_heartbeat_age_s as heartbeat_age_s, named_heartbeat_path as heartbeat_path

DEAD_MAN_MAX_AGE_S_ENV = "CBP_DEAD_MAN_MAX_AGE_S"
DEAD_MAN_MAX_AGE_S_DEFAULT = 180.0
DEFAULT_NAMES = "intent_consumer,live_reconciler"

EXIT_HEALTHY = 0
EXIT_STALE = 1
EXIT_MISSING = 2


def dead_man_max_age_s() -> float:
    raw = os.environ.get(DEAD_MAN_MAX_AGE_S_ENV)
    if raw is None or str(raw).strip() == "":
        return DEAD_MAN_MAX_AGE_S_DEFAULT
    try:
        value = float(raw)
    except Exception as _err:
        return DEAD_MAN_MAX_AGE_S_DEFAULT
    if not math.isfinite(value) or value <= 0.0:
        return DEAD_MAN_MAX_AGE_S_DEFAULT
    return value


def check(names: list[str], *, max_age_s: float, now_epoch: float | None = None) -> dict:
    if not names:
        return {
            "ok": False,
            "overall": "missing",
            "max_age_s": max_age_s,
            "names": {
                "__configured_names__": {
                    "status": "missing",
                    "age_s": None,
                    "reason": "no_heartbeat_names_configured",
                }
            },
        }
    verdicts = {}
    for name in names:
        age = heartbeat_age_s(name, now_epoch=now_epoch)
        if age is None:
            verdicts[name] = {"status": "missing", "age_s": None, "path": str(heartbeat_path(name))}
        elif age > max_age_s:
            verdicts[name] = {"status": "stale", "age_s": round(age, 3)}
        else:
            verdicts[name] = {"status": "ok", "age_s": round(age, 3)}
    statuses = {v["status"] for v in verdicts.values()}
    overall = "ok"
    if "missing" in statuses:
        overall = "missing"
    elif "stale" in statuses:
        overall = "stale"
    return {"ok": overall == "ok", "overall": overall, "max_age_s": max_age_s, "names": verdicts}


def _maybe_alert(report: dict) -> None:
    """Best-effort dispatch through the existing alert stack; never raises."""
    try:
        from services.alerts.alert_dispatcher import send_alert
        from services.config_loader import load_runtime_trading_config

        cfg = load_runtime_trading_config()
        bad = {k: v for k, v in report["names"].items() if v["status"] != "ok"}
        send_alert(
            cfg=cfg if isinstance(cfg, dict) else {},
            level="critical",
            message=f"dead_man:{report['overall']}:{','.join(sorted(bad))}",
            payload=report,
        )
    except Exception as exc:
        print(f"alert dispatch unavailable: {type(exc).__name__}: {exc}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="Dead-man liveness check over trading-loop heartbeats.")
    ap.add_argument("--names", default=DEFAULT_NAMES, help="comma-separated heartbeat names that MUST be alive on this host")
    ap.add_argument("--max-age-s", type=float, default=None, help=f"override {DEAD_MAN_MAX_AGE_S_ENV} (default {DEAD_MAN_MAX_AGE_S_DEFAULT})")
    ap.add_argument("--json", action="store_true", help="print the full JSON report")
    ap.add_argument("--alert", action="store_true", help="dispatch a critical alert on stale/missing (best-effort)")
    args = ap.parse_args()

    max_age = args.max_age_s if (args.max_age_s is not None and math.isfinite(args.max_age_s) and args.max_age_s > 0) else dead_man_max_age_s()
    names = [n.strip() for n in str(args.names).split(",") if n.strip()]
    report = check(names, max_age_s=max_age, now_epoch=time.time())

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for name, v in report["names"].items():
            print(f"{name}: {v['status']}" + (f" (age {v['age_s']}s)" if v["age_s"] is not None else ""))
        print(f"overall: {report['overall']} (max_age_s={max_age})")

    if not report["ok"] and args.alert:
        _maybe_alert(report)

    if report["overall"] == "missing":
        return EXIT_MISSING
    if report["overall"] == "stale":
        return EXIT_STALE
    return EXIT_HEALTHY


if __name__ == "__main__":
    raise SystemExit(main())
