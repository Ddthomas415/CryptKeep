# Algorithmic Trading: Decision Framework v4

A pre-build and pre-live checklist. Work through it in order — each step depends on the one before it.

---

## Step 1 — Locate yourself honestly

Answer these four questions before looking at any strategy. Your answers determine which strategies are even available to you.

| Question | Your answer determines |
|---|---|
| What is my capital size? | Which edges are accessible at your size |
| What is my target holding period? | Which data, tools, and infrastructure you need |
| Can I run infrastructure 24/7? | Whether live execution is realistic or paper-only for now |
| What is my max acceptable drawdown? | Which strategy categories you can survive psychologically and financially |

**Why this comes first:** A mean reversion strategy at $50k looks nothing like one at $5M. A trend system on daily bars requires completely different infrastructure than one on 5-minute bars. Most strategy failures start with a mismatch between the trader and the strategy's actual requirements — not a flaw in the strategy itself.

---

## Step 2 — Build a regime filter before any signal code

No strategy works in all conditions. Define the market condition your strategy needs, then build a simple detector for it before writing a single signal.

| Regime | What it looks like | Strategies that work | Strategies that fail |
|---|---|---|---|
| **Trending** | Sustained directional price movement | Trend following, breakouts, momentum | Classic mean reversion |
| **Ranging** | Oscillation within a defined band | Mean reversion, market making | Trend systems (whipsaw losses) |
| **High volatility expansion** | Wide spreads, fast moves, gaps | Long vol, defensive trend | Tight mean reversion, arb without buffers |
| **Low volatility grind** | Tight spreads, slow drift | Carry, execution-focused, tight MR | Breakout systems (false signals) |

**Implementation note:** Keep the regime detector simple, stable, and explainable. A useful starting point is ATR relative to its 60-day average, or the slope of a slow moving average. Avoid adding so many regime conditions that the filter becomes a second hidden strategy — that introduces a new source of overfitting and makes failure analysis much harder.

**How to use it:** Gate every entry on the regime check. A strategy that fires in the wrong regime is not a different strategy — it is a losing trade you have systematically enabled.

---

## Step 3 — Calculate real expectancy before live deployment

Every strategy must clear this gate before promoting beyond research or paper trading.

```
Expectancy per trade = (Win Rate × Avg Win) − (Loss Rate × Avg Loss) − Costs

Costs = Fees + Spread + Slippage + Funding (if applicable)
```

**How to stress-test this number:** Run the calculation at 2× your estimated slippage. Does it stay positive? Run it across a volatile period in your data. Does it still hold?

**A conservative pre-live filter:** Require expected edge per trade to be several times larger than stressed execution costs. This is a heuristic, not a law — the right multiple depends on your turnover frequency, edge half-life, and liquidity conditions. The purpose is to screen out strategies where execution variance alone can flip the outcome. If your edge is thin enough that one bad fill changes the sign of your expectancy, you do not have a deployable strategy yet.

---

## Step 4 — Match infrastructure to your horizon

The wrong infrastructure for your time horizon is one of the most common and most preventable sources of edge destruction.

| Horizon | Data needed | Latency requirement | Infrastructure minimum |
|---|---|---|---|
| Seconds–minutes | Level 2 order book, tick data | Sub-100ms | Colocated or VPS near exchange |
| Minutes–hours | OHLCV 1m/5m, trade flow | Under 1 second | Stable VPS, WebSocket feeds |
| Hours–days | OHLCV hourly/daily | Minutes acceptable | Any stable server, scheduled jobs |
| Days–weeks | Daily OHLCV, fundamentals | End-of-day acceptable | Even a laptop works |

**Practical implication:** If you are using 5-minute bars and REST API polling, you are not competing with anyone who matters on that timeframe. You need WebSocket. If you are trading daily closes, REST polling is fine. Matching infrastructure to horizon costs nothing except the decision. Mismatching it costs edge you cannot recover through better signals.

---

## Step 5 — Build the risk system before live deployment

These controls must exist and be tested before any signal code runs live. This order is not arbitrary — a strategy without risk controls is a liability, not an asset.

**Hard stops (automated, no exceptions):**
- Maximum capital at risk per trade: **0.25–1.0% of total capital** measured at your stop level, not notional position size — these are different numbers and the distinction matters
- Daily loss limit that halts the system: **1–3% of capital** as a conservative starting default; only widen after evidence justifies it
- Kill switch that closes all positions and stops the system with a single command
- Maximum exposure per symbol, per venue, per correlated group, and across all live strategies simultaneously — individual per-trade limits can add up to catastrophic total exposure; set a portfolio-level cap or they will; two positions in different instruments can represent the same underlying risk if they are correlated

**Regime stops (systematic):**
- If the regime detector signals wrong conditions, the strategy does not run — even if the entry signal fires
- If recent fill slippage exceeds 1.5× your backtest estimate, pause and investigate before continuing

**Drawdown rules:**
- Define your maximum acceptable drawdown before you start (e.g., 15%)
- At 50% of that level: halve position size
- At 75% of that level: paper trading only
- At the limit: stop, full review before any live trading resumes

---

## Step 6 — Operational integrity before every session

A strategy that is sound in theory can destroy capital through operational failures that have nothing to do with the signal.

**Session-start checks:**
- Market data feed is live, current, and internally consistent — confirm timestamp, not just connectivity
- Internal position record matches broker/exchange record within defined tolerance
- Kill switch path is verified as available and reachable; test it regularly and after any material system change — session-start checks confirm availability, not necessarily a full destructive test every session
- No unresolved order retry loops from previous session
- Authentication tokens are valid
- Every halt, restriction, recovery event, and manual override is logged with timestamp and reason

**Automatic halts (no manual decision required):**
- Market data stale beyond your threshold → no new entries
- Broker/exchange rejects orders repeatedly → halt, investigate
- Any unexpected or unresolved position mismatch → restrict to flatten-only until reconciled
- System clock, connectivity, or authentication failure → halt

**Manual overrides:** These should be rare, logged with explicit reason, and followed by review before normal promotion or scaling resumes.

**Recovery rule — apply on every restart:**

If the system cannot confidently determine current positions, working orders, and account state after a restart or reconnect:
- No new entries are permitted
- Only reconcile, flatten, and restrict actions are allowed until full state is confirmed

A system that resumes trading without confirming its own state is a system that is one restart away from a large unintended position. Default to no new risk when state is ambiguous.

---

## Step 7 — Use promotion gates, never skip stages

The most expensive mistake is going live before the evidence warrants it. Use this sequence in order.

**Paper (simulation only) — minimum requirements to advance:**
- 30 trading days minimum
- 50+ completed round trips
- Observed expectancy within a tolerable range of backtest assumptions
- No critical operational bugs encountered
- Kill switch tested

**Shadow (live data, no orders) — minimum requirements to advance:**
- Every signal logged and compared to what actually happened
- Slippage assumptions validated against contemporaneous spread and depth data — shadow mode gives you estimates against live conditions, not certainty about real fills; you are validating assumptions, not measuring outcomes
- Operational integrity checks passing consistently

**Capped live (real orders, reduced size):**
- Start at 25% of intended position size
- Minimum observation period: 20+ completed trades **and** sufficient time in market for the strategy's frequency — a system that trades twice a week needs months at this stage, not two weeks; do not promote a low-frequency system on trade count alone
- Expectancy holding within acceptable range of shadow estimates
- Scale up only after both thresholds are met

**Full size:**
- Only after capped live confirms the strategy behaves as expected at scale
- Increase gradually, not all at once

---

## Step 8 — Define the retirement conditions now

Edges decay. Most people define entries and never define retirement. Define it before you need it, while you are thinking clearly.

**Review monthly:**
- Is average slippage increasing? (Sign of crowding or liquidity change)
- Is win rate drifting below the backtest range? (Sign of regime shift or model drift)
- Are drawdowns taking longer to recover? (Sign of structural change)

**Mandatory review triggers:**
- Two consecutive months of negative expectancy
- Drawdown exceeds 50% of your defined maximum
- Any material market structure change: new regulation, major exchange change, sustained volatility regime shift

**The rule:** You retire the strategy. The strategy does not retire you. Define these thresholds before you start. Deciding under drawdown pressure produces bad outcomes systematically.

---

## One-page summary

1. Locate yourself — capital, horizon, infrastructure, drawdown tolerance
2. Build the regime filter first, keep it simple and explainable
3. Calculate real expectancy including stressed execution costs — thin edge is not deployable edge
4. Match infrastructure to horizon — mismatch silently destroys edge
5. Build risk controls first: 0.25–1.0% capital at risk per trade, 1–3% daily halt, kill switch, portfolio-level and correlation-aware exposure caps
6. Operational integrity before every session: data fresh, positions reconciled, kill switch reachable, all events logged, recovery rule enforced on restart
7. Paper → shadow → capped live → full size — promotion requires both trade count and time in market; never skip a stage
8. Define the retirement conditions before you go live
