# Strategy Research Acceptance

This note is research-facing. It does not change runtime behavior and it does not weaken the final live-order boundary.

Use this note to answer a different question than the promotion ladder:

- Promotion ladder: "May an operator review the next stage?"
- Research acceptance: "Is there enough evidence to treat the current edge claim as credible research rather than thin ranking noise?"

The repo remains:

- crypto-first
- paper-heavy by default
- guarded and fail-closed for live order creation
- not validated for stocks
- not fully validated for shorting
- not proven profitable

This note is intentionally stricter than the current promotion minima. A strategy can be eligible for operator review and still fail research acceptance.

## Why This Exists

The current repo already tracks:

- net return after costs
- max drawdown
- profit factor
- Sharpe / Sortino
- expectancy
- paper/live drift
- slippage sensitivity

But the existing promotion ladder uses small minimums such as `3` or `5` closed trades. Those values are governance gates, not strong evidence thresholds.

Without a separate research contract, it is too easy to confuse:

- "the strategy is not blocked from further review"

with:

- "the strategy has enough evidence to deserve trust"

## Current Architectural Direction

Until stronger evidence exists:

- prove one edge family first
- treat `breakout_donchian` as the active improvement candidate
- treat `ema_cross` as a useful baseline / comparison candidate
- keep `mean_reversion_rsi` frozen unless its negative paper-history evidence is explicitly explained or the hypothesis is rewritten

Do not build portfolio orchestration, dynamic capital weighting, or multi-strategy allocation on top of thin evidence.

## Research Acceptance Questions

Before claiming an edge is credible, answer:

1. Is post-cost expectancy positive?
2. Is the edge robust across more than one regime?
3. Is drawdown tolerable relative to expected return?
4. Does stressed slippage materially break the result?
5. Is paper/live drift measured and acceptable once sandbox evidence exists?
6. Are losses gradual and diagnosable, or rare and catastrophic?
7. Is the sample size large enough that the result is not just ranking noise?

## Initial Research Floor

These are recommended research thresholds for the current repo. They are deliberately conservative enough to block thin evidence, but still realistic for a solo operator to reach in paper mode.

For one strategy under active review:

- at least `30` closed trades across persisted paper history
- at least `3` represented regimes with realized participation
- no represented regime with `0` realized closed trades if that regime is still claimed as supported
- positive net return after fees and slippage
- positive expectancy per closed trade
- max drawdown at or below `10%`
- stressed slippage degradation small enough that the strategy remains positive after costs
- no `high` or `unknown` paper/live drift before any tiny-live review

These are research floors, not promotion guarantees.

## Stronger Confidence Target

Treat the strategy as materially stronger only when the evidence grows beyond the initial floor.

Suggested stronger target:

- at least `50` closed trades across persisted paper history
- at least `10` closed trades in each regime the strategy claims to handle
- drawdown comfortably below the research floor, not merely equal to it
- repeated positive post-cost results across multiple evidence runs
- no meaningful degradation when stressed slippage is applied
- no unresolved mismatch between paper and sandbox/live behavior

## Regime Coverage Rule

Do not let a strategy claim broad robustness if evidence only exists in one kind of tape.

For the current repo, minimum useful regime coverage means realized participation across at least:

- one trend / continuation window
- one reversal / snapback window
- one hostile window such as false-breakout, event-trend, or low-vol fee bleed

If a strategy does not participate in a regime, document that as an unsupported or failure regime instead of silently counting it as covered.

## Slippage And Capacity Rule

The current repo already records stressed-slippage sensitivity. Use it as a research brake:

- if stressed slippage turns post-cost return negative, the edge is not robust enough
- if a small slippage increase materially collapses expectancy, the strategy is too fragile for scaling

Do not talk about scaling capital until this is understood from persisted paper evidence.

## Drift Rule

Once sandbox evidence exists, paper/live drift must become part of research acceptance, not just promotion review.

Treat the strategy as not yet trustworthy if:

- drift is `high`
- drift is `unknown`
- drift is not measured for the reviewed stage

## Kill Conditions

Each strategy under active review should have explicit kill conditions written next to the hypothesis.

At minimum:

- post-cost return turns negative over the current review sample
- max drawdown breaches the reviewed limit
- stressed slippage breaks profitability
- realized participation collapses even though the strategy is still supposedly active
- paper/live drift becomes unknown or high
- failure is concentrated in the regimes the strategy claims to support

## What This Means For The Current Repo

Today, this contract should be read conservatively:

- `breakout_donchian` is the current lead candidate, but still not research-accepted
- `ema_cross` is still useful as a baseline, not a proven edge
- `mean_reversion_rsi` should stay frozen until the hypothesis is reconsidered against negative paper history

That means the next useful work is:

1. finish a complete paper evidence cycle
2. grow persisted paper-history evidence
3. rerun the same strategy under the same contract
4. only then consider capital-allocation or multi-strategy design

## Relationship To The Promotion Ladder

The promotion ladder stays authoritative for stage review.

This note adds a stricter interpretation layer:

- a strategy may be promotion-review eligible
- and still fail research acceptance

When those disagree, trust research acceptance for strategy credibility and trust the promotion ladder only for operator workflow.
