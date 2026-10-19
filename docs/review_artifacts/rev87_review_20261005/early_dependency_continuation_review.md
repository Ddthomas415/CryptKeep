# Early dependency continuation - 2026-10-07

Active role: AUDITOR. Overall review INCOMPLETE. Full-content reading and
bounded source tracing, not renewed acceptance of the series or deployment.

## Current finding

P2, SHOWN: assembled paper-engine numeric validation catches TypeError and
ValueError but not OverflowError at services/execution/paper_engine.py:186-187.
A YAML integer of 10**1000 is successfully parsed as an integer; float conversion
then raises rather than returning an invalid-config refusal. Each of fee_bps,
slippage_bps, starting_cash_quote and max_order_qty reproduces the exception.
The constructor calls _cfg, so a newly created engine cannot initialize under
that input. Actual campaign occurrence and existing-engine behavior are not
verified. This is a narrow remaining numeric-validation gap, not a claim that
all ordinary malformed numeric inputs still break the engine.

VERIFIED_ENV: repository Python, AST-extracted candidate _cfg with controlled
loader/logger dependencies, no production imports or operator-state access.
Command: ./.venv/bin/python -B
docs/review_artifacts/rev87_review_20261005/test_config_numeric_overflow_probe.py
Result: five tests, normal control passes, four safety assertions fail in
0.022 seconds. Separate yaml.safe_load check returned int matching 10**1000.
No whole-engine, full-suite, CI, host or real-account proof. No fix implemented.

Candidate paper_engine.py SHA256:
71f805250d3682ea2ea61ab66cc2f3c9e4ddfe2ac90c2ebe9410bdf47bf8f098.

## Historical versus current contracts

- 0004 retains one-symbol-per-loop dispatch, no cached price reuse after a
  failed fetch, and fresh-fetch price delivery to exits during signal warmup.
  Fetching in the current turn does not itself prove source quote/bar freshness.
  N-symbol cadence and cooldown wall-time effects were already disclosed.
- 0005 counts in-flight strategy buy symbols only, including held/submitting.
  It is not an atomic portfolio reservation across queue/account stores or
  non-strategy producers. Later 0007-0009 add valuation; single-symbol percentage
  limits remain outside that branch. No new concurrent overshoot reproduced.
- 0010 removes wrong-symbol venue-row fallback, retaining exact venue plus
  normalized symbol matching in current tick_reader. Permissive unknown-market
  behavior is a distinct accepted configuration contract, not permission to
  flip defaults. Exact identity matching is not a quote-freshness guarantee.
- 0012 expressly permits off-currency sells and leaves their proceeds in one
  unconverted cash balance. This preserves exit availability, not accounting
  currency integrity. Declaration and historical cash provenance remain distinct.
- 0013 makes unreadable/malformed config block buys without currency-gating
  sells. 0014 only repairs mock signatures. 0015 preserves dispositions while
  reporting a sanitized cause. Later 0040 changes numeric validation, so its
  remaining overflow gap is traced to latest source rather than attributed to
  an unchanged historical constructor. Other gates can still refuse sells.

## Exact full-read artifacts

Paths are relative to the extracted cryptkeep_review_bundle_2026-10-02.

| SHA256 | Artifact |
| --- | --- |
| `711c35f6ef4bbc637ad3050c79ea4870e82c862febdc04f4a6183ce83e7a3ed2` | `9_multi_symbol_fix/0004-fix-act-on-every-configured-symbol-in-the-strategy-runner.patch` |
| `1c2a1363b20fff9c07981f1fcab9717b52225a7ec6e9057c5c6cd4639db81e50` | `9_multi_symbol_fix/strategy_runner_only.diff` |
| `fea9d00379b67e32d55fab689832022f37379f9d6a56418b1b34b681202beedf` | `9_multi_symbol_fix/changes_since_revision_10.diff` |
| `24db9774e4e14b60e4662302f20f06277932f14d66931b86ea0a443d05653e38` | `10_pending_entry_exposure_fix/0005-fix-count-pending-entries-toward-the-concurrent-position-limit.patch` |
| `32bac0dd737cb4a2b132eb0e95b804f91adfcf8af76c5efd70db18b08f9ca0ac` | `10_pending_entry_exposure_fix/production_files_only.diff` |
| `45d896729b60790459e87e07221aedf98daecc91f33facf698770ca115643d7f` | `15_exact_symbol_quotes/0010-fix-price-lookup-returns-a-quote-only-for-the-symbol.patch` |
| `7b2e2ebeca7570de53fb40eca513a0da572b74c35aa0c26f484c7f7ebf63bc26` | `15_exact_symbol_quotes/production_files_only.diff` |
| `52df91c076a86d95f09de813eca6f9620b8489f84ae20a4e89a1c56ffeadde53` | `18_paper_engine_currency/0012-fix-paper-engine-refuses-buys-outside-a-declared-acc.patch` |
| `6d3d287b007a221bbbf0e63bacb9f7246e9c357f15cb77be36c98272a5a1d524` | `18_paper_engine_currency/production_files_only.diff` |
| `7b28e4d7456058bda3b1c7e83875de718f870fafea24d4b90f1e7621734ba89b` | `21_malformed_config_correction_ACCEPTED_WITH_RISK/0013-paper-engine-malformed-config-refuses-buys-Codex-cor.patch` |
| `5f8ada57c766319112c722f86459660fd763fc0de94b3301c8f9c6831e1b0caa` | `21_malformed_config_correction_ACCEPTED_WITH_RISK/0014-tests-paper-engine-loader-mocks-accept-the-strict-ke.patch` |
| `21759140068a6d5ddc3181e8562df6d62a070faef835eb670accc4e1f836579c` | `22_config_error_reason/0015-fix-paper-config-read-failure-reports-its-own-reason.patch` |
| `37f11c056090924318757fb896aae5d6a2f45a2079787eea3df70638ef00bfe4` | `22_config_error_reason/production_files_only.diff` |

Truncated combined output was followed by narrow reads of the missing range;
only complete reads listed above are added to coverage. No production source,
config, accounts, credentials, collectors or deployment changed.
