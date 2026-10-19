# News Collection And Source Readback

## SHOWN

Read-only checks on October11 confirmed the running news service reported54polls,55ingested articles,2915duplicate skips and0errors. Last completed poll:2026-10-11T21:26:02Z. Configured feeds: CoinDesk RSS and Cointelegraph RSS. Archive service health returned200, but archive lookup behavior was not exercised.

Database source aggregation found55news documents, all with non-null published_at. Stored publication range:2026-10-08T19:17:18Z through2026-10-11T18:30:00Z. These dates are supplied by ingestion, not independently verified publisher facts. Latest fetched_at:2026-10-11T18:46:44Z. Poll recency is not article recency.

Read back all55raw object keys from the actual local MinIO store, with a2MBper-object cap. Parsed each archived HTML object using the restored parser's actual extraction function. All55reproduced their stored title, text and URL/title/text content hash. Total bytes read:49,033,820; failures:0. PostgreSQL query used default_transaction_read_only; object-store calls were get_object only. No documents, credentials, services or settings changed.

## Interpretation

The restored system has actual RSS news and reproducible raw-source evidence; it is not solely the Bitcoin FAQ disposable test. This verifies stored provenance consistency, not factual truth, completeness, asset attribution, semantic retrieval relevance, causal market impact or tradable edge. Current vector embeddings remain a deterministic lightweight hash stub, so do not claim semantic search quality from successful retrieval.

No collector or campaign restart, live trading, account mutation, scoring or profitability claim. No tests run: this was runtime readback/audit, with no source-code change. Audit facts SHOWN by main-agent commands; no independent acceptance of wider intelligence quality inferred.
