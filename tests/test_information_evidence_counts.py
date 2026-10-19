import json
import sqlite3

import pytest

from scripts.research import count_information_evidence as audit


def row(**updates):
    return {"capture_ts": "2026-10-18T00:00:00+00:00", "source": "live_public",
            "venue": "coinbase", "symbol": "BTC/USD", "bid": 100, "ask": 101, **updates}


def test_asof_never_uses_future_or_stale_context():
    assert audit.asof_count([1000], [[1001], [900], [900]]) == 0
    assert audit.asof_count([1000], [[699], [900], [900]]) == 0
    assert audit.asof_count([1000], [[700], [900], [1000]]) == 1
    assert audit.asof_count([1000], [[], [900], [900]]) == 0


@pytest.mark.parametrize("updates", [{"bid": 0}, {"bid": 102}, {"ask": None},
                                      {"ask": float("inf")}, {"capture_ts": "2026-10-18"}])
def test_invalid_quote_not_usable(updates):
    assert not audit.valid("quote_snapshots", row(**updates))


def test_gaps_and_repeated_polls_are_counted_separately():
    result = audit.summarize([row(), row(), row(capture_ts="2026-10-20T00:00:00+00:00")])
    assert result["rows"] == 3 and result["unique_capture_times"] == 2
    assert result["duplicate_capture_rows"] == 1
    assert result["gaps_over_24_hours"] == 1 and result["largest_gap_hours"] == 48


def test_samples_and_other_instruments_do_not_enter_btc_join():
    tables = {t: [] for t in audit.COLUMNS}
    tables["quote_snapshots"] = [row(), row(source="sample_bundle")]
    for t in ("funding_snapshots", "basis_snapshots", "open_interest_snapshots"):
        tables[t] = [row(venue="okx", symbol="ETH/USDT:USDT", funding_rate=.001,
                         interval_hours=8, spot_px=100, perp_px=101, open_interest=1)]
    result = audit.audit_projection({"tables": tables})
    assert result["btc_context_capture_join"]["quote_times"] == 1
    assert result["btc_context_capture_join"]["funding_basis_oi_at_or_before_quote"] == 0
    assert result["excluded_non_live_sources"]["quote_snapshots"] == {"sample_bundle": 1}


def test_conflicting_settlement_evidence_is_not_silently_deduplicated():
    first = {"type": "funding", "symbol": "BTCUSDT", "fundingTime": 1606780800000,
             "fundingRate": ".001", "markPrice": ""}
    raw = "\n".join(json.dumps(r) for r in (first, {**first, "fundingRate": ".002"})).encode()
    with pytest.raises(ValueError, match="conflicting_funding_records"):
        audit.audit_funding(raw)
    result = audit.audit_funding("\n".join(json.dumps(first) for _ in range(2)).encode())
    assert result["symbols"]["BTCUSDT"]["unique_settlement_timestamps"] == 1
    assert result["symbols"]["BTCUSDT"]["duplicate_rows"] == 1


def test_missing_readonly_database_is_not_created(tmp_path):
    path = tmp_path / "missing.sqlite"
    with pytest.raises(sqlite3.OperationalError):
        audit.capture(path)
    assert not path.exists()


def test_capture_reads_known_columns_without_changing_database(tmp_path):
    path = tmp_path / "public.sqlite"
    with sqlite3.connect(path) as conn:
        for table, fields in audit.COLUMNS.items():
            columns = audit.COMMON + fields
            conn.execute(f"CREATE TABLE {table} ({','.join(columns)})")
        conn.execute("INSERT INTO quote_snapshots VALUES (1,'live_public','coinbase','BTC/USD',"
                     "'2026-10-18T00:00:00+00:00',100,101)")
    before = path.read_bytes()
    projection = audit.capture(path)
    assert projection["tables"]["quote_snapshots"][0]["bid"] == 100
    assert path.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["public.sqlite"]
