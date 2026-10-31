# SB-1: authorized development result

2026-10-27 New York. Active role ENGINEER for the authorized diagnostic run.
Execution complete. Statistical validation INCOMPLETE; no audit or market run.

## Answer

SB-1 has not demonstrated a usable statistical fix. All96planned development
trials completed in16.908430compute seconds, inside the90-second limit, but
25trials abstained because fewer than10effective blocks remained. The strongest
persistence case computed no bounds at all. Zero positives there is NOT evidence
of good error control. The rho0.8case computed12/16paths and flagged2of them.

| Fixed null case | Computable / 16 | Positive lower bound in any contrast | Abstained |
| --- | ---: | ---: | ---: |
| iid Gaussian | 16 | 0 | 0 |
| AR(1), rho0.5 | 16 | 1 | 0 |
| AR(1), rho0.8 | 12 | 2 | 4 |
| AR(1), rho0.95 | 0 | 0 | 16 |
| AR(1), rho-0.5 | 13 | 0 | 3 |
| Common two-state volatility | 14 | 2 | 2 |

Every case is a constructed no-advantage null, not observed market data. The
5positive results among71computable trials are diagnostics, not a calibrated
market error-rate estimate. Sixteen trials per case cannot certify nominal
5%control or power. Do not pool abstentions into a reassuring5/96headline.
The75%and0%availability cases do not meet the proposed audit's80%utility
criterion descriptively; that is not a completed audit decision on512paths.

Do not claim an improvement versus the old7-day pilot's8/32rho0.8positives:
these are different paths/sample sizes and include abstentions. No paired old/new
method comparison or larger audit was run. No method, guard, seed or parameter
was altered to improve the result. The original failed pilot remains intact.

## Explicit Authority

ED002-SB1-DEVELOPMENT-20261027 records the operator's exact choice:
"Accept prototype; run development only (Recommended)". This supplies the human
acceptance route for the submitted prototype and one diagnostic development
attempt, not independent mathematical review or confidence certification.
`authorization.json` pins accepted prototype SHA256
`a152f15f464005dfa2e5c00877074762241ae4b84133575188d8442f0d72f01a`.

Authorized scope was six fixed null cases x16trials, one process, at most90s
computation, no retries/parameter changes. The512-per-case audit, package
installation, market data and trading were explicitly excluded. Nothing here
activates them. Existing economic/25-symbol/carry/one-hour-delay choices remain.

## What Actually Ran

```sh
env -i PATH=/usr/bin:/bin PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B docs/research/ed002_sb1_development_20261027/run_development.py
```

VERIFIED_ENV: one invocation, exit0,96started/96completed method calls. The
runner has15simport,15spreflight,90scompute and5sfinal-receipt limits. Imports
took0.072037s; measured computation16.908430s. Peak process RSS185,483,264bytes
is an observation, not a separately enforced memory ceiling. Configured BLAS/OMP
threads1; socket/process APIs are refused inside the runner. This is not an
OS-wide execution or thread-count certification.

Six declared182-day generators use the frozen data/shock/selector parameters,
stationary Gaussian initialization,1024burn-in observations and the development
domain. Data and supplied-draw streams are separated by case/trial/source identity.
No audit/power-stage seeds or paths were generated. The unchanged prototype was
called once per trial. Source identity includes the frozen runner, authorization,
prototype and plan; no code changed after the attempt began.

Each journal row preserves the synthetic returns, data/draw seeds, input/draw
hashes and complete method result, including abstention reason. The2,599,518-byte
journal has96unique case/trial pairs, exactly16per case. Large raw draw matrices
were not stored; reproducibility uses seeds, source identity and NumPy version.
`ATTEMPT.json`, `trials.jsonl` and `result.json` refuse overwrite/automatic retry.

Results SHA256:
`3c5b2116e43aa6c218513bb63a4f751d55c3243c809e83c3477411e670bf9197`.
Post-run read-only checks verified all96stream seed derivations, journal hash,
source bindings, trial uniqueness/counts and the complete/abstained totals.
No method re-execution was used to verify those records.

## Helper Proof And Boundaries

Before the one real development invocation:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_sb1_development_helpers.py
```

SHOWN:8deterministic helper tests passed0.32s. They checked cases/budget/stream
separation, known recurrences, volatility thresholds, null-arm formula symmetry,
failure/abstention summaries, argument refusal and existing-attempt preservation.
They invoked no real development/audit stage or RNG. The earlier prototype's
32deterministic tests remain prior proof, not a newly rerun result.

All6runner input bindings,14prototype bindings and16old-pilot bindings remained
unchanged during execution. No source/test repair, added dependency, original
artifact/strategy/config/coverage change, private access, service/schedule,
risk/capital/trading, commit or push occurred. New runner code is not silently
accepted for reuse in a later audit; separate review/authorization remains.

Recommendation: do not launch the larger audit as an automatic next step or
relax the ten-block guard using these outcomes. Review the method's availability
and sample-length assumptions before proposing another run. The current stage
is complete as an authorized diagnostic, not as an inference qualification,
strategy-profit result or a rejection of crypto strategies generally.
