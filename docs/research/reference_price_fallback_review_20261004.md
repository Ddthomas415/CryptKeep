# Hardcoded reference-price fallbacks: independent review

2026-10-04. AUDITOR then ENGINEER (Claude). Reviewed on master 97c24c8e.
State: READY_FOR_INDEPENDENT_REVIEW. Nothing merged, pushed or deployed; no
config or account change. Patch 0037 (commit fccd63aa, cloud clone only) is in
`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_review_bundle_2026-10-02_rev48.zip`,
folder 45. Zip SHA-256:
9d3fa5cd61ebdd9d7648ec57de4bf4fea4d27e184223786b475f05a2d194718d

Backlog reference: REMAINING_TASKS.md, live-money section item 19.

## What holds

- Paper engine refuses `market_quality:no_reference_price` when no finite
  positive price is available (probed with the real engine).
- `live_router.decide_order` refuses `no_reference_price`.
- The only BTC-shaped price literals left in production code are the two
  documented legacy stubs (`live_trader_multi`, `live_trader_fleet`).

## Findings

1. P1 for live, latent now. Both live queue consumers estimated notional as
   `limit_price or (last or 0.0)`. A market intent with no `last` (a tick with
   bid/ask only, or no quote data while `block_when_unknown` is off, the
   default) claimed 0.00 against `max_daily_notional_quote`.
   - `intent_consumer.py`: the next step is `LiveExchangeAdapter.submit_order`
     with no router check, so the order goes out uncounted.
   - `live_intent_consumer.py`: the router then refuses the 0.0 reference;
     fails closed after consuming a trade count.
2. P2. A market order carrying a `limit_price` is safety-checked at that price.
   Paper engine: a 0.1 BTC market buy with limit_price 0.01 reached the safety
   check as notional 0.001 instead of 6000; the fill-time cash check rejected
   it. The runner always queues `limit_price: None`.

## Current state of this checkout (read-only)

`live.enabled`, `live_trading.enabled`, `execution.live_enabled` are false.
Both consumers' last status is `blocked / live_disabled` (May 2026). The
effective config has no `market_quality_guard` block, so the fail-open
defaults apply (backlog item 29, operator decision).

## Correction in 0037

Both consumers: the estimate uses the first positive finite price of limit
price (not for market intents), the mid the market-quality check used, then
last. With none, the intent is refused `risk:no_reference_price` before any
claim. 32 new cases, 28 fail on the previous code. Full suite: 4480 passed, 33
skipped, 19 failed (the same 19 as master).

## Not changed

- The paper engine still uses a market order's `limit_price` as its safety
  reference (finding 2).
- `live_intent_consumer.py` still passes `last`, not the mid, to the router.
- A sell limit far below the market is claimed at its limit price.

## Addendum, same day: finding 2 closed in patch 0038

Commit 9564bee0 (cloud clone only), bundle rev49, folder 46. Zip SHA-256:
54a75d208ea59de90c64270386dc3fa147413eb595f378cc2d3d52b0e32c3e74

- `PaperEngine._pre_submit_gate`: only a limit order uses its limit price as
  the reference. A market order uses the market-quality mid, then last, and is
  refused `market_quality:no_reference_price` when neither is usable, even if
  it carries a limit price.
- No effect expected on the running campaign: the runner queues every intent
  with `limit_price: None`.
- 7 new cases, 5 fail on the previous code. Full suite: 4487 passed, 33
  skipped, 19 failed (the same 19 as master).

Still open: `live_intent_consumer.py` passes `last`, not the mid, to the
router; a sell limit far below the market is claimed at its limit price.

## Correction, same day

Finding 1 called the `intent_consumer.py` path "P1 for live" because its next
step is a direct exchange submit. That file is the retired legacy consumer: no
script imports its run loop and `scripts/compat/run_intent_consumer.py`
refuses to run. The canonical `live_intent_consumer.py` fails closed in that
case. The code finding stands; its severity was overstated. Patch 0037 is
unaffected.
