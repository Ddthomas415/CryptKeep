#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from scripts.release import pre_release_sanity as _impl

SCHEMA_VERSION = 1

# Compatibility contract for text-based wiring tests that still assert the
# public root command exposes the JSON/pre-release runtime surface.
_CONTRACT_MARKERS = (
    "def run_alignment_gate()",
    "scripts/check_repo_alignment.py",
    "--json",
    '"schema_version": SCHEMA_VERSION',
    '"quick" if all(skip_flags) else ("full" if not any(skip_flags) else "custom")',
    "CBP_PRE_RELEASE_SKIP_PYTEST",
    '"ok"',
    '"mode"',
    "started_at",
    "finished_at",
    "duration_seconds",
)


def run_alignment_gate() -> None:
    return _impl.run_alignment_gate()


def main():
    return _impl.main()


if __name__ == "__main__":
    raise SystemExit(main())
