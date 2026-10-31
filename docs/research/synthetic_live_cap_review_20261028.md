# Synthetic cap review: rejection and bounded correction

2026-10-28. Separate GATE reviewer01a11481-515d-7473-8ee3-7f6864c6d40b.
V1 REJECTED; corrected implementation separately ACCEPTED_WITH_RISK for the
exact synthetic scope. SYNTHETIC-CAP-01 closed by the separate GATE below.
Production repair remains INCOMPLETE throughout.

## SYNTHETIC-CAP-01 (P1), SHOWN

The reviewer reproduced a material undercount. The47-case suite passed in the
separate run (0.55s), but did not cover disappeared orders with lost known-fill
coverage. Preserving the outstanding remainder alone did not preserve fills.

Reproducer: cap50/mark1, held35, reserve10. Partialfill6 withheld41/remaining4
and includedfills6 is reconciled while a20buy is refused. A later generation
omits that order and includedfills and reportsheld35. V1 admits another10 at49.
Terminal variant: fullfill10/held45, then missingorder/baseline andheld35 admits
another10 at45. Completeness flags do not resolve these internal inconsistencies.

The reviewer reported matching all bindings, no edits/production behavior/private
access, one narrow47-case run and a minimal probe covering both variants. All
reproduced answers retained execution_authority=false; the defect still matters
inside the prototype's stated financial model.

## Corrected Scope

The operator approved acting on the next review findings within synthetic scope.
Preserved rejected source/tests/docs/bindings/diff in
`../review_artifacts/synthetic_live_cap_20261028_01/rejected_v1.tar`, SHA256
`75df1ab02bfadf006a4810fda41574622c646fb05d0805bd880919443b53660a`.
Original submitted bindings/diff remain unchanged historical evidence.

Added six regression cases before the source correction. The four missing or
regressed baseline cases (partial/terminal x2) fail onv1; both legitimate
holding-reduction cases pass. Existing47cases were deselected for that probe.

Two source lines now require the incoming included-fill baseline to match
retained cumulative fills when an order row is absent. Missing/regressed or
unexpectedly advanced coverage refuses the increase without changing durable
state; an absent zero-fill row can still retain its full obligation. Updated
explicit order evidence can reconcile further fills through the existing path.

Lower holdings remain permissible when known cumulative fill coverage is
preserved; this models a declared coherent net reduction, not an independently
verified external sell/transfer. No provider, ownership, currency or source
completeness assertion has become real account proof.

Final author command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_synthetic_live_position_cap.py
```

53passed in0.66seconds, exit0. This supersedes47as the current author slice,
not the original v1 result. No full suite or new market/fill/statistical run.
New binding/diff are in `../review_artifacts/synthetic_live_cap_20261028_02/`.

At correction submission, one focused separate closure review was requested;
corrected code remained READY_FOR_INDEPENDENT_REVIEW until the actual result.
No production integration, migration, account access, cap setting, service,
scheduler, deployment or trading is authorized by this bounded correction.

## Actual Separate Closure

The same separate reviewer returned ACCEPTED_WITH_RISK for the exact synthetic
scope and closed SYNTHETIC-CAP-01, with no outstanding blocker in this correction.
It verified the archivedv1 hashes and reproduced correction.diff exactly,
confirming no other source changes. Its isolated53-case run passed in0.62seconds.
No files were edited or private/network/runtime operations performed.

Accepted source SHA256:
`1776524826aa38a102e95013a6dee3ec657175ee8708740b1fe78aae0f8ecd26`.
Accepted tests SHA256:
`48d7d315eb832657bf7b26f41b66727e06479c73510c1b2854e3e8c4231c7652`.
Closure request:01a182da-6106-73b1-bf81-13b3743c2373.

The reviewer explicitly retained synthetic completeness/coherence assumptions.
Actual source evidence acquisition, lifecycle integration and independent
integration review remain outstanding. Production repair INCOMPLETE; no
operational authority granted. Do not re-open this closed synthetic defect
without new contradictory evidence or confuse it with the still-unfixed live cap.
