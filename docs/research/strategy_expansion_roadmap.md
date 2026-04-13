# CryptKeep Strategy Expansion Roadmap

This note combines the current repo findings and the recommended next research/build sequence into one path.

It is intentionally conservative:

- prove edge credibility before adding optimization
- extend existing repo lanes before opening new architecture branches
- keep all new research work behind the current execution and promotion boundaries

## Current repo truth

Current repo anchors:

- strategy evidence and ranking:
  - `<your-repo-path>/services/backtest/evidence_cycle.py`
  - `<your-repo-path>/services/backtest/leaderboard.py`
  - `<your-repo-path>/docs/safety/strategy_research_acceptance.md`
- strategy registry and current strategy family count:
  - `<your-repo-path>/services/strategies/strategy_registry.py`
- signal-source feedback weighting already exists:
  - `<your-repo-path>/services/signals/reliability.py`
  - `<your-repo-path>/services/learning/consensus_signal_engine.py`
- research-only crypto-native non-price lane already exists:
  - `<your-repo-path>/services/analytics/crypto_edge_collector.py`
  - `<your-repo-path>/services/analytics/crypto_edges.py`
  - `<your-repo-path>/docs/research/crypto_structural_edges.md`
- webhook signal intake already exists:
  - `<your-repo-path>/services/trader_signals/webhook_server.py`
- runner-specific trailing stop logic already exists:
  - `<your-repo-path>/services/strategy_runner/ema_crossover_runner.py`
- regime-aware scoring already exists:
  - `<your-repo-path>/services/backtest/parity_engine.py`
  - `<your-repo-path>/services/backtest/regimes.py`
- orderbook checks already exist, but as safety/execution diagnostics rather than alpha generation:
  - `<your-repo-path>/services/execution/orderbook_sanity.py`

What that means:

- CryptKeep is no longer purely price-only at the research layer.
- CryptKeep is still dominated by price-based strategy logic at the strategy-selection layer.
- The next value should come from validating and weighting edges better, not from adding many more unproven strategy families.

## Recommended build order

### 1. Walk-forward strategy validation

Do this first.

Purpose:

- answer whether current strategy performance is sample noise or a durable edge
- create a stricter out-of-sample bar before parameter search

Implementation target:

- add anchored walk-forward runs on top of `<your-repo-path>/services/backtest/parity_engine.py`
- write summary artifacts beside the existing evidence-cycle outputs
- surface walk-forward pass/fail in:
  - strategy evidence rows
  - strategy lab report
  - decision record output

Explicit non-goal:

- no auto-promotion from walk-forward results alone

### 2. Strategy feedback ledger

Do this second.

Purpose:

- extend the existing signal-reliability feedback pattern up to the strategy level
- let realized strategy outcomes conservatively influence future research ranking

Implementation target:

- create a rolling strategy-outcome ledger keyed by:
  - `strategy_id`
  - `symbol`
  - `venue`
  - `regime`
- compute:
  - realized expectancy
  - win rate
  - drawdown
  - sample size
  - paper/live drift where available
- feed that back as a penalty/boost into:
  - leaderboard research weighting
  - strategy lab recommendations

Explicit non-goals:

- no auto-live enablement
- no self-optimizing capital allocator

### 3. Funding and basis feature scoring

Do this third.

Purpose:

- use crypto-native non-price context that is already partially supported by the repo
- test whether funding/basis improve strategy selection or regime gating

Implementation target:

- keep `<your-repo-path>/services/analytics/crypto_edge_collector.py` and `<your-repo-path>/services/analytics/crypto_edges.py` research-only
- score whether funding/basis snapshots improve:
  - regime tagging
  - entry filtering
  - strategy ranking confidence
- compare “price-only” vs “price + structural edge features” offline

Explicit non-goals:

- no direct execution from funding/basis alone
- no profitability claim from descriptive summaries

### 4. Offline hyperparameter search

Do this only after walk-forward exists.

Purpose:

- tune strategy parameters as a research tool instead of hand-editing thresholds

Implementation target:

- add an offline research lane for:
  - EMA windows
  - RSI thresholds
  - Donchian length
  - filter thresholds already present in current strategy configs
- require every tuning run to emit:
  - in-sample result
  - out-of-sample walk-forward result
  - stressed slippage result

Explicit non-goals:

- no auto-updating live params
- no hyperopt-driven promotion without separate evidence review

### 5. Governed external signal integration

Do this after the research loop is stronger.

Purpose:

- accept signals from charting or outside research systems without bypassing CryptKeep controls

Implementation target:

- extend `<your-repo-path>/services/trader_signals/webhook_server.py`
- treat TradingView or other webhook sources as:
  - signal producers
  - not execution authorities
- route all accepted signals through existing:
  - intent queue
  - risk gates
  - evidence/journal path

Explicit non-goals:

- no “alert fires, order executes directly” bypass

### 6. Shared exit-policy module

Do this after feedback and validation are in place.

Purpose:

- extract runner-specific exit logic into a reusable policy layer

Implementation target:

- promote current trailing-stop / stop-loss / take-profit / max-bars-hold logic from `<your-repo-path>/services/strategy_runner/ema_crossover_runner.py`
- make it a governed shared exit-policy module usable across strategy families

Explicit non-goals:

- no hidden per-runner divergence in trailing-stop behavior

### 7. Later microstructure research lane

Do this much later.

Purpose:

- explore orderbook imbalance, microprice, tape, and spread as research features

Why it is later:

- current repo orderbook support is diagnostic/safety-oriented, not alpha-oriented
- meaningful microstructure research wants cleaner venue-specific stream quality and stronger event timing discipline

Implementation target:

- keep it in a research-only lane first
- compare:
  - orderbook imbalance
  - spread state
  - microprice drift
  - top-of-book liquidity changes
against existing strategy outcomes

Explicit non-goals:

- no premature live microstructure execution logic

### 8. DCA as a separate research family

This is last.

Purpose:

- treat DCA as a different risk model, not as a small enhancement to current strategies

Why it is last:

- it changes exposure behavior and drawdown semantics materially
- it should not be mixed with the current “prove one edge family first” path

## What not to do next

Avoid these near-term mistakes:

- do not add hyperopt before walk-forward validation
- do not add many new strategies before the current strategy-feedback loop exists
- do not let webhooks bypass the governed intent/risk path
- do not confuse research-only funding/basis summaries with execution-ready alpha
- do not treat orderbook diagnostics as proven microstructure signals

## External references

Use these as references, not templates to copy blindly:

- `Freqtrade`
  - best reference for research workflow, dry-run/live ergonomics, and offline optimization patterns
- `Awesome Systematic Trading`
  - best catalog for surveying tools and related frameworks
- `Intelligent Trading Bot`
  - useful reference for feature engineering and learned-signal thinking
- `Nautilus Trader`
  - useful later if CryptKeep ever needs a more event-driven, lower-latency architecture

## Research search terms

Priority searches:

- `walk forward optimization crypto strategy python`
- `anchored walk forward backtest python`
- `adaptive strategy weighting realized pnl sqlite`
- `funding rate carry signal perp spot basis crypto python`
- `feature importance funding basis regime crypto`
- `bayesian hyperparameter optimization backtesting python`
- `tradingview webhook HMAC python bot`
- `trailing stop exit policy python trading system`
- `order flow imbalance crypto python websocket`

## Recommended next implementation target

If only one next build starts now, choose:

1. walk-forward validation

If two can be carried together, choose:

1. walk-forward validation
2. strategy feedback ledger

That sequence best fits the current repo maturity and the questions still unanswered by the existing evidence cycle.
