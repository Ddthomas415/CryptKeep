# Same-session portfolio binding checkpoint

Active role: ENGINEER. Unwired isolated coordinator only.

Contract: Coinbase production trading scope is represented by venue=coinbase,
environment=production, account_id=coinbase-portfolio:<portfolio UUID>, and
portfolio_id=<portfolio UUID>. account_id here is explicitly a trading-scope
namespace, not a global user/legal account identity. No existing records are
relabelled to this namespace. Credential rotation does not define identity.

SHOWN: coordinator observes portfolio permissions through the exact same session
object used to fetch the order. Observed context must equal existing database
binding. It creates no binding. It rejects unsupported REST/hostname override
before requests; scope mismatch rejects before order fetch. Read-only keys can
read receipts without granting submit authority. Session lifetime stays with
caller. Production execution does not import this coordinator.

VERIFIED_ENV: existing interpreter, isolated source and temporary DBs; simulated
sessions. Eight-file prototype slice: 81 passed in 1.65s, exit 0. New test file:
tests/test_coinbase_bound_receipt.py. No real private request in this stage.

UNVERIFIED: trusted factory must ensure credentials/config do not mutate during
the operation. Same object and endpoint checks alone cannot authenticate a
malicious session, prevent custom transport overrides, or prove remote holdings
ownership. All legacy writers, remote reconciliation and live integration remain
unimplemented. No existing DB/credentials/config/accounts/collectors changed.

Acceptance: READY_FOR_INDEPENDENT_REVIEW; Hume requested.
Independent outcome: Hume ACCEPTED_WITH_RISK, bounded unwired coordinator; no
actionable findings. Static review only, tests not independently repeated.
Next: consolidate prototype into one independently reviewed handoff, enumerating
remaining production integration requirements; do not silently bind old state
or keep claiming that simulated proof is live authority.
