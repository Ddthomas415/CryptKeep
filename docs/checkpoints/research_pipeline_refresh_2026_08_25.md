# Research Pipeline Refresh - 2026-08-25

## Scope

Read-only local research refresh for the accepted price-action and
funding-threshold pipelines. This checkpoint records generated artifact paths,
hashes, and interpretation only.

No campaigns, promotion gates, strategy configs, live/shadow execution,
order routing, ingestion policy, or host services were changed.

## Price-Action Pipeline

Command:

```bash
make price-action-research-pipeline
```

Result:

- `ok=true`.
- Output directory:
  `.cbp_state/data/research/price_action_pipeline/20260825T050434Z`.
- Summary artifact:
  `.cbp_state/data/research/price_action_pipeline/20260825T050434Z/pipeline_summary.json`.
- Summary SHA-256:
  `0c04db99e22fa75f9a13f440466306d0f428cfa1236cb3a7aa68ebb2f7229fe7`.
- Inputs: Coinbase `BTC/USDT`, `1h`, `limit=500`, fee `10.0` bps,
  slippage `5.0` bps.
- Expected steps completed:
  - `context_labels`: `dc60f183669f373ef37c30c8a08806a6256fb05dff47a64f5b22940f80e58754`
  - `forward_returns`: `4b7edeb13066be001a7a8262e2a05e25442714b9b7cea13da0ed79256245485c`
  - `window_stability`: `af10863bca8dc4fffe8815b74d2b29d7a286f9e65a9d76af7ee22abb92299716`
  - `candidate_triage`: `f23a77cb70587654f9c3808f0be1e02bc607433bddd339a624bcbcadb78c96ab`

The candidate triage artifact produced `15` label/side pairs for manual
review. Highest-signal examples by triage output:

- `opening_range_state:inside` long: sample `44`, average delta versus
  unconditioned `0.12745632891795666`, outperform ratio `1.0`.
- `break_and_retest:bearish_hold` long: sample `12`, average delta
  `0.1147470680077031`, outperform ratio `1.0`.
- `fair_value_gap:bearish` long: sample `44`, average delta
  `0.06505364487308771`, outperform ratio `1.0`.

Interpretation:

- These are research-only manual-review candidates.
- They are not strategy configuration, not campaign evidence, not promotion
  evidence, not profitability evidence, and not execution input.
- Any use as confirmation filters still requires separate review against
  out-of-sample stability, sample size, underperformance rate, and strategy
  integration boundaries.

## Funding-Threshold Pipeline

Command:

```bash
make funding-threshold-research-pipeline
```

Result:

- `ok=true`.
- Output directory:
  `.cbp_state/data/research/funding_threshold_pipeline/20260825T050434Z`.
- Summary artifact:
  `.cbp_state/data/research/funding_threshold_pipeline/20260825T050434Z/pipeline_summary.json`.
- Summary SHA-256:
  `3656630cbcea6950f83dbad220ef7bb5c63afeccc149862a32baeb30eaf8b549`.
- Inputs: OKX `BTC/USDT:USDT` funding context, OKX `BTC/USDT` price archive,
  `5m`, `funding_limit=500`, `ohlcv_limit=500`, fee `10.0` bps, slippage
  `5.0` bps.
- Expected steps completed:
  - `price_join`: `8651a8ce06a33bd173c80b15ee16228cb4bbb6e2ea2920ab99a326721d2607c8`
  - `threshold_sensitivity`: `86ac6737ace985f121016f86580f4c8fba3453d717aaef84d72d152cfcb8d9fd`
  - `candidate_triage`: `61bf11cd3d3c87511e52b92b2e3a51d9ac06c794b5995f435331e4605a1a22bb`
  - `window_stability`: `501c60ed5ec8bb712fa67182e82545010859d52ecc24c4630d3afdb089023f75`
  - `stability_triage`: `2a853b8771e7e290594842f9b4dd6b7f63c5932c973a96023d1b5b04a51474da`

The threshold candidate artifacts produced:

- `funding_threshold_candidate_triage.json`: `0` review candidates,
  `414` input rows, `16` threshold pairs evaluated.
- `funding_threshold_stability_triage.json`: `0` review candidates,
  `414` input rows, `16` threshold pairs evaluated.
- Funding-rate percentage range in the joined sample: `0.00303595` to `0.01`.

Interpretation:

- Current default funding thresholds still do not produce an actionable
  `funding_extreme` candidate on this local artifact window.
- This is not a strategy failure or promotion decision; it is research-only
  evidence that the current threshold grid needs more data, different
  symbols/windows, or explicit review before any persistent campaign decision.

## Status Verification

Command:

```bash
make research-pipeline-status-json
```

Result:

- `ok=true`.
- `latest_ok=2`.
- `latest_not_ok=0`.
- `not_run=0`.
- `price_action` latest summary:
  `.cbp_state/data/research/price_action_pipeline/20260825T050434Z/pipeline_summary.json`.
- `funding_threshold` latest summary:
  `.cbp_state/data/research/funding_threshold_pipeline/20260825T050434Z/pipeline_summary.json`.

## Boundaries

- The generated `.cbp_state` artifacts are local research state and are not
  committed by this checkpoint.
- This refresh does not authorize a strategy config change, new campaign,
  paper-gate change, promotion treatment, live/shadow execution path, or
  routing change.
