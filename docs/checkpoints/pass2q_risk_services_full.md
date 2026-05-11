# Pass 2Q — Risk Services Full Audit

**Date:** 2026-05-10
**Pass:** 2Q — all 21 files in services/risk/
**Status:** COMPLETE

---

## SHOWN findings

### Finding 1 — exit_rules.evaluate_exit always returns False (Medium)

```python
# Phase IJ: Exit Rules
def evaluate_exit(position, bar):
    return False
```

Unimplemented stub. Any caller expecting exit rule evaluation gets False
unconditionally. Strategy exit logic lives entirely in pipeline/strategy code.

---

### Finding 2 — live_safety_state.snapshot() fails to kill_switch=False (Shown, dead code)

```python
return {'kill_switch': False, 'cooldown_until': 0.0}   # default on error
```

Fails to trading-allowed on error. Opposite to admin/kill_switch.py which
fails to ARMED. Confirmed dead code — no production caller.

---

### Finding 3 — LiveRiskLimits.from_dict fails closed correctly (Strength)

Missing or zero any limit returns None. Positive required on all four.
Execution path uses from_dict(user_yaml_cfg) not from_trading_yaml.

---

### Finding 4 — canonical_runtime.json referenced but may not exist (Medium)

`from_trading_yaml()` reads from `config_dir() / 'canonical_runtime.json'`.
If missing: returns None, logs error. `risk_gates.py:23` uses as fallback:
`cfg_limits = limits or LiveRiskLimits.from_trading_yaml()`.
Primary execution path (_executor_submit.py) uses from_dict — not affected.

---

### Finding 5 — kill_conditions and performance_kill have sensible defaults (Strength)

kill_conditions: 5 consecutive risk blocks -> kill, 20 loop cooldown.
performance_kill: 3 losing exits, 10% drawdown, 50 loop cooldown. Configurable.

---

### Finding 6 — exposure_controls limits 1 open intent per symbol (Strength)

`max_open_intents_per_symbol: 1` default. Prevents stacking paper positions.

---

### Finding 7 — market_quality_guard block_when_unknown=False (Shown)

Default: unknown tick data does NOT block trading. For live + WS ticks,
operator should set block_when_unknown: True explicitly.

---

### Finding 8 — staleness_guard 5-second freshness default (Strength)

Correct for real-time trading. Reads from canonical health snapshot.

---

## services/risk/ FULLY COVERED (21 of 21 files)

## New High finding — H8

`live_safety_state.snapshot()` fails to kill_switch=False (trading allowed)
on error — opposite direction from admin/kill_switch.py (ARMED). Currently
dead code (no production caller). Dangerous if ever wired into execution.

## Updated findings

| # | Severity | Finding |
|---|---|---|
| H4 | High | Governance dead code |
| H5 | High | resume_if_safe disconnected |
| H6 | High | Soak evidence invisible to promotion gate |
| H7 | High | enforce_direct_origin_block dead code |
| H8 | High | live_safety_state wrong fail-safe (dead code) |
| H1-H3 | Medium | VIEWER role boundary |

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2Q
**Next:** services/signals/ (all 13 files) or services/execution/ remaining 68 files
