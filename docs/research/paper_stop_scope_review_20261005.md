# Paper stop command scope review - 2026-10-05

Reviewer: Claude. Scope: `scripts/paper_stop.py` (`make paper-stop-now`). Result: patch 0068
(`21d7a505`), bundle rev79 folder 76. READY_FOR_INDEPENDENT_REVIEW. Paper operations only.
Not pushed.

## Finding (P2)

Probe: two stand-in component processes in separate state directories; the command run for
campaign A from another directory.

1. Stop flags went to `<working directory>/.cbp_state/runtime/flags`, which neither campaign
   reads. No campaign with its own state directory ever saw a stop request.
2. Processes were stopped with `pkill -f <script name>`: both campaigns' processes were
   killed, and the shell that ran the probe. Neither shut down by its own stop path.

Managed campaigns run `run_tick_publisher`, `run_paper_engine` and `run_strategy_runner`
under each collector, the names the command kills, so `make paper-stop-now` from the repo
root stopped the components of every campaign on the host.

## Patch 0068

- Stops one campaign: the one whose state directory the command runs in.
- Writes the flags there, waits for components to stop by themselves, then signals only the
  process ids recorded in that directory, each only while it still runs the component script.
- Lists other paper processes without touching them. `--all-campaigns` keeps the old stop.

## Operator-visible change

`make paper-stop-now` no longer stops `make paper-run-short` or a managed campaign. Use
`CBP_STATE_DIR=<dir> make paper-stop-now`, or
`python scripts/paper_stop.py --all-campaigns --force-now`.

6 tests with real stand-in processes. Full suite: 4850 passed, 33 skipped, 0 failed.
