# Collector Control (Phase 4)

The dashboard allows starting and stopping the market data collector.

Status is process-local and stored in:
- runtime/collector_state.txt

This phase does NOT replace existing production collectors.
It is intended for:
- Local dev
- Debugging feed health
- Safe manual control

Next phase:
- Gate Live Trading on collector + feed health
