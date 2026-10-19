# Parallel Bounded Adapter

Role: ENGINEER. Risk: HIGH. Status: ACCEPTED_WITH_RISK by separate Hooke review,
standalone composition and timing correction only. No operational freeze or
actual dataset evaluation is accepted.
Objective: compose existing reviewed source/cohort/quote helpers into isolated
bounded-study inputs without running statistics, scoring or modifying snapshots.

Interface: `cmc_bounded_adapter.build(manifest, now_ms=...)`. Each manifest row
holds an explicit preserved snapshot path and its expected content SHA256.
No CLI, directory auto-selection, network, scheduler or primary-gate integration.
The helper refuses before February15,2027 at12UTC, before opening any sources.

The adapter reloads/hash-checks v3 snapshots, rejects duplicate/future sources,
rebuilds prior30day cohort membership, preserves fixed entry-rule exclusions,
recomputes seven-day paired excess and qualifies entry/exit with existing policy.
Missing eligible outcomes or declared dates refuse rather than become zeros.
Snapshot/list/ticker/BTC/book receipt times are checked at the appropriate
chronological maturity boundary. Each retained event binds entry and exit hashes.
Output also binds adapter and dependency hashes. Raw returns remain unclipped
until the separately reviewed bounded calculator receives the normalized input.

Costs intentionally retain the original CMC rule's1.2% per-side fee, inherited
from cmc_return_math.py. This is not the observed account's0.5% taker fee and is
not silently changed here. Historical research fee corrections remain unchanged.

Important limits: content hashes do not authenticate HTTP sources or prove
capture timestamps. The supplied manifest cannot prove no other snapshots were
omitted. Outputs retain source_authentication and inventory_completeness
UNVERIFIED, execution NOT_FILL_PROOF and scoring_authorized false. No source or
timing label is manufactured from current file modification times. A future
operational evaluation requires an independently reviewed inventory freeze and
chronological availability evidence, not simply calling this helper.

Proof: twenty adapter/calculator tests pass, including a synthetic127-snapshot
fixture using real snapshot, cohort, endpoint, cost and qualification helpers.
The tests cover full composition, raw tail retention, early refusal, content
changes, duplicate sources, missing prior/calendar days and missing exit outcomes.
No actual market outcome dataset has been evaluated. Separate review reproduced
a defect where late entry evidence could create an exclusion; receipt checks
now precede qualification/exclusion, with a one-millisecond-late regression.
Parent expanded selection:46passed0.79seconds (adapter, bounded calculator,
completeness adapter and quote qualification). Reviewer reported43passed0.64seconds
under its selection; do not conflate the two counts. No remaining review blockers.
