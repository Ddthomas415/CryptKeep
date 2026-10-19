# VOLFC-1: Chronos-2 vs trailing volatility for Module A sizing (pre-registration)

Status: DRAFT FOR OPERATOR REVIEW. Written 2026-10-18T23:20:47Z by Claude (Cowork) after operator approval
("approve", 2026-10-18) of a pre-registered offline comparison. No forecast, model download or
market-data computation has been run. Once the operator confirms this text, its sha256 is recorded in
the work log and it is frozen. Any change after that is a new, separately logged version.

## 1. Question
Does Chronos-2, used as downloaded, rank next-week volatility across Coinbase USD markets better than the
trailing 60-day volatility Module A uses today? This is a forecast-quality test only. No returns, PnL,
portfolio or strategy result is computed. A PASS justifies a separate pre-registered Module A integration
test; it does not adopt anything.

## 2. Look-ahead control
- amazon/chronos-2 released 2025-10-20 (chronos-forecasting README news section; paper 2025-10-17).
  Training data: Chronos Datasets subset, GIFT-Eval Pretrain subset and synthetic data; dates undisclosed.
- Every evaluation target lies on or after 2025-10-27. Context before release is allowed: the test is
  whether the model forecasts weeks it cannot have seen.
- Model revision (Hugging Face commit hash) and chronos-forecasting / torch versions are pinned and
  recorded before the first forecast. CPU, float32.

## 3. Data
- D_XS (docs/research/trial_ledger_reconciliation_20261015/data_overlap.csv): Coinbase daily candles,
  492 USD products, fetched 2026-10-12. Package ~/Documents/cryptkeep_data_archive/
  xs_momentum_20261012_candles_v1/, raw tar sha256 d2054c51...; every file is checked against
  SHA256SUMS before use. Extracted only to a scratch folder outside the repo.
- Excluded: the 15 Coinbase markets flagged stable_or_wrapped in wp3_universe_20261016/markets.csv.
- Reuse declared: D_XS 2018-2026 was SEEN by E6 (return ranking). Volatility ranking was not tested
  on it. Volatility persistence is well known, so a strong baseline is expected, not news.
- Known limits carried over from WP3: survivorship (removed markets missing), ticker-only identity,
  v0 downloader may have silently dropped blocks, 15 products with internal gaps.

## 4. Design (fixed)
- Decision dates t: the 50 Sundays 2025-10-26 .. 2026-10-04 (UTC daily candles; decide at t's close).
- Point-in-time universe at t: closes present for all of t-60..t (60 log returns), not excluded above;
  rank by median of close x volume over t-29..t; keep the top 100. Markets missing any target day
  t+1..t+7 are dropped for that week and the count is reported (this uses future availability; it is
  acceptable for forecast scoring only, not for a strategy).
- Log return r_d = ln(close_d / close_{d-1}).
- All sigmas are in daily units (no annualization), so QLIKE compares like with like.
- Target: realized sigma = sqrt(mean of r_d^2, d = t+1..t+7).
- Forecasts, all using closes up to and including t:
  - B1 (incumbent): sample std (ddof 1) of the last 60 returns, as in module_a_candidate.
  - B2 (simple benchmark): EWMA variance, lambda 0.94, over the last min(512, available) returns,
    started at the sample variance of the first 20 of them.
  - C (candidate): Chronos-2, univariate, each series forecast independently (any cross-series
    option off; actual setting recorded), context = last min(512, available) returns, prediction
    length 7, quantiles 0.1/0.5/0.9. sigma_C = mean over h=1..7 of (q0.9 - q0.1) / 2.563103.
  - Determinism check: week 1 run twice; outputs must be identical, otherwise report and stop.

## 5. Decision rule (primary; fixed before any run)
- Each week: Spearman rank correlation between forecast and realized sigma across that week's markets.
  rho_X = mean over the 50 weeks. Delta = rho_C - rho_B1.
- PASS only if all three hold:
  1. Delta >= 0.03;
  2. one-sided 95% lower bound of Delta > 0, moving-block bootstrap over weeks (block 4, 10,000
     resamples, seed 20261018);
  3. rho_C - rho_B2 >= 0 (point estimate).
- Otherwise FAIL. Keep trailing 60-day volatility. No rerun of this window with other settings.

## 6. Secondary (reported, never decisive)
- QLIKE on variance: mean of (s_r/s_f - ln(s_r/s_f) - 1), s = sigma^2, per forecast.
- rho by liquidity tercile; number of weeks rho_C > rho_B1; per-week markets used and dropped.

## 7. Trial accounting
- New family VOLFC, 1 candidate configuration (C) and 2 fixed baselines. Added to the trial ledger and
  data_overlap.csv (D_XS used_by VOLFC-1, 2025-10-27 .. 2026-10-11) when the result is recorded.
- Not allowed after any result is seen: changing context, quantiles, horizon, universe size, model
  size, or adding models. Chronos-2-small, TimesFM, fine-tuning and covariates are out of scope.

## 8. Execution and outputs
- Runs in the cloud workspace (dependencies installed there only; repo requirements unchanged).
  Inputs: the verified D_XS files and markets.csv, staged read-only.
- Outputs to this folder: result.json (metrics, versions, revision, hashes), weekly.csv,
  run script with sha256, SHA256SUMS. Independent review before any conclusion is used.
- No trading, credentials, Docker, commit or push.
