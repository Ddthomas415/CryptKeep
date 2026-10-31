# OKX funding pairs in the existing raw journal

2026-10-29 America/New_York. ENGINEER. HIGH-risk financial/persistence logic.
Implementation proof: READY_FOR_INDEPENDENT_REVIEW. Whole Fix3: INCOMPLETE.

## Chosen path and outcome

Use the existing raw_funding_observations journal and standard schema1
observation wrapper. No new SQL table, migration or schema version is needed.
No existing collector, decoder, store, context, model, CLI or configuration
changes. Explicitly supplied public endpoint pairs can now round-trip and
produce the separately reviewed, correctly labelled forecast comparison.

Added services/analytics/okx_funding_contract.py, okx_funding_cash_cost.py and
okx_funding_journal.py, plus tests/test_okx_funding_journal.py. The first two are
promotions of accepted prototypes: classifier byte-identical; cash policy
identical except its internal import points to the promoted classifier. Frozen
prototypes remain unchanged. Production modules do not import research scripts.

## Explicit interfaces

pair_journal_inputs validates both raw byte bodies and receipts through the
reviewed cash-cost policy. It retains original response bytes losslessly as
base64 plus isolated receipts, native requested identity and API-document pin.
The captured_at index is the later endpoint receipt, compared as aware times;
both original receipt strings stay available. The raw schema1 numeric rate and
interval remain unknown. No derived quote, eligibility or payment is persisted.

append_okx_funding_pairs requires an existing caller-owned store, explicit
source and positive row/byte budgets. It streams prepared observations through
the existing writer's whole-batch prevalidation and owned atomic transaction.
The writer's byte budget includes encoded base64/metadata and duplicates. No
store constructor, path selection, SDK, fetch or initialization occurs here.
An invalid later pair is refused before a connection/write by the real writer.
Invalid originals remain caller-owned; this adapter does not destroy or repair
them or manufacture a valid fallback.

recent_okx_funding_quotes calls the existing validating raw reader with explicit
source/limit, verifies the wrapper/content key and recomputes the cash policy
from retained bytes. It does not trust cached derived values or caller flags.
Recognized but unusable pairs produce type-only diagnostics and no quote; raw
evidence is preserved. Unrelated raw observations are counted, not upgraded.
Limits are explicit and scan_exhaustive=False: absence from a limited mixed
scan is not a claim that no older pair exists.

Available cash comparisons remain forecast_not_settled and as_of_receipt;
unknown forecasts remainNone with reasons. Historical settled rates remain
unscaled without interval evidence. Root and policy strategy/execution
authority remainFalse; no crowding eligibility or annualization is introduced.
Native identity in the pair wrapper is not a new unified-symbol mapping.

## Verification

VERIFIED_ENV isolated command, plugin/conftest/cache disabled:

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_okx_funding_journal.py tests/test_okx_cash_cost.py tests/test_okx_funding_contract.py tests/test_synthetic_funding_observations.py tests/test_funding_receipts.py tests/test_funding_store_bridge.py

Initial author206passed1.37s,exit0; earlier203passed1.40s before three extra
unknown/encoding/ownership cases. Independent first review206passed1.30s but
REJECTED v1 for OKX-JOURNAL-01, a malformed-body isolation gap. Corrected
author result207passed1.45s,exit0. Not full suite or production proof.

Actual disposable SQLite close/reopen, source isolation, changed evidence,
duplicate row/byte budgets, invalid later row, injected SQL rollback,
two-thread one-insert race, rehashed invalid body/receipt/policy/derived data,
base64 failure, forged normalization, limited-scan honesty and quote mutation
are covered. New cases refuse external sockets, default directory initialization
and all non-temporary SQLite connections. Race test is not crash-durability or
arbitrary concurrency certification.

First review identified statically that deeply nested JSON retained inside a
shallow base64 wrapper could raise RecursionError and abort the quote scan.
Preserved v1 source/tests/checkpoint/bindings/diff and REVIEW_ATTEMPT_1.json.
Correction adds only RecursionError to the per-pair diagnostic boundary. New
regression reproduces the archived v1 failure, then verifies a newer malformed
pair yields a type-only diagnostic while the older valid pair remains readable
and both raw records remain present. Systemic MemoryError/cancellation are not
silently suppressed. No financial eligibility bypass was claimed or introduced.

The existing reviewed public sample is a parsing/storage fixture; modified
receipts/bytes are deliberate fault-injection fixtures, not new market
observations. No capture, backtest, signal, trader payment or profit computed.
Four existing store/decoder/collector/context source hashes were checked
against the prior accepted v2 bindings and remain unchanged.

## Assumptions and operational boundary

1. The supplied store is caller-owned. Passing a real store would write to that
   store; the adapter is not a sandbox or global authorization gate. All writes
   in this verification were disposable. No real database was opened.
2. Hash-bound public bytes/receipts can still be forged or clock-skewed. This
   path does not authenticate the venue, establish live freshness, confirm
   account settlement or supply missing historical intervals.

The constructor/DDL behavior of the existing store is unchanged. Future actual
store initialization may run its already-reviewed additive DDL and needs
separate operational authority. No such initialization occurred here.

The collector's SDK single-endpoint mode still cannot supply these paired
REST bytes/receipts and is not silently converted. This is an explicit journal
integration, not collector/network wiring or deployment. The next source
boundary is a separately reviewed opt-in pair producer with declared request
budgets; no job, collector mode, schedule or live capture is authorized here.

## Review handoff

Exact four new files, promotions, checkpoint, diff and dependency hashes are
frozen under docs/review_artifacts/okx_funding_journal_20261029/v2/. Separate GATE
must review write/read ownership, budget/atomicity, original-byte preservation,
derived-value refusal and unchanged gates; run only the documented focused
command once. HIGH-risk implementation is not self-accepted.

No account/credential/config/network/realDB/schema/service/server/Docker/
scheduler/collector/trading/capital/risk/deploy/dependency/commit/push action.
