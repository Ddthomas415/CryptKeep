# Root Runtime Launch Blockers

Status: INCOMPLETE

## Snapshot
- Repo truth docs updated: yes
- Scope record present: yes
- Trading config comment aligned: yes
- External sandbox proof present: blocked by venue availability from current environment
- Private authenticated connectivity proof present: partial
- Live lifecycle authority fully governed: no
- Live-mode source of truth singular: no

## Scope
This note tracks the visible launch blockers for the root runtime baseline only.
It does not automatically include companion trees or broader governance surfaces unless explicitly pulled into scope.

Canonical scope record:
- docs/checkpoints/root_runtime_scope_record.md

Next actions board:
- docs/checkpoints/root_runtime_next_actions.md

## Confirmed launch blockers

### 1. Freeze launch scope
Why it exists:
- The repo direction and the active runtime/config story are not fully aligned.

Evidence:
- README.md
- DECISIONS.md
- config/trading.yaml

Close condition:
- One canonical scope record names:
  - in-scope tree
  - operator path
  - deployment path
  - supported venue path
  - out-of-scope companion surfaces

Risk:
- Medium

Review lane:
- Same-thread acceptable if doc-only

---

### 2. Configure one sandbox venue locally
Why it exists:
- External runtime validation cannot start without local sandbox credentials/config.

Evidence:
- Coinbase credentials are present through the approved keyring path
- Binance credentials are present through the approved keyring path
- Coinbase authenticated proof only works in this repo/client path with `sandbox=False`
- Binance sandbox/testnet returned HTTP `451` from `testnet.binance.vision` on April 8, 2026
- Gate.io is not presently reachable/usable from the current operator environment

Close condition:
- One supported and reachable sandbox/testnet venue is configured locally through the approved mechanism

Risk:
- Medium

Review lane:
- Same-thread acceptable if no execution-path code changes

---

### 3. Prove private authenticated connectivity
Why it exists:
- Live-readiness cannot advance without private exchange proof.

Evidence:
- Coinbase private authenticated connectivity is captured in:
  - `docs/checkpoints/private_connectivity_and_readonly_lifecycle_evidence.md`
- Confirmed successful for Coinbase with:
  - credentials source: keyring
  - `sandbox=False`
  - read-style probes for balance, open orders, and trade history
- Binance private connectivity is still externally blocked from the current location because Binance testnet returned HTTP `451` on April 8, 2026

Close condition:
- Redacted record showing:
  - private auth success/failure
  - permission/read probe result
  - venue used
  - credential source used

Risk:
- Low

Review lane:
- Same-thread acceptable

---

### 4. Prove private lifecycle runtime flow
Why it exists:
- Paper-only classification cannot advance without real placement/fetch/cancel/reconcile evidence.

Evidence:
- Coinbase authenticated read-only proof is complete, but no supported Coinbase sandbox path is available in the current repo/client combination
- Binance sandbox lifecycle proof is blocked by external HTTP `451` venue restriction from the current location
- Gate.io sandbox lifecycle proof is blocked by current operator-environment access constraints

Close condition:
- Redacted sandbox evidence for:
  - order placement
  - fetch/status reconciliation
  - cancel
  - post-cancel verification

Risk:
- Low for validation
- High if runtime code changes are needed

Review lane:
- Validation same-thread acceptable
- Implementation requires independent review

---

### 5. Resolve active live lifecycle authority gap
Why it exists:
- Active live reconcile/fetch paths still use direct exchange lifecycle reads.

Evidence:
- services/execution/live_executor.py
- services/execution/exchange_client.py
- docs/safety/lifecycle_matrix.md
- docs/checkpoints/live_lifecycle_gap_note.md

Close condition:
- Either:
  - all active live lifecycle paths route through one governed lifecycle boundary
- Or:
  - the supported live path is explicitly narrowed and documented to exclude bypassed paths

Risk:
- High

Review lane:
- READY_FOR_INDEPENDENT_REVIEW

---

### 6. Collapse live-mode source of truth
Why it exists:
- Multiple persisted live-enable flags and inconsistent arming inputs still exist.

Evidence:
- docs/safety/live_mode_contract.md
- docs/checkpoints/live_mode_source_of_truth_note.md

Close condition:
- One persisted live-enable source
- One sandbox selector
- One final arming contract
- Matching docs/tests

Risk:
- High

Review lane:
- READY_FOR_INDEPENDENT_REVIEW

## Launch-support tasks

### A. Align docs/config with actual supported state
Evidence:
- config/trading.yaml now states that paper is the default and that live-capable surfaces exist, but live readiness is not yet established
- the scope record and blocker list should continue to reflect that same repo truth

Close condition:
- Operator-facing docs and active config describe the same supported state

### B. Remove or fence hidden defaults on launch-capable paths
Evidence:
- defaults such as venue=coinbase and symbol=BTC/USD previously existed on runtime-capable paths
- docs/checkpoints/hidden_defaults_note.md

Current status:
- the canonical operator/config path now requires explicit venue/symbol inputs in:
  - `scripts/run_bot_safe.py`
  - `scripts/bot_ctl.py`
  - `services/execution/live_executor.py`
- hidden-default cleanup outside the fully verified canonical operator path may still remain
- active pipeline config defaults were also tightened in `services/pipeline/ema_strategy.py`
- runtime pipeline scripts were also tightened to require explicit exchange, symbol, and mode in config

Current status:
- Coinbase submit path now blocks locally when the bound portfolio lacks the required quote account for the requested symbol
- This prevents invalid BTC/USD submit attempts from reaching Coinbase on portfolios without USD funding

Close condition:
- Venue, symbol, mode, and account are explicit on the chosen launch path

### C. Produce launch evidence packet
Close condition:
- One packet containing:
  - restart/recovery drill
  - kill-switch drill
  - reconciliation halt/resume drill
  - rollback drill
  - supported venue lifecycle evidence, or an explicit environment-blocked exception record

## Non-blocking repo discipline
- Keep compatibility layers frozen
- Align REMAINING_TASKS.md with actual remaining work
