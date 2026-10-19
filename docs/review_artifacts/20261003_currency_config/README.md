# Malformed-config currency correction

State: ACCEPTED_WITH_RISK by explicit human approval on 2026-10-03.
Recording role: GATE. This is human acceptance, not same-thread independent review.
Accepted patch SHA256:
`9b0c48f4b3bc24169ca84b03b08dc638d9087ad78fdde3adb7255c4153d81ba4`.
Scope: this bounded correction only, not the entire upstream series, merge,
deployment, campaign/config changes or account-history mutation.
Base: 97c24c8e4 plus rev23 numbered patches 0001-0010 then 0012.
Do not apply held 0011. This is a follow-on patch, not a complete series.

`correction.patch` changes only the paper engine config read and tests.
The strict loader and mapping checks distinguish malformed configuration from
valid absence. Invalid config sets the existing currency-invalid flag; new and
resting buys are refused. The currency gate continues to exempt sells.
Existing missing-key and explicit-null currency compatibility is preserved;
the different explicit-null policy in 0009 is not silently changed here.

Proof, VERIFIED_ENV: /tmp/cryptkeep-rev23.ASs8Gh, Python 3.12.
Run with PYTHONDONTWRITEBYTECODE=1 and PYTEST_DISABLE_PLUGIN_AUTOLOAD=1:

```sh
python -m pytest -q -p no:cacheprovider tests/test_review_currency_config_failure.py tests/test_paper_engine_currency.py tests/test_paper_equity_marking.py tests/test_paper_engine_honesty.py tests/test_paper_engine_integration.py tests/test_paper_engine_limit_and_status.py tests/test_paper_engine_live_equivalence_honesty.py
```

182 passed in 4.05s. Seven new regression cases cover malformed YAML, invalid
root/section, unreadable file and restart handling of pending buy versus sell.
Earlier two review probes failed before this correction. Broader tests initially
failed because old loader mocks lacked the strict keyword; the patch updates
those mock signatures, not their expected behavior. Reverse apply check passed
against the corrected isolated tree.

No full-suite, CI, running campaign or Hetzner proof. On malformed configuration
the engine retains its existing default settings to stay available for exits;
this is not proof of correct exit fees/accounting under corrupted config.
Missing configuration still follows the loader's existing absent-file behavior.
Historical cash provenance and off-currency sale conversion remain unresolved.
No main production source, account, config, service or deployment changed.

Human acceptance leaves the documented risks unresolved. Integration still
requires checking the actual target tree and dependencies; the approval is not
evidence of full-system behavior or profitable trading.
