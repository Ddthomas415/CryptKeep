# Shared Submission Review - 2026-10-04

Active role: AUDITOR. Objective: reconcile the conversation and shared artifacts,
including revisions 42-48, without changing trading, configuration or accounts.
Acceptance state: INCOMPLETE.

## Coverage and limits

SHOWN: the inventory contains 68 readable files: 45 ZIP archives, 17 pasted-text
attachments, one DOCX and five XLSX workbooks. The archives contain 4,653 file
occurrences representing 279 distinct byte contents. ZIP member reads completed
with integrity checks and SHA256 hashes. This establishes readability and
deduplication, not correctness or exhaustive semantic review.

Inventory and reproducer:
`docs/review_artifacts/shared_submission_review_20261004/inventory.json` and
`inventory_shared_files.py` in that directory. No attached executable was run.

The standalone document text and workbook contents were inspected. Historical
handoffs were selectively read and reconciled; all seven new revision READMEs
and their production diffs were inspected. The latest reference-price patch was
also read with its tests. Historical command transcripts, all earlier patch/test
variants, the complete 42,325-line archived work log, raw monitor records and
the copied SQLite state have not received exhaustive semantic review. Parsing
an entire data file is not a review of every record.

Two specialist reviews failed at their usage limit. The narrative specialist
returned partial coverage, explicitly INCOMPLETE. Its stale assertion that
0029/0030 were unreviewed is superseded by the local rev41 review record.
No missing supplied file was found. Gaps in revision numbering do not establish
that the user omitted a file.

## Material reconciliations

1. SHOWN: the default development runtime config path is
   `.cbp_state/runtime/config/user.yaml`, not `config/user.yaml`.
   `services/os/app_paths.py` supplies that path;
   `services/admin/config_editor.py` and `services/config_loader.py` use it.
   The latter overlays runtime values on `config/trading.yaml` for its default
   loader. The inspected runtime file disables live execution. Earlier advice
   based on the repo user.yaml's enabled flags used the wrong authority.
   UNVERIFIED: running-process environment overrides, alternate config arguments
   and Hetzner. This does not exclude live submission on all surfaces.
2. The user's $1,000 monthly funding limit is not interchangeable with $1,000
   static invested equity or a $10,000 isolated paper seed. Economic reports
   must identify capital deployed, monthly additions, fees and marginal
   infrastructure cost separately. Existing fee scenarios are scenarios, not
   current account commission proof or expected annual profit.
3. Preserve the accepted completed-daily-close SMA200 crossover contract.
   Historical suggestions to enter whenever eligible or reset a cohort are
   not authority to change it. Different backtests and paper strategies have
   different exits, sizing and gates; their returns are not interchangeable.
4. Backlog item 29 preserves permissive code defaults pending a strict campaign
   config and an observed cycle. The 2,304-check historical look-back is not
   that cycle and is signal-time, not universal order-time evidence.
5. The host is shared by multiple research campaigns. One strategy's economics
   cannot be charged the entire host cost without an allocation contract, nor
   does its failure authorize shutting down shared capture.
6. Original intelligence capabilities remain agreed scope: source discovery,
   news/events, web/archive context, time-aware memory and adaptive research.
   Recovery unit tests do not prove ingestion-to-storage-to-retrieval operation.

## Revisions 42-48

The new patches are 0031-0037. The candidate series now contains 35 applied
patches when 0011 is held and superseded 0019 is excluded. The earlier rev41
ledger is therefore not acceptance of the entire new candidate. These seven
patches have no independent acceptance established by this audit.

| Patch | Static review boundary / remaining proof |
| --- | --- |
| 0031 | Stale-lock reclaim serialization covers participating guarded callers, not mixed old/new starters. Windows fallback lacks that serialization. Collector cleanup exists for other components; its normal strategy-runner startup does not use that cleanup, so a runner bypass there is not established. |
| 0032 | Sample developer state is isolated by the Make target; explicitly supplying the canonical state directory remains possible. Historical rows are not retroactively proven clean. |
| 0033 | Sample snapshot rejection changes the reader contract. Unknown provenance remains permitted; explicit development opt-in and downstream behavior need independent verification. |
| 0034 | Fill provenance propagates selected fields. Missing provenance still qualifies; this is not proof of historical authenticity. |
| 0035 | Journal matching checks coverage/count consistency. It does not establish matching prices, fees, quantities or fee-currency conversions. |
| 0036 | Retirement reporting exposes mismatch without changing trigger policy. Kernel per-fill expectancy and research per-round-trip expectancy are different denominators. |
| 0037 | Finite positive reference-price selection prevents the described zero-notional estimate at that gate. Helper/fake-queue tests do not prove end-to-end live submission. Downstream bid/ask-only handling and the separate paper notional issue remain boundaries. |

CLAIMED: rev48's cloud Python 3.12.3 full suite has 4,480 passes and the same
19 failures as its historical master baseline. This audit did not reproduce
that suite, apply the full series, run CI, inspect Hetzner or execute live paths.
The supplied historical baseline is not necessarily the current local HEAD.

Legacy manifests and handoff tables are append-only and stale in places. Use
patch-specific review records plus a current series ledger; neither a passing
probe nor a later correction silently accepts all prior revisions.

## Next bounded action

Complete independent review of 0031-0037 on an isolated reconstructed rev48
tree, starting with 0037's reference-price consumer boundaries and 0031's lock
participants. Reproduce targeted regressions and distinguish inherited risks
from introduced regressions. Do not add another corrective patch merely to
avoid a review checkpoint. Historical unread coverage remains explicitly open.

No merge, push, deployment, collector start, config change, account mutation or
promotion is authorized by this document. Only audit artifacts were added;
pre-existing checkout edits were preserved.

## Isolated verification follow-up

SHOWN: all 35 selected numbered patches apply with `git apply` to an archive of
97c24c8e4 in `/private/tmp/cryptkeep-review48.L67K5O`. After initializing the
isolated Git repository, its tree hash is
`def09f9cdfe50863740b1073b4aa1b00596a98e7`, exactly the declared rev48 tree.
This proves file-tree identity, not author commit identity or deployment.
No main-checkout code changed.

VERIFIED_ENV: local Python 3.12.10. Command in the isolated tree:
`/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_consumer_notional_reference_price.py tests/test_strategy_runner_lock.py --tb=short`
Result: 44 passed in 4.97 seconds. The lock tests include real child processes;
the notional tests exercise helpers with a fake queue, not exchange submission.

The first full run finished with 4,460 passed, 35 failed and 33 skipped in
125.94 seconds. This run is not a valid regression comparison: the archive
checkout lacked Git metadata and contained an extra top-level `bundle`
directory, causing repository-structure and Git-dependent failures. Patch
files were moved outside the tree and a local Git repository was initialized.
The failed-check rerun completed: 34 passed, one failed in 245.05 seconds.
Command: the same Python interpreter, `-m pytest tests -q --lf
--disable-warnings --tb=short`. The remaining failure is
`tests/test_manual_repo_audit_paths.py::test_manual_repo_audit_writes_required_artifacts`:
the audit script records Git status and log exit 126. No financial-path test
failed in these runs. Do not combine reruns into a fictional single green run.

A separate unmodified archive of 97c24c8e4 completed the full suite with 3,784
passed, three failed, 33 skipped in 291.33 seconds. Its missing Git metadata
caused gitignore, manual-audit and supply-chain checks to fail. Consequently
this is not equivalent to the cloud's claimed 19-failure environment, and no
matching cloud baseline is independently established here. The candidate's
remaining manual-audit failure is also present in this local baseline.

SHOWN by source trace: the live consumer's notional helper uses `price_used`,
but its downstream router override still uses `limit_price or last or 0`.
The router rejects missing/invalid reference prices. Thus bid/ask-only market
quotes can pass the revised cap claim yet be refused downstream. This is a
remaining boundary, not proof of an exchange fill or complete path repair.

The original five-system/intelligence attachment was read through all 1,294
lines during this follow-up. Its SQL, Docker and build prompts remain reference
material, not authority to replace the existing repository. It explicitly
preserves archive/live/future-event retrieval, user explanations and disabled
execution for the research copilot. Its illustrative confidence numbers and
causal explanations are not calibrated evidence.

## Remaining newer-patch test slice

SHOWN: local Python 3.12.10, isolated reconstructed rev48 tree. Command:
`/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_paper_run_short_isolation.py tests/test_ohlcv_snapshot_provenance.py tests/test_sample_snapshot_not_research_data.py tests/test_fill_provenance_fields.py tests/test_paper_gate_journal_evidence_match.py --tb=short`
Result: 50 passed in 0.97 seconds. This is separate from the earlier 44-test
slice; neither is an end-to-end deployment or profitability test.

The tests preserve unknown/bare-list snapshots and legacy fills without the new
fields. They reject explicitly identified samples and flagged mismatches, not
every historically untraceable record. The fill propagation test uses the real
paper engine with mocked price/config/gates/logger; it is stronger than a source
string check but does not establish real venue or archive provenance.

Patches 0035/0036 withhold or qualify expectancy when journal coverage disagrees.
Count matching still does not independently verify execution prices or fees.
These limits must accompany any economic or promotion claim.

Next unresolved acceptance work is the current series ledger's historical
supersession/acceptance gaps (including applied 0017/0018 and journal wiring),
not another broad suite rerun. Passing tests here do not manufacture the missing
review decision. Historical transcript/work-log coverage remains open.
