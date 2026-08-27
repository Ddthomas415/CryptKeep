# Research Pipeline Refresh - 2026-08-27

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
  `.cbp_state/data/research/price_action_pipeline/20260827T070741Z`.
- Summary artifact:
  `.cbp_state/data/research/price_action_pipeline/20260827T070741Z/pipeline_summary.json`.
- Summary SHA-256:
  `8018efda250f9dec667fb38046f7f8105147d1259f59a24c82b43aacff992443`.
- Inputs: Coinbase `BTC/USDT`, `1h`, `limit=500`, fee `10.0` bps,
  slippage `5.0` bps.
- Expected steps completed:
  - `context_labels`: `c6d4defbcc1690fc4f0aa31b105cfc5b658e827f77ba082c6eba4e3571964cee`
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
  `.cbp_state/data/research/funding_threshold_pipeline/20260827T070741Z`.
- Summary artifact:
  `.cbp_state/data/research/funding_threshold_pipeline/20260827T070741Z/pipeline_summary.json`.
- Summary SHA-256:
  `ce21d237c8bb61093dc50a0a81d893ff8d21c119b0e2fa12e9d776ffe677aeb9`.
- Inputs: OKX `BTC/USDT:USDT` funding context, OKX `BTC/USDT` price archive,
  `5m`, `funding_limit=500`, `ohlcv_limit=500`, fee `10.0` bps, slippage
  `5.0` bps.
- Expected steps completed:
  - `price_join`: `1f03edc6a2edd17bd8a2f576c1b64f23d7969e7df926b61d18dbebfe5bac74d6`
  - `threshold_sensitivity`: `2b7f1cddced749427b81d5d1431968573a9e338bf977f26f4aacca90072516cc`
  - `candidate_triage`: `05e71fddb214f7d1b2058b68dabbb184ac8b59ad15a207bff66dc727ecd86178`
  - `window_stability`: `b5a8b96ff251a1fbab13ac09835b999d23b27eb016161eb6ac152d765ab97569`
  - `stability_triage`: `9288b2bf0b79761c644d2811bbdc16fa8721faf25b812a226665a0fa194c6a09`

The threshold candidate artifacts produced:

- `funding_threshold_candidate_triage.json`: `0` review candidates,
  `412` input rows, `16` threshold pairs evaluated.
- `funding_threshold_stability_triage.json`: `0` review candidates,
  `412` input rows, `16` threshold pairs evaluated.
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
  `.cbp_state/data/research/price_action_pipeline/20260827T070741Z/pipeline_summary.json`.
- `funding_threshold` latest summary:
  `.cbp_state/data/research/funding_threshold_pipeline/20260827T070741Z/pipeline_summary.json`.

## Boundaries

- The generated `.cbp_state` artifacts are local research state and are not
  committed by this checkpoint.
- This refresh does not authorize a strategy config change, new campaign,
  paper-gate change, promotion treatment, live/shadow execution path, or
  routing change.
