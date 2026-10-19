# VOLFC-1 result: FAIL (Chronos-2 does not beat trailing 60-day volatility)

Run 2026-10-18 by Claude (Cowork) in the cloud workspace, exactly as pre-registered in
`PREREGISTRATION.md` (frozen sha256 501723e7...; freeze record in the work log). Run script
`run_volfc1.py` sha256 699698aa..., hashed before the real-data run (the work-log entry recording it was
written at the same time the run started, not before).

## Primary (decision rule, Section 5)
| | mean weekly Spearman rho (50 weeks, 4,999 forecasts) |
|---|---|
| B1 trailing 60-day std (Module A incumbent) | 0.5123 |
| B2 EWMA lambda 0.94 | 0.5283 |
| C Chronos-2 (as downloaded) | 0.5217 |

- Delta C - B1 = +0.0095 (needed >= 0.03): not met.
- One-sided 95% block-bootstrap lower bound = -0.0065 (needed > 0): not met.
- C - B2 = -0.0066 (needed >= 0): not met.

Verdict: FAIL on all three criteria. Module A keeps trailing 60-day volatility. Per the
pre-registration this window is not retested with other settings.

## Secondary (not decisive)
- QLIKE (lower is better): B2 0.652, B1 0.668, C 0.670.
- Weeks with rho_C > rho_B1: 29 of 50.
- Mean rho by liquidity tercile (B1 / C): top 0.628 / 0.635, middle 0.482 / 0.484, bottom 0.399 / 0.432.
- Disclosed sensitivity excluding week 1 (see below): Delta = +0.0133, still below 0.03.
- Plain EWMA ranked best on the primary metric and on QLIKE. That is an observation, not a tested
  claim; adopting it would need its own pre-registration.

## Checks
- D_XS tar sha256 d2054c51... and all 494 files matched SHA256SUMS. 15 stable/wrapped markets excluded.
- Each week had 306 or more eligible candidates; 100 selected; 1 market-week dropped for a missing target day.
- Week-1 determinism: identical on repeat.
- Synthetic smoke test before the real run: Chronos recovered known sigma (median ratio 0.998).
- Independent recomputation from `forecasts.csv` with separate code (pandas ranks) reproduced all three
  means and Delta exactly. B1 and realized sigma re-derived from raw candles for 3 random cells matched.
  This was Claude checking its own run; a separate reviewer has not yet checked it.

## Deviation and disclosure
- Hugging Face history: amazon/chronos-2 weights were first uploaded 2025-10-30 14:58Z, unchanged in
  every later commit (pinned revision 29ec3766..., model.safetensors sha256 ddcda3c7...). The
  pre-registration cites the 2025-10-20 README release date. Week 1's targets (2025-10-27..11-02) fall
  before the upload. The frozen rule was not changed; the week-1 exclusion is reported above and does not
  change the verdict.
- "available" context was implemented as the contiguous run of daily closes ending at t (max 512 returns).

## Bookkeeping still to do (not done here, to avoid editing the dated reconciliation artifact)
- Trial ledger: family VOLFC, 1 candidate configuration, 2 baselines, verdict FAIL.
- data_overlap: D_XS used_by VOLFC-1, targets 2025-10-27 .. 2026-10-11, top-100 Coinbase USD markets.

## Environment
Python 3.13.16, torch 2.14.1+cpu, chronos-forecasting 2.3.2, transformers 5.20.1, pandas 3.0.6,
numpy 2.5.4, scipy 1.18.1. CPU, float32, cross_learning False. No trading, credentials, Docker,
commit or push.
