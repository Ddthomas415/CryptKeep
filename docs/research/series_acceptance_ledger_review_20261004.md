# Acceptance ledger and FC-01 session record review

2026-10-04. AUDITOR. Read-only verification of supplied workbook, pasted
handoff and repository records. No new series acceptance or deployment.

## Findings

1. SHOWN: the final series has 28 applied patches, not 26. Bundle rev41's
   folder-36 apply_order.txt lists 26 through 0028, excluding 0011/0019.
   Add 0029 and 0030 once each. The pasted detailed command gets this right;
   workbook Shortest path A2:E2 and ledger section 3 collapse it to 26.
   Following the stale list alone would omit the two latest corrections.
2. SHOWN: "Accepted only through a later correction" is not an acceptance
   state established by these records. For example, the ledger itself says
   0022 has no explicit acceptance since its incomplete review. Use "original
   finding addressed; final acceptance unresolved" for 0012, 0022-0025,
   0027/0028 unless an explicit review supports a stronger disposition.
   Passing later probes does not independently accept every intervening diff.
3. SHOWN: a full-suite/tree-hash check closes verification gaps only. It
   cannot settle conflicting ownership, stop basis/position identity, recovery
   authority, currency/account provenance, concurrency or host readiness.
   Four-minute runtime is CLAIMED, not a guaranteed local bound.

## FC-01 check

Recomputed from frozen result rows: selected mean midpoint +5.9496 bps,
rejected +9.0691 bps; break-even fee 2.9727 bps per side; seven positive
pre-fee and one positive after-fee selected entries. Matches session record.
Incremental +$76.49 decomposes into $84.04 avoided fees minus $7.55 foregone
positive gross bid/ask PnL. It is not new profitable selection evidence.
Maker 25-bps arithmetic remains a fee-only hypothetical, not validated maker
execution. No bootstrap recomputation or independent live-database count in
this review. No basis for changing the accepted scoped FC-01 STOP decision.

## Next scoped action

Clean isolated reproduction: base 97c24c8e4884629347a5492ae848133becd9027b,
folder-36 list plus 0029/0030, 28 total, exclude held 0011 and superseded 0019.
Compare pristine tree to claimed 0544af67b7a1eb90e27774af488dacd81530d263
before adding reviewer probes, then run one full suite and compare failure
identities with a same-environment baseline. Reviewer probes are a separate
overlay, not part of the pristine tree hash. No push, merge or deployment.

That integration run was not performed in this artifact review. Overall
series remains INCOMPLETE. Workbook and other agent's records left unchanged.
