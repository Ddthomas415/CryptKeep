# Multi-Symbol Architecture Map

Status: current repo truth as traced from source on 2026-05-07.

This note maps the repo's current multi-symbol surfaces. It is intentionally narrower than `docs/ARCHITECTURE.md` and `docs/CURRENT_RUNTIME_TRUTH.md`.

## Executive summary

- The repo has real multi-symbol components.
- The current supervised bot runtime can now fan out across an explicit managed symbol list.
- The only visible in-process multi-symbol execution loop lives in `services/strategy_runner/ema_crossover_runner.py`.
- Symbol scanning and dynamic selection now feed the supervised paper runtime when `managed_symbols.source=scanner` is enabled, but they are still not the live execution authority.
- `live_trader_multi` exists, but the current implementation is dry-run gated and not part of the canonical managed service set.

## 1. Canonical managed bot runtime

Current operator-facing runtime truth says the canonical managed service set is:

- `pipeline`
- `executor`
- `intent_consumer`
- `ops_signal_adapter`
- `ops_risk_gate`
- `reconciler`
- `ai_alert_monitor`

Source:

- `docs/CURRENT_RUNTIME_TRUTH.md`
- `services/process/bot_runtime_truth.py`

Multi-symbol shape in this lane:

- `scripts/run_bot_runner.py` resolves managed symbols through `services/runtime/managed_symbol_selection.py`, then injects that symbol set into managed child processes through `CBP_SYMBOLS`.
- `scripts/run_pipeline_loop.py` resolves managed symbols from `CBP_SYMBOLS`, then `execution.symbols` / `pipeline.symbols`, then legacy fallback fields, and builds one pipeline instance per symbol.
- `scripts/run_intent_executor.py` resolves the same managed symbol set from `CBP_SYMBOLS` and removes the reconcile symbol filter when more than one managed symbol is active.
- `services/execution/intent_executor.py` claims queue work by venue/mode, and each claimed intent carries its own `symbol`.

Current conclusion:

- This supervised lane is config-aware of symbol lists.
- The active `pipeline` service can now evaluate a managed list of symbols in one supervised process.
- The `executor` can submit whichever symbol is present on the claimed intent and reconcile either one managed symbol or the full managed set.
- Current canonical bot control is materially closer to end-to-end multi-symbol paper readiness, but candidate selection and broader ownership questions are still separate.

## 2. Strategy-runner multi-symbol lane

`services/strategy_runner/ema_crossover_runner.py` is a real multi-symbol loop:

- `_cfg()` reads `CBP_SYMBOLS`, `strategy_runner.symbols`, `preflight.symbols`, or a single fallback symbol.
- `run_forever()` materializes `symbols = list(cfg.get("symbols") or [cfg.get("symbol")])`.
- The main loop iterates `for symbol in symbols`.
- State keys are namespaced per `(venue, symbol, strategy_id)`.
- The runner also calls `validate_multi_symbol_state(...)` to detect duplicate open positions or too many open intents per symbol.

Source:

- `services/strategy_runner/ema_crossover_runner.py`
- `services/validation/paper_multi_symbol_validation.py`

Current conclusion:

- This lane implements real multi-symbol signal evaluation and per-symbol state handling.
- It is the clearest current execution-capable multi-symbol path visible in source.
- It is not the current operator-facing managed runtime truth.

## 3. Scanner, rotation, and candidate-selection lane

The repo has multiple upstream multi-symbol analytics surfaces:

- `services/market_data/symbol_scanner.py`
- `services/runtime/dynamic_symbol_selector.py`
- `services/market_data/rotation_engine.py`

Current wiring shape:

- `docs/symbol_scanner.md` predates the current supervised-paper wiring and is now stale on that point.
- `services/runtime/dynamic_symbol_selector.py` selects a ranked list of tradeable symbols from scanner output.
- `services/runtime/managed_symbol_selection.py` is the current caller and uses a refresh-cached scanner result plus freshness-bounded active-symbol preservation in paper mode.
- `services/market_data/rotation_engine.py` is used by dashboard pages and a backtest selector, not by the supervised execution runtime.

Current conclusion:

- This lane is now the candidate-selection authority for the supervised paper runtime when explicitly enabled.
- It is still not the live symbol-selection authority, and it does not replace the broader ownership decision between the supervised runtime family and `strategy_runner`.

## 4. Multi-exchange data ingestion lane

The repo also has a separate multi-exchange ingestion surface:

- `services/data/multi_exchange_collector.py`
- `scripts/collect_market_data_multi.py`
- `docs/PHASE28_MULTI_EXCHANGE_INGESTION.md`

Current conclusion:

- This lane broadens market-data collection across venues.
- It is not, by itself, a multi-symbol execution architecture.
- It should be treated as a data-ingestion/input surface unless a later runtime explicitly consumes it.

## 5. Experimental live-multi lane

`services/live_trader_multi/main.py` is not current canonical runtime truth:

- It exits unless `CBP_RUN_MODE=live`.
- It prints `live_trader_multi started (dry-run mode)`.
- The body uses simulated order logic and placeholder fill recording.

Current conclusion:

- `live_trader_multi` is present, but the visible implementation is still dry-run shaped.
- It is not part of the managed service set documented in `docs/CURRENT_RUNTIME_TRUTH.md`.
- It should not be treated as the repo's canonical live multi-symbol architecture.

## 6. Doc drift that matters

The repo currently presents more than one runtime story:

- `docs/CURRENT_RUNTIME_TRUTH.md` says the canonical operator path is the supervised `start_bot.py` / `stop_bot.py` / `bot_status.py` stack.
- `docs/ARCHITECTURE.md` still says strategy runtime execution centers on `services/strategy_runner/ema_crossover_runner.py`.
- `docs/GOLDEN_PATH.md` still presents `run_strategy_runner.py` as part of the canonical paper runtime.
- `docs/ARCHITECTURE.md` also marks `services/strategy_runner/` as a frozen transitional family.

Current conclusion:

- The repo does not have one clean, canonically documented multi-symbol execution story.
- The main gap is ownership clarity: which runtime family is authoritative for multi-symbol execution.

## 7. Current map

```text
Config symbols list
  |
  +-- supervised bot runtime
  |     run_bot_runner -> pipeline + executor/intent_consumer
  |     current behavior: pipeline fans out across managed symbols; executor consumes queued intents by symbol
  |
  +-- strategy runner lane
  |     run_strategy_runner -> ema_crossover_runner
  |     current behavior: loops across symbols inside one process
  |
  +-- analytics lane
  |     symbol_scanner -> dynamic_symbol_selector -> rotation_engine
  |     current behavior: ranking/selection insight, not execution-wired
  |
  +-- data lane
        collect_market_data_multi -> multi_exchange_collector
        current behavior: ingestion only
```

## 8. What is true today

- The repo supports symbol lists in config.
- The current supervised runtime can execute an explicit managed symbol list in the `pipeline` / `executor` paper path.
- The older strategy-runner lane does have a real multi-symbol loop.
- Multi-symbol candidate selection is now execution-wired for supervised paper mode only.
- A canonical multi-symbol architecture decision is still outstanding.

## 9. Next decision to make

Choose one of these as the canonical owner of multi-symbol execution:

1. Supervised `pipeline` / `executor` family
2. `strategy_runner` family
3. A new explicitly documented orchestration layer that consumes candidate selection and shards symbol execution deliberately

Until that decision is made, treat multi-symbol support as partial and lane-specific rather than as one unified system capability.
