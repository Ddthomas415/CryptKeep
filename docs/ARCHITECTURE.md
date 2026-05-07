# Architecture

## Current Repo Shape

Crypto Bot Pro is a crypto-first operator platform with four major concerns:

- market-data collection and runtime snapshots
- strategy runtime and evidence generation
- paper trading and guarded live execution
- dashboard/operator workflows

The repo is no longer a read-only market-data phase repo. It contains execution paths, paper trading, reconciliation, authentication, and operator controls.

Focused architecture note:

- `docs/architecture/multi_symbol_architecture_map.md` — current multi-symbol runtime and ownership map

## Major Layers

### 1. Operator / UI Layer

Primary dashboard code lives in:

- `dashboard/`

Current operator-facing pages and services include:

- dashboard pages such as `dashboard/pages/60_Operations.py`
- runtime/status loaders in `dashboard/services/*`
- operator controls in `dashboard/services/operator.py`

This layer is responsible for:

- surfacing runtime truth
- showing evidence and safety status
- offering guarded start/stop/recovery actions

It is not the final authority for live-order submission.

### 2. Strategy Runtime Layer

Current strategy runtime execution centers on:

- `services/strategy_runner/ema_crossover_runner.py`
- `scripts/run_strategy_runner.py`

Related strategy implementations live in:

- `services/strategies/*`

This layer is responsible for:

- reading fresh market snapshots
- computing strategy signals
- applying strategy-side filters and exit logic
- emitting intents for paper/live downstream execution
- writing runtime status for operator surfaces

This layer is not the final live-order boundary.

### 3. Market Data Layer

Current canonical market-data family is:

- `services/market_data/*`

Important pieces include:

- snapshot/tick readers
- symbol routing
- system-status publication
- tick publisher runtime scripts

The strategy runner currently depends on runtime snapshots, especially:

- `.cbp_state/runtime/snapshots/system_status.latest.json`

Fresh-tick availability is therefore an operational dependency of strategy execution.

### 4. Execution Layer

Execution code is spread across:

- `services/execution/*`
- `storage/*`

Current major execution responsibilities:

- intent handling
- paper engine behavior
- exchange adapters and clients
- reconciliation/fill confirmation
- final live-order submission boundary

### 5. Evidence / Evaluation Layer

Evidence and decision-record logic lives primarily in:

- `services/backtest/evidence_cycle.py`
- `services/analytics/paper_strategy_evidence_service.py`
- `docs/strategies/*`

This layer is responsible for:

- scorecards and leaderboard generation
- paper-history integration
- evidence artifacts
- decision-record generation

This is a real working subsystem, but current strategy evidence in the repo remains conservative and often thin.

## Canonical Safety Boundaries

### Final live submit boundary

The final raw-order submit authority is:

- `services/execution/place_order.py`

This is the key fail-closed live-order boundary. No new raw exchange submit path should bypass it.

See:

- `docs/safety/live_order_authority_layers.md`
- `docs/safety/phase1_live_order_boundary.md`

### Lifecycle truth

Submit safety is stronger than broader lifecycle safety.

Current lifecycle review summary is documented in:

- `docs/safety/lifecycle_matrix.md`

Today:

- submit paths are centralized more strongly
- cancel/fetch/reconcile paths still include direct exchange calls
- submit safety should not be overgeneralized to full lifecycle safety

## Canonical vs Transitional Families

The repo still carries compatibility and transitional families.

Current documented split:

- Canonical:
  - `services/strategies`
  - `services/market_data`
  - `services/paper_trader`
- Transitional / compatibility:
  - `services/strategy`
  - `services/strategy_runner`
  - `services/marketdata`
  - `services/paper`

See:

- `docs/architecture/transitional_service_families.md`

Contributor rule:

- prefer canonical families for new work
- do not add new direct imports into frozen compatibility families unless a migration step explicitly requires it

## Runtime Modes

Current supported runtime understanding is documented in:

- `docs/safety/live_mode_contract.md`

Practical current model:

- `paper` is the safest normal execution mode
- `sandbox live` exists for controlled live-stack exercises
- `real live` exists but remains high-caution and guarded

## State and Storage

The repo uses local runtime/data state heavily.

Common storage surfaces include:

- `.cbp_state/runtime/*` for runtime flags, locks, snapshots, logs
- `.cbp_state/data/*` for paper trading, journals, idempotency, pnl, and related SQLite state
- `data/*.sqlite` for additional local stores

This means operational correctness often depends on:

- lock files
- runtime status files
- local SQLite state
- snapshot freshness

## What This Repo Is Today

Based on the current code and docs, the repo is best understood as:

- a crypto-first operator platform
- with paper trading and guarded live execution
- with a real evidence/decision workflow
- with reconciliation and operator safety surfaces

It should not be described as only a market-data collector.

## Known Architectural Debt

The current repo still shows these structural realities:

- multiple service families exist for similar concepts
- some compatibility paths remain intentionally frozen
- docs and implementation have historically drifted
- submit safety is stronger than full lifecycle proof
- strategy evidence exists, but strong promotion/profit claims are not supported by current paper-history depth

These are real repo traits, not hidden features.

## Open Scope Questions

The following are still scope questions, not settled facts:

- whether `services/desktop/service_manager.py` is intended to become a supported service-control path
- whether sidecar trees like `crypto-trading-ai/` and `phase1_research_copilot/` are active product scope or retained companion work
- whether deprecated compatibility shims should remain for callers or be removed after migration

Those decisions should be made explicitly rather than inferred from file presence.

## Service Family Migration Deadlines

The following parallel/transitional service families are frozen for compatibility
and scheduled for removal. No new code should be added to transitional families.
Migration target: **2026-07-01**.

| Transitional (frozen) | Canonical (use this) | Status |
|---|---|---|
| `services/strategy/` | `services/strategies/` | Frozen — no new imports |
| `services/strategy_runner/` | `services/strategies/` + scripts | Frozen — no new imports |
| `services/paper/` | `services/paper_trader/` | Frozen — no new imports |
| `services/marketdata/` | `services/market_data/` | Frozen — no new imports |

**Rules until removal:**
- Do not add new files to transitional families.
- Do not add new callers that import from transitional families.
- When adding a feature that would touch a transitional family, add it to the canonical family instead.
- Migration of existing callers can be done incrementally — file a tracking issue per family.

**Removal process (per family):**
1. Confirm no active callers remain (grep for imports).
2. Move any still-needed logic to canonical family.
3. Delete the transitional directory.
4. Update this doc.

## Signal / Candidate Layer (System 1)

As of 2026-04, the repo includes a scored signal and candidate ranking layer
upstream of the strategy runner:

- `services/signals/signal_library.py` — individual signal scores
- `services/signals/market_ranker.py` — composite score + ranking
- `services/signals/trade_type_classifier.py` — quick_flip / swing_trade / pass
- `services/signals/candidate_engine.py` — builds ranked candidate list
- `services/signals/candidate_strategy_mapper.py` — maps candidate to strategy
- `services/signals/candidate_store.py` — latest + append-only JSONL history
- `services/signals/candidate_advisor.py` — top candidate selection
- `scripts/review_candidate_outcomes.py` — candidate-vs-outcome review loop

The candidate advisor can optionally override strategy selection via
`CBP_USE_CANDIDATE_ADVISOR=1`. This is behind a flag and should not be enabled
in live trading until outcome attribution confirms the layer adds signal.

**Current status:** paper-only, evidence accumulation phase.
