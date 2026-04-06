# CryptKeep — Launch Evidence Checklist

This checklist must be completed and passing before live mode may be armed
with real capital. It is a pass/fail gate, not a judgment call.

Complete each section in order. Do not skip sections. Record the result
(PASS / FAIL / N/A) and the date for each item.

---

## Section 1 — Environment

| # | Check | Result | Date |
|---|---|---|---|
| 1.1 | `python3 -m pytest tests -q` passes with 0 failures | | |
| 1.2 | `python3 tools/repo_doctor.py --strict --json` passes | | |
| 1.3 | `python3 -m py_compile` passes on all changed files | | |
| 1.4 | `git status` shows clean working tree | | |
| 1.5 | Branch is ahead of origin (changes are tracked) | | |

---

## Section 2 — Configuration

| # | Check | Threshold | Result | Date |
|---|---|---|---|---|
| 2.1 | `CBP_MAX_TRADES_PER_DAY` is set and > 0 | Required | | |
| 2.2 | `CBP_MAX_DAILY_LOSS` is set and > 0 | Required | | |
| 2.3 | `CBP_MAX_DAILY_NOTIONAL` is set and > 0 | Required | | |
| 2.4 | `CBP_MAX_ORDER_NOTIONAL` is set and > 0 | Required | | |
| 2.5 | `CBP_MAX_ORDER_NOTIONAL` ≤ `CBP_MAX_DAILY_NOTIONAL` | Logical consistency | | |
| 2.6 | `config/trading.yaml` `mode:` is set to `live` | Required | | |
| 2.7 | `config/user.yaml` is in `.gitignore` (not tracked) | Required | | |
| 2.8 | API keys are in keyring or `.env`, not in YAML files | Required | | |
| 2.9 | Preflight passes in live mode with no ERROR checks | `run_preflight()` returns `ok=True` | | |

---

## Section 3 — Drills

Each drill must be run and the observed behavior recorded. A drill is only
PASS if the system behaved as specified — not just if it didn't crash.

### Drill 3.1 — Kill switch drill

**Steps:**
1. Start the live executor in paper mode
2. While it is running, arm the kill switch via the dashboard halt button
3. Observe that no new orders are submitted after the button is pressed
4. Confirm system guard shows HALTED in dashboard Operations page

**Pass criteria:** No orders submitted after halt. System guard = HALTED within 2 ticks.

| Result | Observed behavior | Date |
|---|---|---|
| | | |

---

### Drill 3.2 — Restart drill

**Steps:**
1. Submit a paper intent so it is in `submitted` state
2. Kill the live executor process (`kill -9 <pid>`)
3. Restart the executor
4. Confirm the intent is still in `submitted` state (not duplicated, not lost)
5. Confirm no duplicate order was submitted

**Pass criteria:** Intent state is consistent after restart. No duplicate order.

| Result | Observed behavior | Date |
|---|---|---|
| | | |

---

### Drill 3.3 — Stale data drill

**Steps:**
1. Stop the tick publisher while the executor is running
2. Wait 10 seconds (longer than `max_ws_recv_age_ms`)
3. Confirm the executor blocks new submissions with `LIVE blocked` reason
4. Restart the tick publisher
5. Confirm submissions resume within 2 ticks

**Pass criteria:** Submissions blocked during stale period. Resume after publisher restart.

| Result | Observed behavior | Date |
|---|---|---|
| | | |

---

### Drill 3.4 — Reconciliation drift drill

**Steps:**
1. Manually set an intent to `submitted` in the DB with a fake exchange order ID
2. Run the reconciler
3. Confirm the reconciler detects the order cannot be found after the stale threshold
4. Confirm the intent moves to `error: stale_order_not_found`

**Pass criteria:** Stale intent detected and marked error within one reconciler cycle after threshold.

| Result | Observed behavior | Date |
|---|---|---|
| | | |

---

### Drill 3.5 — WebSocket reconnect drill

**Steps:**
1. Start the full stack (tick publisher + executor)
2. Kill the WebSocket connection (stop and restart the tick publisher)
3. Confirm no orders are submitted during the gap (stale data gate trips)
4. Confirm normal operation resumes within 2 ticks of publisher restart

**Pass criteria:** No orders during gap. Automatic recovery without manual intervention.

| Result | Observed behavior | Date |
|---|---|---|
| | | |

---

### Drill 3.6 — Rollback drill

**Steps:**
1. Deploy a config change that sets `CBP_MAX_ORDER_NOTIONAL` to 0
2. Run preflight — confirm it fails with an ERROR
3. Revert the config change
4. Run preflight again — confirm it passes

**Pass criteria:** Preflight correctly blocks bad config. Recovery is one config change + restart.

| Result | Observed behavior | Date |
|---|---|---|
| | | |

---

## Section 4 — Paper trading gate

| # | Check | Threshold | Result | Date |
|---|---|---|---|---|
| 4.1 | Minimum paper trading duration | ≥ 7 days of continuous operation | | |
| 4.2 | Paper fill rate matches expected strategy frequency | ≥ 80% of expected signals resulted in intents | | |
| 4.3 | No reconciliation exceptions in paper logs | 0 unresolved exceptions | | |
| 4.4 | No duplicate fill events in paper run | 0 duplicate trade_ids in fills table | | |
| 4.5 | Paper PnL is within expected range for the strategy | Not deeply negative over the paper period | | |
| 4.6 | All Phase 1–4 audit tasks are committed | All 24 build plan tasks closed | | |

---

## Section 5 — First live notional cap

| # | Setting | Required value | Configured value | Date |
|---|---|---|---|---|
| 5.1 | `CBP_MAX_ORDER_NOTIONAL` for first live run | ≤ $25 USD | | |
| 5.2 | `CBP_MAX_DAILY_NOTIONAL` for first live run | ≤ $50 USD | | |
| 5.3 | `CBP_MAX_DAILY_LOSS` for first live run | ≤ $25 USD | | |
| 5.4 | `CBP_MAX_TRADES_PER_DAY` for first live run | ≤ 5 | | |

These are the first-live maximums. They can be raised after 7 days of
stable live operation with no reconciliation exceptions.

---

## Section 6 — Sign-off

This checklist is COMPLETE when all items in Sections 1–5 are marked PASS
and all drills have a recorded observed behavior.

| Field | Value |
|---|---|
| Completed by | |
| Date completed | |
| Git commit at time of sign-off | |
| First live notional cap confirmed | |
| Branch pushed to origin | |

**Do not arm live trading until this checklist is signed off.**
