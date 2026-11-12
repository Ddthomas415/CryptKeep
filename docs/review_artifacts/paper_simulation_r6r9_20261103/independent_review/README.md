# Initial Independent R6/R9 Review

Archived at the owner's request after the initial rejection. Historical evidence,
not a review of the correction. No implementation source was edited and no probe
was rerun while creating this archive.

- Original disposition: `original_review.md`.
- Exact probe code: `probe_fingerprint_only.py` and `probe_active_bindings.py`.
- Original shell commands: `probe_fingerprint_only.command.sh` and
  `probe_active_bindings.command.sh`. Each command embeds the corresponding
  Python file's code as the original `python -B -c` argument.
- Original execution results: `probe_fingerprint_only.result.json` and
  `probe_active_bindings.result.json`.
- Reviewed candidate hashes: `reviewed_hashes.json`.

The first execution had one fingerprint-only failing check. The second had two
failing replay checks: the active adapter and active transition alias. These
are three probes of one finding, not three separate findings.

Commands were run from `/Users/baitus/Downloads/crypto-bot-pro`. The original
shell commands created fresh temporary state directories using `mktemp`; their
expanded randomized names were not returned in the original output and are not
invented here. The `.py` files preserve the exact code passed to `-c`; running
the original command files preserves the original import/cwd semantics.

Result JSON files transcribe the original exec-command tool outputs, including
exit codes and pytest text. They are not newly generated test receipts. In-memory
monkeypatches were restored by pytest; production files were not rewritten.

This archive does not authorize correction acceptance, deployment or operation.
The bounded fingerprint correction requires a later independent recheck against
its own frozen hashes and before/after receipts.

What do I know that could change the owner's decision that I have not yet said?
