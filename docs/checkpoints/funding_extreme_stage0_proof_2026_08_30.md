# Funding Extreme Stage 0 Proof - 2026-08-30

Status: accepted isolated Stage 0 wiring proof; not promotion evidence.

This checkpoint records the terminal result for the one-shot
`funding_extreme_default` Stage 0 run started during
`docs/checkpoints/runtime_check_2026_08_30.md`.

## Scope

- SHOWN: isolated state directory:
  `.cbp_state_challengers/funding_extreme_default`.
- SHOWN: no `--daily-loop` was used.
- SHOWN: no persistent campaign manifest was changed.
- SHOWN: no live routing, live execution, or canonical paper campaign behavior
  was changed.
- SHOWN: the verifier is read-only.

## Run Contract

The accepted run used:

- strategy: `funding_extreme`
- session strategy id: `funding_extreme_default`
- symbol: `BTC/USDT`
- OHLCV venue: `coinbase`
- signal source: `public_ohlcv_5m`
- strategy context venue: `okx`
- strategy context symbol: `BTC/USDT:USDT`
- strategy context source: `live_public`
- commit: `4e21a4c69`

The collector command was the readiness-generated one-shot command using
`CBP_CRYPTO_EDGE_DB_PATH` and `--strategy-context-db-path` so the isolated
challenger state consumed the canonical read-only crypto-edge store instead of
requiring manual edge-store seeding.

## Terminal Result

The 900-second one-shot run completed:

- SHOWN: `status=completed`
- SHOWN: `reason=completed`
- SHOWN: run ended at `2026-08-30T08:29:03.263926+00:00`
- SHOWN: strategy runtime was `903.7023799419403` seconds
- SHOWN: `signal_action=hold`
- SHOWN: `signal_changed=false`
- SHOWN: `enqueued_total=0`
- SHOWN: `fills_delta=0`
- SHOWN: `closed_trades_delta=0`
- SHOWN: `net_realized_pnl_delta=0.0`
- SHOWN: evidence cycle skipped with `paper_history_unchanged`

This is a clean wiring proof. It is not an actionable-fill proof and does not
show profitability.

## Verification

The default verifier invocation first failed because the saved baseline was
stale:

```bash
make funding-stage0-verify
```

SHOWN blockers:

- `completed_session_expected_commit`: expected `fd7f11e9c`, actual
  `4e21a4c69`
- `completed_session_public_ohlcv`: baseline expected OHLCV venue `okx`, while
  the accepted readiness-generated run used OHLCV venue `coinbase`

The explicit-contract verifier then passed against the actual approved run:

```bash
./.venv/bin/python scripts/verify_funding_stage0_proof.py \
  --expected-commit 4e21a4c69 \
  --symbol BTC/USDT \
  --venue coinbase \
  --signal-source public_ohlcv_5m \
  --strategy-context-symbol BTC/USDT:USDT \
  --strategy-context-venue okx \
  --strategy-context-source live_public
```

SHOWN result:

- `status=passed`
- `blocking_checks=0`
- artifact JSON:
  `.cbp_state/data/funding_stage0_verification/funding_stage0_verification.latest.json`
- artifact markdown:
  `.cbp_state/data/funding_stage0_verification/funding_stage0_verification.latest.md`

## Decision Boundary

This proof confirms:

- the managed paper collector can run `funding_extreme`;
- the runner can pair Coinbase public OHLCV with OKX live-public funding
  context;
- the isolated challenger run did not mutate canonical fill counts;
- the prior network/OHLCV blocker did not recur in this accepted run.

This proof does not confirm:

- positive expectancy;
- actionable `funding_extreme` trade behavior;
- crypto-edge promotion qualification;
- persistent-campaign suitability.

Next decisions remain separate: archive-backed funding research review,
high-risk crypto-edge qualification policy, and any future persistent campaign
authorization.
