## Evidence verdict follow-up (2026-09-23)

Inspected the campaign's stored `strategy_evidence.latest.json`, dated
2026-09-02T00:18:24Z. Its top-level source is `multi_window_synthetic`.
The breakout leaderboard's +34.158906% average return is a synthetic-window
metric, NOT the return earned by the paper campaign. Its walk-forward summary
contains only one closed test trade. None of its ten candidates has
research_acceptance.accepted=true. This is a verdict on this local artifact,
not an assertion that other campaign or host evidence does not exist.

Breakout has 12 attributed paper closes in this artifact. Composite hybrid,
EMA cross, SMA200 trend and momentum are synthetic_only; mean reversion,
volatility reversal, gap fill, breakout volume and pullback recovery are
insufficient. No candidate in this artifact demonstrates a validated live edge.
Do not select a live strategy using the synthetic return ranking.

Traced the contradictory win counts: journal analytics counts gross-price
winners (5); strategy feedback counts net-of-fees winners (2). Feedback's
numeric win rate was already correct, but its summary_text interpolated the
gross summary's rate. The local text fix uses the existing net_win_rate and
labels it explicitly. No numeric metric, ranking, gate, strategy or fill changed;
paper_history's gross metric remains unchanged, not silently redefined.
Recomputing feedback from the 24 extracted fills now prints 16.7% net-of-fees
win rate and reproduces +2.5135597278 USDT net within 1e-9.

An untouched-period runner-faithful evaluation remains incomplete: the existing
parity engine is signal-based, whereas the runner applies stateful exit-stack
priority, transition-only actions and duplicate-action suppression. The earlier
inspected/gapped data must not be relabeled as unseen validation data. No
profitability verdict is upgraded by this reporting correction.

# Breakout historical paper-fill baseline

Date: 2026-09-23. Active role: AUDITOR. Read-only local ledger analysis.
This is a measured historical PAPER outcome, not an actual account return,
fresh host status, MCB-1 markout result, or promotion qualification.

Source: `.cbp_state_challengers/breakout_default_daily/data/paper_trading.sqlite`.
Generated artifact (ignored/local, not backed up by Git):
`.cbp_state/data/research/paper_economic_baseline_20260923/breakout_fill_baseline.json`.
Artifact includes extracted fill/order rows, source-row hash, positions,
individual paired trades, exit attribution and limitations. Snapshot read in
one SQLite read transaction with mode=ro and query_only enabled.

## Results

Period: June 11-September 2, 2026, Coinbase BTC/USDT. Latest stored fill is
September 2; this is not a claim that no subsequent host trade exists.
24 distinct fills, 12 matched buy/sell pairs, 0.001 BTC each, no unmatched
position in this extraction. Quote-fee currency checked as USDT.

| Measure | Observed result |
| --- | ---: |
| Fill-price PnL before separately recorded fees | +3.6798422225 USDT |
| Recorded entry and exit fees | 1.1662824947 USDT |
| Net closed-trade PnL | +2.5135597278 USDT |
| Winners | 2 of 12 |
| Median trade net PnL | -0.1284012616 USDT |
| Largest winner | +8.6742241159 USDT |
| Net excluding largest winner (concentration diagnostic only) | -6.1606643881 USDT |
| Recorded paper fee / executed notional | 7.5 bps per side |

All prices are modeled paper fill prices. Slippage already embedded in them
was NOT subtracted again. Reporting-currency conversion unavailable; USDT is
not relabeled USD. No account fee-tier claim or portfolio-return percentage.

| Recorded exit category | Trades | Net USDT |
| --- | ---: | ---: |
| trailing_stop | 5 | -7.1566430165 |
| donchian_break_down | 3 | +1.3813854995 |
| take_profit | 1 | +8.6742241159 |
| no_signal / inside_channel / donchian_break_up fallback labels | 3 | -0.3854068711 |

Fallback labels are recorded signal_reason, not proof of the exit's cause.
11 pairs have public_ohlcv and sample_mode=false on both legs; one lacks that
basic provenance. This two-field check is NOT canonical gate qualification.
23/24 fills carry bid/ask metadata. The extraction contains no forward quote
path: do not synthesize markouts or claim 24 eligible independent signals.

## Reconciliation and decisions

Position summary says realized_pnl=3.0697863284 USDT, 0.5562266006 above the
fill-derived net. Cause is UNVERIFIED; no store repair or historical rewrite
was performed. Explicit cash-flow reconstruction is used for this report.
Matched-pair arithmetic agrees with a second Decimal cash-flow calculation
(all sales net of fees minus all purchases inclusive of fees) within 1e-9 USDT.
Uniqueness, sides, quantities, currency, pairing and total-fee checks passed.
No production code changed; full suite not run for read-only analysis.

Economic read: modest positive modeled net, concentrated in one large winner;
insufficient evidence of durable edge. Removing that winner is not a fair
strategy rejection test, especially for trend-following. Losing trailing exits
do not establish that loosening/removing trailing stops helps: that requires
the counterfactual path and risk comparison. Do not retune from this table.

Next economic work must compare the complete runner policy (including its
exit stack, transitions and sizing), not the shelved signal-only model. MCB-1
can use this as legacy cost/outcome context, not substitute it for prospective
candidate capture. No new collection service, campaign, gate or trading change.
Acceptance state: INCOMPLETE for economic treatment validation.

## Fixed-notional capital sensitivity

2026-09-23: user delegated conservative interpretation of their budget.
Research assumptions: 1,000 total simulated capital, no additional monthly
deposits, no leverage, 500 aggregate entry-notional exposure ceiling.
For this quote-denominated calculation these amounts are USDT, not a verified
USD conversion. No campaign or live-account configuration was changed.

Repriced quantities for the same 12 historical pairs to 20/50/100 USDT entry
notional, retaining recorded entry/exit prices and proportional recorded fees.
Decimal arithmetic checked chronological non-overlap, cash sufficient for each
entry plus its fee, and entry notional below the exposure ceiling.

| Entry USDT | Net USDT | Fees USDT | Ending cash USDT | Return on 1,000 | Closed-trade drawdown USDT |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | 0.675683 | 0.360777 | 1000.675683 | 0.067568% | 1.824904 |
| 50 | 1.689208 | 0.901943 | 1001.689208 | 0.168921% | 4.562259 |
| 100 | 3.378416 | 1.803887 | 1003.378416 | 0.337842% | 9.124518 |

All arms have two winners. This linear fixed-fill sensitivity is NOT a fresh
strategy backtest, unseen-period test, executable fill simulation, or pooled
multi-strategy account test. Exchange minimums, quantity rounding, changed-size
market impact, actual account fees, and reporting-currency conversion are not
validated. Drawdown uses closed-trade cash only, not intratrade marked equity.
Results include the provenance-incomplete historical pair noted above and do
not qualify new promotion evidence. Larger size scales these gains and losses;
it does not establish a better edge. Economic treatment validation remains
INCOMPLETE; do not increase live sizing based on this table.
