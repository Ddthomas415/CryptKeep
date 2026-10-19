# High-risk backlog lane: what the code actually shows today (2026-10-09)

Claude (cloud session), read-only check of the working tree (branch codex/research-bundle-proof @ 620bc8dbe + local
changes). The lane map (docs/BACKLOG_EXECUTION_LANES.md, dated 2026-07-21) still lists these as open; several are
already implemented. Do not rebuild them.

| Lane item | Code evidence now | Real remaining gap |
|---|---|---|
| Daily-loss gross vs net | services/risk/risk_daily.py realized_today_usd() returns snapshot "pnl" (fee-inclusive net) and raises on corrupt rows | Review acceptance only (07-13 slice "proof-ready") |
| Config authority / corrupt-config fail-closed | strict=True loads in _executor_submit.py:319, live_reconciler.py:101, live_intent_consumer.py:100/120, intent_consumer.py:100/120, safety.py:21, master_read_only.py:10, live_enable.py:31 | Startup-from-documented-bundle proof + accepted rationale for remaining compatibility shims (operator/host evidence) |
| Decimal / quantization | Decimal at order boundary, market rules, notional, live risk gates, risk_daily writes (07-13/14 slices) | Fee/PnL/storage paths still float: storage/paper_trading_sqlite.py (29 float() calls), storage/execution_store_sqlite.py (11), risk_daily.py (6). Large multi-slice migration; paper changes would alter accounting of the running ES campaign. |
| Position-truth reconciliation authority | services/reconciliation/exchange_reconciler.py (243 lines) still has ZERO production importers; severity is magnitude-only; CRITICAL reaches no control | Needs operator decisions first (docs/decisions/position_truth_resolution_authority.md section 5: who wins, trust/hysteresis policy, named halt authority), then a scheduled loop. Live lane is off, so no drift can exist yet. |
| Promotion-gate / sweep-influence / live-shadow changes | Standing rules, not discrete tasks | n/a |
