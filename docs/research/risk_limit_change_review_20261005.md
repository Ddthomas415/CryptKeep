# Risk-limit change review (deferred live-money item 14) - 2026-10-05

Reviewer: Claude. Scope: dashboard Settings save, `risk_limit_change` event,
`save_user_yaml`, first-run risk presets. Result: patch 0064
(`520f1153`), bundle rev75 folder 72. READY_FOR_INDEPENDENT_REVIEW. Not pushed.

## Finding (P2)

The values these audited paths record are read by no order path.

| Written by | Keys | Production readers |
|---|---|---|
| First-run presets (`safe_paper`, `paper_relaxed`, `live_locked`) | 12 top-level `risk.*` keys: allow-lists, min/max qty and notional, intents per day, `max_daily_loss_quote`, `max_position_notional_per_symbol`, `max_total_notional` | writer, display, preflight `>= 0` check |
| Dashboard Settings page | `risk.max_position_notional_per_symbol`, dashboard `max_daily_loss_pct` | writer, display |

The Settings page said the values "shape scout thresholds, paper fills, and
approval expectations". The audit event is named `risk_limit_change`.

## What binds orders (unchanged)

- Live: `risk.live.*` in the trading config, and `CBP_MAX_*` in `.env`.
- Paper: strategy runner exposure limits (`build_risk_limits`).

On this laptop (read-only check, checkout `620bc8dbe`):

- `config/trading.yaml` `risk.live`: daily loss 25, per trade 25, trades per day 5, position 50.
- `.env`: order 25, daily notional 50, daily loss 15, trades per day 10, symbol loss limit 3.
- `.cbp_state/runtime/config/user.yaml` `risk`: every stored-only key is 0 or empty, so no preset is in effect here; `max_concurrent_positions: 10` (this one is read by the strategy runner). `execution.live_enabled: false`.

## Patch 0064 (labelling only)

- Setup summary carries `enforced: False` and a note naming the binding limits.
- Preflight adds a WARN row when any stored-only key is set; verdict unchanged.
- `risk_limit_change` event carries `extra.enforced_by_order_path: false`.
- Settings page text corrected.
- A test scans production source and fails if a reader for a stored-only key appears.

Full suite: 4813 passed, 33 skipped, 0 failed.

## Not fixed

- No key is wired into enforcement. Which limits should bind, and where, is an operator decision.
- Changes to the limits that do bind (trading config, `.env`) write no operator event.
- Settings-save rollback needs a working journal; the reason says `rolled_back` whether or not the rollback write succeeded.
