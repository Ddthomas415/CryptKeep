# Live Start Gate (UI) — Phase 5

UI blocks starting the LIVE bot unless:
- Collector is running (Market Data Collector panel)
- Feed Health has no BLOCK for configured symbols (from events.sqlite)
- WS gate is OK (if Phase 348 is present)

This is UI-only gating; the live runner should still enforce its own safety checks.
