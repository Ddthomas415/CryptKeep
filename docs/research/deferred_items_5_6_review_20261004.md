# Deferred hygiene items 5 and 6: independent review, no new defect

2026-10-04. AUDITOR (Claude). Read-only. No patch, no config or account
change. Recorded so this is not repeated.

## Item 5 - backtest-to-paper fill parity

- Holds: `parity_engine.run_parity_backtest` and the paper engine both price a
  market fill as mid +/- slippage with the fee on notional
  (`fill_model.apply_fee_slippage`); the repo's parity tests pass in the full
  suite.
- The parity proof covers fill arithmetic and one replayed round trip. It does
  not cover rule parity. The rule differences between the gate's baseline
  backtest and the paper runtime are already recorded in
  `e01_paper_evidence_audit_20261002.md`, findings 11 and 12, and the
  trailing-stop part was corrected by #588
  (`docs/checkpoints/managed_exit_risk_audit_2026_09_08.md`). Re-checked today
  against the queue (read-only): the three cohort sells of 2026-06-18, 06-24
  and 07-09 carry `exit_stack_rule: trailing_stop`. Nothing new.
- Still open and the operator's: the gate counts those three round trips as
  3/5 for a rule set that no longer has that exit; its baseline
  (win rate 22.6%, avg win +78.7%, avg loss -4.1%) comes from an all-cash,
  same-close, no-stop simulation.

## Item 6 - `synthetic_mid_ohlcv` branch

- Holds: intents from the synthetic branch carry no market-data provenance
  (`evidence_extra` is only filled on the public-OHLCV branch), so their fills
  are rejected by qualification as `missing_market_data_source` and cannot
  count toward the paper gate.
- Observation, not changed: the effective `user.yaml` here still has
  `strategy_runner.signal_source: synthetic_mid_ohlcv`, strategy `momentum`,
  symbols BTC/USD, ETH/USD, SOL/USD. A runner started without the campaign's
  managed settings would trade that on one-second synthetic bars in the same
  paper account as the campaign. The April 2026 `sma_200_trend` round trips
  held for 2 to 20 minutes are consistent with that source; they predate the
  cohort and are diagnostic only.
