# Project Directional Plan

Date: 2026-08-01

## Direction Lock

CryptKeep's direction is an event-driven trading intelligence platform built as
a modular monolith.

The project is not a single BTC paper-gate project, and the BTC paper campaign
must not become the identity of the system. The paper gate is one validation
track inside the broader platform.

## North Star

Build the original two-brain trading intelligence system:

- research intelligence brain: source discovery, web/archive context, event
  extraction, time-aware memory, strategy research, and operator explanations;
- deterministic trading machine brain: market sensing, strategy scoring,
  symbol selection, paper/shadow/live state handling, portfolio/risk checks,
  and execution boundaries.

The LLM/research layer investigates and explains. The deterministic risk and
execution engine is the only authority allowed to move capital.

## Architectural Filter

Architecture exists to improve one or more of:

- research velocity;
- evidence quality;
- operational safety;
- maintainability.

If a proposed architecture change does not clearly improve at least one of
those outcomes, it should not be prioritized.

## Near-Term Build Direction

Implement the smallest useful event foundation before adding broader platform
complexity.

The first event foundation is an append-only journal for events that have a
real producer and a real consumer. Initial candidates are:

- `CampaignStarted`
- `CampaignEnded`
- `StrategySignalProduced`
- `RiskDecisionMade`
- `EvidenceArtifactGenerated`

The event list is intentionally demand-driven. Add a new event type only when
both sides exist: one concrete producer and one concrete consumer.

## Reproducibility Minimum

Every research or campaign event that can influence future decisions should
carry enough provenance to interpret it later:

- strategy id or strategy version;
- config hash or config artifact id;
- dataset or evidence artifact id;
- run timestamp;
- commit SHA.

This is not a model registry, feature store, or microservice mandate. It is the
minimum evidence needed to avoid losing the meaning of historical results.

## Explicit Non-Goals For Now

Do not prioritize these until implementation evidence creates a forcing
function:

- service mesh;
- broad microservice extraction;
- full CQRS rollout;
- exhaustive bounded-context documents;
- formal model registry;
- full feature store;
- broad stocks/options execution expansion;
- Telegram or voice control as execution authority.

These may become valid later, but they are not the next build direction.

## Stop Rule For Architecture Reviews

Do not commission another broad architecture review unless at least one trigger
is present:

- implementation exposes a concrete limitation;
- research results change system requirements;
- operational failures repeat;
- project scope materially changes.

Until then, architecture work should be converted into implementation and
measurement.

## Immediate Research Objective

The next platform work should help answer concrete strategy questions:

- why current Donchian evidence is weak or thin;
- why mean-reversion results are negative;
- which symbol, strategy, timeframe, and regime combinations produce credible
  post-cost evidence;
- whether failures come from strategy logic, market selection, execution
  assumptions, or data quality.

The event journal should be judged by whether it improves those answers, not by
whether it completes a theoretical architecture.

## Boundary With Existing Safety Model

This plan does not weaken existing paper/shadow/live gates.

Existing deterministic safety boundaries remain:

- LLM output is advisory only;
- risk checks remain final pre-capital authority;
- live execution remains gated;
- paper and shadow evidence remain separate from live capital deployment;
- promotion decisions require governed evidence and accepted operator review.

