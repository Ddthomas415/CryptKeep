# Versioned archived-witness proposal, October 24

Role: ENGINEER. Risk: HIGH acceptance-input proposal.
Separate GATE: ACCEPTED_WITH_RISK, archived topical proposal only.
Not effective. Runtime: INCOMPLETE.

## Scope

The operator approved preparing and independently reviewing a versioned proposal,
not changing current approvals or starting services. Existing question, retrieval
order, three-citation budget, body/identity verifier and guard remain unchanged.
Original witness7 is retained byte-for-field, alongside its earlier review.

The proposal considers **all three** entries in the body-verified saved-order
projection: 5,47,18. This is an October11 archive diagnostic, not reconstructed
current ranking or proof of the failed V6d response. No candidate was promoted
from elsewhere in the corpus to obtain a pass.

## Candidate content

The parent read all three full saved bodies. Proposed topical assessments, pending
independent review:

- Document5 reports the historical Bitcoin liquidation episode and thin-liquidity/
  tariff context. Its proposed excerpt spans the reported price decline and
  leveraged-position liquidations.
- Document47 reports a Bitcoin sell-off, liquidation totals and short-term-holder
  exchange flows. Its opening sentence supplies the proposed witness.
- Document18 reports Bitcoin price recovery and liquidation pressure on bearish
  traders in a news roundup. Its proposed excerpt is the full Bitcoin-focused
  sentence, not the unrelated ETH/SOL discussion elsewhere in the saved body.

These are attributed archived reports, not independently verified market facts,
numerical accuracy, causal findings, fresh explanations or trading signals.
An extraction flag validates the accepted saved boundary/lineage, not the entire
publisher page or current database. Full saved bodies are copied into the packet
so the reviewer can judge context instead of relying only on excerpts.

## Packet and proof

Directory: `docs/review_artifacts/companion_witness_proposal_v2_20261024/`.

- `proposal.json`, SHA256 `5095d72eef7a2a9ac1d158aa8aa81fa78944b7c5788db61c735424b75591bf20`:
  versioned envelope, `effective:false`, original7 plus proposed5,47,18. Each record
  uses the existing exact-question/original-hash/body-hash/excerpt fields. This
  envelope fails closed if accidentally supplied as the effective approval list.
- `candidate_bodies.json`, SHA256 `f13d83396261c1bdb46e1a971c5c815a75efbf19313c82fea2eff08433225810`:
  full saved bodies, identity/times, exact excerpts, unique offsets and hashes.
- `proof.json`, SHA256 `bc037c49778d099990e40b0f17f66207d90b4dfdba2c2326092b502f975e902f`:
  20 source/input bindings and explicitly counterfactual offline comparisons.

The current approval file remains hash-bound to
`f4de03c65058769eb434e5931065deaeb5795087983a92a3b2f54dacd8feff45`.
No existing packet or approval was overwritten. The generator writes only a new
directory and exclusively creates its artifacts.

VERIFIED_ENV targeted command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_witness_proposal.py tests/test_companion_witness_selection.py tests/test_companion_archive_contract.py tests/test_companion_evidence_checks.py
```

Result: **165 passed in 10.51s**, including six new cases. Full suite not run.
Network/subprocess tripwires are active in the new fixture paths. All20bindings
match after packet generation. Tests establish mechanics, not semantic approval.

With saved top-three inputs5,47,18, the unchanged verifier refuses current
approvals and passes only when explicitly given proposed records in memory.
Witness7 still passes. Unproposed document1, unverified-body document25, wrong
question, altered body hash and invented excerpt remain refused. Saved original
rows substitute for a live database read; positive flags are fixture results.

## Remaining boundary

Independent review must read full bodies, decide topical support for the exact
question and bind the record hashes. A favorable review is limited to this
archived proposal; it cannot change effective approvals by itself. Unknown live
citations, actual current DB lineage, selection, installed source and runtime
acceptance remain unverified. No services, HTTP/DB queries, credentials, schedules,
accounts, trading rules, risks, fresh preparation or retry/reset were touched.

## Independent acceptance

Separate GATE ACCEPTED_WITH_RISK, no findings. The reviewer read all three full
saved bodies and accepted each for the unchanged historical topical question:
5 supplies retrospective liquidation/news context; 47 supplies Bitcoin sell-off/
liquidation reporting; 18 supplies short-side liquidation pressure after news.
For18, this does not explain the cause of the preceding long-side liquidation.
For47, exchange transfers alone do not establish actual selling. Article facts,
numbers and causal attributions remain CLAIMED, not independently verified.

Review: `independent_review.json`, SHA256
`c24620ca184ccd01d8afc14e6fdc2ecc96073181c09bc0dc880920e9b8598525`.
All20source/input bindings verified; all three packet files reproduced byte for
byte, including final newline. Six new tests independently passed in0.26s.
Parent165test slice was not independently repeated. Parent read the entire
review and verified all23listed source/artifact bindings unchanged.

This completes the authorized proposal and independent semantic review. The
immutable proposal retains its creation-time review-request state; this separate
receipt supplies the later archived-topical disposition. `effective:false` stays
false. Neither artifact activates an approval list or grants a runtime operation.
Future packet integration must use a fresh separately scoped draft/review,
preserving original question, bodies/excerpts, identity checks and consumed
attempt records. Existing packet approvals and current runtime remain untouched.
