# Subject versus archived-headline context, October 24

Active role: ENGINEER. Risk: HIGH (answer-validation/fail-open boundary).
Separate GATE: ACCEPTED_WITH_RISK for offline correction only.
Runtime: INCOMPLETE.

## Scope and behavior

The operator's continuation authorizes the next recommended offline guard
correction, not a new preparation, startup, database request or runtime retry.

SHOWN in controlled fixtures: the existing mixed BTC/ETH archived headline can
now remain in a BTC answer without selecting static dashboard fallback. The
correction does not approve its citation or establish market causation.

Changed production file: `dashboard/services/views/_shared_signals.py` only.
An explicit response `asset` different from the requested asset is refused before
the client can relabel it. Missing legacy asset metadata retains old behavior,
but cannot enable the context exception.

The exception is deliberately limited to the existing deterministic fallback's
single exact labelled **current-cause archived-headline passage**. It requires
the requested subject, fallback/non-model metadata, execution-disabled flag,
keyword-only/non-causal markers, article-view marker and ordered bound keyword
citations. Each citation must have a unique positive integer ID, its matching
`keyword_ID`, method, title, source and URL. A title with a foreign known ticker
must also mention the selected ticker. The reconstructed passage must match
exactly, including its non-causal disclaimer, and occur once. All surrounding
text and the full precedent/catalyst fields retain the whole-token guard.

This is structural context classification, **not semantic verification or a
security/provenance attestation**. Payload markers do not authenticate a source.
The separate unchanged evidence checker still requires the original archived
body/lineage and exact approved witness. Unsupported comparative prose, foreign-
only headlines, malformed/unbound context and genuinely wrong subjects remain
refused. No generic LLM mixed-asset exception or widened ticker universe is added.

## Proof and preserved evidence

The old production guard and two old test files were preserved before editing in
`docs/review_artifacts/companion_context_guard_20261024/pre_change_sources.tar`,
SHA256 `d1105b8a4172f216257f66879f259c51ada3cc706d258a06ed3bc0f72409f4fe`.
The tar also contains macOS extended-attribute sidecars; no disk extraction is
required. Original report, receipt, question, approvals and article archive are
unchanged. Their old source hashes describe the old snapshot, not the new guard.

Initial exclusive report (retained, superseded by the correction below):
`docs/review_artifacts/companion_context_guard_20261024/report.json`, SHA256
`feafa7f4e6d2d81d4c74c53c99b57c283120ada6b14a254e1ae30fee2dba3952`.
Its 17 source/input bindings were verified unchanged after generation.
The old report remains `3376c9eb...be09`; no historical result was overwritten.

| Controlled lexical selection | Client/identity fixture | Unchanged evidence fixture | Combined |
| --- | --- | --- | --- |
| 7 | Pass | Pass | Pass |
| 47 | Pass | Fail | Fail |
| 5, 7 | Pass (formerly rejected) | Pass | Pass |
| 5, 47 | Pass (formerly rejected) | Fail | Fail |

Saved rows substitute for a live DB read. Retrieval selections and disabled-risk
replies are fixtures; no actual ranking or current persistent identity is proven.
All-false evidence output is one aggregate refusal, not five diagnosed defects.

VERIFIED_ENV targeted command:

```sh
./.venv/bin/python -m pytest -q tests/test_explain_headline_context.py tests/test_explain_asset_guard.py tests/test_explain_diagnostics.py tests/test_companion_archive_contract.py tests/test_companion_evidence_checks.py
```

Initial result: **234 passed in 11.05s**, including 40 new parameterized regressions.
New tests cover actual client selection, subject mismatch, surrounding/precedent/
catalyst assertions, malformed metadata/citations, missing bindings, foreign-only
headlines, repeated passages, changed disclaimers and unchanged witness refusal.
Network/subprocess tripwires are active in the new fixture paths.

Additional offline probe: four explicit subject mismatches (ETH, SOL, null,
integer) with a BTC-only narrative refused through the actual client. This
isolates primary-asset checking from the mixed-headline rejection. No service
transport was invoked. Whitespace diff check passed; full suite not run.

## Remaining boundary

Separate review is requested on the frozen source, tests and new report.
No source repair beyond this presentation guard, approval expansion, retrieval
forcing or trading/risk/campaign change occurred. No lifecycle or HTTP operation
was performed and no credential was supplied to transport or exported.

The actual historical response prose remains unavailable; its precise rejection
cause remains UNVERIFIED. The receipt did not cite approved witness7, which this
guard correction cannot repair. Runtime remains INCOMPLETE. A later retrieval
diagnosis needs its own bounded scope; no consumed attempt may be reset or reused.

## First review and bounded correction

The separate reviewer returned INCOMPLETE with one reproduced P2, CG-1. Removing
the context without a separator could turn `ETH` + context + `demand increased.`
into `ETHdemand increased.`, hiding an outside whole token. This was a genuine
normalization bypass, not a proven citation-approval bypass. The first review is
retained as `independent_review.json`, SHA256
`14e7674136622fe281396165dfc9e5aefbd9fc799e3557f37bbce9caf27f9771`.

One-line correction preserves a space at the removed passage boundary. Added
the exact reproducer for ETH and SOL through the actual normalizer. The reviewed
pre-correction source/test snapshot remains in `reviewed_candidate_sources.tar`,
SHA256 `8e8347685076f339277d6ad1ea59275cece1a255146e762f8d74e5a16dca2fc4`.
No other production behavior or evidence criteria changed in this correction.

Final targeted command, isolated from inherited environment and pytest plugins:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_explain_headline_context.py tests/test_explain_asset_guard.py tests/test_explain_diagnostics.py tests/test_companion_archive_contract.py tests/test_companion_evidence_checks.py
```

Result: **236 passed in 10.91s**, including 42 new context regressions. Full suite
not run. Corrected exclusive `report_corrected.json` SHA256
`4a6b83e046ec903e3b70dc4f489e13997a8214fb7d3667ba0dc86d51cd58508c`,
all 17 bound inputs/sources checked unchanged. Previous reports remain intact.
Narrow independent re-review completed on CG-1 and the corrected frozen files.
Separate GATE accepted the offline correction with risk; runtime INCOMPLETE.

## Independent correction acceptance

Separate GATE returned ACCEPTED_WITH_RISK, no remaining blockers, CG-1 resolved.
Retained `independent_review_corrected.json` SHA256
`9a8acc659bda7e7f53059b3297c714b63ace0b0531d7cafc5265bcb60a8c5819`.
Reviewer verified the exact one-space production delta from the preserved
candidate, all 17 corrected report bindings and the retained earlier artifacts.
Its isolated context-plus-archive test command passed **47 tests in 1.14s**,
including both new boundary reproductions. It did not repeat the broader parent
slice or a full archive/source audit. Parent read the whole review and verified
all 22 listed source/artifact bindings unchanged.

This closes the scoped offline implementation and review. No operational action
is authorized by that acceptance. The next unresolved issue is retrieval of
approved question evidence, not this corrected presentation guard. No witness
was added or forced into retrieval, and no fresh runtime packet was prepared.
