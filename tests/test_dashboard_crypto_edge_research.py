from __future__ import annotations

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


def test_load_crypto_edge_workspace_adds_provenance_and_freshness(monkeypatch) -> None:
    from storage import crypto_edge_store_sqlite

    monkeypatch.setattr(crypto_edge_store_sqlite, "CryptoEdgeStoreSQLite", lambda: _FakeStore())

    payload = crypto_edge_research.load_crypto_edge_workspace(history_limit=3)

    assert payload["ok"] is True
    assert payload["data_origin_label"] == "Mixed Sources"
    assert payload["freshness_summary"] in {"Fresh", "Recent", "Aging", "Stale", "Unknown"}
    assert len(payload["provenance_rows"]) == 3
    assert payload["provenance_rows"][0]["source"] in {"Live Public", "Sample Bundle"}
    assert len(payload["trend_rows"]) == 3
