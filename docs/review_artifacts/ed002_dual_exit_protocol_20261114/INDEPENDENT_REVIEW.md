# ED-002 dual-exit proposal: independent design review

Bot relation: BOT_RULES; runtime configuration not checked.
Reviewer: Nash, separate agent `01a1cee8-b4ec-7343-9992-b771df07aba1`.
Recorded by Codex from actual separate responses, not author self-certification.
Decision2026-11-14T22:51:35Z: **ACCEPTED_WITH_RISK for offline design coherence only**.

## Exact accepted handoff

```text
818f9067c175f09928583dbd963c229d07e0c9fcdc83414b020cde7ffb6ce3a6  docs/research/ed002_dual_exit_protocol_proposal_20261114.md
5dd2e22b5f0be0a42ec1e81e129ce92594ae34cf8b1937c30f7aca3ac7644a39  docs/research/ed002_dual_exit_protocol_bindings_20261114.json
```

The proposal's READY_FOR_INDEPENDENT_REVIEW header records the author's immutable handoff state; this separate
receipt records the subsequent design GATE. The exact reviewed proposal and bindings are retained unchanged.
The21 current source/input bindings remain equal to their previously verified values. Binding a source is not
independent functional certification of that source or the current runtime.

## Findings and bounded correction

The initial draft/binding are preserved under `initial_draft/`. Initial coherence acceptance was withheld:
pre-entry peak exclusion alone did not explicitly prevent a price-triggered exit using a close at/before the
fill that created the reference. Author identified the concern and the reviewer confirmed the blocking ambiguity
(O169). The correction declares:

- `last_reference_fill_ts` advances on EVERY actual BUY/addition, even if weighted reference price is unchanged.
- Price-based stop/trailing/TP evaluation and peak updates require `bar_end_T > last_reference_fill_ts`.
- Original age/peak are retained across additions; time exit uses T minus original entry fill time, not later E.
  It can liquidate recently added units in an older position, with additional turnover/costs disclosed.
- Missing valuation/state/permission remains INCOMPLETE; time eligibility is not an execution waiver.
- Future synthetic proof must cover first-fill/equal-time, addition/equal-time and delayed-gap boundaries.

Three wording clarifications were also requested and applied in the same bounded correction:
same entry/sizing ALGORITHM per arm's own wallet is not identical trades; S consumes the final returned strategy
action, not observer.raw_action; event-driven liquidation invalidates both BTC hold and the fixed-unit mix.

Final reviewer response: all four corrections present, required boundary cases explicit,21 input bindings unchanged,
initial draft/binding hashes match, no remaining blocker from this bounded review. Correction review checked text
and refreshed bindings only; no tests, additional source inspection or operations were performed for that check.
This is not end-to-end simulator verification. No acceptance of statistical qualification, signal performance,
live runner parity, actual future data/announcement coverage, host readiness, cost invoices or execution fills.

## Authority retained

Owner approved resuming OFFLINE DESIGN and proposing both models. The new rules remain **PROPOSED, NOT ADOPTED,
NOT IMPLEMENTED**. Design review does not authorize code changes, collection, evaluation, dates/freeze/activation,
deployment, trading, risk/capital changes or R10 resumption. Existing defaults and prior experiment criteria remain.
Next proposed boundary is owner adoption of the exact new rules plus a separately bounded synthetic-only
implementation—not an automatic experiment, new infrastructure layer or market-data test.

What do I know that could change the owner's decision that I have not yet said? Implementation correctness and
future input/event coverage remain unproved; a coherent reviewed proposal is not an operational trading system.
