# Bounded Confirmation Collection

Purpose: replace five manual downloads and a separate hashing step with one
foreground command. This is research data maintenance, not a profitable strategy
or a new statistical method. Frozen strategies and evaluation dates stay unchanged.

From the repository root, inspect without network access or archive writes:

```sh
./.venv/bin/python -B scripts/research/collect_confirmation_batch.py \
  --plan research/coinbase_confirmation_usd_v1/plan.json \
  --archive research/coinbase_confirmation_usd_v1/public_archive.sqlite \
  --registration research/coinbase_confirmation_usd_v1/registration_20261009.json \
  --previous research/coinbase_confirmation_usd_v1/collection_prefix_20261010T180000Z.json \
  --output research/coinbase_confirmation_usd_v1/collection_batch_NEW.json
```

For ingestion, add `--collect`, choose a new output filename, and use the latest
successful checkpoint as `--previous`. At most 24 completed hours per market are
requested, with one public request per market. `--max-hours` can reduce that bound.
There is no scheduler, persistent process, private credential use or scoring.

The command verifies frozen source identities, preregistration and prior prefix
hashes before ingestion and again afterward. It requests only missing timestamps
and ignores fetched rows outside that set. A successful output is a content
checkpoint, never proof of phase completion, exchange authenticity or fills.

Failure returns an INCOMPLETE artifact and nonzero exit status. Preserve it. Retry
using the same prior successful checkpoint and a new output filename: existing
bars are not requested again. Interrupted reservations remain INCOMPLETE; inspect
them rather than overwrite them. Cooperating copies use an archive-specific lock;
other archive writers do not honor this lock and must not run simultaneously.
No claim of power-loss durability or automatic restart recovery is made.

Implementation proof: ten targeted tests passed locally and independently.
Separate reviewer accepted the wrapper and tests WITH RISK after the alias-lock
correction and a successful test through the real archive-writing implementation.
Actual public-network ingestion has not been run with this wrapper.
No production or campaign integration is authorized by this workflow.
