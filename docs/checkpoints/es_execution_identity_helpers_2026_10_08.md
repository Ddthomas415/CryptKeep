# ES execution identity helpers - first implementation slice

Role: ENGINEER. Objective: pure versioned identity format and validation before
producer/journal/gate integration. HIGH-risk analytical eligibility support.
Implementation state: READY_FOR_INDEPENDENT_REVIEW.

Changed source: services/strategies/execution_identity.py.
Tests: tests/test_execution_identity.py.

## Implemented, not activated

Version 1 payload binds an explicit cohort ID, strategy name and resolved
parameter, entry, exit, sizing, cost and market dictionaries to four declared
implementation fingerprints. Strict top-level fields, cost/market schemas,
finite JSON values, canonical sorted serialization and SHA256 are enforced.
Evidence stores detached copies; later input mutation does not alter the result.

Missing/invalid expected identity, missing evidence, contradictory content/hash
and different policy hashes return explicit analytical rejection reasons.
Intent-to-fill helper validates content and refuses copying when effective paper
cost settings differ. No order is blocked by these helpers because no production
caller imports them yet.

## SHOWN verification

VERIFIED_ENV: repo Python 3.12, explicit --noconftest, synthetic pure inputs,
bytecode/cache disabled, no runtime imports or operator state access.

Command: PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest --noconftest
-q -p no:cacheprovider tests/test_execution_identity.py

Result: 16 passed in 0.13 seconds. Tests cover canonical ordering/detachment,
SMA/exit/fee/basis/size/symbol/software changes, missing/contradictory metadata,
invalid costs and effective-cost checked intent-to-fill copying. No full suite,
loaded child process, journal path or actual gate acceptance tested.

## Limits and integration contract

- Fingerprints are supplied by callers. Correct derivation from loaded code and
  resolved runtime policy is not implemented or proven here.
- Hashes identify content, not authenticity. Anyone able to replace both fields
  can fabricate a consistent identity. Journal reconciliation must bind the same
  canonical payload, not trust a label or hash alone.
- Policy dictionaries have arbitrary JSON keys. Producers must build an explicit
  allowlisted policy payload; never serialize full user config or credentials.
- This slice is deliberately unwired. No claim that the actual gate now rejects
  wrong-policy fills. Existing six-scenario characterization still describes it.
- No account reset, historical conversion, threshold reduction, config activation,
  producer environment flag, deployment or collector restart.

Independent reviewer Averroes requested for this exact helper slice. Its review
does not authorize the still-unimplemented pipeline.

Subsequent independent GATE: ACCEPTED_WITH_RISK, unwired slice only. Reviewer
reran the command: 16 passed in 0.10s, no blocking defect. Limits: arbitrary policy
dictionaries do not prove strategy-specific completeness; 5 versus 5.0 hashes
differ; caller-provided software digests and expected identities are not trusted
runtime evidence. Fill copying does not prove an independently approved cohort.
No whole-cohort, integration, promotion or deployment acceptance.

Next bounded implementation after accepted helpers: actual resolved policy capture
and immutable intent metadata, with default-off activation and error paths that
leave protective exits/trading unchanged. Producer-to-engine-to-journal-to-gate
propagation requires separate integration proof before canonical cohort activation.
