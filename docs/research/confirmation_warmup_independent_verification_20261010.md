# Coinbase warm-up independent verification

Role: AUDITOR. Scope: read-only verification of the separate session's warm-up freeze.
Acceptance: ACCEPTED_WITH_RISK for content readiness only; no activation or scoring.
Environment: VERIFIED_ENV, repository Python virtual environment.

SHOWN:
- BTC/USD, ETH/USD, SOL/USD, ADA/USD and XRP/USD each contain exactly 300 validated hourly bars at the registered boundaries.
- Reconstructing the freeze in memory exactly matches the saved manifest.
- Each original 276-bar prefix matches the October 9 preflight hash.
- Plan, strategy snapshot, fee receipt, runner and registration identities match the frozen contract. Registration predates evaluation start.
- Manifest SHA256: `3a2ba0a2414f4211cdd0b2f957cfcec9501272bfd2e0b01642b72b8e25a6ef19`.
- Targeted verification: `./.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_coinbase_confirmation_runner.py`: 9 passed.

The archive was opened read-only. No downloads, simulations, activation, campaign, account or scheduler changes were performed.

Limits: content hashes do not authenticate venue history or prove future collection reliability, execution realism or profitability. This review does not close activation or ongoing evaluation obligations.
