# Result: E8 CryptKeep Composite v1, trend ensemble + rebalance bands (2026-10-13). Verdict: FAIL

- **Pre-registration:** `PREREGISTRATION.md` (sha256 6dce29e4...), written before running.
- **Script and result:** `composite.py` (971917e0...), run once; result `composite_result.json` (ba49b592039daec7...).
- **Simulator check passed:** with the candidate's rule and band 0, the new simulator reproduces the reviewed harness within 1e-6 USD in D and H.

| Fee/side | Period | Composite v1 | Candidate (incumbent) | Hold BTC | 25/25/50 mix |
|---|---|---|---|---|---|
| 0.50% | D 2017-01..2023 | $38,010 (Sharpe 1.592, DD 45.0%, turnover 4.6x/yr) | $42,583 (1.564, 51.9%, 9.25x) | $42,355 (1.092, 83.8%) | $23,676 (1.316, 61.2%) |
| 0.50% | H 2024-01..2026-10 | $1,278 (0.450, 34.0%, 6.3x) | $1,846 (0.869, 32.0%, 12.7x) | $1,848 (0.707, 53.1%) | $1,341 (0.526, 35.8%) |
| 0.90% | D | $33,423 (1.542, 45.9%) | $32,852 (1.469, 54.1%) | $42,187 (1.091, 83.8%) | $22,739 (1.302, 61.4%) |
| 0.90% | H | $1,192 (0.364, 35.5%) | $1,605 (0.706, 33.9%) | $1,841 (0.704, 53.1%) | $1,325 (0.510, 35.9%) |

- **Pass checks:** the D checks pass at both fees (higher Sharpe; turnover 0.50x the incumbent's). **The H Sharpe check fails at both fees.**
- **Verdict:** FAIL. The candidate stays.
- **Sensitivity (reported only; none rescues H):**
  - band 0: H Sharpe 0.43;
  - band 0.20: H Sharpe 0.62;
  - no vol scaling: H Sharpe 0.42.
- **DSR (composite, D+H, 0.50%):** 0.97 at N=15 and 0.78 at N=120. This is dominated by the D period.

## Reading
- **The holdout did its job.** An ensemble that looked better in 2017-2023 lost half its risk-adjusted return in 2024-2026. The slower lookbacks (100 and 200 days) were too slow for that regime.
- **What the evidence supports:** halving turnover is valuable (D), and the band was not the failure point.
- **Next:** a separate pre-registered test of the band alone on the unchanged candidate (cost reduction only).
- **Caveat:** 2024-26 is not a true holdout for the candidate itself, because that period was inside the windows used when the candidate was selected.
