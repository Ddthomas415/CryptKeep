# Independent shared Coinbase precision review

Bot relation: BOT_RULES. Runtime configuration/current cache not inspected.
Reviewer: Nash, separate agent, no implementation edits.

Plan GATE2026-11-14T10:36:10Z: ACCEPTED_WITH_RISK, plan only. Required default/
False parity, invalid flag/mode refusal, requested/native/raw product identity,
real cache/validator/quantization tests and explicit alias-cache limits.

Final GATE2026-11-14T10:41:32Z: ACCEPTED_WITH_RISK, source/synthetic scope only;
no material blocker. Confirmed unconditional increment validation, identity
binding, compatibility and preserved historical evidence. Fixture corrections
do not relax production minimums. Alias-cache behavior remains unchanged.

Independent command:

```sh
./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q \
  tests/test_coinbase_shared_precision.py tests/test_refresh_paper_market_rules.py \
  tests/test_coinbase_market_mode_gate.py
```

Result:121passed1.09seconds, private temporary state, plugin autoload disabled.
The author220-case total is separate, not independently reproduced as a whole.
No source edits, real HTTP/cache refresh, accounts or operations performed.

Exact accepted hashes, matched against current files10:43:31Z:

```text
87c0f06cb4f4073eb02e364f014ba74a9c57ae9f16489dfa12632fb0132b3b87  services/markets/fetch_coinbase_ccxt.py
f38340b4def64e2b8bd88d2dcc5c5c059dc6c94f5faef241439b432b907b10bc  tests/test_coinbase_shared_precision.py
8ad264681077cea51a7cf047b0a25c2ea3310dfdaf1e30b0e326ff26448ebbaf  tests/test_refresh_paper_market_rules.py
b50bd71c2d9b212a9ced7d0c2389cd9cc411eb847ad0b0f664dba82c88dedd94  tests/test_coinbase_market_mode_gate.py
```

Reviewer confirms rules/CLI hashes match prior reviewed versions. Existing fresh
cache rows may still carry wrong increments; this source review neither migrates
them nor establishes operational correctness, deployment or trading readiness.

What do I know that could change the owner's decision that I have not yet said?
The old cache may remain in use after a source update; verify actual cache rows
through a separately authorized refresh/read-back before accepting operation.
