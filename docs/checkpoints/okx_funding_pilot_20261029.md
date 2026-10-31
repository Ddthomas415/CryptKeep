# Isolated Live Funding Service Test

2026-10-29 America/New_York. AUDITOR. Evidence READY_FOR_INDEPENDENT_REVIEW.
Original Fix3 and recurring collector rollout remain INCOMPLETE.

Operator continued after the explicit proposal for one foreground funding-only
service test, two public requests and a new isolated database. Called the
reviewed collect_once API exactly once, not run_forever. No background loop,
global PID/status/stop-file control or active configuration was invoked.

SHOWN tool result: at14:20:56EDT/18:20:56UTC the service captured one pair via
two public BTC-USDT-SWAP requests. Funding capture0.504477458s, no failed pairs.
Raw writer stored one row in the new isolated DB; reopening/readback returned
one forecast comparison, labelled forecast_not_settled. Strategy/execution
authorityFalse, historic settled normalizationNone, legacy funding row count0
in this NEW database. None of these are trader returns or observed payments.

Original bodies/receipts, source/config/result hashes, transport stdout and DB:

docs/review_artifacts/okx_funding_pilot_20261029/20261029T182056Z_5544cd086ad64e1f8787f2e44546edc3/

Both decoded body hashes/lengths match stored receipts. Source58accepted
bindings unchanged before/after. New DB reopened through actual application
interfaces, not just a test double. Python SQLite audit hook allowed only the
exact pilot path;18connections recorded, all to that target. New connections
include existing constructor/report/readback behavior, not18network requests.
Child dispatch wrapper fixed expected recipients/count<=2/timeouts<=10s.
No retry occurred; one authorized service invocation/twoGETs now consumed.

Protected original SQLite/WAL/SHM file metadata matched before/after, as did
existing collector health/PID/stop state and active plan metadata/hashes where
read. Existing DB contents were not opened or hashed. This is scoped metadata
evidence and capture attestation, not global byte-level or host-wide proof.

All local writes were new diagnostic plan/options/SQLite/evidence files under
the unique artifact directory. Fresh DB initialized its schema; the original
archive did not. No existing data cleanup/checkpoint/backup/migration, service,
job, server, Docker, private account/credential, capital/risk or trading change.

Binary signature trust remains UNVERIFIED, as disclosed before approval. The
30s funding budget does not bound every local/SQLite/OS operation. Saved clocks
and public payloads do not independently authenticate venue payments or current
freshness. GC closed local resources; only pilot.sqlite remains, no pilot WAL.

Freeze evidence for one independent offline review. Reviewer may inspect ONLY
the new pilot via mode=ro/immutable=1 after confirming no WAL, with no store
constructor or DDL; verify row/receipt hashes and authority fields. No new
network request or collector invocation is part of that review. Historical304
source tests were not rerun or presented as this operation's proof.

Next operational boundary is restoration of the existing full-family collector,
not another prototype. This isolated test has not restored that collector or
authorized recurring capture or writes to the original archive.
