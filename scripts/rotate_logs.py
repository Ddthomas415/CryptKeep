from __future__ import annotations
from cbp_desktop.logging_control import rotate_logs

def main() -> int:
    out = rotate_logs()
    print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
