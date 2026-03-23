# Post-Phase-1 remaining cleanup

## Completed
- Gateway → orchestrator service auth forwarding is committed.
- Phase 1 service-token auth wiring is present across reviewed services.
- Read-side crypto-edge `store_path` redaction is present in:
  - `storage/crypto_edge_store_sqlite.py`
  - `services/analytics/crypto_edge_collector_service.py`

## Remaining non-OpenAI cleanup
1. Raw exception text still exists outside Phase 1:
   - `services/execution/place_order.py`
   - `services/ops/risk_gate_service.py`
   - `services/ops/signal_adapter_service.py`
   - `services/analytics/paper_strategy_evidence_service.py`

2. Remaining raw `store_path` exposure outside the redacted read path:
   - `services/ops/risk_gate_service.py`
   - `dashboard/pages/60_Operations.py`
   - `scripts/record_crypto_edge_snapshot.py`
   - `scripts/collect_live_crypto_edge_snapshot.py`
   - `scripts/load_sample_crypto_edge_data.py`

3. Repo hygiene noise:
   - `__pycache__/*.pyc` still appears in grep sweeps

## Immediate safety action
- Rotate `SERVICE_TOKEN` in `phase1_research_copilot/.env`
- Rebuild Phase 1 services after rotation

## Next highest-value task
- Patch raw exception-text logging in:
  - `services/ops/risk_gate_service.py`
  - `services/ops/signal_adapter_service.py`
  - `services/analytics/paper_strategy_evidence_service.py`

## On hold
- Any task requiring a real `OPENAI_API_KEY`
