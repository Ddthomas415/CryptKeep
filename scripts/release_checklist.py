#!/usr/bin/env python3
from __future__ import annotations

import runpy
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


def main() -> None:
    runpy.run_module("scripts.release.release_checklist", run_name="__main__")


if __name__ == "__main__":
    main()
