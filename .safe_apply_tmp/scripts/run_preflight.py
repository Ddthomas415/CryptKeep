#!/usr/bin/env python3
from __future__ import annotations
import json
from services.app.preflight_wizard import run_preflight

def main():
    print(json.dumps(run_preflight(), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
