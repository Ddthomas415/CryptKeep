from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


import argparse
from services.config_loader import load_runtime_trading_config
from services.runtime.process_supervisor import start_process, status
from services.runtime.managed_symbol_selection import resolve_managed_symbol_selection

CORE_SERVICES = ["pipeline", "executor", "intent_consumer", "ops_signal_adapter", "ops_risk_gate", "ai_alert_monitor"]
ALL_SERVICES = CORE_SERVICES + ["reconciler"]


def _service_envs() -> dict[str, dict[str, str]]:
    cfg = load_runtime_trading_config()
    execution = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}
    live = cfg.get("live") if isinstance(cfg.get("live"), dict) else {}
    mode = str(cfg.get("mode") or execution.get("executor_mode") or "").strip().lower() or "paper"
    live_enabled = bool(execution.get("live_enabled", live.get("enabled", False)))
    venue = str(execution.get("venue") or (cfg.get("pipeline") or {}).get("exchange_id") or cfg.get("venue") or "").strip().lower()
    selection = resolve_managed_symbol_selection(cfg, venue=venue or "coinbase", mode=mode, live_enabled=live_enabled)
    symbols = [str(x).strip() for x in list(selection.get("symbols") or []) if str(x).strip()]
    if not symbols:
        return {}
    env = {"CBP_SYMBOLS": ",".join(symbols)}
    return {
        "pipeline": dict(env),
        "executor": dict(env),
        "intent_consumer": dict(env),
        "reconciler": dict(env),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with_reconcile", action="store_true", help="Also start live reconciler loop")
    args = ap.parse_args()

    py = sys.executable
    envs = _service_envs()

    # Start the managed pipeline loop, execution services, telemetry/risk services, and the AI alert monitor.
    r1 = start_process("pipeline", [py, "scripts/run_pipeline_safe.py"], env=envs.get("pipeline"))
    r2 = start_process("executor", [py, "scripts/run_intent_executor_safe.py"], env=envs.get("executor"))
    r3 = start_process("intent_consumer", [py, "scripts/run_intent_consumer_safe.py", "run"], env=envs.get("intent_consumer"))
    r4 = start_process("ops_signal_adapter", [py, "scripts/run_ops_signal_adapter.py", "run"])
    r5 = start_process("ops_risk_gate", [py, "scripts/run_ops_risk_gate_service.py", "run"])
    r6 = start_process("ai_alert_monitor", [py, "scripts/run_ai_alert_monitor.py"])

    out = {"pipeline": r1, "executor": r2, "intent_consumer": r3, "ops_signal_adapter": r4, "ops_risk_gate": r5, "ai_alert_monitor": r6}

    if args.with_reconcile:
        out["reconciler"] = start_process("reconciler", [py, "scripts/run_live_reconciler_safe.py", "run"], env=envs.get("reconciler"))

    out["status"] = status(ALL_SERVICES)
    print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
