# Independent count review

Reviewer: Hegel, separate GATE subagent
`01a15187-d8bb-71c1-8bfb-095bd45e4bac`. Disposition: ACCEPTED_WITH_RISK.
No blockers for the bounded offline counting utility and these frozen results.
This records the separate review, not an implementing-thread self-approval.

SHOWN: separate recomputation without importing the counter or reopening the
source SQLite database matched every numeric/date field in all six groups and
historical summaries. Counts: funding 13,781; basis 13,778; OI 10,449; Coinbase
quotes 14,057; Kraken quotes 14,053; Coinbase books 10,449. Excluded sample rows:
3 funding, 3 basis, 6 quotes. No invalid counted rows or duplicate group capture
timestamps. Independent forward sweep matched 10,431/14,057 quote timestamps;
only preceding/equal contexts were used, with maximum allowed age 300 seconds
and observed matched ages 0-230 seconds. No timestamp exceeded capture time.

Historical BTC 7,770 and ETH 7,536 unique funding timestamps, with no duplicate
or conflicting records. Missing mark-price counts: 4,536 and 4,302. All day,
spacing and gap statistics matched. These are capture observations and
settlement-timestamp records, not independent trade opportunities or payments.

VERIFIED_ENV, exit 0, 11 passed in 0.18s:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_information_evidence_counts.py
```

Reviewed hashes, unchanged before/after:

| Artifact | SHA256 |
| --- | --- |
| counter | `41dd0a1cd2d7f82b0f38e66204ca41703811cdbb6b4b6400b0fc7afedaeabf62` |
| tests | `8d2dff36b0d6c230f28db371d49abc7db1e159617a8a0b5e866390497527e4b0` |
| projection.json | `780bfc99746cb69f17b715240930d083c3e6acbb53b1869930ef6ac87b263021` |
| counts.json | `6efa228fcbb744a509a01a652d63cedba1a410b81629d584beb34368e2eacb12` |
| original funding JSONL | `15edda37d3119f1cdadcbfa8ec10ed938fe359c9dd89e920384471bd167db3a9` |

Residual risks: the parser coerces floats/ints and does not strictly reject all
boolean/fractional malformed inputs. Exact frozen records passed independent
finite-rate and positive-integer timestamp checks. Basis prices are validated,
not days_to_expiry; mark absence is counted, not general mark validity. Code's
read-only mode/query_only/one transaction and fixture tests do not independently
prove concurrent live-WAL behavior or the parent's capture execution.

No reviewer edits, network, services, credentials, Git mutation or strategy
execution. No strategy, profitability, arbitrary-future-input or operational
acceptance follows.
