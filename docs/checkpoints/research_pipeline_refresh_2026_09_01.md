# Research Pipeline Refresh - 2026-09-01

Status: latest local research pipelines are refreshed. Price-action research
produced manual-review candidates; funding-threshold research produced no
actionable funding candidate under the tested assumptions.

## Scope

- SHOWN: commands were run locally only.
- SHOWN: outputs were written under `.cbp_state/data/research`.
- SHOWN: no campaign, promotion gate, strategy config, live routing,
  execution path, host service, or Hetzner state was changed.
- SHOWN: generated artifacts are research-only and are not campaign evidence,
  promotion evidence, strategy config, or execution input.

## Commands

```bash
make price-action-research-pipeline
make funding-threshold-research-pipeline
make funding-threshold-research-pipeline FUNDING_THRESHOLD_RESEARCH_PIPELINE_ARGS="--window-rows 50 --min-windows 2"
make research-pipeline-status-json
```

## Results

Price-action pipeline:

- SHOWN: completed with `ok=true`.
- SHOWN: summary artifact:
  `.cbp_state/data/research/price_action_pipeline/20260901T233946Z/pipeline_summary.json`.
- SHOWN: summary SHA-256:
  `503cd0f18a3289ec796e5ab666aeb524a77767a4ea889617e95822b9395d2d5c`.
- SHOWN: candidate-triage artifact:
  `.cbp_state/data/research/price_action_pipeline/20260901T233946Z/candidate_triage.json`.
- SHOWN: candidate-triage dataset hash:
  `c29d4bf4114f7269be05673653068007be312772954241a0fbe372c703c330b0`.
- SHOWN: `15` rows were marked `candidate_for_manual_review`.
- SHOWN: highest reported candidate was
  `opening_range_state:inside`, side `long`, sample size `44`,
  `outperform_window_ratio=1.0`, `underperform_window_ratio=0.0`,
  `avg_delta_vs_unconditioned_pct=0.12745632891795666`.

Funding-threshold pipeline:

- SHOWN: default run reached price-join, sensitivity, and candidate-triage
  steps, but failed the stability step with `reason=insufficient_windows`
  because `187` joined rows with `window_rows=100` produced only `1` window.
- SHOWN: rerun with `--window-rows 50 --min-windows 2` completed with
  `ok=true`.
- SHOWN: summary artifact:
  `.cbp_state/data/research/funding_threshold_pipeline/20260901T233955Z/pipeline_summary.json`.
- SHOWN: summary SHA-256:
  `af8c6b1dbe7cb3fbf02a49a6cfdde8aa81a6ef8949f0a27824d30a8290f95207`.
- SHOWN: stability-triage artifact:
  `.cbp_state/data/research/funding_threshold_pipeline/20260901T233955Z/funding_threshold_stability_triage.json`.
- SHOWN: stability-triage dataset hash:
  `549b39c1fd0bb58de28f2d7c0d547783ca1839909031b6160b6d1f478e35e906`.
- SHOWN: `16` threshold pairs were evaluated and all remained
  `not_candidate`.
- SHOWN: the candidate-triage stage had `review_candidates=[]`.

Pipeline status after refresh:

- SHOWN: `make research-pipeline-status-json` reported both pipeline IDs as
  `latest_ok`.
- SHOWN: latest price-action generated at `2026-09-01T23:39:47.026076+00:00`.
- SHOWN: latest funding-threshold generated at
  `2026-09-01T23:39:55.734818+00:00`.

## Interpretation

- Price-action labels are research leads only. They require separate manual
  review and cannot be used as strategy configuration, campaign evidence,
  promotion evidence, profitability evidence, or execution input from this
  checkpoint alone.
- Funding-extreme remains unsupported by this local threshold run: the latest
  joined dataset produced no actionable funding threshold candidate under
  `fee_bps=10.0`, `slippage_bps=5.0`, `horizon_bars=1`, and the tested
  threshold grid.
- The default funding stability window is too large for this particular joined
  dataset. The successful `window_rows=50` rerun is a research-only sizing
  adjustment, not a campaign or gate-policy change.

## Remaining Risk

- LOW: checkpoint documentation only.
- These artifacts are local `.cbp_state` research outputs and are not committed.
- Research conclusions remain bounded to the input data and parameters listed
  above.
- Acceptance state: `ACCEPTED`.
