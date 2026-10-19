# Result: E9 rebalance band (0.10) on the unchanged candidate (2026-10-13). Verdict: FAIL on the registered criteria

- **Pre-registration:** `PREREGISTRATION.md` (90ff88d8...), written before running.
- **Script and result:** `band.py` (9ed16dde...), run once; result `band_result.json` (af6b15bd7431007a...).
- **Simulator check passed** (band 0 reproduces the reviewed harness within 1e-6 USD).

| Fee/side | Period | Candidate + band 0.10 | Candidate (no band) | Hold BTC |
|---|---|---|---|---|
| 0.50% | D 2017..2023 | $53,367 (Sharpe 1.620, DD 54.0%, turnover 8.36x, 20.9 rebalances/yr) | $42,583 (1.564, 51.9%, 9.25x, 38.7/yr) | $42,355 (1.092, 83.8%) |
| 0.50% | H 2024..2026-10 | $1,867 (0.883, 32.0%, 11.95x, 22.5/yr) | $1,846 (0.869, 32.0%, 12.69x, 38.1/yr) | $1,848 (0.707, 53.1%) |
| 0.90% | D | $42,232 (1.536, 56.1%) | $32,852 (1.469, 54.1%) | $42,187 (1.091, 83.8%) |
| 0.90% | H | $1,638 (0.730, 33.8%) | $1,605 (0.706, 33.9%) | $1,841 (0.704, 53.1%) |

**Registered verdict: FAIL.**
- **Why:** check 1 requires turnover ≤ 0.75x the incumbent's. Turnover fell only to 0.90x (8.36 vs 9.25 per year), at both fees.
- **Every other check passed.** The banded rule had a higher Sharpe and a higher ending value than the unbanded candidate in both D and H, at both fees.
  - Its D drawdown was 2.1 points worse (54.0% vs 51.9%). That figure is not part of check 1.
  - Rebalance count roughly halved (20.9 vs 38.7 per year).
- **Sensitivity (reported only):** band 0.05 is close to no band. Band 0.20 gave D Sharpe 1.69 and H Sharpe 0.905, with turnover 7.44x (0.80x).

## Reading
- **The registered turnover criterion was the wrong yardstick.** It is recorded here as a design error, NOT corrected after the fact.
  - The candidate's turnover is dominated by full entries and exits when the trend flips. A band cannot avoid those.
  - What the band removes is the frequent small resizing trades. That halves the number of trades but not their volume.
  - Both periods have now been seen, so re-testing the band on this history with a different criterion would be post-hoc.
- **The honest way forward is forward evidence:** track "candidate + band 0.10" as a separate account beside the unbanded candidate in tracker v2, starting from its first live decision. That needs a code change, tests and review.
