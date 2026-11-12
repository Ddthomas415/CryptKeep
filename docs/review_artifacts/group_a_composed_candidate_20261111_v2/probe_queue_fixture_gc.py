"""Deterministic synthetic control; never opens an operating account database."""
import gc
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


def run(tree):
    tree = Path(tree).resolve()
    if not tree.is_relative_to('/private/tmp'):
        raise ValueError('scratch_tree_required')
    sys.path.insert(0, str(tree))
    with tempfile.TemporaryDirectory(prefix='cbp-fixture-gc-', dir='/private/tmp') as temporary:
        root = Path(temporary)
        os.environ.clear()
        os.environ.update(PATH='/usr/bin:/bin', LC_ALL='C', HOME=str(root), CBP_STATE_DIR=str(root/'state'))
        import pytest
        import sqlite3
        from storage import paper_trading_sqlite as store
        from tests import test_paper_account_snapshot as tests
        original_helper = tests.queue_db
        original_snapshot = store.PaperTradingSQLite.account_reconciliation_snapshot
        results = []
        enabled = gc.isenabled()
        gc.disable()
        try:
            for explicitly_close_writer in (False, True):
                gc.collect()
                observations = {'explicitly_close_fixture_writer': explicitly_close_writer}
                folder = root/str(explicitly_close_writer)
                folder.mkdir()
                def checkpoint_before_reader(self):
                    path = store.DB_PATH.parent/'intent_queue.sqlite'
                    before = path.read_bytes()
                    gc.collect()  # Happens before the production reader is called.
                    after_gc = path.read_bytes()
                    observations['queue_changed_before_reader'] = before != after_gc
                    value = original_snapshot(self)
                    observations['queue_changed_during_reader'] = after_gc != path.read_bytes()
                    return value
                def closed_helper():
                    opened = []
                    original_connect = sqlite3.connect
                    def track(*args, **kwargs):
                        con = original_connect(*args, **kwargs)
                        opened.append(con)
                        return con
                    with pytest.MonkeyPatch.context() as nested:
                        nested.setattr(sqlite3, 'connect', track)
                        path = original_helper()
                    for con in opened:
                        con.close()
                    return path
                with pytest.MonkeyPatch.context() as patch:
                    patch.setattr(store, 'DB_PATH', folder/'paper.sqlite')
                    patch.setattr(store.PaperTradingSQLite, 'account_reconciliation_snapshot', checkpoint_before_reader)
                    if explicitly_close_writer:
                        patch.setattr(tests, 'queue_db', closed_helper)
                    db = store.PaperTradingSQLite()
                    try:
                        tests.test_snapshot_readonly_quoted_queue_opens_after_ledger_lock_and_closes_connections(db, patch)
                        observations['original_assertions_passed'] = True
                    except AssertionError:
                        observations['original_assertions_passed'] = False
                results.append(observations)
        finally:
            gc.collect()
            if enabled:
                gc.enable()
        assert results[0]['queue_changed_before_reader'] is True
        assert results[0]['original_assertions_passed'] is False
        assert results[1]['queue_changed_before_reader'] is False
        assert results[1]['original_assertions_passed'] is True
        assert all(row['queue_changed_during_reader'] is False for row in results)
        return {'scope': 'synthetic_fixture_GC_control_only', 'sqlite_version': sqlite3.sqlite_version,
                'unchanged_test_source_sha256': hashlib.sha256(Path(tests.__file__).read_bytes()).hexdigest(),
                'results': results, 'operating_databases_opened': False}


if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1]), sort_keys=True, indent=2))
