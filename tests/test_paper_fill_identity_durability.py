import pytest

from storage import paper_trading_sqlite as storage


@pytest.fixture
def paper(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "paper.sqlite")
    db = storage.PaperTradingSQLite()
    db.set_state("cash_quote", "1000")
    return db


def fill(paper, *, evidence=None, oid="o1"):
    order = dict(order_id=oid, client_order_id=oid, ts="2026-10-09T20:00:00Z",
                 venue="coinbase", symbol="BTC/USDT", side="buy", order_type="market",
                 qty=1., status="new")
    if not paper.get_order_by_order_id(oid):
        paper.insert_order(order)
    return paper.apply_fill(order=order, ts=order["ts"], price=100., qty=1.,
                            fee=.075, fee_currency="USDT", execution_identity_evidence=evidence)


def test_evidence_survives_reopen_and_retry_cannot_relabel(paper):
    original = {"execution_identity_fill_status": "invalid", "reason": "synthetic"}
    result = fill(paper, evidence=original)
    reopened = storage.PaperTradingSQLite()
    assert reopened.get_fill_execution_identity(result["fill_id"]) == original
    assert fill(reopened, evidence={"new": "must_not_replace"})["idempotent"]
    assert reopened.get_fill_execution_identity(result["fill_id"]) == original


def test_legacy_fill_not_upgraded(paper):
    result = fill(paper)
    fill(paper, evidence={"new": "must_not_backfill"})
    assert paper.get_fill_execution_identity(result["fill_id"]) is None


def test_bad_evidence_rolls_back_accounting(paper):
    with pytest.raises(ValueError):
        fill(paper, evidence={"bad": float("nan")})
    assert paper.list_fills() == []
    assert paper.get_position("BTC/USDT") is None
    assert paper.get_state("cash_quote") == "1000"
    assert paper.get_order_by_order_id("o1")["status"] == "new"


def test_corrupt_storage_is_not_verified(paper):
    result = fill(paper, evidence={"synthetic": True})
    paper.set_state("fill_execution_identity:" + result["fill_id"], "[]")
    assert paper.get_fill_execution_identity(result["fill_id"]) == {
        "execution_identity_fill_status": "invalid_storage"}
