# Versioned Article Extraction

## Scope

Deploy the independently accepted parser source to the existing local parser
only. Preserve its image for rollback, environment, bindings, network and other
services. Verify authenticated HTML parsing without submitting documents for
ingestion; normal research audit events may be emitted.

Build a separate diagnostic dataset from preserved raw news pages, not an
overwrite or a live index switch. Keep original timestamps, raw-object references,
original IDs as lineage, source/raw hashes and a complete original snapshot.
Unknown extraction layouts remain explicitly unverified. Only news-ingestion
lineage is supported; that caller supplies empty asset hints in the visible code.
Unsupported lineage or absent raw references are reported as exclusions.

## Verification Plan

The read-only builder uses PostgreSQL read-only mode and MinIO GET requests.
Each original content hash is checked. Fresh output files are exclusively created
in a new temporary directory and their hashes enter a manifest. Existing documents,
raw objects and trading/campaign data are not updated.

Five queries are compared against original and derived rows through the actual
full-text SQL, using a synthetic CTE that shadows documents rather than inserts.
This is a descriptive before/after check, not a blinded relevance benchmark.
No old timestamp becomes a new event or fresh holdout observation.

Output files are hashed and exclusively created, not protected by filesystem
immutability. Original confidence values are retained rather than recalibrated.
Comparisons may also reflect lineage exclusions; report those separately.
Stored-content integrity checks do not independently prove that each raw object
generated that stored content. This dataset remains diagnostic, not approved for
automatic replacement of live search records.

## Operator Artifacts

- `/private/tmp/cryptkeep_parser_deploy_20261011.py`
- `/private/tmp/cryptkeep_parser_Dockerfile_20261011`
- `/private/tmp/cryptkeep_build_article_archive_20261011.py`

These are bounded operator artifacts, not a general deployment framework.
Private rollback configuration includes credentials and must not be shared.
Outcome, dataset location, hashes and independent disposition are in the work log
and receipt. Full repository tests, sustained health, general publisher coverage
and live archive selection are outside this slice.
