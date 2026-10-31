# One-shot OKX public transport check

2026-10-29 America/New_York. AUDITOR. Evidence READY_FOR_INDEPENDENT_REVIEW.
Original funding Fix3 remains INCOMPLETE.

SHOWN: the reviewed producer was invoked once at10:59:36EDT/14:59:36UTC for
BTC-USDT-SWAP. Two fixed public GETs returned HTTP200/APIcode0 and matching
instrument identity: one current row and five historical rows. Producer
capture duration0.514316166s. Both captures complete,524/943bytes, below1MiB.
No redirect, retry, SDK, account or collector invocation was requested.

Original bytes, local request/receipt times, body hashes, source/binding pins,
limits and environment caveat are saved in:

docs/review_artifacts/okx_funding_pair_transport_20261029/20261029T145936Z_eddbeac2a3134ea68bc7f2b649d64b1a/

An offline readback verified both hashes/lengths and all row identities/API
codes. Current source ts14:59:15.320UTC was21.059382s before local receipt;
this is an observed age, not adoption of a freshness threshold. Scheduled
gap8h; current and reported-settled rates differ. No annualization, strategy
return, account payment or historical-interval qualification follows.

## Authorization and preflight limitation

Operator replied ok to the stated single2GET/10s-per-process/30s-capture/new
evidence-only check, no DB/collector/schedule/trading change. A first launcher
preflight stopped before producer import or any GET because systemcurl's hash
differed from the older capture. That historical hash assertion was an added
launcher condition, not a reviewed producer requirement. No producer retry or
second capture was used to obtain the successful result.

Read-only signature checks reported CSSMERR_TP_NOT_TRUSTED for curl and control
/usr/bin/true. SIPenabled/root-restricted metadata and the same reported
curl8.7.1 interface do not establish valid signature trust. Authenticated-root
inspection returned No macOS installations found. Cause, OS-update provenance
and physical-laptop equivalence remain UNVERIFIED; do not call curl corrupted,
the laptop repaired or trust restored. Original failed preflight retained.

Separate GATE01a1882a-9764-7740-9d03-3bb600f36e88 ACCEPTED_WITH_RISK proceeding
with the SAME human-authorized check, explicitly retaining binary authenticity
UNVERIFIED. Current executable pinb6f8c43b623b760e2fa95910e3f62bb518257c48b4ef54ed09285e49d6d1b85f
was checked before execution; no binary, source, TLS or trust-store change.
PREFLIGHT.json/PREFLIGHT_DISPOSITION.json retain exact scope and disposition.

## What was and was not verified

SHOWN actual public transport/response validation and append-only local file
receipt, not merely fake-transport tests. Producer/source33bindings checked
before the operation. Python SQLite audit hook forbade sqlite3.connect; only
collect_okx_funding_pair called, not the journal wrapper. No store creation,
DB write, service/job/collector configuration, account, credential, capital,
risk, order, deployment or Git publication action.

The30s budget covers producer capture checks and bounded child communication,
not all file checks/writes or a hard whole-process/OS-cleanup deadline.
Historical252tests were not rerun or mislabeled as post-restart proof. No new
source implementation was made. One approved producer invocation/two GETs are
now consumed; no ongoing capture or automatic retry remains authorized.

Freeze this record and the artifacts for bounded independent offline review.
No new market-data request is needed to verify these receipts. Operating a
recurring producer, initializing a real store, semantic/interval/crowding
qualification and live freshness remain outside this check.
