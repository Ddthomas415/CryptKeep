# One-time Coinbase scope observation

Active role: ENGINEER. Risk: HIGH. Implementation state:
READY_FOR_INDEPENDENT_REVIEW. This specification is not runtime proof.

## Objective and authority

The operator's continuation answers the pending request for one read-only
permissions/portfolio check using the existing connection: at most two GETs,
10 seconds per request, no retries, 30-second child wait plus at most 10 seconds
owned cleanup. Offline verification and separate review precede invocation.
No balances, orders, transfers, paging activation, configuration changes,
collector operations, service changes, or new credentials are permitted.

The fixed recipients are HTTPS api.coinbase.com, GET only:
`/api/v3/brokerage/key_permissions`, then `/api/v3/brokerage/portfolios` only
after a valid view-permitted response. No query parameters or pagination.

## Reuse and privacy

Reuse `services.security.credentials_loader.load_exchange_credentials`,
`services.security.exchange_factory.make_exchange`, and the installed SDK's
pure signing method. Do not use SDK HTTP, load markets, or request balances.
Do not auto-load another credential source, prompt for login, or create keys.
The existing credential loader may read configured environment variables or
OS keyring. Configuration values and credential strings remain in memory.

The parent forbids socket connections/DNS, application SQLite access and
subprocesses other than the fixed HTTP worker. SDK output is suppressed.
Workers receive signed headers through a private stdin pipe, never argv.
Raw responses travel through a private stdout pipe, never an on-disk log.
Each worker performs one Requests GET with TLS verification, redirects disabled,
zero adapter retries and environment proxies disabled. Response body is capped
at 1 MiB decoded; this is not a wire-byte or total interpreter-memory guarantee.

The saved report includes permission booleans, enumerated portfolio types,
counts, UUID SHA256 hashes, timestamps, HTTP codes, byte counts and type-only
errors. Never save names, raw UUIDs, request headers, tokens or raw error bodies.
Unexpected fields are discarded. JSON duplicates/non-finite values are refused.

## Failure matrix and deadlines

Missing credentials, wrong venue/recipient or malformed signing: no GET.
View denied or first HTTP/parse failure: no second GET. Any request failure:
no retry. Malformed portfolio response: retain prior sanitized permission facts
but report failure and no complete-account claim. Timeouts/cancellation can
leave request outcome uncertain; never infer no request from an empty report.
`requests_attempted` counts worker dispatches, an upper bound on actual GETs.

Use accepted `okx_full_cycle_20261029/bounded_cycle.py:run_once` only, not its
collector-specific main. One exclusive attempt marker before launch, new
owned process group, 30-second wait and TERM/KILL cleanup of at most 10 seconds.
Per-worker subprocess wait is at most 10 seconds, including import and HTTP.
Parent acceptance deadline is 30 seconds with monotonic regression checks.
Initial local checks, Popen and receipt writes are not interruptibly timed.
Final reaping proves direct-child state, not a global process inventory.

Output is exclusively created before private work. A crash may leave an empty
file. Preserve it and the attempt marker; do not reset or repeat automatically.
Coinbase/OS may retain access/audit logs; no claim of zero remote side effects.

## Execution recipe and acceptance limits

After independent acceptance and unchanged source pins, invoke the helper once
with this repository's `.venv/bin/python -B probe.py --output <owned-folder>/scope.json`.
Use an inherited environment privately for existing environment-backed keys;
do not print or persist it. Save only the sanitized stdout and helper receipts.
The approved operation uses a unique new folder; a failed attempt is consumed.

Both valid HTTP 200 responses establish only dated key permissions and the
portfolio rows returned to that key. Neither one portfolio nor many proves an
exhaustive account inventory. `account_wide_coverage` and list exhaustiveness
remain UNVERIFIED; `execution_authority` remains false. A rejected request does
not establish that the user is signed out or that credentials need replacement.
No active paging policy, risk or cap scope changes follow from this observation.

Offline verification command:
`./.venv/bin/python -B -m pytest -q -p no:cacheprovider docs/review_artifacts/coinbase_scope_probe_20261029/test_probe.py`
Tests use invented keys and stubbed HTTP, including installed-SDK signing only.
They do not establish actual endpoint access, account coverage or live execution.
