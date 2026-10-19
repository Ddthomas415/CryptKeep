# Published Snapshot Inventory

Role: ENGINEER. Risk: HIGH evidence integrity. Status: ACCEPTED_WITH_RISK by
separate Hooke review, standalone tool and placement correction only.

The inventory tool records every published, nonhidden top-level JSON file in
one declared snapshot folder. Legacy files are preserved as baseline-only
diagnostics; structurally valid v3 files form the adapter manifest. It does not
read prices to calculate results. Original snapshots remain untouched.

Each subsequent seal must preserve every prior filename, hash and classification;
only new v3 files may be appended. Selection refuses changed/deleted sources or
new files not yet included in a chained seal, so it cannot quietly choose a subset
of the sealed directory inventory. Parent seal hashes bind the immediate lineage.

Example from the repo root, after implementation review:

```sh
./.venv/bin/python -B scripts/research/cmc_snapshot_inventory.py \
  --snapshots docs/research/cmc_trending_log/snapshots \
  --output docs/research/cmc_trending_log/inventory_baseline_20261010.json
```

On later runs use a new output filename and `--previous` with the last seal.
Never overwrite a seal or use a new baseline to conceal a mismatch. No automatic
schedule or folder permission changes are introduced. A seal must live outside
the snapshot folder, and outputs use exclusive creation.

`verified_manifest(seal_path, now_ms=...)` checks current folder contents against
the seal and returns all sealed v3 entries in the exact format accepted by the
bounded adapter. It does not evaluate the study or grant scoring permission.
Use after the fixed maturity boundary only for operational study evaluation.

Limits: the first baseline cannot recover files omitted before it existed or
prove capture timestamps. Neither hashes nor parent links authenticate a venue
or protect against replacement of the entire evidence chain. Preserve seal hashes
in the work log or an independent record; no immutable external anchor exists here.
Two matching scans detect observed changes, not an atomic filesystem snapshot;
concurrent writers and changes after verification remain integration risks.
Hidden pending files are unpublished reservations, not counted as evidence.

Verification: seven inventory tests plus twenty adapter/calculator tests pass;
parent27passed0.53seconds, independent27passed0.51seconds. Review found nested
seal outputs were not rejected; corrected resolved descendant check with direct
and nested regressions. No remaining blockers within scope.

After acceptance, created inventory_baseline_20261010.json: nine published files,
four schema3 manifest entries; five legacy diagnostics preserved but not selected
as primary inputs. Read-only verified_manifest check passed against the folder.
Baseline SHA256: a3c9ad9afa297c67b00a8485d3fe8949f20b1a4f79b53b7e00c320da0d9274ad.
No market evaluation performed. This locally recorded anchor is not immutable
external evidence or retrospective source-authentication proof.
