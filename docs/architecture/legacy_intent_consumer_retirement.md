# Legacy Intent Consumer Retirement

The canonical managed intent-consumer entrypoint is
`scripts/run_intent_consumer_safe.py`, which delegates to
`scripts.live.run_live_intent_consumer` after startup guards.

`scripts/compat/run_intent_consumer.py` is a retired compatibility entrypoint.
Its `run` mode fails closed with `legacy_intent_consumer_retired` and points
operators to the canonical safe wrapper. Its `stop` command remains available
so old operator stop commands can still create the legacy stop marker without
starting the retired consumer.

Reason: the legacy consumer path is live-execution-adjacent and does not carry
the canonical claim-boundary TTL, state-authority, and wrapper hardening. It
must not be used for unattended live or shadow operation.

Future revival requires a separate high-risk review. At minimum, revival must
prove parity with the canonical live consumer for intent TTL, dedupe, risk
claiming, state-authority writes, heartbeat behavior, and operator-visible
status.
