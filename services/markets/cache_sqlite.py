from __future__ import annotations
import sqlite3, time, json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from services.markets.models import MarketRules

def _exec_db_from_trading_yaml(path: str = "config/trading.yaml") -> str:
    try:
        import yaml
        cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        ex = (cfg.get("execution") or {})
        return str(ex.get("db_path") or "data/execution.sqlite")
    except Exception:
        return "data/execution.sqlite"

def _connect(exec_db: str) -> sqlite3.Connection:
    Path(exec_db).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(exec_db, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA synchronous=NORMAL;")
    return c

def ensure_schema(exec_db: str) -> None:
    with _connect(exec_db) as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS market_rules_cache(
          venue TEXT NOT NULL,
          canonical_symbol TEXT NOT NULL,
          updated_ts REAL NOT NULL,
          rules_json TEXT NOT NULL,
          PRIMARY KEY (venue, canonical_symbol)
        );
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_mrc_updated ON market_rules_cache(updated_ts);")

def upsert(exec_db: str, rules: MarketRules) -> None:
    ensure_schema(exec_db)
    payload = json.dumps(asdict(rules), ensure_ascii=False)
    with _connect(exec_db) as c:
        c.execute(
            "INSERT INTO market_rules_cache(venue, canonical_symbol, updated_ts, rules_json) VALUES(?,?,?,?) "
            "ON CONFLICT(venue, canonical_symbol) DO UPDATE SET updated_ts=excluded.updated_ts, rules_json=excluded.rules_json",
            (rules.venue, rules.canonical_symbol, float(time.time()), payload)
        )

def get(exec_db: str, venue: str, canonical_symbol: str) -> Optional[MarketRules]:
    ensure_schema(exec_db)
    with _connect(exec_db) as c:
        r = c.execute(
            "SELECT rules_json FROM market_rules_cache WHERE venue=? AND canonical_symbol=?",
            (venue.lower().strip(), canonical_symbol.upper().strip())
        ).fetchone()
        if not r:
            return None
        d = json.loads(str(r["rules_json"]))
        return MarketRules(**d)

def is_fresh(exec_db: str, venue: str, canonical_symbol: str, ttl_s: float) -> bool:
    ensure_schema(exec_db)
    with _connect(exec_db) as c:
        r = c.execute(
            "SELECT updated_ts FROM market_rules_cache WHERE venue=? AND canonical_symbol=?",
            (venue.lower().strip(), canonical_symbol.upper().strip())
        ).fetchone()
        if not r:
            return False
        return (float(time.time()) - float(r["updated_ts"])) <= float(ttl_s)

def any_fresh(exec_db: str, ttl_s: float) -> bool:
    ensure_schema(exec_db)
    with _connect(exec_db) as c:
        r = c.execute("SELECT MAX(updated_ts) AS mx FROM market_rules_cache").fetchone()
        if not r or r["mx"] is None:
            return False
        return (float(time.time()) - float(r["mx"])) <= float(ttl_s)

def default_exec_db() -> str:
    return _exec_db_from_trading_yaml()
