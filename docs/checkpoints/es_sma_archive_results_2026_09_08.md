# ES SMA-Only Archive Comparison

Active role: AUDITOR. Research-only, not promotion evidence or exit-policy proof.

## Method and Results

Frozen Coinbase BTC/USD daily archive, 2018-01-01 through 2026-06-04 inclusive:
3077 contiguous rows, exact endpoints verified. Existing baseline/parity engine;
BTC/USDT strategy label uses BTC/USD data explicitly. Both scenarios start with
1000 quote units, 210-bar warmup, ATR20, 7.5 bps fee and 5 bps slippage per side.
Only sma_period differs. The engine sizes entries from available cash; this
is not the campaign's fixed-quantity sizing or a risk-capped portfolio simulation.

| Metric | SMA20 | SMA200 |
| --- | ---: | ---: |
| Closed trades | 157 | 31 |
| Net return after modeled costs | 250.94% | 854.35% |
| Maximum drawdown | 72.89% | 64.29% |
| Profit factor | 1.206 | 2.801 |
| Win rate | 25.48% | 22.58% |

Both runs have equal buy and sell counts (157/157 and 31/31). These are
cumulative historical modeled returns, not annualized or expected future returns.
No parameter selection or promotion decision is justified by this in-sample run.
The large drawdowns are material limitations, not evidence of deployment safety.

## Provenance

Code commit: 0caece988 (full SHA recorded in JSON). Input rows SHA256:
c0d64661f4c09b4ca7be047694dceff46b22846ba576177f55e4464a623e28eb.
Artifact: .cbp_state/data/research/es_sma_comparison/20260908/es_sma_comparison_20260908.json
SHA256: 41dff0e85c483fd462b80872094711a2add278115115bdf053694ad5cd502775.
Reproduction script alongside artifact:
es_sma_comparison_20260908.py, SHA256
115bbee16e0238cc79514498fa6bf238068edf60c309ffaf0086c1271a6e288a.
Database opened mode=ro. No market fetch, campaign or canonical evidence write.

## Advisory

The periods have materially different historical behavior; do not treat earlier
SMA20-like paper evidence as validated SMA200 performance. SMA200's stronger
in-sample result does not establish an edge. Preserve the corrected identity,
then validate out of sample before making a strategy promotion recommendation.

This does not compare the old and new exit policy: the parity engine omits
runner stops. Archive inventory includes 12000 BTC/USDT 5m rows and 662 1h rows,
but counts alone establish neither continuity nor historical tick/loop coverage.
Next: validate intraday coverage over the paper trade dates before designing
a labeled approximation. Never interpret one daily bar as one runner loop.

Acceptance state: ACCEPTED for this bounded research observation only.
