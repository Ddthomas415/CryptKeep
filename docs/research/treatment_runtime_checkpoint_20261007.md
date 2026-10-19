# Treatment runtime checkpoint - 2026-10-07

Active role: AUDITOR. Acceptance: INCOMPLETE.
Objective: establish current runtime and cost evidence before corrective financial changes.

## Shown evidence

- Checkout HEAD: 620bc8dbeee71cca327042902759e219e18f30b6. Working tree is dirty, including strategy_runner.py. This is not proof of the source loaded by an existing process or of integration of the reviewed bundle.
- Laptop paper status command: exit 1, one of two configured collectors alive. ES PID 46484 is alive; process listing confirms a Python process started October 4. Its latest completed session is October 7, 00:00:06-00:00:30 UTC, with no new fills. Latest reported fill is July 9. Breakout PID 1510 is absent and its recorded status is stale from October 4.
- Context status command: exit 0, PID 46947 alive, 505 successful writes reported; latest capture October 7, 09:40:09 UTC. Research-only and execution-disabled status is recorded. This proves current collection status, not uninterrupted coverage or trading edge.
- Existing Coinbase credentials were read without mutation. Authenticated SPOT transaction-summary query succeeded: Intro tier, maker_fee_rate 0.0025 and taker_fee_rate 0.005, equivalent to 25 and 50 bps per side. No secret was printed. These are current account rates, not historical execution costs or proof that paper configuration uses them.
- Hetzner read-only status attempt returned tailscale_ssh_auth_required. No remote campaign or deployed version was verified. The failure is a host-access authorization requirement, not evidence that exchange credentials are broken.

## Commands and proof boundaries

Read-only commands used: restore_paper_campaigns.py --status with the laptop manifest; run_crypto_edge_collector_loop.py --status; report_hetzner_paper_campaign_status.py --strict with SSH transport and the documented host/app path; targeted process listing; authenticated Coinbase transaction-summary GET through installed ccxt.

VERIFIED_ENV for laptop inspection and successful account query. Remote runtime remains UNKNOWN_ENV. No collector was started, no order was sent, and no config, account, credentials or cohort was changed. No tests were run in this checkpoint.

## Next bounded treatment

Keep the stopped breakout finding separate from accounting correction; restarting it requires an explicit operational instruction. Obtain host authorization before claiming the remote checkpoint complete. Do not use all-history paper PnL as comparable cohort evidence.

Financial correction must address durable completion/retry and exactly-once side effects together: merely refusing terminal status after canonical rejection is insufficient if subsequent reconciliation skips the already-recorded trade. Current checkout differs from the reviewed candidate, so corrections must be based on its actual source and cannot silently import unaccepted bundle dependencies. Implementation requires isolated failure tests and independent high-risk review before any deployment.
