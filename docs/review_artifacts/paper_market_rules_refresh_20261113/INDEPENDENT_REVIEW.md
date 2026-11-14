# Independent paper metadata provisioning review

Bot relation: BOT_RULES. No runtime configuration, market capture or operation
verified. Reviewer Nash did not author or modify the implementation.

Plan review2026-11-14T04:59:23Z: ACCEPTED_WITH_RISK, plan only. Required branch
before ambient resolution, all-input prevalidation, scope separation, persisted
cash-reader usability and explicit path-stability assumptions. Source/readiness
was not accepted at that stage.

Final review2026-11-14T05:13:20Z: ACCEPTED_WITH_RISK, paper-opt-in source and
synthetic scope only; no material blocker. Includes the later native precision
correction in the opt-in path, not a default/live-provider change.

Reviewer independently confirmed installedCCXT4.5.48/TICK_SIZE4/native fields;
flag propagation, native increment handling/agreement/representability and
unchanged defaults were inspected. Independently47tests passed0.40seconds:

```sh
./.venv/bin/python -B -m pytest --noconftest -c /dev/null \
  -p no:cacheprovider -q tests/test_refresh_paper_market_rules.py
```

Reviewer reports private temporary state and disabled plugin autoload. No HTTP,
credential/account/service/scheduler/host or source-edit action by reviewer.
Author138-case result is not independently reproduced as a complete selection.

Accepted hashes, matched against current files at2026-11-14T05:15:07Z:

```text
380bc2514fcd81f2833e884328dea752d9a38c50371d49be02d7fe1bab668c24  scripts/refresh_market_rules.py
58d3e100fb432b6ab94b2571ddc3fba5e3a21449785dc58723c9cb35b22be01e  services/execution/paper_cash_entry.py
1223d6ddc12b0b6cf4c83bf399fcadb7e5c515dbf3c3a5863244dc3cf7519a87  services/markets/rules.py
c6d3f3fdccee920169ec7b404189db067937069ddecca7cd74cfd6235d154810  services/markets/fetch_coinbase_ccxt.py
b3f88866dba6223ba71f61b0bbbc12ffb1699695d57e68ed38ca4129bf247665  tests/test_refresh_paper_market_rules.py
```

Risks retained: trusted foreground path stability; no verified network deadline,
actual product availability, operating profile or periodic refresh. Legacy/global
precision defect remains unfixed. No full-simulation or commissioning acceptance.

What do I know that could change the owner's decision that I have not yet said?
This source acceptance does not apply to the old/global precision path and does
not certify an actual provider response or account's current cache.
