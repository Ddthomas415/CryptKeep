#!/usr/bin/env python3
from __future__ import annotations
from services.app.diagnostics_exporter import export_zip_to_runtime

def main():
    p = export_zip_to_runtime()
    print({"ok": True, "exported_to": str(p)})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
