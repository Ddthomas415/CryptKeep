# Paper Trading Honesty

Paper trading is a simulation aid. It is not live-equivalent execution.

`services/execution/paper_engine.py:PaperEngine.submit_order()` first applies local pre-submit gates for snapshot freshness, master read-only mode, market-quality health, deterministic safety checks, and local paper cash/position adequacy. If those gates pass, it inserts a paper order but does not fill it in the same call. Fill simulation happens only in a later, explicit `evaluate_open_orders()` pass or through the paper runner loop that calls it.

This is still not live-equivalent. `evaluate_open_orders()` is a local synchronous fill simulation, and the paper submit gates only mirror a deterministic subset of the local live blocking model. They do not mirror exchange ownership, remote dedupe, exchange acknowledgement, or exchange-side recovery behavior. Live trading still uses separate submit, exchange acknowledgement, reconciliation, trade attribution, fill-ingestion, and exchange-side recovery paths.

Do not use paper fills as proof of live execution realism. Paper results may omit exchange latency, submit_unknown handling, partial-fill uncertainty, stale-order reconciliation, trade cursor behavior, and exchange lookup failures.
