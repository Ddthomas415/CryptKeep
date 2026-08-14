# Paper Universe Widening Decision

Date: 2026-07-04

Status: Do not widen canonical paper universe yet

## Decision

Do not widen the canonical `es_daily_trend_v1` paper universe during the active
promotion campaign.

Widening can be reconsidered only after:

- the current canonical gate state is recorded from live operator output;
- `scripts/check_promotion_gates.py` uses symbol-aware chronological
  entry/exit pairing, or the gate is explicitly documented as single-symbol
  only;
- each candidate symbol has venue/source support and provenance qualification;
- per-symbol risk caps are written;
- cross-symbol correlation and non-independence are explicitly accepted or
  excluded from the gate count.

## Evidence

- SHOWN: the current backlog calls out
  `scripts/check_promotion_gates.py::_count_round_trips` as a `min(buys, sells)`
  helper that must be replaced before cross-symbol round trips can count.
- SHOWN: the active canonical campaign is still accumulating
  provenance-qualified paper evidence for `es_daily_trend_v1`.
- CLAIMED: recent operator status has shown qualified round trips progressing
  slowly, but this decision must not use raw or cross-symbol fills to bypass
  the evidence contract.

## Rationale

Widening the universe could increase evidence velocity, but it also changes the
meaning of the paper gate. A same-strategy, multi-symbol campaign does not
produce the same evidence as a single-symbol campaign unless the gate can pair
entries/exits by symbol and report cross-symbol dependence clearly.

The current correct path is to preserve the canonical campaign and treat
multi-symbol expansion as a separately reviewed evidence-design change.

## Future Reconsideration Packet

Before approving any widened paper universe, prepare a packet with:

1. candidate symbols and venues;
2. signal source and timeframe per symbol;
3. provenance qualification fixture for each symbol/source;
4. symbol-aware round-trip counting proof;
5. per-symbol and portfolio-level paper risk caps;
6. correlation/non-independence caveat;
7. rollback plan to the current canonical single-symbol campaign.

## Operator Outcome

No campaign, manifest, strategy config, gate threshold, or runtime process is
changed by this decision.

## Executable Guard

`tests/test_paper_universe_widening_decision.py` pins the do-not-widen status,
reconsideration requirements, packet fields, and no-runtime-change outcome so
evidence velocity cannot silently weaken the canonical paper-gate contract.
