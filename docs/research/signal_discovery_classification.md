# Signal Discovery Surface Classification

Date: 2026-07-03

## Finding

The repo has two discovery/ranking layers:

- `services/signals/` - candidate scan and advisory strategy mapping.
- `services/market_data/composite_ranker.py` and
  `services/market_data/rotation_engine.py` - market-data composite ranking and
  rotation candidates used by backtest/research tools.

## Classification

| Surface | Classification | Current role |
|---|---|---|
| `services/signals/signal_library.py` | `research_only` | Score primitives for candidate scans |
| `services/signals/market_ranker.py` | `research_only` | Candidate composite score/ranking |
| `services/signals/trade_type_classifier.py` | `research_only` | Classifies candidate setup type |
| `services/signals/candidate_strategy_mapper.py` | `research_only` | Maps candidate setup to strategy name |
| `services/signals/candidate_engine.py` | `research_only` | Builds ranked candidate list |
| `services/signals/universe_loader.py` | `research_only` | Loads scan universe/defaults |
| `services/signals/candidate_store.py` | `advisory_only` | Stores candidate snapshots |
| `services/signals/candidate_advisor.py` | `advisory_only` | May advise strategy selection behind explicit flag |
| `services/market_data/composite_ranker.py` | `research_only` | Composite ranking for research/backtest |
| `services/market_data/rotation_engine.py` | `research_only` | Rotation candidates consumed by selector backtests |

## Promotion Rule

No discovery score may affect trade/no-trade, sizing, or promotion until all are
true:

- archive-backed walk-forward proof exists
- metrics are net of fees/costs
- campaign config explicitly enables the behavior
- paper evidence records the discovery input as provenance
- the change is independently reviewed if it touches gates or execution

## Practical Next Step

Use these layers to propose candidates and research hypotheses. Do not allow
them to mutate canonical campaign manifests automatically.

## Executable Guards

- `tests/test_strategy_discovery_hygiene_contract.py` proves the classification
  table still matches the tracked source tree.
- The same guard blocks direct imports of discovery/ranker modules from
  execution, control, governance, and the governed paper evidence collector.
- `services/strategies/strategy_selector.py` is the only documented runtime
  bridge to `candidate_advisor`, and it remains gated by
  `CBP_USE_CANDIDATE_ADVISOR`.
- `open_interest_shift` is a config-only research placeholder until it is
  registered in `strategy_registry.compute_signal`; config tooling and the
  default preset must keep it `trade_enabled=false`.
