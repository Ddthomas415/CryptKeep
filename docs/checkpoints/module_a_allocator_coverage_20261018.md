# Module A allocator causality coverage

Date: 2026-10-18. ENGINEER stage, test-only follow-up to GATE-MA-001.
Objective: persist the actual-allocator prefix probe and its look-ahead canary.
Implementation proof complete; subsequent separate GATE accepted the appended
test coverage and closed GATE-MA-001. Test-only disposition: ACCEPTED.

SHOWN: only appended to `tests/test_module_a_candidate.py`; existing test prefix
reconstructs to its previously reviewed SHA256
`0a6e2422be327f53f5927df5ada2f93a9ccaca1adb3c57cd36313982d420fd9d`.
Current complete test SHA256:
`8939cbc7c3da3ce49b170af411c112e75154c86778e172a7261831c7ca4e3a03`.
Unchanged simulator SHA256:
`bd7139ff115efd743239a26f6d31be09766d622f90b8c1d89e449de958e6477c`.

The four persistent cases use seeded synthetic prices for four assets and invoke
the actual `module_a_target`/`trailing_vol`/`capped_weights` path. Both weekly
Sunday-close and daily-fixture schedules decide at cutoff12. Prices at opens
and closes strictly after that cutoff are replaced independently.

- Current allocator: NAV, target decisions including the cutoff decision, and
  fill/cash/holding trace through the cutoff are unchanged.
- Deliberately next-day allocator: earlier decisions and NAV through the cutoff
  remain equal, but the cutoff target differs. Comparing NAV alone misses it.

VERIFIED_ENV: isolated local synthetic pytest, exit0, **56 passed in2.96s**:

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
  tests/test_module_a_candidate.py tests/test_harness_contracts_wp4.py \
  tests/test_corrected_research_math.py
```

No financial source, original draft, study, threshold, data or trading behavior
changed. This closes a regression-coverage gap, not a demonstrated current leak.
Prior review and SHA256SUMS remain preserved as point-in-time evidence of their
earlier test bytes; this checkpoint identifies the new test version explicitly.
The new separate review is `allocator_prefix_review.json` in the same
information_edge_repair_20261018 artifact directory. Earlier scoped acceptance
does not automatically accept changed tests.

Separate reviewer `01a15057-2395-77d2-93f9-d1b0b4649a8d` verified exact hashes,
prior-test-prefix identity, cutoff indexing and actual allocator call chain.
One independent targeted invocation with the command above restricted to
`tests/test_module_a_candidate.py -k actual_allocator` returned exit0,
**4 passed,22 deselected in0.18s**. No blocking findings. Review SHA256:
`1ee4000a1b296db365b60e96726bfb771ba4b629c0c841d4395f8faf9a3100d9`.
This acceptance closes only the named test-coverage gap; the earlier financial
source disposition and its other limitations are unchanged. Reviewer closed.

No market-data run, source/latency scoring, Module A activation, full-harness
integration, actual profitability, service startup, credential access, cleanup,
Git-lock removal, commit, push or scheduled-task change occurred. Broader Module A
contract, benchmark, historical parity and integration remain INCOMPLETE.
