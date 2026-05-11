# Pass 3I — Remaining Service Directories

**Pass:** 3I | **Status:** COMPLETE for these directories

## Findings

**Strength:** services/strategy/ — ALL files deprecated with DeprecationWarning,
removal date 2026-07-01, canonical replacements documented.

**Medium:** learning/guardrails.py — 8th threshold set:
min_metric=0.52, max_drawdown_pct=0.25.
learning/runtime_policy.py — 9th threshold set:
rollback_max_metric_drop=0.03, fail_open=False (correct).

**Shown:** services/evidence/webhook_server.py — SECOND evidence webhook.
Supervisor DOES manage 'evidence_webhook'. Signals webhook NOT managed.
Two webhooks with different oversight levels.

**Noted:** services/marketdata/ (6 files) vs services/market_data/ (29 files).
Two directories with similar names and overlapping functionality.
marketdata/ not labeled as deprecated.

**Strength:** journal/fill_sink.py — canonical fill accounting pipeline.
Chains CanonicalJournal -> RiskDailyDB -> LivePositionStore.
Atomic health marker on accounting failure.

**Strength:** meta/ disabled by default (enabled=False). Opt-in feature.

**Strength:** markets/rules.py 6h TTL cache for exchange market rules.
Lot size, min notional, tick size validation before order submission.

## Fragmentation tally

| Pattern | Count |
|---|---|
| Risk/acceptance threshold sets | **9** |
| Strategy name normalizations | 4 |
| Intent tracking stores | 3 |
| Webhook servers | **2** |
| Market data modules | **2** |

## Remaining dirs with 0 coverage

diagnostics/, desktop/, paper_trader/, paper/, portfolio/,
trading_runner/, trader_signals/, imitation/, update/, profiles/,
logging/, data_collector/, data/, ws/, runtime/, os/
