# Engineering item 9: stuck-exit rule (fix 2) wired into the live path. Specification draft

Claude (Cowork), 2026-11-14 (owner: "begin working on all recommended supporting tasks", area A2). Self-checked; Codex
verifies the cited lines before building. No code changed. Live path only. Bot relation: BOT_RULES.

## 1. What the item is, and what already exists
- Owner decision 3 (2026-10-31): a protective or signal exit that is refused stays pending and is retried until it fills
  or is superseded; never converted, repriced, marked filled or dropped. Applied to the paper simulation as R12
  (`paper_simulation_spec_20261031/README.md` line 249). R12's paper implementation exists:
  `services/execution/paper_exit_retry.py` ("Paper-only pending-exit recovery; no exchange or live execution
  authority", line 1), serviced from the runner at `strategy_runner.py` line 1340; durable exit identity via
  `paper_exit_policy` / `paper_exit_id` in intent meta (runner 1966). Source accepted with risk 2026-11-03.
- Item 9 is the same rule for the live path. Findings it answers: CP-09 (`capital_protection_audit_20261031`, line 60:
  "exit orders are not exempt from entry limits ... a rejected intent is terminal (no retry) ... the loss limit blocks
  the exits it should protect"; SHOWN by probe P-2), BA-05 and BA-18 (refused or lost orders not re-sent).

## 2. Where the live path rejects exits today (SHOWN, HEAD 3b49ead3f)
`services/execution/live_intent_consumer.py` (601 lines), the live loop's consumer:
- market-quality guard: line 342 writes status `rejected` (terminal) for any side;
- venue clock guard: line 358, same;
- risk claim (`_risk_check_and_claim`, lines 98-116: trades per day, daily notional, minimum notional): line 373, same;
- router decision: line 424, same;
- intent TTL expiry: line 327 (sells expire like buys).
`services/execution/place_order.py` 598-680: kill switch, armed check, market-orders-disabled, per-order notional,
daily snapshot, trades per day, daily loss, daily notional, all raised as `CBP_ORDER_BLOCKED:*` with no side check.
`_executor_submit.py` (the other submit path) keeps blocked intents `pending` (lines 407, 414), so it already retries;
Codex confirms which path the live loop runs (live_trader_loop.py is 6 lines) before building.

## 3. Rule to implement (mirrors R12; Codex may object with evidence)
A sell that reduces or closes an existing position ("exit") is identified by the runner at emission (as the paper path
does: policy and identity in meta), and the live consumer treats it as follows:
1. Exempt from entry limits: trades per day, daily loss, daily notional, per-order notional, "market orders disabled",
   and the router's size-based refusals do not reject an exit. Still enforced for exits: the kill switch (owner's stop),
   arming, venue clock sanity, market-rules validity (precision/minimums), stale quotes (wait, not reject), and the
   reducing check: quantity at most the current holding minus pending sells, read before each send (R12 wording).
2. Refused or failed exits are not terminal: status returns to `pending` with the refusal reason and count; retried at
   the next consumer loop; alert once pending over 2 minutes (R3 condition "an exit is delayed over 2 minutes").
3. Supersession: before each send read the holding; if zero, close the pending exit as `superseded`, not sent.
4. Never fills twice: the exit's identity is the client order id; the dedupe store refuses a second submit for it
   (existing `OrderDedupeStore`); a `submit_unknown` is resolved by remote lookup before any retry (existing stale
   `submitting` recovery, lines 144-).
5. Configuration: default-off key `live_risk.exit_retry: live_exit_retry_v1`; absent = today's behaviour. No activation
   without the owner.

## 4. Tests (fail before, pass after; synthetic adapter, no exchange)
- Daily loss limit hit: a buy is rejected, an exit is submitted (CP-09 probe P-2 inverted).
- Trades-per-day used up: same.
- Exit refused once by the adapter: pending, retried next loop, filled; one fill; refusal count 1 recorded.
- Holding already zero when the retry comes: `superseded`, nothing sent.
- Stale quote: exit waits (pending) and submits when fresh; alert after 2 minutes pending (clock injected).
- Kill switch on: exit NOT sent (owner's stop wins), status pending with reason, alert.
- Configuration absent: existing live-consumer tests byte-identical (parity run).

## 5. Remains the owner's
Activating the key; whether the kill switch should also stop exits (this spec keeps the owner's stop absolute, as the
paper spec's R2 "one command stops all" implies; the alternative, "protective exits run through a kill switch", is a
separate owner decision); live trading itself.

## 6. Prior work cited (not rebuilt)
Owner decision 3; R12 and `paper_exit_retry.py`; CP-09, CP-10; BA-05, BA-18; `_executor_submit.py` pending-on-block
behaviour; cooldown patches 0001/0002 (protective exits during cooldown, R1).
