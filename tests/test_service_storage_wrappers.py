from __future__ import annotations

import importlib


def _reload_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    return app_paths


def test_services_storage_wrappers_delegate(monkeypatch, tmp_path):
    _reload_paths(monkeypatch, tmp_path)

    import storage.paper_trading_sqlite as paper_storage
    import storage.trade_journal_sqlite as journal_storage
    import services.storage.paper_trading_sqlite as paper_wrap
    import services.storage.trade_journal_sqlite as journal_wrap

    importlib.reload(paper_storage)
    importlib.reload(journal_storage)
    importlib.reload(paper_wrap)
    importlib.reload(journal_wrap)

    paper_storage.DB_PATH = tmp_path / "paper_trading.sqlite"
    journal_storage.DB_PATH = tmp_path / "trade_journal.sqlite"

    paper = paper_wrap.PaperTradingSQLite()
    journal = journal_wrap.TradeJournalSQLite()

    assert paper.list_orders(limit=1) == []
    assert journal.list_fills(limit=1) == []
