# Independent review: ES durable paper-fill identity storage slice (2026-10-09)

Reviewer: Claude (cloud session), not the author. ~22:14 UTC. Read-only; no code edited.
Reviewed: git diff of storage/paper_trading_sqlite.py (+19) and services/execution/paper_engine.py (+28);
docs/checkpoints/es_durable_fill_identity_2026_10_09.md; services/strategies/execution_identity.py.
Reproduced: the checkpoint's five-file command -> 46 passed (system python3 3.10; the repo .venv interpreter does
not resolve inside the laptop Linux VM, so the venv itself was not exercised).

## Recommendation: ACCEPT WITH RISK (storage slice only). Human acceptance still required.

Confirmed by reading and tests:
- Evidence is written in the same BEGIN IMMEDIATE transaction as fill insert, cash/position and order status; any
  exception triggers ROLLBACK and re-raise (test_bad_evidence_rolls_back_accounting).
- Idempotent retry returns before the evidence write, so an existing fill can never be relabeled; legacy fills are
  never backfilled (tests cover both).
- Getter returns {"execution_identity_fill_status": "invalid_storage"} for non-dict/corrupt content - never a
  verification claim.
- Engine evidence is produced only after identity_rejection_reasons passes and canonical_identity re-encodes the
  payload with allow_nan=False and strict type checks, and only when the declared costs equal the engine's
  fee/slippage/quote/basis; market venue/symbol must match the order. Any failure -> pure-string invalid marker.

## Findings
1. LOW - new failure source inside the fill transaction. json.dumps(allow_nan=False) can now abort a paper fill
   (including an exit). For engine-produced evidence this is effectively unreachable (payload already passed
   canonical_identity; the invalid marker is strings only), so the risk is theoretical. Documented by the author.
2. LOW (pre-existing, not introduced here) - in PaperEngine's fill loop an exception from _apply_fill propagates
   and stops the remaining orders of that cycle. Any DB error already did this; the slice does not widen it in
   practice. Worth a separate ticket if exits must be isolated per order.
3. NOTE - the evidence proves agreement with the declared paper cost policy only (not real costs/slippage), as the
   checkpoint states. No schema change; key namespace fill_execution_identity:<fill_id> in paper_state.

## What still separates this from a working evidence chain (verified by grep, 2026-10-09)
A. Journal transfer NOT done: services/execution/intent_reconciler.py _journal_identity_extra() still writes
   journal_identity_status "order_policy_only", fill_cost_policy_verified False; it never calls
   PaperTradingSQLite.get_fill_execution_identity(fill_id). Needed: per fill, copy the stored fill evidence; set
   fill_cost_policy_verified True only when stored status == "cost_policy_verified" AND the stored identity sha
   equals the order's; missing -> "missing_fill_evidence", corrupt -> "invalid_storage"; never upgrade an already
   journaled row (journal insert is first-write-wins today - keep it).
B. Gate integration NOT done: services/control/paper_evidence_qualification.py, paper_gate_qualification_report.py
   and paper_promotion_policy.py contain no reference to execution_identity / fill_cost_policy_verified. Whether
   unverified fills should stop counting toward promotion is an OPERATOR policy decision, not an engineering one.
