# Additive Keyword Retrieval

## Scope

The local companion source now supports question-specific English full-text
retrieval alongside its existing temporal buckets and hash-vector diagnostics.
The original question reaches the memory service through both orchestrator paths.
Keyword citations preserve document identifiers and explicitly mark semantic
relevance as unverified. No paid model, migration, index replacement, trading
change, or deployment is included.

## Evidence

- SHOWN: Parameterized query filters by asset, excludes future receipt and
  publication times, bounds the question to 2,000 characters and results to 20.
- SHOWN: Targeted restored-route, orchestrator and tools tests: 31 passed, with
  90 existing framework deprecation warnings.
- SHOWN: The exact SQL extracted from source ran against PostgreSQL using a
  read-only connection and a synthetic CTE rather than persistent inserts.
  Six fixtures returned only matching IDs 1 and 6; foreign-asset, unrelated,
  future-receipt and future-publication rows were excluded. An unmatched term
  returned no rows. The initial fixture needed an explicit text-array cast;
  only that test fixture changed.
- UNVERIFIED: Deployment and live endpoint integration of this change.

## Limits

Keyword rank is not semantic understanding, calibrated confidence, or evidence
of a market edge. The existing Qdrant request still precedes lexical retrieval,
so its availability remains a dependency. The result cap does not bound scan
cost; no full-text index or performance claim is introduced. Existing archive
and vector data were not rewritten. The full repository suite was not run.

Implementation proof is complete. Independent source review disposition is
recorded in the work log; deployment remains separate.
