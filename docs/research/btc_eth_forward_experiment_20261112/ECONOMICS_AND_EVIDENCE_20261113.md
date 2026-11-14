# Economics, selection and regime assessment before a bot build

Bot relation: STANDALONE historical research, not bot execution. Runtime trading configuration not checked.

2026-11-13, owner-approved bounded research packages. **Inference:** the saved record supports a credible downside-avoidance hypothesis and cheap prospective evidence collection, but does not establish enough economic advantage to justify committing another two weeks to full bot integration now. This is a recommendation, not a new queue order or a claim the strategy cannot work. No numerical audit, strategy backtest or parameter search was repeated.

## 1. Financial context: historical scenarios, not expected returns

**SHOWN:** the saved 2024-2026 primary-cost model has rule CAGR23.1%, fixed25/25/50 CAGR10.5%, BTC hold CAGR24.6%, and respective drawdowns32.0%,35.8%,53.1%. All include their modeled trading costs; none includes overhead. These rounded historical rates are not prospective expected rates. Sources: [comparison JSON](../btc_eth_corrected_comparison_20261012/comparison_result.json), [descriptive result](../candidate_descriptive_20261107/results.json); calculations were independently reproduced in the completed audit, not rerun here.

The following is **what-if arithmetic on those past annualized rates**, not a forecast, capital recommendation or reconstruction of annual cash withdrawals. It assumes linear capital scaling and a $240 annual allocated cost, paid externally. Incremental actual spending, minimum-order effects and execution capacity are unverified. A passive comparator's additional operating cost is set to zero for this illustration only, not established as fact.

| Hypothetical capital | Trading-cost-net gain at historical23.1% | Less allocated$240 | Economic return | Historical fixed-mix10.5%, before its overhead | Historical BTC24.6%, before its overhead |
| ---: | ---: | ---: | ---: | ---: | ---: |
| $1,000 | $231 | -$9 | -0.90% | $105 | $246 |
| $5,000 | $1,155 | $915 | 18.30% | $525 | $1,230 |
| $10,000 | $2,310 | $2,070 | 20.70% | $1,050 | $2,460 |
| $25,000 | $5,775 | $5,535 | 22.14% | $2,625 | $6,150 |

**Derived, not predicted:** absolute fixed-cost break-even using that old23.1% rate is $240/0.231=$1,038.96. Relative to the fixed mix's10.5%, the old return difference12.6points gives $240/0.126=$1,904.76 under the same assumptions. Relative to BTC, the old return difference is negative: no positive capital erases the underperformance plus positive operating cost by scaling alone. These are distinct economic questions; none supplies a defensible expected break-even or values the drawdown difference automatically.

Allocated cost sensitivity: $240/year is a24%,4.8%,2.4%,0.96% annual hurdle at the four capital sizes. Day-prorated182-day cost is $119.67, corresponding to11.97%,2.39%,1.20%,0.48%. If incremental spending were zero, the additional-cash-cost scenario equals the trading-cost-net result; zero is a sensitivity, not the actual marginal bill. Report actual bills/allocation separately when established. The owner's earlier monthly contribution discussion is not modeled as deposits into these frozen carry-forward accounts.

**Gross before trading costs: NOT COMPUTED from these saved summaries.** They do not store a reconciled fee/adverse-price decomposition sufficient to invent gross CAGR. [Financial section8a](CRITERIA_DRAFT_V3_3.md#8a-separate-financial-economics-reporting-only) now requires accounting-gross versus zero-cost-counterfactual distinction, fees/adverse-price decomposition, marginal/allocated overhead, all four capital scenarios and absolute/benchmark-relative break-even. It changes no Q1/Q2 threshold. Primary NAV is already net of modeled trading costs; do not subtract them again. A forward evaluator is still unimplemented, not supplied by this report.

**Decision implication:** the historical model can show positive absolute after-trading-cost return and still be less attractive than a benchmark or uneconomic after allocated cost. Larger capital dilutes fixed cost but cannot create a return edge; it may worsen execution impact. No actual account fee, current invoice, income target, capital commitment or scalability was verified here.

## 2. Selection bias: known exposure versus the actual selection chain

**SHOWN:** the majors source declares one primary before running plus three secondary variants, not an established four-way winner contest. An identifiable upstream Binance comparison contains10 non-benchmark rules, correcting11. The broader October8-9 program has577 configurations by the reconciled counting convention. An exact timestamped project-wide number examined before selecting the primary is unresolved; do not say all later searches caused its original selection.

The dated configuration floor747 becomes752 in the October21 supplement; the [accepted audit](../second_stage_review_20261112/CODEX_VERIFICATION_20261113.md) identifies a current convention-specific subtotal at least1,267 or1,767 including another exit convention. The118 stress-neighborhood settings are explicitly post-selection. These totals are not effective independent trials. Full selection history, consistent symbol pooling, effectiveN and Sharpe dispersion remain unresolved, so the old conditional DSR is not a current certification. No new DSR was computed or threshold weakened.

Sources: [majors primary declaration](../majors_trend_20261009/majors.py), [pass2](../trial_ledger_reconciliation_20261015/pass2_findings_20261015.md), [October21 supplement](../trial_ledger_supplement_20261021_record_repair/README.md), [existing DSR limitations](../trial_ledger_reconciliation_20261015/count_reconciliation.md).

## 3. Regime dependence: what the existing result actually separates

**SHOWN, descriptive:** [November7 definitions](../candidate_descriptive_20261107/PLAN.md) label a week bull when BTC is above its200-day average and that average rises versus20days earlier; bear is the reverse; mixed is the rest. These are not a trend-strength threshold or proof of literal sideways conditions. Do not relabel them as such.

- Bull270weeks: rule+4,642.7%, BTC+3,006.3%, ETH+76,325.0% compounded across labeled weeks. Arithmetic mean weekly return is1.606% for the rule versus1.806% BTC. Higher compounded outcome is not the same as higher arithmetic mean, nor proof of timing skill; the rule also holds ETH.
- Bear144weeks: rule+14.1%, BTC-36.6%, ETH-71.6%. This is the strongest descriptive support for avoiding sustained declines.
- Mixed95weeks: rule+58.5%, BTC+342.4%, ETH+53.5%. Whipsaw/cost exposure is a plausible mechanism, not independently isolated causation.
- Insufficient-history21weeks remain separately reported; do not silently drop them. Calendar2018 rule-41.0% versus BTC-73.4%;2022 -23.0% versus-64.2%. The rule lagged BTC in six of seven rising calendar years; partial2016/2026 and few shared cycles limit inference.
- **Strong-upward, literal-sideways and high/low-volatility-conditioned performance: NOT COMPUTED under those definitions in the inspected saved evidence.** Volatility sizing/aggregate volatility statistics are not a substitute. Defining new partitions and recomputing outcomes would be a separate descriptive analysis, not evidence already available and not done in this bounded reuse package.

These compound noncontiguous labeled weeks, not independently replicated portfolios or an executable regime-switching strategy. Cross-asset expansion E10 reduced drawdowns without consistent Sharpe improvement and used present-day surviving Coinbase coins with unequal histories. That supports a scoped defensive hypothesis, not universal alpha.

**Concentration:** the saved108 closed holding spells are resized and overlap across BTC/ETH, not108 independent bets. Five supply82.084% of closed-spell net P&L. Removing five leaves103 spells +$15,144.76; removing ten leaves98 -$26,688.70. The dollars overweight later account sizes; removing winners is descriptive arithmetic, not a feasible counterfactual strategy replay. Open marked P&L is separate. This dependence can make a26-week window inconclusive; it does not prove either durable profitability or inevitable failure.

Sources: [saved results](../candidate_descriptive_20261107/results.json), [E10](../multisymbol_trend_20261015/README.md), [survivorship notes](../integrity_audit_20261015/METHODOLOGY_NOTES.md). Nash independently inspected these sources at2026-11-13T17:11:26Z, without rerunning or changing them; this does not validate a new regime model or current runtime.

## 4. Stop and reassess

Finish the financial-reporting correction, bounded public/shadow preparation and one reviewed diagnostic if ready, then stop. The preparation package expires **2026-11-13T18:00:00Z**. No ongoing job or eight-week sample is silently started. Today's Friday observations cannot be registered as Monday00:00 quotes or fill any missing primary history.

Enough evidence to spend two more weeks building the bot: **not demonstrated yet**. The smallest useful further evidence is source-qualified timely quotes/arrival context, explicit sensitivity to unfilled maker orders and honest primary tracker delivery. Even an optimistic shadow saving is not a return edge or actual maker fill probability. The unchanged26-week design is still DRAFT; no bot modification, schedule, account order or deployment is approved here.

This reuses the already completed numerical audit. No strategy signal, parameter, frozen verdict or primary ledger changed. Uncomputed partitions, gross decomposition, invoices, prospective expected returns and real account fills remain unknown; do not turn them into promises of positive results.

What do I know that could change the owner's decision that I have not yet said?

The historical candidate did better than a fixed mix in the inspected recent model and had smaller drawdowns, so there is a coherent reason to investigate it. At the same time it lagged BTC, its fixed-cost economics depend on capital and allocation, and its selection/regime evidence remains weak for prediction. A narrowly successful quote diagnostic cannot resolve those strategic uncertainties or justify a full build by itself.
