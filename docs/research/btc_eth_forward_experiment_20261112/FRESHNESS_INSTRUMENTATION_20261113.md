# Existing diagnostic: freshness and returned-range instrumentation

Bot relation: STANDALONE public-data diagnostics only; runtime trading configuration not checked.

2026-11-13. Status: ACCEPTED_WITH_RISK for offline source/synthetic scope only, following the separate review below. Owner direction: "carry out the next recomended steps" after the specific offline instrumentation recommendation. No live invocation is authorized or performed.

## Practical outcome

The existing diagnostic now records more evidence about why a response may be inadequate. It does **not** qualify freshness, complete trade coverage, clock alignment, real fills or E1. It does not fix an established upstream fault: that cause remains UNVERIFIED.

The unchanged HTTP/request/qualification/model path is reused. No new collector, pagination, URL, service, job or controller is introduced. The original failed capture and frozen v3.3 criteria remain unchanged. All new time/range fields are diagnostics, never acceptance gates or a way to rescue an excluded event.

## Requirements and implementation

| Requirement | Disposition and evidence |
| --- | --- |
| Retain bounded public freshness metadata | DONE: case-insensitive allowlist retains date/content-type/cursors plus Age, Cache-Control, Expires, Last-Modified, Via, CF-Cache-Status and X-Cache when present. Values remain at most256characters each; auth/cookies/unknown headers are omitted. Missing headers remain missing; historical headers are not reconstructed. |
| Explain time differences without claiming latency | DONE: receipts retain reported Age, signed HTTPDate/source-time versus receipt differences and wall-minus-monotonic difference. Missing/malformed/non-UTC source times, a future source time or invalid local ordering get diagnostic issues. All freshness/clock qualification remains UNVERIFIED; no numeric cutoff is fitted to the failed sample. |
| Explain returned page range | DONE: one-page timestamp range, start/end bracketing, in-window rows, malformed timestamps, duplicate/conflicting IDs and oversized-page warning. Only first100rows are examined, with over-limit state explicit. Both bracketing flags may be true while interval coverage remains UNVERIFIED. Counts are returned rows, not deduplicated executable volume. |
| Preserve evidence on exclusion | DONE: book timing and trade-range diagnostics are stored before the original validator. A page preceding the window remains INCOMPLETE with the original reason, but its explanatory metadata is retained. No timestamp shifting or alternate-interval rescue. |
| Preserve models and budgets | DONE, self-checked: before/after synthetic successful/HTTP-failed/exception captures are exactly equal after removing only the three new diagnostic fields. Request sequence/delays match. Fees, quantities, status rules, ten-request cap, fixed endpoints and all existing safeguards remain unchanged. |
| Preserve original artifacts and criteria | DONE: source and tests archived before editing; all ten saved raw/receipt bindings and report.json remain immutable; frozen hash unchanged. Prior reports' source hashes refer to the archived pre-change source. |
| Independent review | DONE: separate Nash GATE18:42:08Z, ACCEPTED_WITH_RISK for source/synthetic scope only; no blocking finding,53independent tests passed0.36s. No self-approval of high-risk source. |

## Exact artifacts and proof

- Source: `scripts/research/capture_candidate_execution_diagnostic.py`, SHA256 `1780557810062f397921f92125e986b05b42144fbaa734d01a8b5728f87d3ad7`.
- Tests: `tests/test_candidate_execution_diagnostic.py`, SHA256 `44f63296eba1aab167ac70df627d7512cc25dd67a9b4dbbb1fc79ac13af57507`.
- [Preserved source](diagnostic_proof_20261113/before_freshness_instrumentation.py), SHA256 `4ac85819a81ee00d10307550dfc2bd532c2d1b2e676d57080e848c6c788dff88`.
- [Preserved tests](diagnostic_proof_20261113/tests_before_freshness_instrumentation.txt), SHA256 `b8f587ad74330bb7c165786cfdb4e4f97c9a7b5869777d97ab99e562dc017ac3`.
- Frozen criteria remain SHA256 `8414bbcf00883f74e1cfa49c4c3161e4a742e19282b28235dc48a4a2ac1aaad6`.

First15selected synthetic regression cases failed on the original source, showing missing headers/diagnostic functions and discarded range context. After implementation, the full focused file passed53tests in0.32seconds (32prior cases,21new). No full suite, statistical audit, backtest, market replay or public capture was run. Synthetic fixtures reject sockets/DNS/process starts and inject their transport/clock; real HTTP is not used.

```sh
./.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_candidate_execution_diagnostic.py
```

The compatibility test loads the preserved source and compares the successful and two transport-failure paths. It is source/test proof, not actual endpoint behavior. The old offline diagnosis's exact reproduction command imports the then-current source; to reproduce its historical source identity now, use the archived source above. Its saved JSON and verdict are not regenerated or overwritten.

## Limits and minimum next boundary

SHOWN source behavior does not establish what any future public endpoint will send. Age/Date/cache-status are reported metadata, not a trusted calibration or proof of a cache fault. Missing, negative or malformed Age remains unknown, never zero. Book timestamps and trading timestamps may have different semantics. These fields intentionally cannot turn coverage or clocks into qualified evidence.

Full interval collection and a defensible arrival/freshness rule remain NOT DONE; this item adds no pagination or time threshold. It keeps the old conservative exclusion and all E1 pre-registration gates. Any future collection requires its own bounded scope and review; the expired ten-GET authorization is not renewed here. A meaningful next data request would need a declared question and evidence sufficient to resolve it, not another attempt whose objective is merely a green status.

No schedules, servers, account credentials, accounts, orders, risk/capital settings, trading logic, installs, backup clients, commits or pushes were touched. The broader multi-symbol and intelligence objectives remain unchanged. This is not a new strategy experiment, an economic finding or a deployed collector.

What do I know that could change the owner's decision that I have not yet said?

This improves failure visibility, not the market evidence itself. The same future response could still correctly produce INCOMPLETE. That is preferable to a software change that silently converts unqualified timestamps into apparent execution evidence.

## Independent review receipt

Separate Nash GATE `01a1cee8-b4ec-7343-9992-b771df07aba1`, checked **2026-11-13T18:42:08Z**: **ACCEPTED_WITH_RISK, offline source/synthetic scope only; no blocker**. Reviewer read actual source/test diffs against preserved originals and this report; checked supplied hashes before/after; verified unchanged qualification/model/endpoints/request/body limits/delays, bounded secret-excluding headers, and persistent UNVERIFIED diagnostics. Independently ran53synthetic tests in0.36s including the three exact compatibility cases. The author's15-case fail-before run was not independently repeated. No edits, network, capture invocation, saved-market replay or broad suite.

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_candidate_execution_diagnostic.py
```

Acceptance does not renew collection authority or establish upstream cause, freshness/clock/complete-interval qualification, E1, account fills or financial advantage. No automatic implementation beyond this item follows.

What do I know that could change the owner's decision that I have not yet said?

The reviewed implementation answers what the transport returned more clearly; it does not determine whether that response is adequate for execution research. That remains a separate evidence/contract question, not a reason to weaken this diagnostic's exclusions.
