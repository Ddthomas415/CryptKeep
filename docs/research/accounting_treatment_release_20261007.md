# Accounting treatment: review and release limits

Financial/concurrency risk: HIGH. Publication for CI only; no deployment approval.

The bounded treatment persists reconcile fills and canonical retry payloads
atomically, requires durable sink completion before terminalization, refuses
unknown execution quantity or execution average, and bounds recorded quantity
against venue evidence. Failed/competing writes leave an intent incomplete
without stopping reconciliation of other intents.

Symbol-loss effects are exactly-once per venue/fill. Existing counters remain
unchanged at a durable cutover; identities journaled before activation are
legacy and are not bulk replayed. Canonical sink uses operator-approved durable
journal recording order, per symbol across venues. Later effects refuse while
earlier nonlegacy effects remain unapplied; no exchange-time history reordering.
The optional research/ root is allowed; unrelated roots remain rejected.

Independent reviewer Hume accepted three bounded corrective diffs after
read-only source/JUnit inspection, not independent test execution or release
approval. Earlier human bounded acceptances do not authorize deployment.

## Proof and base identity

Original frozen candidate base620bc8dbe: full isolated suite3812 passed,
33 skipped, zero failures, 35 warnings, 289.77s. Patch SHA256:
1299a32e2fd07be52cf1075898a675d8f7c2b3aedbacae80af16e2a3d7420c47.
Unrelated mixed-working-source3889-pass proof is not attributed to this patch.

Publication base97c24c8e4 is newer. Patch applies unchanged; all ten treatment
source/test hashes must match frozen manifest. The original full-suite run is
not a full-suite result on this newer base. Current-base targeted result and
CI are recorded separately in the work log/PR. Optional companion skips are
not integration proof. No genuine venue/power-loss/host/deployment proof.

## Operator constraints

Before any authorized cutover deployment, stop old accounting writers. Preserve
existing counters; no historical replay/restatement or account cleanup implied.
Earlier orphaned journal events can block later loss accounting indefinitely;
no new orphan repair tool/drain is provided. Direct low-level store callers retain
unordered defaults. Position and daily-risk effects remain separate transactions.
Other execution paths, missing partial fee/VWAP evidence and historical untracked
fills remain outside demonstrated coverage. No live arming, config/credential,
campaign/process/order change is authorized by this pull request.
