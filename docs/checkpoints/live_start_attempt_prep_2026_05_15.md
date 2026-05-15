# Live Start Attempt Prep — 2026-05-15

Purpose:

- preserve the exact current state before any real live-start attempt
- record the operator inputs still required
- provide a reversible rehearsal and rollback sequence

This is a preparation artifact. It is **not** approval to arm live trading.

## Current shown state

- active branch: `fix/p1-pre-live`
- current branch tip: `24a816166`
- canonical live execution regression slice:
  - `79 passed in 1.11s`
- canonical live-mode contract slice:
  - `36 passed in 0.75s`
- non-persistent live-mode preflight rehearsal:
  - `ok=true`
  - only `live_keys_hint` remains `WARN`

Real runtime state is still paper:

- `execution.executor_mode=paper`
- `execution.live_enabled=false`

Real shell/live envs are currently unset:

- `CBP_MAX_TRADES_PER_DAY`
- `CBP_MAX_DAILY_LOSS`
- `CBP_MAX_DAILY_NOTIONAL`
- `CBP_MAX_ORDER_NOTIONAL`
- `CBP_EXECUTION_ARMED`
- `CBP_LIVE_ENABLED`

Runtime user config hygiene is currently acceptable:

- `.cbp_state/runtime/config/user.yaml` is not tracked in git
- no secret-like keys were shown in that YAML

## Required operator inputs before a real attempt

These are still human decisions, not code gaps.

1. First-live limits
   - `CBP_MAX_TRADES_PER_DAY=_____`
   - `CBP_MAX_DAILY_LOSS=_____`
   - `CBP_MAX_DAILY_NOTIONAL=_____`
   - `CBP_MAX_ORDER_NOTIONAL=_____`

2. Venue and symbols
   - venue: `_____`
   - symbols: `_____`

3. Key source confirmation
   - keyring or `.env` confirmed: `YES / NO`
   - operator who verified it: `_____`

4. Attempt window
   - date/time window: `_____`
   - operator in control: `_____`
   - rollback owner: `_____`

5. Real-live confirmation gate
   - if `live.sandbox=false`, current code still requires:
     - `ENABLE_LIVE_TRADING=YES`
     - `CONFIRM_LIVE=YES`

## First-live maximums

Do not exceed the current launch-checklist first-live caps:

- `CBP_MAX_ORDER_NOTIONAL <= 25`
- `CBP_MAX_DAILY_NOTIONAL <= 50`
- `CBP_MAX_DAILY_LOSS <= 25`
- `CBP_MAX_TRADES_PER_DAY <= 5`

## Non-persistent rehearsal

Use this first. It does not change the real runtime config.

### 1. Set temporary live limits in the current shell

```bash
export CBP_MAX_TRADES_PER_DAY=5
export CBP_MAX_DAILY_LOSS=25
export CBP_MAX_DAILY_NOTIONAL=50
export CBP_MAX_ORDER_NOTIONAL=25
```

### 2. Run canonical live-mode preflight against a temp config

```bash
./.venv/bin/python - <<'PY'
from pathlib import Path
import json, os, yaml
from services.config_loader import load_runtime_trading_config
from services.preflight.preflight import run_preflight

cfg = load_runtime_trading_config()
execution = dict(cfg.get("execution") or {})
live = dict(cfg.get("live") or {})
pipeline = dict(cfg.get("pipeline") or {})

execution["executor_mode"] = "live"
execution["live_enabled"] = True
live["enabled"] = True
pipeline["exchange_id"] = str(
    pipeline.get("exchange_id")
    or execution.get("venue")
    or live.get("exchange_id")
    or "coinbase"
)

symbols = cfg.get("symbols") or execution.get("symbols") or execution.get("symbol") or ["BTC/USD"]
cfg["symbols"] = symbols if isinstance(symbols, list) else [symbols]
cfg["execution"] = execution
cfg["live"] = live
cfg["pipeline"] = pipeline

tmp = Path("/private/tmp/cbp_live_preflight_runtime.yaml")
tmp.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
out = run_preflight(str(tmp))
print(json.dumps({"ok": out.ok, "checks": out.checks, "cfg_path": str(tmp)}, indent=2))
PY
```

Expected result:

- `ok=true`
- no `ERROR` checks

## Real attempt prep sequence

Do not do this outside an explicit change window.

### 1. Backup the real runtime config

```bash
cp .cbp_state/runtime/config/user.yaml /private/tmp/user.yaml.live-attempt.bak
```

### 2. Record current branch and working tree

```bash
git rev-parse --short HEAD
git status --short
```

Expected:

- branch tip is the reviewed commit intended for the attempt
- only known unrelated untracked files, or a clean tree

### 3. Set real attempt envs in the operator shell

```bash
export CBP_MAX_TRADES_PER_DAY=_____
export CBP_MAX_DAILY_LOSS=_____
export CBP_MAX_DAILY_NOTIONAL=_____
export CBP_MAX_ORDER_NOTIONAL=_____
export CBP_EXECUTION_ARMED=YES
```

If `live.sandbox=false`, also set:

```bash
export ENABLE_LIVE_TRADING=YES
export CONFIRM_LIVE=YES
```

### 4. Update the real runtime config

The real runtime config must resolve to:

- `execution.executor_mode=live`
- `execution.live_enabled=true`
- `live.enabled=true`
- correct live venue/symbols

### 5. Run the canonical preflight again against real runtime state

```bash
./.venv/bin/python -c 'from services.preflight.preflight import run_preflight; import json; r = run_preflight(); print(json.dumps({"ok": r.ok, "checks": r.checks}, indent=2))'
```

Expected result:

- `ok=true`

## Rollback sheet

If any live-start gate or drill fails, stop and roll back in this order.

### 1. Halt live intent immediately in the operator shell

```bash
unset CBP_EXECUTION_ARMED
unset CBP_LIVE_ENABLED
unset CBP_EXECUTION_LIVE_ENABLED
unset ENABLE_LIVE_TRADING
unset CONFIRM_LIVE
```

### 2. Restore paper-mode runtime state

```bash
cp /private/tmp/user.yaml.live-attempt.bak .cbp_state/runtime/config/user.yaml
```

### 3. Force persisted live state to disabled and kill-switched

```bash
./.venv/bin/python - <<'PY'
from services.admin.live_disable_wizard import disable_live_now
import json
print(json.dumps(disable_live_now("real_live_attempt_rollback"), indent=2))
PY
```

Expected result:

- `live_enabled=false`
- persisted armed state false
- system guard `HALTED`
- kill switch armed

### 4. Re-run paper-safe status checks

```bash
./.venv/bin/python scripts/bot_status.py
./.venv/bin/python scripts/preflight_check.py
```

## Exit criteria before a real live-start attempt

All of these should be true:

- operator inputs above are filled in
- first-live limits are explicitly chosen and within Section 5 caps
- canonical real runtime preflight returns `ok=true`
- rollback owner is assigned
- Section 3 drills are being executed as a real sign-off, not as a thought exercise
