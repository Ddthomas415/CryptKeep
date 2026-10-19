# Explanation asset guard: bounded offline repair

Date: 2026-10-16 10:16 UTC (06:16 New York). Active role: ENGINEER.
Risk: HIGH (user-facing research-response rejection boundary).
Implementation state: READY_FOR_INDEPENDENT_REVIEW.
Runtime objective: INCOMPLETE.

## Authorization And Contract Evidence

Operator requested the next steps following the diagnostics review. This
implementation is offline only. No service, live query, account, credential,
collector, scheduler, campaign, strategy, deployment or trading action is included.

SHOWN: `tests/test_dashboard_view_data.py` already requires rejecting SOL-only
prose for a BTC request, even when the returned asset metadata says BTC. The
current helper scans current_cause, past_precedent and future_catalyst for
BTC/ETH/SOL. No independently established rule in the inspected material
distinguishes legitimate mixed-asset explanation from unrelated asset copying.

The smallest repair therefore changes lexical matching only: a complete
alphanumeric token can be a ticker; a substring of a larger word cannot.
Unicode letters/digits are part of tokens. Punctuation and underscores separate
tokens so $ETH, ETH-USD, ETH/USD and ETH_USD remain recognized. The known ticker
set and the inspected narrative fields are unchanged. Metadata still cannot
override a wrong-asset narrative.

This is not a semantic asset-identity solution. Mixed BTC/ETH narratives remain
rejected under the pre-existing rule; that limitation is explicit and not
endorsed as correct financial interpretation. Asset names, aliases, renamed
tokens, unknown tickers and quoted source text are not newly interpreted.

## Changes And Why

- `_shared_signals.py`: import re and replace substring membership with whole
  Unicode-alphanumeric token membership. No model, extra dependency, policy
  framework, fallback change or removal of the guard.
- `test_explain_asset_guard.py`: ordinary words in all three fields, complete
  ticker/selected-asset matrix, case and separators, Unicode/numeric suffixes,
  wrong-asset metadata case, unchanged mixed-asset limitation and empty input.
- `test_explain_diagnostics.py`: replaces the previous bug-characterization
  assertion with a positive regression through both actual client routes using
  mocked transport. Receipt shows acceptance rather than foreign-asset rejection.

The earlier diagnostics checkpoint remains a historical record. Its statement
that the guard was deliberately unchanged was true for that earlier scope;
this separately authorized patch supersedes that source state, not the record.

## Verification

VERIFIED_ENV: Python 3.12.10. No dependencies installed. Fully offline fixtures.

Before the production change, the following selected regressions failed:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
tests/test_explain_asset_guard.py tests/test_explain_diagnostics.py \
-k 'ordinary_words or unicode_alphanumeric'
```

Result: 6 failed, 33 deselected in 0.28s. All six failed because the old helper
returned True for ordinary-word/embedded-token fixtures.

After the change:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
tests/test_explain_asset_guard.py tests/test_explain_diagnostics.py \
tests/test_verify_companion_stack.py tests/test_dashboard_companion_http.py \
-k 'not test_environment_proxy_never_receives_companion_bearer'
```

Result: 58 passed, 1 deselected in 0.61s. The pre-existing listener test is
deliberately excluded; no fresh listener failure or listener execution occurred.

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
tests/test_dashboard_view_data.py -k research_explain
```

Separate result: 4 passed, 55 deselected in 0.15s. `git diff --check` passed.
These are targeted runs, not one 62-test invocation or a full-suite result.
No historical strategy reruns or live transport requests.

Separate AUDITOR review: ACCEPTED for the narrow offline repair, no actionable
findings. Its independently run guard/diagnostics slice passed 39 tests in
0.29s and confirmed primary/companion acceptance, foreign-copy fallback and safe
receipt outcomes. It inspected the existing SOL-for-BTC rejection test but did
not independently rerun the parent's four existing contract tests or reproduce
the before-fix run. Because the diagnostics tests are untracked, it could not
verify their exact historical edit against Git. Source hashes above identify
the current reviewed content; this is not a clean-branch/release assertion.
Aliases, semantic identity, mixed-asset policy and live integration remain
outside its acceptance. No operational acceptance follows from code review.

## Proposed Runtime Boundary, NOT Executed Or Authorized Here

After independent review, a further existing-stack attempt needs specific
approval. Before any start, recheck current inventory and preservation of the
named container identities/volumes; do not assume an older snapshot is current.
The proposed target is the same seven existing containers from the operation
record: timescaledb, qdrant, minio, audit-log, risk-stub, memory and orchestrator
(all with the phase1- prefix). No compose recreation, image rebuild, migration,
volume removal or extra service/collector is proposed.

One actual dashboard-client query would capture the sanitized receipt BEFORE
acceptance checks. Required proof: non-static provider, execution disabled,
traceable citation identity against the existing persistent record, and no
substitution of dashboard fallback for retrieved evidence. Distinguish health,
retrieval, citation traceability and relevance; none establishes profitability.
Existing service-token use would need explicit approval, process memory only;
no exchange/private account credential is required.

Rollback must stop only containers started by the authorized attempt, with
post-attempt inventory. Whether successful services remain running must be
explicit in that authorization. Normal startup/audit writes may occur; stopping
containers does not undo them. Do not run the isolated-stack verification script
as a substitute: it builds and removes its own stack and is outside this scope.

The previous runtime failure's cause remains UNRESOLVED. Repairing a demonstrated
offline false positive does not establish that it caused that failure.

## Source Hashes

```text
098f3c879199deadfbb5aa22ce90194d0adfb0bab9bb5ebba0e3ef622999a654  dashboard/services/views/_shared_signals.py
b2136972cc253d10bf14cf76f3b074c468f6f7066f2d943182cae07e16e68f62  tests/test_explain_asset_guard.py
508e912012fd08e4fca5d858e215046dec66b220677f9997b72ffc8b6912ffd3  tests/test_explain_diagnostics.py
```

These identify current source/tests, not a committed release or deployed image.
