# Pass 3J — Final Remaining Service Directories

**Pass:** 3J | **Status:** COMPLETE — all safety-critical dirs now sampled

## Findings

**Medium:** Three separate paper trading implementations:
- services/execution/paper_engine.py (REVIEWED)
- services/paper_trader/ (main.py, paper_execution_venue.py, paper_state.py)
- services/paper/ (main.py, paper_broker.py, paper_state.py)

**Strength:** diagnostics/live_start_gate.py WS thresholds match ops/risk_gate_engine:
warn_ms=1200, block_ms=2500. Only pair among 9 threshold sets that are consistent.
Configurable via CBP_WS_WARN_MS and CBP_WS_BLOCK_MS.

**Strength:** services/os/file_utils.py confirmed as canonical atomic_write source.
All atomic_write calls across codebase resolve to this implementation.

**Noted:** app_paths.py supports PyInstaller frozen deployment (sys._MEIPASS).
APP_NAME='CryptoBotPro'. PyInstaller-aware path resolution.

**Strength:** diagnostics/preflight.py validates port availability (can_bind)
and config availability before startup.

## Updated fragmentation tally

| Pattern | Count |
|---|---|
| Risk/acceptance threshold sets | 9 |
| Paper trading implementations | **3** |
| Strategy name normalizations | 4 |
| Intent tracking stores | 3 |
| Webhook servers | 2 |
| Market data modules | 2 |

## True remaining NOT_AUDITED (lower-risk)

services/imitation/, services/update/, services/profiles/,
services/logging/, services/data_collector/, services/data/,
services/ws/, services/desktop/, services/ai_engine/,
services/marketdata/, storage/ remaining ~16 files

## Handoff

**All safety-critical service directories now at least SAMPLED.**
**Next:** Compile complete findings and remediation plan
