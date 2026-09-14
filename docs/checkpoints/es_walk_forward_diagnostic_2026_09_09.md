# ES Retrospective Walk-Forward Diagnostic

Active role: AUDITOR. Research only, not an untouched holdout or promotion proof.
Existing run_anchored_walk_forward engine, frozen 3077 daily rows and row hash
c0d64661f4c09b4ca7be047694dceff46b22846ba576177f55e4464a623e28eb.
Two fixed SMA periods, ATR20, 210-bar warmup, 730-bar initial history, six
nonoverlapping 365-bar evaluation windows. No fitting or parameter search.
157 remaining bars excluded by the declared complete-window plan.
Initial cash 1000; 7.5 bps fee and 5 bps slippage per side. BTC/USD data proxy
for BTC/USDT. Existing engine carries equity/positions through window boundaries.

| Window | SMA20 return | SMA200 return | SMA20 drawdown | SMA200 drawdown |
| --- | ---: | ---: | ---: | ---: |
| 1 | 159.93% | 171.21% | 27.33% | 27.03% |
| 2 | 4.75% | -21.32% | 55.29% | 64.24% |
| 3 | -45.45% | 0.00% | 49.02% | 0.00% |
| 4 | 28.27% | 93.22% | 27.52% | 18.57% |
| 5 | 55.34% | 81.43% | 33.75% | 26.18% |
| 6 | -15.42% | -17.60% | 24.85% | 32.07% |

Closed exits in evaluation windows: SMA20 122; SMA200 29. SMA20 has four
positive windows, SMA200 three positive plus one flat. The engine's
positive_test_window_count includes zero; do not describe four SMA200 wins.
SMA200's better aggregate result is not uniform superiority: it is worse in
windows 2 and 6, and its worst within-window drawdown is 64.24%.

Recommendation: retain the approved configuration correction for identity
integrity, but do not promote or increase exposure based on this comparison.
Neither the aggregate return nor this retrospective segmentation validates
deployment risk. Next research should compare risk-matched sizing and a
predeclared benchmark on a genuinely reserved period, rather than tune SMA
until these already-seen windows look better. Runner exits remain unmodeled.

Artifacts: .cbp_state/data/research/es_walk_forward/20260909/.
JSON SHA256 4ffc114964a5fadc40e565c674f213270615bcdfcdff2c5c6db2e2946f62df25.
Script SHA256 b089eae1c2010d0ad8c42dcc1bbc5128bdc9363092b8e25c2aafa195f139fe1d.
Code commit ec50782f3; full hash in JSON. Script verifies frozen data hash and
six windows. Existing walk-forward/archive tests: 7 passed in 0.38s.
No production code, campaign, gate or archive changes. Full suite not rerun.
Acceptance state: ACCEPTED for retrospective research observation only.
