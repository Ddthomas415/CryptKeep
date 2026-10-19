# Owned Coinbase receipt lifecycle checkpoint

Active role: ENGINEER. Unwired one-shot lifecycle in isolated candidate.

SHOWN: existing private-session factory/shared credential loader is reused;
wrong database context refuses before construction. Raw session is not returned
or accepted from caller. Local synchronous operation observes portfolio and
fetches order on that session, then attempts closure in finally. TLS verification
must be enabled, verbose private transport disabled, and inspected proxy fields
unset. Timeout fixed20s. Cleanup failure reported as a sanitized error.
No automatic binding, settlement, credential writes or order submission.

VERIFIED_ENV: existing interpreter and isolated files/temp DBs. Factory/session
test doubles; nine-file slice89 passed in2.18s exit0. No actual private request.

Durable delta (apply only to isolated original13file package):
docs/review_artifacts/spot_exit_account_prototype_20261007/lifecycle_delta.tar.gz
SHA256 e38a94f7b94ea941c30ca0bfb199d276efb4ae20e81a8036c1771c277bbeb0c0.
LIFECYCLE_SHA256SUMS covers the two new files; original archive remains unchanged.

UNVERIFIED: actual factory-to-coordinator integration, authentication on target
host, historical ownership, all production writers, mutable transport plugins
or hostile in-process code. No guarantee against privileged session mutation.
Earlier real permissions observation is not this lifecycle's integration proof.
No production gates/config/accounts/collectors/deployment changed.

Acceptance: READY_FOR_INDEPENDENT_REVIEW; Hume requested.
Independent outcome: Hume ACCEPTED_WITH_RISK, bounded unwired wrapper; tests and
archive not independently rerun/verified. Implementing agent verified both delta
file hashes after extraction. Cleanup failure can occur AFTER receipt commit;
an exception is not rollback evidence. Retry uses immutable receipt semantics.
