from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir

DEFAULT_REQUIRED_KINDS = ("funding", "open_interest", "basis", "order_book")

_KIND_TABLES = {
    "funding": "funding_snapshots",
    "open_interest": "open_interest_snapshots",
    "basis": "basis_snapshots",
    "quotes": "quote_snapshots",
    "order_book": "order_book_snapshots",
}


def default_crypto_edge_store_path() -> Path:
    return (data_dir() / "crypto_edge_research.sqlite").resolve()


def _resolve_store_path(db_path: str | Path | None) -> Path:
    if db_path:
        return Path(db_path).expanduser().resolve()
    return default_crypto_edge_store_path()


def _connect_read_only(path: Path) -> sqlite3.Connection:
    uri = f"file:{path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (str(table),),
    ).fetchone()
    return row is not None


def _latest_meta_for_source(
    conn: sqlite3.Connection,
    *,
    table: str,
    source: str,
) -> dict[str, Any] | None:
    if not _table_exists(conn, table):
        return None
    row = conn.execute(
        f"SELECT snapshot_id, capture_ts, source, COUNT(*) AS row_count FROM {table} "
        "WHERE source = ? "
        "GROUP BY snapshot_id, capture_ts, source "
        "ORDER BY capture_ts DESC LIMIT 1",
        (str(source),),
    ).fetchone()
    if row is None:
        return None
    return {
        "snapshot_id": str(row["snapshot_id"]),
        "capture_ts": str(row["capture_ts"]),
        "source": str(row["source"]),
        "row_count": int(row["row_count"] or 0),
    }


def _kind_row(
    *,
    kind: str,
    table: str,
    source: str,
    required: bool,
    meta: dict[str, Any] | None,
    table_exists: bool,
) -> dict[str, Any]:
    row_count = int((meta or {}).get("row_count") or 0)
    available = bool(table_exists and row_count > 0)
    if not table_exists:
        reason = "missing_table"
    elif not available:
        reason = "missing_source_snapshot"
    else:
        reason = "available"
    return {
        "kind": kind,
        "table": table,
        "source": source,
        "required": bool(required),
        "available": available,
        "reason": reason,
        "row_count": row_count,
        "capture_ts": (meta or {}).get("capture_ts"),
        "snapshot_id": (meta or {}).get("snapshot_id"),
    }


def build_short_context_readiness(
    *,
    db_path: str | Path | None = None,
    source: str = "live_public",
    required_kinds: tuple[str, ...] = DEFAULT_REQUIRED_KINDS,
) -> dict[str, Any]:
    store_path = _resolve_store_path(db_path)
    source_filter = str(source or "live_public").strip() or "live_public"
    required = tuple(str(kind).strip() for kind in required_kinds if str(kind).strip())
    required_set = set(required)

    if not store_path.exists():
        families = [
            _kind_row(
                kind=kind,
                table=table,
                source=source_filter,
                required=kind in required_set,
                meta=None,
                table_exists=False,
            )
            for kind, table in _KIND_TABLES.items()
        ]
        return {
            "ok": False,
            "status": "missing_store",
            "research_only": True,
            "execution_enabled": False,
            "store_path": "redacted",
            "source_filter": source_filter,
            "required_kinds": list(required),
            "row_families": families,
            "live_public_replay_ready": False,
            "fixture_replay_ready": False,
            "replay_scope": "fixture_only",
            "blockers": ["Crypto-edge research store does not exist."],
            "recommendations": [
                "Load deterministic sample data for fixture replay, or collect "
                "accepted live-public rows.",
                "Do not use short/context replay with missing required context families.",
            ],
        }

    try:
        conn = _connect_read_only(store_path)
    except Exception as exc:
        return {
            "ok": False,
            "status": "store_unreadable",
            "research_only": True,
            "execution_enabled": False,
            "store_path": "redacted",
            "source_filter": source_filter,
            "required_kinds": list(required),
            "row_families": [],
            "live_public_replay_ready": False,
            "fixture_replay_ready": False,
            "replay_scope": "fixture_only",
            "blockers": [
                "Crypto-edge research store could not be opened read-only: "
                f"{type(exc).__name__}."
            ],
            "recommendations": ["Repair or recreate the crypto-edge research store before replay."],
        }

    try:
        families: list[dict[str, Any]] = []
        for kind, table in _KIND_TABLES.items():
            exists = _table_exists(conn, table)
            meta = (
                _latest_meta_for_source(conn, table=table, source=source_filter)
                if exists
                else None
            )
            families.append(
                _kind_row(
                    kind=kind,
                    table=table,
                    source=source_filter,
                    required=kind in required_set,
                    meta=meta,
                    table_exists=exists,
                )
            )
    finally:
        conn.close()

    missing_required = [
        str(row["kind"])
        for row in families
        if bool(row.get("required")) and not bool(row.get("available"))
    ]
    available_required = [
        str(row["kind"])
        for row in families
        if bool(row.get("required")) and bool(row.get("available"))
    ]
    has_all_required = not missing_required and bool(required)
    is_live_public = source_filter == "live_public"
    live_ready = bool(is_live_public and has_all_required)
    fixture_ready = bool((not is_live_public) and has_all_required)

    if live_ready:
        status = "live_public_ready"
        replay_scope = "live_public"
        blockers: list[str] = []
        recommendations = [
            "Live-public short/context row families are present; keep replay read-only.",
            "Do not route short/context signals to paper or execution without separate review.",
        ]
    elif fixture_ready:
        status = "fixture_ready"
        replay_scope = "fixture_only"
        blockers = [
            f"Source `{source_filter}` is not live_public, so it cannot prove "
            "live-public derivatives context."
        ]
        recommendations = [
            "Use this source only for deterministic fixture replay.",
            "Collect and accept live_public rows before relying on live derivatives context.",
        ]
    elif available_required:
        status = "live_public_partial" if is_live_public else "fixture_partial"
        replay_scope = "fixture_only"
        blockers = [
            f"Missing required row family for `{source_filter}`: {kind}."
            for kind in missing_required
        ]
        recommendations = [
            "Keep replay limited to deterministic fixtures or accepted complete row families.",
            "Collect the missing required row families before short/context replay.",
        ]
    else:
        status = "blocked"
        replay_scope = "fixture_only"
        blockers = [f"No required row families are available for `{source_filter}`."]
        recommendations = [
            "Run a read-only crypto-edge collection proof or load sample data.",
            "Do not use short/context replay with no required context evidence.",
        ]

    return {
        "ok": True,
        "status": status,
        "research_only": True,
        "execution_enabled": False,
        "store_path": "redacted",
        "source_filter": source_filter,
        "required_kinds": list(required),
        "row_families": families,
        "available_required_kinds": available_required,
        "missing_required_kinds": missing_required,
        "live_public_replay_ready": live_ready,
        "fixture_replay_ready": fixture_ready,
        "replay_scope": replay_scope,
        "blockers": blockers,
        "recommendations": recommendations,
    }
