# Training-Calibrated Drawdown Diagnostic

Active role: AUDITOR. Research only. Not executable sizing or untouched holdout.

Used the existing ES risk.max_drawdown_pct=12 as a calibration target. On each
of the same six anchored windows, selected the largest cash-sleeve weight in
[0,1] whose preceding training equity curve had maximum drawdown <=12%, using
60-step bisection. Froze that weight for the next 365 bars. No evaluation values
enter the calibration function. Compared fixed SMA20, SMA200 and buy-and-hold.

| Window | SMA20 return / DD | SMA200 return / DD | Buy-hold return / DD |
| --- | --- | --- | --- |
| 1 | 26.82% / 5.94% | 23.10% / 3.97% | 52.10% / 12.28% |
| 2 | 0.78% / 15.58% | -2.15% / 12.69% | 8.29% / 13.28% |
| 3 | -1.74% / 2.01% | 0.00% / 0.00% | -2.36% / 2.47% |
| 4 | 0.80% / 1.00% | 2.26% / 0.66% | 3.40% / 0.82% |
| 5 | 1.53% / 1.44% | 1.97% / 1.08% | 2.70% / 0.99% |
| 6 | -0.43% / 0.73% | -0.43% / 0.88% | -0.15% / 0.94% |

SHOWN: training drawdown constraints did not bound next-window drawdown. Both
strategies exceeded 12% in window 2; benchmark exceeded it in windows 1 and 2.
Do not convert fitted weights into campaign sizing instructions.

Method limits: allocation scales historical sleeve equity plus zero-yield cash;
training includes compounding from the original start, while evaluation rebases
at each segment boundary. Accordingly weights are not constant-volatility risk
targets and shrink as accumulated training sleeve growth changes. Existing
positions carry through boundaries. Additional resizing transaction costs are
not included; endpoints are marked to market, not liquidated. This is a
sensitivity diagnostic, not an investable portfolio backtest or equal future
risk comparison. Prior history was already inspected. Runner exits not modeled.

Decision: keep exposure unchanged; neither corrected identity nor favorable
aggregate return grants promotion. Close this retrospective diagnostic series
rather than tune repeatedly. Further deployment evidence needs the corrected
runtime verified in isolation plus a predeclared prospective evaluation; do not
claim unseen data exists without establishing it. No campaign reset authorized.

Artifacts: .cbp_state/data/research/es_train_risk_match/20260909/ contains script
and JSON es_train_risk_match_20260909. Same frozen dataset hash as prior report.
Local script checks analytic 50%-loss calibration, zero-drawdown behavior and
training-target satisfaction. Existing walk-forward tests: 7 passed in 0.37s.
No production edits, archive writes or full-suite proof.
Acceptance state: ACCEPTED for diagnostic only; deployment proof INCOMPLETE.
