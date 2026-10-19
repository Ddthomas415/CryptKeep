# Article Boundary Correction

## Confirmed Problem

Authenticated local retrieval of `What news explains Bitcoin liquidations?`
returned a Visa APAC stablecoin article (document 11). The old parser extracts
the entire page, so navigation, recommendations and disclosure text affect both
full-text retrieval and inferred asset tags. This is a data-quality failure, not
evidence of a useful market relationship.

## Source Correction

The parser now uses the observed `post__body` container or an explicit article
boundary inside main containing document-body sections. It excludes known site
chrome within those regions. Ambiguous, missing or empty boundaries retain the
compatible whole-page fallback but explicitly mark it unverified. Metadata
records extraction_version, extraction_method and article_body_boundary_verified.
This last flag means an observed structural boundary, not factual verification.

Raw HTML remains intact; original database records and object-store content were
not changed. Asset hints/title inference remain supported. A first selector draft
could not handle the Visa page's split sections and same-class disclosure; the
actual archive probe exposed this before acceptance and the draft was corrected.

## Proof

Separate GATE: ACCEPTED_WITH_RISK for source. Independent targeted tests:
40 passed, 90 existing deprecation warnings. Six new cases cover excluded chrome,
retained Bitcoin content, unknown/ambiguous layouts, compatibility, split sections
and empty bodies.

Actual read-only PostgreSQL/MinIO proof, using three preserved pages:

| Document | Old Characters | Derived Characters | Old Assets | Derived Assets |
| --- | ---: | ---: | --- | --- |
| 11, Visa survey | 10030 | 1569 | BTC ETH SOL XRP | none |
| 39, Blockchain.com CFTC licenses | 5723 | 2671 | BNB BTC ETH SOL XRP | none |
| 47, Bitcoin liquidations | 6223 | 3234 | BNB BTC ETH SOL XRP | BTC |

Source raw SHA256 hashes:

- 11: 3772b714f76b17f5436ce976d7e110e0822f1d8f3dff4d73d0cf915c89c7fa11
- 39: 264982800fff6430f1a9c6c3cdb98cb853fd7adccbf70a6a359e942c9f762568
- 47: f4c03384fb880c8dbf9adfad06edb097544c1ee0a6b23615b907609f08ebd122

These runtime probes are parent-thread SHOWN, reviewer CLAIMED; the reviewer did
not independently replay the three objects. They establish these boundaries, not
general semantic correctness across all publishers.

## Remaining Work

This source correction is not deployed. Existing retrieval still uses original
whole-page records. Next: scoped parser deployment, then a separately versioned
derived archive and relevance recheck, preserving original IDs, hashes and raw
objects. Do not silently overwrite the old archive or claim current search is
already repaired. Unknown layouts remain potentially contaminated and unverified.
