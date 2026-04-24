# services/supervisor/

Legacy supervisor family. No longer on any canonical operator path.
`scripts/compat/supervisor.py` is its only remaining caller.

For active process management, see:
- `services/process/` — process lifecycle primitives
- `services/runtime/` — bot_runner path process supervision
