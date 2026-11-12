# Initial Independent Written-Exit Accounting Review

Historical evidence archived at the owner's request after the initial rejection.
This is not a review of the subsequent strict-decoding correction.

- `original_review.md`: original consolidated disposition.
- `probe_recovery.py`: exact original code for two recovery checks.
- `probe_runner.py`: exact original code for the runner entry-admission check.
- Adjacent `.command.sh` files: original shell commands with the Python code
  embedded as the original `python -B -c` argument.
- Adjacent `.result.json` files: original execution output transcriptions.

There are three probes of one finding: two failed, one passed. The first failed
on acceptance of duplicate event keys; the second passed acknowledgement-loss
recovery; the third failed because the real runner admitted a buy after accepting
ambiguous accounting metadata.

Commands were run from `/Users/baitus/Downloads/crypto-bot-pro`. The commands retain
their original `mktemp` expressions; expanded randomized directory names were not
returned in the original output and are not invented here. Run the command files
from the repository root to retain the original `-c` import/cwd semantics.

All results are explicitly historical transcriptions, not newly executed
receipts. No tests were rerun or implementation files inspected/edited to create
this archive. The initial report's 11/11 hash check refers to the original final
candidate described in `../final_hashes.json`, not the later correction.

The original submitted queue source is retained by the author. Correction
acceptance requires a later bounded review of its own hashes and before/after
regressions; this archive grants no source or operational acceptance.

What do I know that could change the owner's decision that I have not yet said?
