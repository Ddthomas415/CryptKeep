# Coinbase USD preregistration checkpoint

The reviewed separate USD plan was preregistered before its October 10 00:00
UTC evaluation boundary. The receipt binds the plan, strategy snapshot, fee
receipt and runner hashes. It is explicitly preregistration, not activation.

Receipt: `research/coinbase_confirmation_usd_v1/registration_20261009.json`.
Coverage: `research/coinbase_confirmation_usd_v1/warmup_preflight_20261009.json`.

Bounded public ingestion appended only the newly completed October 8 23:00
hour for each of the five USD markets. Strict replay verifies 276 contiguous
valid bars per market through October 9 00:00 UTC exclusive. Full warmup remains
incomplete: 24 hours remain before the final candle closes at October 10 00:00.
No simulated outcomes, orders, activation or new background job were produced.

Next scoped action: collect remaining completed warmup candles after the
boundary, verify all 300 bars and freeze with the registered identity before
any evaluation scoring. Do not change the registered contract silently.
