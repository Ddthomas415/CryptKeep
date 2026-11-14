# Engineering item 3: position cap with complete balance reading, wired into the live order path. Specification draft

Claude (Cowork), 2026-11-14 (owner: "begin working on all recommended supporting tasks", area A2). Self-checked; Codex
verifies the cited lines before building. No code changed. Live path only; it does not block the paper simulation
(PROJECT_STATE item 3 note). Bot relation: BOT_RULES (the live order path).

## 1. What exists (SHOWN, HEAD 3b49ead3f)
- The limit is parsed and never checked. `services/risk/live_risk_gates.py`: `LiveRiskLimits.max_position_notional_usd`
  (lines 23, 42-43) is read from configuration, and `start_manager.py` 47-55 refuses a start when it is missing, but
  `LiveRiskGates.check_live` (167-191) tests only per-trade notional, trades per day and daily loss. This is H-06 / CP-14 /
  C-05 in the registers.
- Two call sites: `services/execution/risk_gates.py` line 30 and `services/execution/_executor_submit.py` line 405.
- Accepted building blocks (source only, default-off, never activated):
  - the synthetic reservation model `scripts/research/synthetic_live_position_cap.py` `admit()` (lines 124-244): a
    buy is admitted only when fresh, identity-complete evidence of held units plus pending buys, bounded by a per-unit
    USD price, plus the proposal stays within `cap_usd`; sells are admitted only with complete reducing evidence;
    reservation written inside `BEGIN IMMEDIATE` in a caller-owned SQLite fixture. GATE accepted with risk
    2026-10-28 (`synthetic_live_cap_20261028_02`, 53 tests). "The accepted synthetic reservation model is not being
    reopened" (item 3 note).
  - Coinbase balance paging observation `services/execution/coinbase_balance_observation.py` (explicit policy,
    budgeted paging, withhold on failure, no `fetch_balance` fallback), integrated default-off into the sync and async
    order preflights; GATE accepted 2026-10-29 (`coinbase_paging_integration_20261029`, 211 tests). Its CLOSURE lists
    as remaining: authenticated account scope and completeness, pending/manual orders and durable reservation
    integration, live-cap enforcement.
  - `coinbase_portfolio_guard.enforce_coinbase_quote_account_available` (quote-currency account presence only).
- Blocked on the owner (item 3 note, 2026-10-30): whether the one default portfolio returned on 2026-10-29 covers all
  manual holdings and open orders; no further private call or cap-policy activation authorised.

## 2. What can be built now without the owner's answer (offline, default-off, synthetic evidence)
Wire the enforcement with an injectable evidence provider, so that the only piece waiting on the owner is the real
provider.

1. Configuration: `live_risk.position_cap_enforcement: reservation_v1` (absent = today's behaviour, unchanged).
   When present, `start_manager` requires `max_position_notional_usd > 0` (already) and a configured evidence provider
   name; an unknown provider refuses the start.
2. `check_live` gains one step after the per-trade notional check and before the daily counters: call
   `admit(connection, bucket=(venue, portfolio_id, base_asset), proposal={...}, snapshot=provider.snapshot(),
   now_ms, max_age_ms, max_skew_ms, cap_usd=limits.max_position_notional_usd, reduction=provider.reduction() for sells)`.
   Any `EvidenceError`, stale or missing snapshot, or provider exception refuses the order with a fixed-vocabulary reason
   (`POSITION_CAP_EVIDENCE_UNAVAILABLE`, `POSITION_CAP_EXCEEDED`, `POSITION_CAP_REDUCING_UNVERIFIED`); never a fallback
   to "allow". The per-unit USD bound for a buy is the intent's limit price, or for a market order the current ask times
   `(1 + slippage allowance)` from the existing quote path; no bound, no admission.
3. Both call sites pass the same intent fields; `_executor_submit.py` 405 must not bypass the step for retries.
4. Provider interface (one module, `services/risk/position_cap_evidence.py`): `snapshot()` returns held units per base
   asset, pending buy units, as_of and received times, identity_complete and pending_orders_complete flags;
   `reduction(base)` returns held units, pending sell units and the same flags. Two implementations now: `synthetic`
   (test fixture) and `coinbase_paging_v1` constructed from the accepted balance observation plus open orders, with
   `identity_complete=False` until the owner's account-scope answer is recorded, so the real provider refuses every
   buy until then (fail-closed by construction, not by instruction).
5. Reservation store: the existing exec DB (`default_exec_db()`), one KV table owned by `admit()`'s prefixed key, so
   two concurrent intents cannot both pass the cap.

## 3. Tests (each must fail before the wiring and pass after)
- With `reservation_v1` configured and the synthetic provider: a buy that would take held + pending + proposal over the
  cap is refused with `POSITION_CAP_EXCEEDED`; one just under is admitted and reserved; a second identical buy in the
  same instant is refused (reservation); a sell with complete reducing evidence is admitted; a sell for more than held
  minus pending sells is refused.
- Evidence stale beyond `max_age_ms`, clock skew beyond `max_skew_ms`, missing flags, provider exception: refused with
  `POSITION_CAP_EVIDENCE_UNAVAILABLE`; no order reaches the exchange adapter (assert the adapter mock is not called).
- Configuration absent: byte-identical behaviour to HEAD on the existing live-gate tests (parity run).
- `coinbase_paging_v1` with `identity_complete=False`: every buy refused; sells still require reducing evidence.
- Both call sites covered (risk_gates.py 30, _executor_submit.py 405).

## 4. Remains the owner's
- The account-scope answer (does the default portfolio cover all holdings and open orders), which flips
  `identity_complete` for the real provider; any private API call to establish it; activation of the policy in
  configuration; the live-trading permission itself.

## 5. Prior work cited (not rebuilt)
H-06 (2026-10-13), CP-14 (capital_protection_audit_20261031), C-05 (open caveats), item 3 note 2026-10-30,
`synthetic_live_cap_20261028_02`, `coinbase_paging_integration_20261029`, `ed002_live_cap_review_20261028`.
