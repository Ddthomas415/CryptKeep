# Coinbase portfolio-scope source checkpoint

Active role: ENGINEER. Isolated unwired observer only.

Official source inspected:
https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/data-api/get-api-key-permissions
GET /api/v3/brokerage/key_permissions uses bearer authentication and documents
portfolio_uuid as the portfolio associated with the key, plus permissions and
portfolio type. It does not document a global user identity in this response.

SHOWN: installed CCXT 4.5.48 exposes v3PrivateGetBrokerageKeyPermissions. This
was inspected by constructing an uncredentialed client without a request.
New isolated observer uses supplied session endpoint, validates explicit view
permission, boolean trade permission and non-nil UUID. It conservatively allows
DEFAULT/CONSUMER types only; this is prototype policy, not a venue guarantee.
It returns portfolio scope, never automatically creates AccountContext or binds
existing state. Read-only keys do not become trade authorization.

VERIFIED_ENV: original Python interpreter, isolated candidate, fake sessions
and temporary DBs. Seven-file prototype slice: 77 passed in 1.87s, exit 0.
New tests: tests/test_coinbase_portfolio_scope.py.

UNVERIFIED: authenticated response, session endpoint/environment, global account
identity, relationship to stored holdings/orders, production integration and
all-writer enforcement. No private exchange call, credential loading, account
mutation, config change, collector change or deployment occurred.

Acceptance: READY_FOR_INDEPENDENT_REVIEW; Hume requested.
Independent review: Hume ACCEPTED_WITH_RISK, bounded unwired observer; no
actionable finding. Static review, no independent test rerun or live approval.
Next proof requires approved read-only authenticated verification on the actual
target host/session and an explicit portfolio-to-account namespace contract.
Do not synthesize a global account identity from this response.
