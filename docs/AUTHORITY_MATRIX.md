# CryptKeep — Authority Matrix & Source-of-Truth Matrix

## Authority Matrix

Defines who may perform each production-affecting action. "System" means the
action is automated and requires no human input. "OPERATOR" means any
authenticated dashboard user with the OPERATOR role. "ADMIN" means only the
account with ADMIN role. "Any" means any process or script.

| Action | Who may perform | How |
|---|---|---|
| Arm live trading | OPERATOR | Dashboard → Operations → Resume Live Trading button |
| Halt live trading | OPERATOR, System (watchdog, stop_bot) | Dashboard halt button, or `stop_bot.py`, or watchdog automatic |
| Resume after halt | OPERATOR | Dashboard → Operations → Resume Live Trading button (calls `resume_if_safe`) |
| Override reconciliation | ADMIN only | CLI only — no dashboard path |
| Approve config changes with trading impact | OPERATOR | Must save via dashboard or commit + deploy |
| Change live risk limits (`CBP_MAX_*`) | ADMIN | Environment variable change + process restart |
| Rotate API credentials | ADMIN | Keyring or `.env` update + process restart |
| Force-delete a stuck intent | ADMIN | CLI only — `sqlite3` direct or admin script |
| Merge code to `master` | Repository owner | GitHub PR + CI pass |
| Enable a new strategy in paper mode | OPERATOR | Dashboard → Operations → Strategy Controls |
| Promote paper config to live | OPERATOR + explicit live arming | Operations page live arming sequence |
| Push to origin | Repository owner | `git push` after local validation |

### Hard rules

- No action in the "ADMIN only" row may be performed from the dashboard.
- `resume_if_safe()` checks `live_guard` before setting RUNNING — it cannot
  be bypassed from the UI.
- `disable_live_now()` is always available to OPERATOR. There is no role
  restriction on halting.
- A process restart is required for any environment variable change to take
  effect. Config file changes take effect on next tick via mtime cache.

---

## Source-of-Truth Matrix

Defines which component is authoritative for each data type, and what happens
when internal state and external (venue) state disagree.

### Orders

| Situation | Authority | Action |
|---|---|---|
| Order submitted, no exchange response yet | Internal (`live_intent_queue`, status=`submitted`) | Wait for reconciler |
| Exchange confirms filled | Exchange | Reconciler sets `filled`, writes fill to `live_trading_sqlite` |
| Exchange confirms canceled | Exchange | Reconciler sets `canceled` |
| Exchange says not found, order is < staleness threshold | Internal | Leave as `submitted`, retry next cycle |
| Exchange says not found, order is > `CBP_STALE_ORDER_SEC` | Exchange wins | Reconciler sets `error: stale_order_not_found` |
| Internal says submitted, exchange says open | Exchange | Status stays `submitted`, no action |
| Internal says filled, exchange disagrees | **Internal wins** — do not regress a terminal state | `_ALLOWED_STATUS_TRANSITIONS` blocks this |

### Fills

| Situation | Authority | Action |
|---|---|---|
| Fill arrives via WebSocket | Exchange | `CanonicalFillSink.on_fill()` records it — idempotent via `fill_id` |
| Fill arrives via reconciler poll | Exchange | Inserted into `live_trading_sqlite` via `ldb.insert_fill()` |
| Duplicate fill event (same `fill_id`) | `INSERT OR IGNORE` wins | Silently discarded |
| Fill with no `fill_id` | `fill_hook.py` synthesizes a deterministic hash key | Treated as idempotent |

### Positions

| Situation | Authority | Action |
|---|---|---|
| Position calculated from fills | `PnLStoreSQLite` | Authoritative for paper mode PnL |
| Position calculated from exchange | `live_trading_sqlite` via reconciler | Authoritative for live mode open positions |
| Disagreement between the two | Live path wins for live mode | Paper store is not used in live execution path |

### Balances

| Situation | Authority | Action |
|---|---|---|
| Pre-submission balance check | Exchange (live fetch via `_enforce_funding_gate`) | Raises `CBP_ORDER_BLOCKED:insufficient_spendable_balance` if insufficient |
| Balance for risk gate decisions | Exchange (live fetch) | Not cached — fetched fresh per submission |
| Balance displayed in dashboard | Dashboard service snapshot | May be slightly stale — informational only |

### Config

| Situation | Authority | Action |
|---|---|---|
| `config/trading.yaml` change | File on disk | Takes effect on next tick (mtime-cached in `_load_yaml_cached`) |
| `config/user.yaml` change | File on disk | Takes effect on next page load in dashboard |
| Environment variable change | Process environment | Requires process restart to take effect |
| In-flight change during active trading | Previous value continues until next tick | No hot-swap of risk limits mid-tick |

### Market data

| Situation | Authority | Action |
|---|---|---|
| Tick data for gate decisions | `tick_reader.py` flat file (written by tick publisher) | If stale > `max_ws_recv_age_ms`, submission is blocked |
| Bid/ask for spread gate | Same flat file | `market_quality_guard` reads it — no network call on hot path |
| Stale tick (publisher stopped) | Submission blocked | `_check_market_freshness_for_live()` enforces this |

### System guard state

| Situation | Authority | Action |
|---|---|---|
| Guard file says HALTED | File wins — no orders submitted | `_hard_off_guard()` checks this before every submit cycle |
| Guard file says RUNNING but kill switch is ON | Kill switch wins | `live_guard.live_allowed()` checks both |
| Guard file missing or corrupt | Fail closed — treated as HALTED | `get_system_guard_state(fail_closed=True)` behavior |
| Guard says HALTING | Reconciler runs cleanup mode, then promotes to HALTED | `_maybe_promote_system_guard_halted()` |
