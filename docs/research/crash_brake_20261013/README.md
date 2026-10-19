# Result: E7 funding-rate crash brake (2026-10-13). Verdict: FAIL

Pre-registered in `PREREGISTRATION.md` before any funding-vs-price analysis.
- **Script:** `crash_brake.py` (sha256 efedd6c7...), run once.
- **Result:** `crash_brake_result.json` (sha256 f61ecf894a2af291...). It contains the prereg, script, input and funding-file hashes, and every brake week.
- **Execution:** the reviewed corrected harness, with Sunday-start periods. D begins 2020-12-06 and H begins 2024-01-07, the first Sundays on or after the registered dates.

| Fee/side | Period | Braked rule | Candidate (no brake) | Hold BTC | 25/25/50 mix | Brake cut exposure |
|---|---|---|---|---|---|---|
| 0.50% | D 2020-12..2023 | $3,548 (Sharpe 1.352, DD 32.8%) | $3,654 (1.341, 32.8%) | $2,171 (0.714, 76.7%) | $2,108 (0.865, 48.6%) | 11 of 160 weeks |
| 0.50% | H 2024..2026-10 | $1,808 (0.853, 31.3%) | $1,846 (0.869, 32.0%) | $1,848 (0.707, 53.1%) | $1,341 (0.526, 35.8%) | 2 of 144 weeks |
| 0.90% | D | $3,139 (1.239, 35.3%) | $3,250 (1.236, 35.3%) | $2,162 (0.712, 76.7%) | $2,076 (0.850, 48.7%) | 11 |
| 0.90% | H | $1,569 (0.686, 33.5%) | $1,605 (0.706, 33.9%) | $1,841 (0.704, 53.1%) | $1,325 (0.510, 35.9%) | 2 |

**Why it fails:** condition 1 fails at both fees. In D the brake raised Sharpe by only about 0.01, and the worst drop was unchanged (32.8% vs 32.8%). Ending value was lower in every period.
- **Sensitivity (reported only):** the 80th and 95th percentile thresholds, brake-to-zero and BTC funding for both assets all give no improvement in D. They cannot rescue the FAIL in any case.
- **DSR (braked, D+H, 0.50%):** 0.84 at N=15 and 0.56 at N=120. This describes the underlying trend exposure; it is not evidence for the brake.

## Reading
- **The brake is redundant with the trend rule here.** When funding was extreme the trend rule was usually already positioned, and the drawdowns it suffers did not coincide with brake weeks. This is consistent with the literature finding that past returns explain over half of the funding premium. **REJECTED** as an overlay at this specification.
- **Side observation (candidate, not the brake):**
  - At 0.90% fees in H (2024-26), the candidate's Sharpe (0.706) ties holding BTC (0.704), and it ends lower: $1,605 vs $1,841.
  - Its advantage there is the smaller worst drop (33.9% vs 53.1%).
  - At 0.50% its Sharpe is 0.869 vs 0.707.
  - Confirming the real fee tier is therefore material. This was a single run at the registered holdout with nothing tuned.
