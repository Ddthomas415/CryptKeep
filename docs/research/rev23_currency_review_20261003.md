# Rev23 bounded review

Active role: AUDITOR. Environment: VERIFIED_ENV, isolated checkout only.
Acceptance: INCOMPLETE. Patch 0012 is not accepted pending the finding below.

## P1 - Invalid configuration disables the currency refusal

SHOWN in rev23 services/execution/paper_engine.py:61-83: _cfg calls the
non-strict YAML loader and replaces a non-mapping paper_trading section with
an empty mapping. Both paths produce quote_currency_declared=false and
quote_currency_invalid=false. _currency_refusal then returns None for a buy
in ADA/EUR. A malformed previously declared account can therefore lose this
check on restart. Other order gates may still refuse the order; this finding
does not claim an actual fill or live submission.

Two independent regression probes in
/tmp/cryptkeep-rev23.ASs8Gh/tests/test_review_currency_config_failure.py fail:
one uses the real YAML loader with malformed YAML, the other supplies a
non-mapping section. Both expected a currency refusal and received None.

Required correction: distinguish valid absence from unreadable/malformed
configuration. Fail closed for exposure-increasing buys without making this
currency gate block protective sells. Test malformed YAML, unreadable config,
non-mapping root/section and valid undeclared compatibility. Review separately
the explicit-null policy: 0012 treats it as undeclared, whereas 0009's strict
currency reader rejects it. Do not silently widen scope or stop protective exits.

## Delivered evidence and limits

- Read the latest pasted continuation and folders 17, 19 and 20 instructions;
  inspected patch 0012 production changes and its supplied tests.
- SHA256 comparison: rev20 to rev21 adds only 0012 among numbered patches.
  Numbered patches are identical across rev21, rev22 and rev23. Prior bounded
  review of 0010 is not erased by stale handoff wording calling it unreviewed.
- Folder 17 now names the runtime config path. It remains a proposal; actual
  child-process state-root selection and observed-cycle proof are not verified.
- Folder 19 is disabled, uses historical 10,000 USDT/7.5 bps assumptions and
  lacks an enforced end date. It is not authorization for capital, launch,
  cohort reset, replacing the laptop campaign or accepting realistic net PnL.
- Currency declaration does not repair historical cash. Off-currency sells
  remain allowed and may credit unconverted proceeds; this limitation is stated
  in the handoff, not newly fixed. Do not call the patch full accounting repair.

## Reproduction

Exported base 97c24c8e4 to /tmp/cryptkeep-rev23.ASs8Gh and applied numbered
0001-0010 then 0012. Excluded held 0011. No main production source changes.
Python: /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python (3.12).
All pytest runs used PYTHONDONTWRITEBYTECODE=1,
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 and -q -p no:cacheprovider.

- tests/test_paper_engine_currency.py tests/test_paper_equity_marking.py:
  153 passed in 3.12s.
- Delivered folder20/test_single_symbol_differential.py, DIFF_OUT pointing
  to review_trace.json in the isolated tree: 76 passed in 9.44s.
- Delivered compare_traces.py against trace_0001-0003.json: 75 scenarios
  identical, 0 different; baseline 132 orders, 0 error scenarios.
- tests/test_review_currency_config_failure.py: 2 failed in 0.24s as above.

The supplied baseline was not regenerated in this turn. Harness substitutes
config, market data, engine and queue; its equality cannot validate 0012's
engine behavior. No fresh full suite, CI, process, host or live integration
proof. External full-suite counts remain CLAIMED. No changes to config,
historical accounts, credentials, services, GitHub or deployment.

Next action: correct the malformed-config buy refusal in 0012 and rerun the
focused tests plus independent review. Do not start a duplicate collector
merely to avoid waiting for review; no need to wait until October 13 to fix this.
