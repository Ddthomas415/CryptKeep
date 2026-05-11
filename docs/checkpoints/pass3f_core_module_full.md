# Pass 3F — core/ Module Full Read

**Pass:** 3F | **Status:** COMPLETE — core/ fully covered (12 of 12)

## Findings

**Strength:** core/models.py — Side, OrderType, TimeInForce, OrderStatus enums.
Order, Fill, OrderAck, PortfolioState as frozen dataclasses.
Frozen = immutable after creation. Correct for domain objects.

**Strength:** core/event_factory.event_from_dict — fail-fast on unknown
event_type (raises ValueError). Pydantic v2 model_validate at construction.
No silent pass-through.

**Strength:** core/price_aggregator — median mode for multi-venue price
aggregation (outlier-resistant). 10s staleness default consistent with
~1500ms WS freshness gate at appropriate granularity.

**Strength:** core/symbol_parse.split_symbol — handles /, -, _ separators.
Falls back to _KNOWN_QUOTES suffix matching. Clean defensive parsing.

**Noted:** core/ uses Pydantic v2 (model_validate). If any consumer
uses v1 syntax (parse_obj) there would be runtime errors.
Not confirmed whether any consumers mix v1/v2.

## core/ coverage: 12 of 12 COMPLETE

All 12 files reviewed or sampled.

## Directories at 100% coverage

services/risk, services/signals, services/analytics,
services/security, services/ai_copilot, core/

## Handoff

**Active role:** AUDITOR
**Next:** Full findings compilation or remaining ~110 files across 30 dirs
