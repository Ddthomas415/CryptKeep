# coinbase_confirmation_usd_v1 warm-up pre-check (read-only), 2026-10-09 ~11:20 UTC

Claude (cloud session). Archive opened read-only (sqlite mode=ro); nothing written to the archive, plan or
registration. Public Coinbase /candles fetched for comparison only and not stored.

| Product | Archive bars in window | Missing from archive (completed hours) | Public API has them | Gaps now |
|---|---|---|---|---|
| BTC-USD | 276 | 11 | 11 | none |
| ETH-USD | 276 | 11 | 11 | none |
| SOL-USD | 276 | 11 | 11 | none |
| ADA-USD | 276 | 11 | 11 | none |
| XRP-USD | 276 | 11 | 11 | none |

Window: 2026-09-27 12:00 UTC + 300 hourly bars (last bar opens 2026-10-09 23:00, closes 2026-10-10 00:00).
287 of 300 bars were complete at check time; 13 remain. No product has a gap so far.
Still required at 00:15 UTC Oct 10 (scheduled check-in): backfill the remaining bars into the archive with the
existing ingestion path, verify all 300 per product, hash and freeze the prefix, write the readiness record.
Activation stays separate and is not authorized by this check.
