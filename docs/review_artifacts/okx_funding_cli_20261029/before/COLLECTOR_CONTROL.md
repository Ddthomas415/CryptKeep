# Crypto Edge Collector Control

The dashboard allows OPERATOR users to start and stop the read-only crypto
structural-edge collector loop.

Current dashboard control path:
- `dashboard.services.operator.start_crypto_edge_collector_loop(...)`
- `dashboard.services.operator.stop_crypto_edge_collector_loop(...)`
- `python scripts/data/run_crypto_edge_collector_loop.py --status`
- `python scripts/data/run_crypto_edge_collector_loop.py --stop`

Runtime status is read through
`services.analytics.crypto_edge_collector_service.load_runtime_status()`.

This control surface does NOT replace existing paper evidence collectors or
reviewed systemd/timer deployment paths.
It is intended for:
- Local dev
- Debugging feed health
- Safe manual control

Hard boundary:
- this collector is read-only research infrastructure
- dashboard controls require OPERATOR role
- missing script paths must fail closed as `missing_script:<path>`
