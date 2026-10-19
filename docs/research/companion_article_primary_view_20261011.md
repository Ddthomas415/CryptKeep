# Article Primary View

## Decision and Boundaries

Use the reviewed versioned extraction as a read-only primary search projection.
Retain original database records, raw objects and vector index. Unknown article
boundaries remain diagnostic rather than primary news evidence. Non-news archive
and manual sources remain supported. No database migration or row rewrite.

The deployed image bundles the selected archive and a required-policy marker.
Missing required data, hash mismatch, changed source lineage or altered original
timestamps produces a 503 rather than silently using the noisy original records.
Each request checks the frozen source IDs against live records. Derived files
remain versioned; their original diagnostic-only manifest records preparation
history rather than independently authorizing live use.

The reviewed manifest digest is pinned in source outside the bundle. Each
document retrieval statement checks full source lineage and retrieves from the
same PostgreSQL snapshot, failing integrity even when its query matches nothing.
Snapshot consistency is per statement, not across the entire request.

Temporal, keyword and vector-result document lookups use the same projection.
New news records require parser boundary metadata for primary inclusion; unknown
ones are retained in diagnostics, with newer diagnostics capped at 100 and an
explicit completeness flag. Non-semantic vector diagnostics remain unchanged.
Responses expose the active archive hash/status and explain the distinction.
This downgrade applies only to news-ingestion lineage, not manually supplied news.

## Proof

Targeted source tests: 48 passed, 90 existing framework deprecation warnings.
Final corrected source: 51 passed, independently reproduced. Read-only PostgreSQL
fixtures confirmed manual news inclusion, timestamp-drift invalidation and the
external manifest pin. Initial review found these three gaps before deployment;
all were corrected without changing original data.
Read-only actual PostgreSQL proof verified all 55 source records and original
timestamps. Primary keyword results:

- Bitcoin liquidations: IDs 5, 47, 18, 7, 8.
- Regulation: IDs 20, 51, 33, 27.
- Full liquidation question and an unmatched term: no matches.
- Unverified document 25 stays diagnostic; false Bitcoin-tagged Visa document 11
  is absent from these primary matches.

This is structural correctness, not semantic understanding or a relevance
benchmark. Strict keyword conjunction can miss relevant ordinary-language
questions. Confidence remains uncalibrated, and no trading decision is authorized.

## Deployment

Only memory/orchestrator images require updating; existing settings and storage
are preserved. Old images/configuration are retained for rollback. Source and
operator changes require separate review before launch. Final disposition and
actual endpoint proof are recorded in the work log.
