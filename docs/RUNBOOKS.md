# CryptKeep — Incident Severity Matrix & Operator Runbooks

---

## Severity Matrix

| Severity | Definition | Examples | Response time | First action |
|---|---|---|---|---|
| **SEV-1** | Live capital at risk. Orders may be uncontrolled or system cannot halt. | Executor submitting orders after halt button pressed. Kill switch not responding. Runaway order loop. | Immediate | Runbook R1 |
| **SEV-2** | Live trading halted by system. No capital at risk. Operator action required to diagnose and resume. | System guard HALTED after watchdog trip. Reconciliation drift exceeded. Exchange WebSocket dropped and not recovered. | Within 15 minutes | Runbook R2 |
| **SEV-3** | Degraded operation. Paper mode only or informational. No live capital at risk. | Paper fill rate dropped. Evidence collector stopped. Preflight warning. Config validation failure. | Within 1 hour | Runbook R3 |

---

## Escalation rules

- SEV-1: Do not investigate before halting. Halt first, investigate after.
- SEV-2: Do not resume without completing the relevant runbook checklist.
- SEV-3: Document the issue before fixing. Do not rush.
- Downgrade only after confirming the capital risk has been eliminated.
- All SEV-1 events require a written post-incident summary within 24 hours.

---

## R1 — Executor won't halt / orders uncontrolled

**When to use:** Halt button pressed but orders continue. Kill switch shows
ARMED in dashboard but orders still submitting. Runaway submission detected.

### Step 1 — Force halt via CLI (do this first, before anything else)

```bash
cd /path/to/CryptKeep
python3 -c "
from services.admin.live_disable_wizard import disable_live_now
result = disable_live_now(note='emergency_r1')
print(result)
"
```

If that fails:

```bash
python3 scripts/stop_bot.py --all
```

If that fails, kill all python processes:

```bash
pkill -f "live_executor"
pkill -f "run_live"
```

### Step 2 — Verify halt at exchange level

Log into Coinbase/Binance manually. Cancel any open orders that should not be there.

### Step 3 — Verify system guard state

```bash
python3 -c "
from services.admin.system_guard import get_state
print(get_state(fail_closed=False))
"
```

Expected: `state: HALTED`. If not HALTED, set it manually:

```bash
python3 -c "
from services.admin.system_guard import set_state
set_state('HALTED', writer='manual_r1', reason='emergency_force_halt')
"
```

### Step 4 — Verify kill switch is armed

```bash
python3 -c "
from services.admin.kill_switch import get_state
print(get_state())
"
```

Expected: `armed: True`. If not, arm it:

```bash
python3 -c "
from services.admin.kill_switch import set_armed
set_armed(True, note='manual_r1')
"
```

### Step 5 — Document what happened

Record: time of first anomalous order, time of halt, any orders that need
manual cancellation, system guard state before and after.

### Step 6 — Do not resume until root cause is identified

See R2 for resume procedure.

---

## R2 — Live trading halted by system, needs operator resolution

**When to use:** Dashboard shows system guard HALTED or HALTING. Reconciliation
drift alert. Exchange WebSocket disconnected and did not recover. Watchdog tripped.

### Step 1 — Read the current system state

```bash
python3 -c "
from services.admin.live_disable_wizard import status
import json
print(json.dumps(status(), indent=2))
"
```

This shows: live_enabled, kill_switch_armed, system_guard state.

### Step 2 — Read the reconciliation state

```bash
python3 -c "
from services.admin.state_report import get_state_report
import json
print(json.dumps(get_state_report(), indent=2))
"
```

Check for: any intents stuck in `submitted` state, any fills with no matching intent, any reconciliation exceptions.

### Step 3 — Read recent managed-service logs

```bash
tail -100 .cbp_state/runtime/logs/market_ws.log | grep -E "ERROR|WARNING|SAFE-IDLE|watchTicker"
tail -100 .cbp_state/runtime/logs/intent_consumer.log | grep -E "ERROR|WARNING|EXCEPTION"
tail -100 .cbp_state/runtime/logs/reconciler.log | grep -E "ERROR|WARNING|stale"
```

If `CBP_STATE_DIR` is set, use `$CBP_STATE_DIR/runtime/logs/...` instead of `.cbp_state/runtime/logs/...`.

### Step 4 — Identify cause from the checklist below

| System guard shows | Likely cause | Action |
|---|---|---|
| HALTING | Watchdog tripped — reconciler should promote to HALTED on next cycle | Wait one reconciler cycle, then check again |
| HALTED (watchdog) | Watchdog detected unhealthy condition | Check watchdog logs, fix condition, then resume |
| HALTED (stop_bot) | Operator-initiated stop | Normal — resume when ready |
| HALTED (safe_mode_recovery) | Stale RUNNING state on startup | Normal auto-recovery — review why it was stale |

### Step 5 — Resolve any stuck intents

If intents are stuck in `submitted` and the exchange confirms they are filled or canceled:

```bash
python3 -c "
from storage.execution_store_sqlite import ExecutionStore
s = ExecutionStore()
# List stuck submitted intents
intents = s.list_intents(mode='live', exchange='coinbase', symbol='BTC/USDT', status='submitted', limit=50)
for i in intents:
    print(i['intent_id'], i['status'], i['reason'])
"
```

Manually resolve confirmed fills by setting status in the DB — only do this
if you have confirmed the exchange state by logging in manually.

### Step 6 — Resume (only after cause is resolved)

```bash
python3 -c "
from services.admin.resume_gate import resume_if_safe
import json
result = resume_if_safe(note='operator_r2_resume')
print(json.dumps(result, indent=2))
"
```

If resume is blocked, the output will show the reason. Fix the blocking
condition before retrying.

### Step 7 — Monitor for one full cycle after resume

Watch the market WS, intent consumer, and reconciler logs for 5 minutes after resuming to confirm
normal operation:

```bash
tail -f .cbp_state/runtime/logs/market_ws.log .cbp_state/runtime/logs/intent_consumer.log .cbp_state/runtime/logs/reconciler.log
```

---

## R3 — Degraded operation (paper mode / informational)

**When to use:** Paper fill rate dropped. Evidence collector stopped.
Preflight warning. Config validation error. Non-critical service stopped.

### Step 1 — Run preflight

```bash
python3 -c "
from services.preflight.preflight import run_preflight
import json
r = run_preflight()
print(json.dumps({'ok': r.ok, 'checks': r.checks}, indent=2))
" | grep -A2 '"ok": false'
```

### Step 2 — Check service status

In the dashboard → Operations → Service Controls, run Status on each service.

Or from CLI:

```bash
python3 scripts/bot_status.py
```

### Step 3 — Run diagnostics

```bash
python3 -c "
from services.admin.system_diagnostics import run_diagnostics
import json
print(json.dumps(run_diagnostics(), indent=2))
"
```

### Step 4 — Restart stopped services

From dashboard → Operations → Service Controls → select service → Start.

Or via CLI:

```bash
python3 scripts/start_bot.py
```

### Step 5 — Document and monitor

Log the issue with a timestamp. Monitor for recurrence. If the same SEV-3
issue recurs within 24 hours, escalate to SEV-2.

---

## R4 — Duplicate order suspected

**When to use:** You believe the same order was submitted twice to the exchange.

### Step 1 — Halt immediately

See R1 Step 1.

### Step 2 — Check fills table for duplicates

```bash
python3 -c "
import sqlite3
c = sqlite3.connect('data/execution.sqlite')
rows = c.execute('''
    SELECT trade_id, COUNT(*) as cnt
    FROM fills
    GROUP BY trade_id
    HAVING cnt > 1
''').fetchall()
for r in rows:
    print(r)
c.close()
"
```

### Step 3 — Check dedup store

```bash
python3 -c "
from storage.order_dedupe_store_sqlite import OrderDedupeStore
s = OrderDedupeStore(exec_db='data/execution.sqlite')
# Inspect recent claims
import sqlite3
c = sqlite3.connect('data/execution.sqlite')
rows = c.execute('SELECT * FROM order_dedup ORDER BY claimed_at DESC LIMIT 20').fetchall()
for r in rows:
    print(dict(r))
c.close()
"
```

### Step 4 — Check exchange directly

Log into Coinbase/Binance and verify how many orders were actually placed.
Cancel any duplicate open orders immediately.

### Step 5 — Document for post-incident review

Record all intent IDs, client_order_ids, exchange order IDs, and fill IDs
involved. The dedup mechanism should have prevented this — if it failed,
that is a bug requiring investigation before resuming.

---

## R5 — Config change caused unexpected behavior

**When to use:** A config change was deployed and the system is behaving
unexpectedly (orders at wrong notional, wrong symbols, unexpected halts).

### Step 1 — Halt immediately

See R1 Step 1.

### Step 2 — Identify what changed

```bash
git diff HEAD~1 config/
git log --oneline -5
```

### Step 3 — Revert the config change

```bash
git revert HEAD  # if the config change was in a commit
# or manually restore the previous values
```

### Step 4 — Run preflight to confirm revert is clean

```bash
python3 -c "
from services.preflight.preflight import run_preflight
r = run_preflight()
print('ok:', r.ok)
"
```

### Step 5 — Resume only after preflight passes

See R2 Step 6.

---

## Post-incident summary template

Fill this out within 24 hours of any SEV-1 or SEV-2 incident.

```
Date and time of incident:
Severity:
Duration (from first alert to resolution):

What happened (factual, no speculation):

What capital was at risk (if any):

How was it detected:

How was it halted:

Root cause:

Fix applied:

How to prevent recurrence:

Git commit(s) that fix the issue:

Reviewed by:
Date of review:
```
