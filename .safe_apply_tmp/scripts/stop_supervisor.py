from __future__ import annotations

from pathlib import Path

def main() -> int:
    data_dir = Path("data/supervisor")
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "STOP").write_text("stop", encoding="utf-8")
    print("Stop flag written. Supervisor will shut down.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
