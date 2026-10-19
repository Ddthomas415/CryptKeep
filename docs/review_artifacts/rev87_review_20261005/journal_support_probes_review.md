# Journal support probes and wiring supplement - 2026-10-07

Active role AUDITOR. Overall review INCOMPLETE. Sixteen submitted artifacts
fully read; none executed. Quoted scripts are evidence, not operator commands.

## What the probes establish

- The unconfirmed/contradictory-unwritten probes target historical behavior.
  Later candidate apply requires confirmation and confirm rejects unwritten
  contradiction. Do not reopen those defects without contradictory evidence.
- Identifier, note and scope byte-corruption probes test different surfaces.
  Latest unresolved reader preserves damaged identifiers/notes; damaged scope
  holds all scopes. Last turn's isolated checks covered scope and payload,
  not every supplied probe or operator recovery.
- Reducer value probes show that a finite numeric value is not necessarily
  valid for a particular counter. Current journal remains a generic numeric
  store; runner reducer computes the streak as an integer. Accepting 2.5 in a
  direct arbitrary reducer is not proof this runner produces 2.5. Existing
  corrupt streak can still make runner reduction fail; application stays pending.
- Raw surrogate input is distinct from invalid UTF-8 already stored in SQLite.
  quarantine_raw encodes text as UTF-8; arbitrary surrogate-containing strings
  are not demonstrated as preserved by the current isolated tests.
- Several scripts only print anomalies or error counts. The stress and schema
  race scripts print wrong final states/process failures without asserting or
  returning failure for those outcomes. Exit 0 alone cannot prove their stated
  invariants. Their original reported results remain CLAIMED unless reproduced.
- mutate.py assumes /home/claude/work/review_0021 and deletes per-mutation
  directories under a caller-supplied root. No safe local execution inferred;
  inherited environment and path containment are not established. Not run.
- The 7,140-cell supplement explicitly concerns frozen 0022 ordinary paths,
  single symbol, doubles and no fees. Its 87 corrupt-state differences and
  4,697 sells are author-reported, not reproduced here. It does not prove
  recovery, profitability or equivalence of later patches.
- The restart probe clears process-local memory but keeps the harness in one
  process. It is a useful memory-loss specification, not a real restart or
  power-failure test. It is not executed in this slice.

No new current defect reproduced. No source/config/account/runtime changes.
No stress, mutation, runner suite, host or CI execution.

## Exact full-read artifacts

Paths relative to extracted cryptkeep_review_bundle_2026-10-02.

| SHA256 | Artifact |
| --- | --- |
| `0a6e02b9e9d10397acd86b551fb221ffe30a1cf208ed3d297f7c483062acdacd` | `30_review_fixes_0021_0022/reviewer_probes_0021/common.py` |
| `e7b61689426c491cc97e975e27283833a0b00db625a3335257cd639e0bb2db0e` | `30_review_fixes_0021_0022/reviewer_probes_0021/mutate.py` |
| `c9803ae5e111655302d90d60985c2dc5a72eec6f970724fa583f6aff3ea3b6bf` | `30_review_fixes_0021_0022/reviewer_probes_0021/p10_reader_locked.py` |
| `6e1a15cdee57327cbe9325aa08e4a82423c7cc14dd093894dc28122a747da881` | `30_review_fixes_0021_0022/reviewer_probes_0021/p11_counter_type.py` |
| `afc670c53f09aecfb2739e42d3e746f4f1c2e960b2865b85d7f74296028df580` | `30_review_fixes_0021_0022/reviewer_probes_0021/p1_unconfirmed_apply.py` |
| `c3a2a404c7ee83211d40a0edd8df90b2e7d4917d544487e340521cbfa0f7ba61` | `30_review_fixes_0021_0022/reviewer_probes_0021/p2_unwritten_then_confirm.py` |
| `39a45d2dcce2eb34261ea723d226b9f86d6343dc82d024e99680ac55b49e449b` | `30_review_fixes_0021_0022/reviewer_probes_0021/p3_values.py` |
| `16453801aa1bd09f1a3e6c91a51173f9f8aa7e6663e6ca1a6901423275dc3a0b` | `30_review_fixes_0021_0022/reviewer_probes_0021/p4_unresolved_raises.py` |
| `5aca9960aacf0da1286b9c3857e233e3ff3b4d500f0bfc874d84ce3bee893b4c` | `30_review_fixes_0021_0022/reviewer_probes_0021/p5_scope_inputs.py` |
| `a1b202fbf81dd553dc67e5d051211d88c465b5a27dcc2c040929758d2c8edb2c` | `30_review_fixes_0021_0022/reviewer_probes_0021/p6_quarantine_raw_surrogate.py` |
| `1ee74d1f9bbfff1b064a2135efb7d76b82391a3ac5c85b6030404c71dc9d9d94` | `30_review_fixes_0021_0022/reviewer_probes_0021/p7_scope_corrupt.py` |
| `05ab17e06f5799e2736d3aa521cf88caf6e0a46d9614e9eebbc432f98657dd28` | `30_review_fixes_0021_0022/reviewer_probes_0021/p8_stress.py` |
| `f6840daa031c0c97d8257f7b9f8fb27ed200b269ceb11d2a8053786acd5a8bc2` | `30_review_fixes_0021_0022/reviewer_probes_0021/p8b_stress_seq.py` |
| `707bf3558f94264bb746e7044fbd4d0fde89f638aa866cfb9535da3e70de8b40` | `30_review_fixes_0021_0022/reviewer_probes_0021/p9_upgrade_race.py` |
| `1b2a50e8a5d43d74208a4f8d868429d4a353e03b176c589607d99954cd70451e` | `29_runner_journal_wiring/SUPPLEMENT_matrix_result.txt` |
| `a2507befb71c6dfca4384408b072795fd63cf50d2793202403fb3573d3769a96` | `29_runner_journal_wiring/codex_restart_probe_as_received.patch` |
