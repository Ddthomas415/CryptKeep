# Archive-first backtesting (backlog item 11): sweep and walk-forward review

2026-10-04. AUDITOR then ENGINEER (Claude). Master 97c24c8e plus the patch
series. State: READY_FOR_INDEPENDENT_REVIEW. Research tooling only; additive;
default behaviour unchanged. Nothing merged, pushed or deployed. Patch 0049
(commit dea64378, cloud clone only) is in
`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_review_bundle_2026-10-02_rev60.zip`,
folder 57. Zip SHA-256:
1d67d0a48b035634c9de71d0cba884f7b7d5ffb1b45016cb769b90d4a369d7de

Correction to `series_end_to_end_proof_20261004.md`: it says the items still
marked "ready for independent review" were accepted, docs-only or deferred. I
had checked three. Items 1, 3, 7, 9 and 11 to 16 also carry unreviewed slices.

## What holds

The walk-forward refuses an incomplete archive. Artifacts carry the dataset
hash. Costs go through the shared fill model. A nested research config is
resolved to the keys the strategy reads (#600, 2026-09-23).

## Findings

1. The only sweep artifact here compares twelve copies of one backtest.
   `.cbp_state/data/research/archive_parameter_sweep/breakout_default_btcusdt_5m_sweep.latest.json`
   (2026-08-01): all 12 variants have 4 windows, 11 closed trades,
   non-negative ratio 0.25, average test return -0.6034%, average drawdown
   1.7013%. Its grid set `strategy.signal.donchian_len` and
   `strategy.no_trade_filters.*`, which the strategy did not read before #600.
   The result is negative, so no positive claim rests on it. It was not re-run.
2. Selection bias, shown with the repo's own walk-forward engine on random-walk
   daily data with no edge (30 seeds, 24 ema_cross variants, 10 windows,
   default costs):

   | Measure | Average test return per window | Positive in |
   | --- | --- | --- |
   | Best variant, on the windows it was picked on | +2.13% | 21 of 30 seeds |
   | Same variant on a fresh random walk | -1.16% | 10 of 30 seeds |
   | All variants together | +0.28% | |

3. P3. `positive_test_window_count` counts a window that returned exactly 0,
   including one where the strategy never traded.

## Correction in 0049

- `--holdout-windows N` keeps the last N windows out of the ranking; each
  variant carries `selection_summary` and `holdout_summary`.
- The artifact carries `parameter_effect`, with a warning when every variant
  produced identical results.
- Walk-forward summaries carry `strictly_positive_test_window_count` and
  `idle_test_window_count`.

10 new cases. Full suite: 4622 passed, 33 skipped, 19 failed (the same 19 as
master).

## For the thesis gate

The stop/retirement policy asks for positive walk-forward expectancy after
measured costs. A figure read off the best variant of a sweep without a holdout
does not meet that description.

## Not changed

The default ranking order and triage thresholds; the August artifact; a holdout
is one split and, with few windows, a small sample.
