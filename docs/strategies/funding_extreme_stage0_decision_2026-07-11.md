# Funding Extreme Stage 0 Decision

Status: accepted Stage 0 wiring proof; not promoted to persistent campaign.

Date: 2026-07-11

## Evidence

The isolated `funding_extreme_default` Stage 0 proof passed after using an OKX
public-OHLCV proof contract and seeding the challenger edge store from the
canonical crypto-edge store:

```bash
make funding-stage0-readiness FUNDING_STAGE0_ARGS="--venue okx"
make funding-stage0-baseline FUNDING_STAGE0_ARGS="--venue okx"
CBP_STATE_DIR="$PWD/.cbp_state_challengers/funding_extreme_default" CBP_CRYPTO_EDGE_DB_PATH="$PWD/.cbp_state/data/crypto_edge_research.sqlite" ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --strategies funding_extreme --session-strategy-id funding_extreme_default --symbol BTC/USDT --venue okx --signal-source public_ohlcv_5m --strategy-context-symbol BTC/USDT:USDT --strategy-context-venue okx --strategy-context-db-path "$PWD/.cbp_state/data/crypto_edge_research.sqlite" --runtime-sec 900 --strategy-drain-sec 2
make funding-stage0-verify FUNDING_STAGE0_ARGS="--venue okx"
```

2026-07-21 note: newer readiness output generates the
`CBP_CRYPTO_EDGE_DB_PATH` / `--strategy-context-db-path` override explicitly so
the isolated challenger state can consume the same read-only crypto-edge store
validated by readiness. The original proof required manually seeding the
challenger edge DB from canonical evidence; that manual copy is no longer the
preferred workflow.

Verifier result:

- `status=passed`
- `blocking_checks=0`
- `expected_commit=f652f8321`
- completed session timestamp: `2026-07-12T02:53:13.816650+00:00`
- reconciliation result: `pass`
- OHLCV contract: `okx BTC/USDT public_ohlcv_5m`
- market-data provenance: `market_data_source=public_ohlcv`, `ohlcv_sample_mode=false`
- funding context: `strategy_context_ok=true`, `strategy_context_reason=funding_context_ready`
- context contract: `live_public OKX BTC/USDT:USDT`
- signal result: `signal_ok=true`, `signal_action=hold`, `signal_reason=funding_neutral`
- canonical fill count unchanged: `176`
- challenger fill count: `0`

## Decision

Keep `funding_extreme_default` as the next high-value profitability research
candidate, but do not start a persistent campaign or treat it as promotion
evidence yet.

The Stage 0 proof confirms:

- the managed paper runner can execute `funding_extreme`;
- the runner can pair public OHLCV with OKX funding context;
- the context-backed signal path fails less ambiguously than the prior
  `no_public_ohlcv` blocker;
- the isolated challenger run does not mutate canonical paper fills.

The proof does not confirm:

- positive expectancy;
- actionable funding-extreme trade behavior;
- paper-gate qualification for crypto-edge provenance;
- suitability for persistent paper campaign inclusion.

## Next Conditions

Before any persistent campaign or promotion-gate integration:

- Run archive-backed research for `funding_extreme` against stored
  crypto-edge/funding history once the research path is available.
- Implement the high-risk crypto-edge paper-qualification extension separately:
  accepted fresh edge provenance must qualify, stale/mismatched edge fixtures
  must reject, and existing OHLCV qualification fixtures must remain unchanged.
- Decide whether challenger edge-store seeding should remain an operator step
  for isolated proofs or become explicit tooling before future context-backed
  Stage 0 runs.
