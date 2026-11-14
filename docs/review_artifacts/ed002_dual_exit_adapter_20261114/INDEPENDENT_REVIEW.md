# Independent dual-exit core source review

Bot relation: BOT_RULES; runtime configuration not checked.
Reviewer: Nash, separate agent `01a1cee8-b4ec-7343-9992-b771df07aba1`.
Recorded by Codex from separate actual responses, not implementing-thread certification.
Final source/correction disposition2026-11-14T23:33:17Z: **ACCEPTED_WITH_RISK**, limited to the FIRST
per-policy adapter and synthetic proof. No remaining material blocker in that bounded scope.

## Source boundary

```text
27a243ac71638620be811739eee28ec946a521899ccb3bb476c2f0cf26116099  SOURCE_MANIFEST.json
8c4792d086ab9411f9129f3d8c9bef115196aed3ccac5678f9aee35cb6d4136f  AUTHOR_HANDOFF.md
```

The reviewer verified all15 source/test/snapshot pins and two preserved before sources. Source/test bytes and
manifest remain unchanged after acceptance. README now records the disposition; AUTHOR_HANDOFF preserves the
exact pre-closeout README hash checked by the reviewer. Earlier initial-core source is retained, not hidden.

## Plan and implementation findings

The separate bounded implementation-plan review accepted the explicit opt-in context design with risks, requiring
unchanged legacy default identity, journal/source validation, consistent trace/target annotations and explicit
required-held-exit failures. No replacement simulator was requested.

Author probes independently of review showed edited execution prices and an alternate valid frame/fill ledger
with a transplanted input binding could pass initial reconstruction (O170), and a required held exit with a
missing execution open could remain COMPLETE (O171). Before/after regressions and final source implement
bound-source/settlement validation and incomplete required-exit handling. The separate reviewer explicitly
verified the source-correspondence correction; that regression independently passed1case in0.25s.

The reviewer then blocked source acceptance for O172: a50% pending target injected after a recorded HOLD/None
decision produced an additional modeled4.58141 A BUY at hour303 and returned COMPLETE. Financial validity
did not establish policy provenance. The correction replays source-derived policy decisions over the bound
history through the SAME fresh adapter/ledger and compares full canonical state, including pending/executed
targets. It does not merely compare two editable serialized copies.

Final correction proof: four injected/altered/deleted pending and altered executed-target regressions passed
within an independent12-case correction selection; the original independent injected-target probe now rejects.
The prior52-case selection (1.00s) and1source-correspondence case are reused evidence for earlier stages, not
claimed as an independent full final suite. Author273passed25.52s was not independently repeated. No tests were
rerun for the final documentation/pin closure; reviewer reported no remaining material blocker.

## Acceptance limits

This is a pure per-policy synthetic model, not an operationally qualified or complete study. Sixteen-arm
orchestration, event/report integration, actual announcement/data coverage, long-horizon replay capacity,
current host/runtime/source deployment and measured fills remain unverified. Caller-declared source identity
is not attestation. Test-body guards do not establish OS-wide isolation or facts about hidden processes.
No actual market-data experiment, account/credential, scheduler/server/service, deployment/trading or R10
operation is accepted or authorized by this review. Existing financial, confirmation and live-safety gates remain.

What do I know that could change the owner's decision that I have not yet said? This accepted component is
not yet a complete or operationally qualified study; carry replay cost and future input/event coverage remain unknown.
