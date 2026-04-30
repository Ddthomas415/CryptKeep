from __future__ import annotations

import importlib

from services.execution.intent_reconciler import reconcile_once


def test_reconcile_once_journals_filled_strategy_intent() -> None:
    updates: list[tuple[str, str, str | None]] = []
    journal_rows: list[dict] = []

    class FakeQueue:
        def list_intents(self, *, limit: int, status: str) -> list[dict]:
            assert limit == 20
            assert status == "submitted"
            return [
                {
                    "intent_id": "intent-1",
                    "source": "strategy",
                    "strategy_id": "ema_cross",
                    "client_order_id": "paper_intent_intent-1",
                    "linked_order_id": "paper-order-1",
                }
            ]

        def update_status(self, intent_id: str, status: str, *, last_error: str | None = None, **_kwargs) -> None:
            updates.append((intent_id, status, last_error))

    class FakePaperDb:
        def get_order_by_order_id(self, order_id: str) -> dict | None:
            assert order_id == "paper-order-1"
            return {
                "order_id": order_id,
                "venue": "coinbase",
                "symbol": "BTC/USD",
                "side": "buy",
                "status": "filled",
            }

        def list_fills_for_order(self, order_id: str, *, limit: int) -> list[dict]:
            assert order_id == "paper-order-1"
            assert limit == 5000
            return [
                {
                    "fill_id": "fill-1",
                    "ts": "2026-03-19T12:00:01Z",
                    "qty": 0.25,
                    "price": 100.0,
                    "fee": 0.05,
                    "fee_currency": "USD",
                }
            ]

        def get_position(self, symbol: str) -> dict:
            assert symbol == "BTC/USD"
            return {"qty": 0.25, "avg_price": 100.0}

        def get_state(self, key: str) -> str:
            if key == "cash_quote":
                return "975.0"
            if key == "realized_pnl":
                return "0.0"
            raise AssertionError(f"unexpected key: {key}")

    class FakeJournal:
        def insert_fill(self, row: dict) -> None:
            journal_rows.append(row)

        def count(self) -> int:
            return len(journal_rows)

    out = reconcile_once(
        qdb=FakeQueue(),
        pdb=FakePaperDb(),
        jdb=FakeJournal(),
        max_intents=20,
    )

    assert updates == [("intent-1", "filled", None)]
    assert len(journal_rows) == 1
    assert journal_rows[0]["strategy_id"] == "ema_cross"
    assert journal_rows[0]["client_order_id"] == "paper_intent_intent-1"
    assert journal_rows[0]["order_id"] == "paper-order-1"
    assert out == {
        "submitted_checked": 1,
        "intents_updated": 1,
        "fills_journaled": 1,
        "journal_count": 1,
    }


def test_intent_reconciler_acquire_lock_reclaims_stale_lock(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import services.execution.intent_reconciler as intent_reconciler

    importlib.reload(app_paths)
    importlib.reload(intent_reconciler)

    intent_reconciler.LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    intent_reconciler.LOCK_FILE.write_text('{"pid": 999999, "ts": "2026-03-19T12:00:00Z"}\n', encoding="utf-8")

    def fake_clean(lock_file):
        lock_file.unlink()
        return True

    monkeypatch.setattr(intent_reconciler, "clean_stale_lock_file", fake_clean)

    assert intent_reconciler._acquire_lock() is True
    assert intent_reconciler.LOCK_FILE.exists()
    intent_reconciler._release_lock()
