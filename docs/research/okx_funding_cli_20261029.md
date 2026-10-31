# Paired Funding Operator Entry Point

2026-10-29 America/New_York. ENGINEER, HIGH risk: collector startup surface.
Implementation READY_FOR_INDEPENDENT_REVIEW; operating rollout INCOMPLETE.

Delivered a usable existing CLI path, not another independent runner:
--okx-pairs with an explicit options file, native-ID plan, DB/source and raw
journal limits. No flag/default enables this implicitly. Shared batch validator
was extracted without changing capture behavior; CLI uses the same function.
Strict JSON reuses reviewed duplicate/nonfinite/overflow hooks. Bad config,
missing limits and control-flag conflicts fail before any lifecycle action.

--check-config reads only local public config and prints identities, file
hashes, limits and other-stream counts. No DB, PID, status, process or network
operation; runtime/DB ownership remain UNVERIFIED. An actual preview ran twice
(once visibly, once to retain exact stdout), exit0; designated temporary DB
target remained absent. PREVIEW.json retains the captured stdout.

CLI-to-service integration was exercised with fake transport and disposable
SQLite. Paired exit status is nonzero for failed cycles or already_running,
which cannot prove the existing process uses paired mode. Legacy CLI behavior
stays unchanged. The template preserves every original plan family, adding
only the known BTC native ID. No active plan/config/job was edited.

Author isolated11filecommand:304passed2.25s,exit0,8existing slow-marker
warnings because project config is bypassed:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_okx_funding_cli.py tests/test_run_crypto_edge_collector_loop.py tests/test_okx_funding_service.py tests/test_okx_funding_pair_producer.py tests/test_okx_funding_journal.py tests/test_okx_cash_cost.py tests/test_okx_funding_contract.py tests/test_synthetic_funding_observations.py tests/test_funding_receipts.py tests/test_funding_store_bridge.py tests/test_crypto_edge_collector_service.py
```

New tests refuse real transport/lifecycle/default-directory/non-tempSQL; cover
preview side effects, config errors/depth/overflow, flag conflicts, exit codes,
template preservation, validator ownership and CLI-to-real-service handoff.
Not full-suite/live operation proof. Two assumptions: local operator inputs
and injected dependencies follow their interfaces; public data/clock do not
prove freshness or payments.

Existing COLLECTOR_CONTROL.md now contains the exact preview command, first-run
checks and recovery limitations. Source is ready for separate review, not
runtime authorization. Process listing previously failed; actual collector
ownership/DB target remain unverified. Binary trust caveat persists. Other
streams are outside funding limits; preview does not freeze later plan edits.
Store construction may initialize schema, and rollback cannot undo writes.

Six changed/new operator files plus before copies/diff/dependencies are frozen
in docs/review_artifacts/okx_funding_cli_20261029/. No new API, realDB, service,
job, account, credentials, capital/risk, trading or deployment operation.
