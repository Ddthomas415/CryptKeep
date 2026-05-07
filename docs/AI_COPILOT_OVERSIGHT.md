# AI Copilot Oversight Watch

The repo now includes a read-only oversight surface for repo-wide operator questions.

Purpose:
- monitor canonical runtime truth
- pull launch blockers and progress docs into one context bundle
- answer targeted repo questions with file-level evidence

Entry point:

```bash
python3 scripts/run_ai_oversight_watch.py --question "Why is pipeline down?"
```

Context-only mode:

```bash
python3 scripts/run_ai_oversight_watch.py --question "What controls live execution?" --context-only
```

Report artifact mode:

```bash
python3 scripts/run_ai_oversight_watch.py --question "What is the current repo oversight summary?" --write-report
```

What it watches:
- canonical bot runtime status
- heartbeat and system health
- launch blockers and remaining tasks
- repo git state
- targeted file hits across `services/`, `scripts/`, `docs/`, `tests/`, `dashboard/`, and `config/`

Safety:
- read-only only
- does not arm live trading
- does not write config
- does not touch databases
