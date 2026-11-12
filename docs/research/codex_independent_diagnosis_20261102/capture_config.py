"""Read only owner-authorized trading leaves; never copy config files or inspect .env."""
from datetime import datetime, timezone
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
LEAVES = {"strategy_id", "strategy_name", "strategy_preset", "venue", "symbol", "symbols",
          "signal_source", "timeframe", "fast_n", "slow_n", "min_bars", "max_bars", "loop_interval_sec",
          "qty", "order_type", "stop_loss_pct", "take_profit_pct", "trailing_stop_pct", "max_bars_hold",
          "max_position_notional_usd", "max_order_notional_usd", "max_daily_notional_usd", "max_positions"}


def filtered(block):
    if type(block) is not dict:
        return {}
    out = {}
    for key in LEAVES:
        value = block.get(key)
        if type(value) in (str, int, float, bool) and (type(value) is not str or len(value) <= 160):
            out[key] = value
        elif key == "symbols" and type(value) is list and all(type(x) is str and len(x) <= 40 for x in value):
            out[key] = value
    strategy = block.get("strategy")
    if type(strategy) is dict and type(strategy.get("name")) is str:
        out["strategy.name"] = strategy["name"][:100]
    elif type(strategy) is str:
        out["strategy"] = strategy[:100]
    return out


def main():
    records = []
    for name in ("config/user.yaml", ".cbp_state/runtime/config/user.yaml"):
        path = ROOT / name
        record = {"path": name, "exists": path.is_file()}
        if path.is_file():
            try:
                with path.open() as handle:
                    config = yaml.safe_load(handle)
                record["trading_settings"] = {section: filtered(config.get(section))
                    for section in ("strategy_runner", "preflight", "risk", "paper") if type(config) is dict and section in config}
                runner = config.get("strategy_runner", {}) if type(config) is dict else {}
                record["runner_risk"] = filtered(runner.get("risk")) if type(runner) is dict else {}
            except Exception as error:
                record["error_type"] = type(error).__name__
        records.append(record)
    result = {"captured_at": datetime.now(timezone.utc).isoformat(), "records": records,
              "limitations": "File settings only; process environment, preset resolution, campaign overrides and server runtime unverified. No credentials printed/copied; no configuration changes."}
    with (HERE / "runtime_trading_settings.json").open("x") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
