# Paper Trading Honesty

Paper trading is a simulation aid. It is not live-equivalent execution.

`services/execution/paper_engine.py:PaperEngine.submit_order()` inserts a paper order and then calls `evaluate_open_orders()` inside the same `submit_order` call. If the order is marketable, `evaluate_open_orders()` may call `_apply_fill(...)` immediately.

This means paper trading can fill in the same submit_order call. Live trading uses separate submit, exchange acknowledgement, reconciliation, trade attribution, and fill-ingestion paths.

Do not use paper fills as proof of live execution realism. Paper results may omit exchange latency, submit_unknown handling, partial-fill uncertainty, stale-order reconciliation, trade cursor behavior, and exchange lookup failures.
