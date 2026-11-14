# Exit-unblocked variants: source and synthetic verification

Bot relation: BOT_RULES; runtime configuration not checked. Checked 2026-11-14T16:51Z.
Stages: ENGINEER implementation, then separate Nash GATE. Source status: ACCEPTED_WITH_RISK
(Nash, 2026-11-14T16:53:05Z), source/synthetic scope only. Overall engineering item 4: INCOMPLETE.

## Result and scope

SHOWN: three separate opt-in presets now return raw SELL signals before entry-quality filters:
`breakout_exit_unblocked`, `ema_cross_exit_unblocked`, `mean_reversion_exit_unblocked`.
Only literal Boolean `False` enables the bypass. Absent/True retains current behavior; malformed parser inputs
are rejected, and malformed direct or registry calls cannot accidentally bypass filters. BUY filtering, raw
observer output, indicators and runner exit controls are unchanged. Registry forwards the flag only when present.
Config parsing preserves it. The variants retain their underlying strategy names and all risk settings.

SHOWN: all eleven existing preset dictionaries match the preserved before-source; the three defaults also have
fixed canonical-JSON SHA256 assertions. Deep-copy tests prevent shared variant/default dictionaries. The source
diff is six files, not a runner change. `before/` preserves those exact original files and checksums;
`SOURCE_SHA256SUMS` binds the final six sources, tests and unchanged runner/indicator/filter dependencies.
The previously accepted delivery archive is unchanged and does not contain these new variants.

## Verification and correction history

- Before implementation: new suite 46 failed / 10 passed in 0.55s. Breakout/mean-reversion rejected the new keyword,
  EMA ignored it, presets were absent and config/registry did not propagate it. This is feature-regression proof,
  not an economic test. A runner-test call's missing helper arguments was corrected before its green run.
- Initial consolidated run: 205 passed / 1 failed. The newly added flat-series HOLD fixture was wrong because the
  existing RSI convention produces a SELL there. Only the fixture was corrected, with explicit nontriggering RSI
  thresholds; no original RSI behavior or trading parameter changed. Then 206 passed in 6.41s.
- Independent Nash review blocked initial acceptance: `bool(0)`/`bool([])` could accidentally enable bypass, and a
  direct `None` call also bypassed. The correction narrows the new flag only; unrelated Boolean handling is unchanged.
- Added 24 malformed-value regressions: all 24 failed before the correction; after it the consolidated suite is
  **230 passed in 6.60s**, no failures, errors or skips. Final new-test suite contains 80 cases.
- Coverage includes every post-decision filter individually, for both SELL and BUY, observer/indicator/reason parity,
  insufficient-history/HOLD behavior, exact preset isolation, parser/registry plumbing, real runner pure preset and
  exit-policy resolution, explicit True override, disabled strategy, and 2,175 deterministic synthetic prefix cases
  comparing complete default outputs and observer events with preserved before-source. Five price scales are not
  five real markets. The Donchian confirmation branch uses injected context for branch isolation; a valid break
  already confirms direction. No market observations or profits are manufactured by these fixtures.

Reproduce from the repository root in the existing venv (VERIFIED_ENV for these offline commands):

```sh
env PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_exit_unblocked_variants.py tests/test_strategy_filters.py \
  tests/test_strategy_config_tools.py tests/test_strategy_registry.py \
  tests/test_strategy_runtime_runner.py tests/test_managed_strategy_parameter_isolation.py \
  tests/test_ema_cross_adapter.py tests/test_ema_parity_regression.py \
  tests/test_ema_unification_regression.py tests/test_ema_cross_runtime_invalidation.py \
  tests/test_ema_strategy_cfg_defaults.py tests/test_ema_runner_risk_defaults.py \
  tests/test_breakout_runner_exit_stack.py tests/test_managed_exit_policy.py
shasum -a 256 -c docs/review_artifacts/exit_unblocked_variants_20261114/SOURCE_SHA256SUMS
git diff --check
```

No full-suite, application startup, archive replay, market HTTP, runtime configuration, credentials/accounts,
cache/ledger, service/scheduler, SSH/host, R10/tool/cloud, deployment, trading, commit or push was performed.
Existing unrelated worktree edits remain intact. Independent correction review accepted source/synthetic scope:
80 new tests passed in 0.90s; ten current seals and six original snapshot seals passed. See
`INDEPENDENT_REVIEW.md`; the author's 230-pass consolidated run is not an independent full-suite result.

## Requirement disposition and remaining evidence

- DONE, independently reviewed source scope: three opt-in source variants; unchanged defaults and BUY gates; strict Boolean
  boundary; configuration/preset/registry plumbing; synthetic source-parity and existing focused regressions.
- NOT DONE: section 4's historical action-sequence default parity and S/R market-archive comparisons, per-trade CSVs,
  after-cost metrics, drawdown and in-market-share comparisons. Original requirements remain; this source increment
  does not replace them. No return, edge, economic improvement or execution-readiness conclusion follows.
- NOT DONE: paper/live selection, deployment or current runtime equivalence; these are separate decisions.
- SHOWN correction: the specification reused -$15/+$28/+$65 estimates that November 3 explicitly WITHDREW for wrong
  original-quantity accounting. The dated specification addendum corrects this without changing saved results.
  Original specification SHA256 before addendum: `20b8e334f818186cc65fe07fc857dd26e5260cb51be22fcefec1b9cf3dde8b09`.

Open questions: does unblocking improve net results or merely increase turnover; how do signal-only and modeled
runner-stack arms differ; does actual runtime configuration select these defaults; what changes under forming
candles, missing observations and executable fills? None is answered by unit tests. Mean reversion's raw sell still
requires its existing overbought/above-SMA condition; this does not add a loss exit. Current evidence supports only
the declared source behavior. R10 remains STOPPED and the simulation work remains preserved, not replaced.

What do I know that could change the owner's decision that I have not yet said? Earlier financial expectations
were withdrawn; source-correct unblocked exits may still perform worse after fees. The next economic answer needs
the retained historical S/R comparison, not more source hardening or an automatic paper/live promotion.

## Dated historical closeout - 2026-11-14T17:13Z

The owner separately approved that historical comparison. It completed once on unchanged frozen data and
passed separate Nash result review17:12:59Z ACCEPTED_WITH_RISK. See
`docs/research/exit_variants_spec_20261114/HISTORICAL_COMPARISON.md` and `HISTORICAL_REVIEW.md`.
Engineering item4 source/offline scope is now complete; earlier INCOMPLETE/NOT DONE labels above remain as
dated source-stage history. Original source/test pins and defaults remain unchanged. No variants promoted,
runtime configuration inspected/changed, deployment, paper/live activation or R10 authority.

What do I know that could change the owner's decision that I have not yet said? All60 unblocked historical
symbol/model/cost cases lost after costs; correct source behavior is not evidence of economic advantage.
