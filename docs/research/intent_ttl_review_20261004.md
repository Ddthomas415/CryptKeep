# Intent TTL (live-money backlog item 18): independent review

2026-10-04. AUDITOR then ENGINEER (Claude). Reviewed on master 97c24c8e.
State: READY_FOR_INDEPENDENT_REVIEW. Nothing merged, pushed or deployed; no
config or account change. Patch 0039 (commit 5ebd5eb9, cloud clone only) is in
`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_review_bundle_2026-10-02_rev50.zip`,
folder 47. Zip SHA-256:
d56b4b6a571e049ac6630b6d37253c640f3d73b49e5c496f3af97c4fb7a4971e

## What holds

- `intent_ttl.check_intent_age` fails closed on missing, unparseable,
  non-finite, future-dated and aged timestamps.
- `live_intent_consumer` expires an aged intent before market-quality, risk,
  dedupe and router steps.
- The legacy `intent_consumer` has no runnable entry point.

## Finding (P1 for live, latent now)

The second live submit path, `live_executor.submit_pending_live` (used by
`live_event_executor`), had no intent age check. With a real execution store,
a pending intent created three days earlier was submitted to the (fake)
exchange client. The same path puts a blocked intent back to `pending` and
retries it every tick, so an old intent goes out when its block clears.
This checkout's effective config has all three live switches false.

## Correction in 0039

Each pending intent is checked with the same `check_intent_age` (same
`CBP_MAX_INTENT_AGE_SEC`, default 300 s) from its `ts_ms`. One that fails is
set to the existing terminal status `canceled` with the `intent_ttl:` reason,
counted in a new `expired` result field, and not submitted. An intent whose
reason already records a remote order id is left to the existing recovery step.

8 new cases with a real execution store, 7 fail on the previous code. Full
suite: 4495 passed, 33 skipped, 19 failed (the same 19 as master).

## Decisions for the operator

1. Status name: `canceled` + reason is used because the execution-store state
   machine is pinned by `tests/test_intent_state_machine_contract.py`. A
   distinct `expired` status means changing that contract.
2. Window: 300 s also applies to intents merely waiting on a block.
3. `CBP_MAX_INTENT_AGE_SEC` has no upper bound; a very large value disables
   the check on both live paths.

## Not changed

- The shadow recorder records a would-be fill for a pending intent of any age.
- `ExecutionStore.upsert_intent` rewrites `ts_ms` on conflict, so
  re-upserting an intent resets its age.

## Correction, same day (patch 0045)

Patch 0039 cancelled an aged pending intent unless its reason recorded a
remote order id. An intent whose submit outcome is `unknown` has no remote id,
so 0039 could cancel locally an intent whose order might be live at the venue.
Patch 0045 fixes this: the TTL does not cancel an intent whose dedupe row says
submitted, acknowledged or unknown, has a remote order id, or cannot be read.
Review 0039 and 0045 together. See
`live_submit_classification_review_20261004.md`.
