from __future__ import annotations
import yaml

def main() -> int:
    cfg = yaml.safe_load(open("config/app.yaml","r",encoding="utf-8").read()) or {}
    v = (((cfg.get("app") or {}).get("version")) or "0.0.0")
    print(str(v))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
