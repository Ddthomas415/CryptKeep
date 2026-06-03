# Infrastructure Activation Audit - 2026-06-03

## Scope

This is a first-pass inventory of repo infrastructure that exists beyond the
current active `sma_200_trend` paper campaign.

The objective is not to "turn everything on." The objective is to classify what
is active, partially wired, dormant, research-only, superseded, or unsafe to
enable so future activation work can be sequenced without corrupting the current
evidence campaign.

## Evidence Basis

SHOWN:
- `docs/GOLDEN_PATH.md` defines the canonical runtime as the managed
  `sma_200_trend` paper campaign, paper sim monitor, promotion gate checker,
  and operator dashboard.
- `scripts/check_promotion_gates.py --json` reports the current paper gate at
  `29/30` days and `7/10` round trips, with manual review still required.
- `scripts/run_paper_strategy_evidence_collector.py --status` reports the daily
  collector alive and idle, waiting for the next UTC day.
- `docs/ARCHITECTURE.md` documents the signal/candidate layer as paper-only and
  evidence accumulation phase.
- `docs/ARCHITECTURE.md` marks several transitional service families as frozen
  and says not to add new callers to them.
- `docs/GOLDEN_PATH.md` marks packaging/desktop surfaces as optional and older
  sidecar workspaces as archived.
- Repo files exist for AI engine, signals/candidate ranking, AI copilot,
  alerts, learning/feedback, desktop/service management, dashboard pages, and
  many operator scripts.

UNVERIFIED:
- Any percentage estimate like "30-40% of the repo is used." That number is not
  directly proven by the current audit.
- Whether each dashboard page has live data. Page-by-page runtime inspection was
  not performed in this pass.
- Whether each script is currently documented correctly in `scripts/SCRIPTS.md`.
  Script documentation needs a separate script-index audit.

## Current Active Operating Path

Classification: `active`

Current production-facing paper path:
- `scripts/run_paper_strategy_evidence_collector.py --daily-loop`
- `scripts/check_promotion_gates.py --json`
- `scripts/run_paper_sim_monitor.py`
- `services/analytics/paper_strategy_evidence_service.py`
- `services/analytics/paper_sim_monitor.py`
- `services/strategies/es_daily_trend.py`
- `services/strategies/evidence_logger.py`
- `services/execution/paper_engine.py`
- `services/strategy_runner/ema_crossover_runner.py`
- `dashboard/`

Activation rule:
- Do not mix new strategy, ML, alert, or candidate-selection behavior into this
  path until the current paper gate and manual review state are resolved.

## Subsystem Classification

| Subsystem | Classification | Evidence | Smallest safe next step |
|---|---|---|---|
| `sma_200_trend` paper evidence path | `active` | Golden Path and current collector/gate status show this is the live paper campaign. | Keep isolated until gate decision completes. |
| Strategy registry | `active / partially_wired` | `strategy_registry.py` supports more strategies than the current campaign uses. | Add candidate strategies to evidence evaluation one at a time. |
| `pullback_recovery` | `partially_wired` | Present in registry, absent from current aggregate leaderboard rows. | Add to leaderboard/evidence evaluation before paper campaign. |
| `ema_cross`, `breakout_donchian`, `mean_reversion_rsi` | `partially_wired` | Existing strategies and presets, but current real paper history is only `sma_200_trend`. | Create separate paper-only challenger campaign plan. |
| `funding_extreme`, `open_interest_shift` | `research_only` | Presets/config support exist, but these require derivatives/funding/open-interest inputs. | Audit data plumbing and risk model before leaderboard or paper use. |
| `order_book_imbalance` | `research_only / unsafe_to_enable` | Module exists but requires reliable level-2 order book input and short-timeframe execution assumptions. | Prove market-data feed and read-only signal logging first. |
| Signals/candidate layer | `partially_wired` | `docs/ARCHITECTURE.md` describes it as paper-only; `run_candidate_scan.py`, candidate engine, advisor, and strategy selector wiring exist. | Run read-only candidate scan and compare against current evidence without routing trades. |
| AI engine | `research_only / partially_wired` | `services/ai_engine` has model, features, signal service, trainer; live router imports signal service. | Keep research-only until enough labeled paper outcomes exist. |
| Learning/feedback | `partially_wired / research_only` | Consensus filter and reliability pieces exist; feature store, runtime policy, and canary enforcement are not the active campaign authority. | Document which learning outputs are advisory only before using them for strategy selection. |
| AI copilot | `partially_wired / research_only` | Copilot reports, strategy lab, drift/safety scripts, and dashboard surfaces exist; no autonomous operator loop is currently the source of truth. | Keep report-only; do not let copilot mutate runtime or promotion state. |
| Alerts | `partially_wired` | Alert router/dispatcher/email notifier exist; paper sim monitor also writes watch reports and desktop notifications. | Route one existing low-risk event class, such as campaign-complete or new-fill paper alert, through a single documented alert path. |
| Dashboard pages | `partially_wired` | Many pages exist; Home/Operations are known active, but page-by-page live-data proof is not complete. | Perform a dashboard page data-source audit. |
| Desktop/build surfaces | `optional / partially_active` | Golden Path says packaging/desktop are optional; build workflows and docs exist. | Keep optional; do not treat desktop launcher as core runtime authority. |
| Operator scripts | `partially_wired / underdocumented` | Many scripts exist; `scripts/SCRIPTS.md` documents some, but a full script-index audit was not performed. | Audit script docs against actual script inventory and classify safe operator commands. |
| Transitional service families | `superseded / frozen` | `docs/ARCHITECTURE.md` says no new imports for frozen families. | Do not activate; only migrate or remove through dedicated cleanup. |
| Archived sidecar workspaces | `superseded / research_only` | Golden Path marks older sidecar workspaces as archived. | Do not make active product dependencies without a separate ADR. |

## Activation Order

1. Preserve current paper campaign isolation.
2. Complete the paper gate and manual review for `sma_200_trend`.
3. Wire alerts for already-authoritative events only: campaign completed,
   new fill, position closed, investigate recommendation.
4. Run the signals/candidate layer read-only and compare candidates to actual
   paper outcomes.
5. Add `pullback_recovery` to leaderboard/evidence evaluation.
6. Create a challenger paper campaign plan for `ema_cross` and
   `breakout_donchian`.
7. Keep AI engine and learning systems research-only until labeled real paper
   outcomes are sufficient for validation.
8. Defer short-side, funding, open-interest, and order-book strategies until
   data plumbing, risk controls, and venue assumptions are explicit.
9. Audit dashboard pages and script docs so operators know which surfaces are
   authoritative.

## Immediate Recommendation

The highest-leverage activation work is not ML or short-side execution. It is:

1. Keep the current `sma_200_trend` campaign clean.
2. Make alert routing reliable for existing paper events.
3. Add `pullback_recovery` to leaderboard/evidence evaluation.
4. Run the candidate layer read-only and measure whether it identifies useful
   opportunities earlier than the current strategy.

## Risks

- HIGH: trading infrastructure and strategy-selection surfaces.
- Do not enable dormant systems directly from this audit.
- Every activation step that can affect strategy selection, order routing,
  promotion gates, or operator alerts needs its own implementation proof and
  independent review.

Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.
