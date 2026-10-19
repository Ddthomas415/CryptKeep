# First evaluation collection checkpoint

Role: AUDITOR. Environment: VERIFIED_ENV for local contract and command interface.

At 00:49 UTC October 10 (8:49 p.m. New York October 9), zero evaluation hourly bars are complete. The first bar opens at 00:00 UTC and closes at 01:00 UTC (9 p.m. New York). Do not ingest it as completed before that boundary.

The existing bounded public backfill supports explicit Coinbase venue, exact USD symbol, hourly timeframe, start/end boundaries, page/bar limits, isolated study archive and separate receipt. Collection must stop at the last completed hourly boundary and preserve the warm-up prefix. All five registered products must be checked for continuous coverage after ingestion; a public response or successful command alone is not coverage proof.

No public request, scoring, background collector, campaign or scheduler change occurred at this checkpoint. Separate GATE reviewer Hooke accepted the activation record WITH RISK, with no blocking findings: hashes, registration timing and research-only scope match. Absence of earlier scoring cannot be independently proven from these artifacts; activation is not runner-enforced. This document does not schedule a future run or assert that collection has started.
