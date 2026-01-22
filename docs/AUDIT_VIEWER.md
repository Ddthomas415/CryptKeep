# Order Audit Viewer (Phase 210)

Audit DB:
- data/execution_audit.sqlite
- tables: orders, fills

UI:
- Dashboard -> Order Audit Viewer

CLI:
- Show statuses + db path:
  python scripts/audit_view.py

- Show recent orders:
  python scripts/audit_view.py --orders --limit 50 --venue binance --symbol BTC/USDT

- Show recent fills:
  python scripts/audit_view.py --fills --limit 100
