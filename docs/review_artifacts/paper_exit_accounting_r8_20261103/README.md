# R8 written-exit accounting prerequisite

Bot relation: BOT_RULES; runtime configuration not checked.

Active role: ENGINEER. Author source disposition: READY_FOR_INDEPENDENT_REVIEW (self-checked).
Separate corrected source GATE: **ACCEPTED_WITH_RISK**. Initial O-50 rejection is preserved, not relabelled.
Full R8 and engineering item 2 remain INCOMPLETE.

## Decision And Contract

Count one provisional reference-price outcome per **written strategy sell intent**, not per attempted write,
blocked sell, retry or fill. This preserves the previously selected intent-time contract; it does not measure
realized P&L, portfolio return, fees or profitability. Cancelled/rejected written intents still count; the R12
same-root retry does not create another event. Stop-reset placement and entry/stop basis are deliberately unchanged.

Reuses the October ordered journal (0020/0021/0023) and queue-first recovery design (0022). The written queue row
carries `meta.exit_event`; it can be recovered after journal failure/restart. Journal status and performance-counter
updates commit in one strategy-state transaction. Oldest unresolved evidence blocks later events and new entries,
not protective orders merely because journal bookkeeping failed. Bad/conflicting evidence is retained, not guessed
unwritten or discarded. Recovery uses queue row order and an identity-checked cursor; applied identities are permanent.

## Inspected And Changed

Inspected real runner emission/reset/kill paths, paper queue/state stores, paper consumer/reconciler, TTL/recovery
tests, the accepted R1/R12/capture work and October prior-art patches. Changed the runner's accounting boundary,
added a queue evidence iterator and the accounting adapter, restored the existing journal, and extended loaded-code
identity to the new dependencies/storage methods. Existing FakeDB decision tests explicitly stub durable accounting;
new real-SQLite tests, not array appends, prove it. No installed package, grant, AGENTS change or operational action.

### Requirements

- Written intent counted once, unwritten/blocked intent not counted: implemented; real runner/SQLite tests pass.
- Queue commit/ack loss, journal prepare/confirm/apply interruption and restart ordering: implemented/tested.
- Multiple written losses arm the owed performance kill; current 49 subsequent-gate boundary retained: tested.
- Unknown/quarantined evidence prevents new entries without a new journal-only exit restriction: tested with
  otherwise usable runner state/queue. Not a guarantee that a totally failed strategy DB can compute fresh exits.
- Durable source/capture identity and unchanged default signal/exit selection/stop-reset point: tested.
- Full R8 creation/pickup/final timestamps, 120-second buy expiry, stranded claims, deletion detection and watcher:
  **not completed by this prerequisite**. R4, all service/start/provider gates and commissioning remain open.

## Proof

- `baseline_hashes.json`/`*.before` preserve the accepted stage baseline. `final_hashes.json` binds eleven final
  source/test files; `stage.final.diff` includes the strengthened cooldown fixture, not unrelated worktree changes.
- `runner_before.*`: two expected counter failures against saved before-runner source (not fixture/API failures).
- `contradiction_before.*`: a written event versus permanent `unwritten` journal marker fails the draft controller.
  `fingerprint_before.*`: the newly referenced storage method mutation fails the draft fingerprint guard.
  All source overrides are isolated subprocesses; production files were never swapped for before runs.
- Development proof: 44 new accounting integration cases passed; restored journal 93 cases passed; 92 existing
  runner cases passed. Current focused capture/normal-action subset: 10 passed/25 deselected. These are not additive
  unique-case totals or independent acceptance.
- Consolidated `focused.command.json`, log/XML: **788 passed, one compatibility-fixture failure**, 32 files,
  139.69 seconds. That fixture used an array append and stubbed accounting as if it were durable queue evidence.
  It now writes the actual SQLite queue and uses actual accounting; all original cooldown assertions remain.
  `cooldown_fixture.final.xml`: **21 passed** in that file after the test-only correction. Production source was
  unchanged. Do not call this one all-green 789-case command; no full repository suite was run.
- Draft omissions O-48/O-49 were found by a test worker/main before independent handoff, corrected with regressions,
  and recorded in PROJECT_STATE. Separate review is pending; author checks do not certify the work independently.

## Independent Rejection And Bounded Correction

The reviewer independently ran 137 journal/accounting cases but found a P1 not covered by them: duplicate JSON
keys at the queue boundary could replace a loss with a gain and admit a paper buy. That finding is not dismissed
because the ordinary tests passed. The initial queue source and 44-case test file remain as `*.submitted`.

The correction reuses the journal's strict finite-object decoder for queue evidence, rejecting duplicate keys
at every nesting level. Original raw metadata is preserved in quarantine. An empty document is invalid rather
than silently treated as absent legacy SQL NULL. Eight new flat/held regressions cover these representations,
unchanged raw evidence, zero counts, blocked entries and available protective sells.
`duplicate.before.*` shows **8 expected failures** against the initial queue/controller boundary in isolated
processes. `correction.after.command.json`, log/XML shows **167 passed in 15.32 seconds**: all 93 journal cases,
52 accounting cases, 21 cooldown cases and the storage-method fingerprint case. This is the corrected focused
selection, not a rerun of the earlier 32-file selection or the full repository suite. `corrected_hashes.json`
binds the eleven final files; `stage.corrected.diff` preserves the delta. Source is frozen for separate re-review.
O-50 records the omitted ambiguity boundary and the rejected candidate; accepted-work rework is not inflated.

**Final independent correction review:** `independent_review/final_review.md` records **167 passed in 16.32s**,
all three original probes passing unchanged, eight expected old-method failures and 11/11 corrected hashes.
The separate reviewer accepted this prerequisite **with risk**, not full R8 or permission to operate. Main's source
handoff remains READY_FOR_INDEPENDENT_REVIEW; the acceptance is the separate GATE's, not self-certification.

## Remaining Limits

SQLite's inherited WAL/NORMAL durability is not a power-loss guarantee. This restores lazy journal schema
creation/upgrade code but did not access or migrate any runtime DB. Before any operation, inventory/backup and
applicable host/schema compatibility still need the separately authorized operational process.

No current server/configuration/DB/position/process, actual alert delivery, fill, execution cost or market outcome
was inspected. Fixed-venue/scoped tests are not a venue-change ownership repair (October 0024/0025 remain prior art).
Legacy JSON plans are not automatically imported; existing pending/quarantined/contradictory rows can keep entries
blocked until explicitly resolved, with no operator-release tool added. If queue evidence is unavailable, even
confirmed events wait and entries stay blocked; the owed kill is settled when evidence can be read again.
Previously stored legacy sells without event metadata are not recounted. Deleted primary evidence with no journal
copy cannot be reconstructed; R8 inventory/deletion monitoring is still required. Signal-history consumption and
no retry until signal change remain inherited behavior. These limits must not disappear in a deployment handoff.

Open questions: independent findings; actual persisted legacy state/venue ownership; operator contradiction
resolution; all remaining R8/R4/operational acceptance. No additional material finding is withheld within the
inspected scope; uninspected runtime state remains unknown.

What do I know that could change the owner's decision that I have not yet said?
