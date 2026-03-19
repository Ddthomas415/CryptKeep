from __future__ import annotations

import sys

from dashboard.services import crypto_edge_research


class _FakeStore:
    def latest_report(self) -> dict:
        return {
            "ok": True,
            "has_any_data": True,
            "funding_meta": {"capture_ts": "2026-03-18T10:00:00+00:00", "source": "live_public", "row_count": 1},
            "basis_meta": {"capture_ts": "2026-03-18T09:30:00+00:00", "source": "live_public", "row_count": 1},
            "quote_meta": {"capture_ts": "2026-03-18T10:05:00+00:00", "source": "sample_bundle", "row_count": 2},
            "funding": {"count": 1},
            "basis": {"count": 1},
            "dislocations": {"count": 2},
        }

    def recent_snapshot_history(self, *, limit_per_kind: int = 5) -> list[dict]:
        return [{"kind": "quotes", "source": "sample_bundle"}]

    def recent_funding_history(self, *, limit: int = 5) -> list[dict]:
        return [
            {"capture_ts": "2026-03-18T10:00:00+00:00", "annualized_carry_pct": 12.0, "dominant_bias": "long_pays"},
            {"capture_ts": "2026-03-18T09:00:00+00:00", "annualized_carry_pct": 8.0, "dominant_bias": "long_pays"},
        ]

    def recent_basis_history(self, *, limit: int = 5) -> list[dict]:
        return [
            {"capture_ts": "2026-03-18T09:30:00+00:00", "avg_basis_bps": 6.0},
            {"capture_ts": "2026-03-18T08:30:00+00:00", "avg_basis_bps": 4.0},
        ]

    def recent_dislocation_history(self, *, limit: int = 5) -> list[dict]:
        return [
            {"capture_ts": "2026-03-18T10:05:00+00:00", "positive_count": 2, "top_symbol": "BTC/USD"},
            {"capture_ts": "2026-03-18T09:05:00+00:00", "positive_count": 1, "top_symbol": "BTC/USD"},
        ]

    def latest_report_for_source(self, *, source: str) -> dict:
        assert source == "live_public"
        return {
            "ok": True,
            "has_any_data": True,
            "funding_meta": {"capture_ts": "2026-03-18T10:00:00+00:00", "source": "live_public", "row_count": 1},
            "basis_meta": {"capture_ts": "2026-03-18T09:30:00+00:00", "source": "live_public", "row_count": 1},
            "quote_meta": None,
            "funding": {"count": 1, "dominant_bias": "long_pays"},
            "basis": {"count": 1, "avg_basis_bps": 6.0},
            "dislocations": {"count": 0, "positive_count": 0, "top_dislocation": None},
        }


def test_load_crypto_edge_workspace_adds_provenance_and_freshness(monkeypatch) -> None:
    from storage import crypto_edge_store_sqlite

    monkeypatch.setattr(crypto_edge_store_sqlite, "CryptoEdgeStoreSQLite", lambda: _FakeStore())

    payload = crypto_edge_research.load_crypto_edge_workspace(history_limit=3)

    assert payload["ok"] is True
    assert payload["data_origin_label"] == "Mixed Sources"
    assert payload["freshness_summary"] in {"Fresh", "Recent", "Aging", "Stale", "Unknown"}
    assert len(payload["provenance_rows"]) == 3
    assert payload["provenance_rows"][0]["source"] in {"Live Public", "Sample Bundle"}
    assert payload["history_rows"][0]["source_label"] in {"Live Public", "Sample Bundle"}
    assert payload["history_rows"][0]["freshness"] in {"Fresh", "Recent", "Aging", "Stale", "Unknown"}
    assert len(payload["trend_rows"]) == 3


def test_load_latest_live_crypto_edge_snapshot_isolates_live_public(monkeypatch) -> None:
    from storage import crypto_edge_store_sqlite

    monkeypatch.setattr(crypto_edge_store_sqlite, "CryptoEdgeStoreSQLite", lambda: _FakeStore())

    payload = crypto_edge_research.load_latest_live_crypto_edge_snapshot()

    assert payload["ok"] is True
    assert payload["has_live_data"] is True
    assert payload["data_origin_label"] == "Live Public"
    assert payload["freshness_summary"] in {"Fresh", "Recent", "Aging", "Stale", "Unknown"}
    assert "funding bias long_pays" in payload["summary_text"]


def test_load_crypto_edge_change_summary_uses_trend_rows(monkeypatch) -> None:
    from storage import crypto_edge_store_sqlite

    monkeypatch.setattr(crypto_edge_store_sqlite, "CryptoEdgeStoreSQLite", lambda: _FakeStore())

    payload = crypto_edge_research.load_crypto_edge_change_summary(history_limit=3)

    assert payload["ok"] is True
    assert payload["has_change_data"] is True
    assert len(payload["rows"]) == 3
    assert payload["summary_text"].startswith("Recent structural changes from stored snapshots:")


def test_load_crypto_edge_collector_runtime_reads_status_file(tmp_path, monkeypatch) -> None:
    status_path = tmp_path / "crypto_edge_collector.json"
    status_path.write_text(
        """
        {
          "status": "running",
          "ts": "2026-03-18T10:00:00+00:00",
          "loops": 3,
          "writes": 2,
          "errors": 1,
          "source": "live_public",
          "last_reason": "collected"
        }
        """.strip(),
        encoding="utf-8",
    )

    class _FakeCollectorService:
        @staticmethod
        def status_file():
            return status_path

    monkeypatch.setitem(sys.modules, "services.analytics.crypto_edge_collector_service", _FakeCollectorService)

    payload = crypto_edge_research.load_crypto_edge_collector_runtime()

    assert payload["ok"] is True
    assert payload["has_status"] is True
    assert payload["status"] == "running"
    assert payload["source_label"] == "Live Public"
    assert payload["freshness"] in {"Fresh", "Recent", "Aging", "Stale", "Unknown"}
    assert "Collector status running" in payload["summary_text"]
