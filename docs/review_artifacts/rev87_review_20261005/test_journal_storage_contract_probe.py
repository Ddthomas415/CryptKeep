"""Load only the candidate journal; every database is temporary and owned here."""
import ast
import importlib.util
import json
import logging
import math
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path


SOURCE = Path('/private/tmp/cryptkeep-rev87-candidate-20261005/storage/exit_event_journal.py')


class JournalContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cryptkeep_journal_probe_')
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'state.sqlite'
        store = types.ModuleType('storage.strategy_state_sqlite')

        def connect():
            con = sqlite3.connect(self.path, isolation_level=None)
            con.execute('CREATE TABLE IF NOT EXISTS strategy_state '
                        '(k TEXT PRIMARY KEY,v TEXT,updated_ts TEXT)')
            return con

        store._connect = connect
        store._now = lambda: '2026-10-07T00:00:00Z'
        package = types.ModuleType('storage')
        package.strategy_state_sqlite = store
        previous = {key: sys.modules.get(key) for key in ('storage', 'storage.strategy_state_sqlite')}
        sys.modules['storage'] = package
        sys.modules['storage.strategy_state_sqlite'] = store
        try:
            spec = importlib.util.spec_from_file_location('isolated_journal_probe', SOURCE)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            for key, value in previous.items():
                if value is None:
                    sys.modules.pop(key, None)
                else:
                    sys.modules[key] = value
        self.journal = module.ExitEventJournal()
        runner_path = SOURCE.parent.parent / 'services/execution/strategy_runner.py'
        names = {'_exit_scope', '_usable_exit_event', '_reconcile_exit_events_from_queue',
                 '_venue_risk_hold', '_venues_with_history', '_position_hold', '_venue_and_entry_permission'}
        tree = ast.parse(runner_path.read_text())
        selected = ast.Module(body=[node for node in tree.body
                                    if isinstance(node, ast.FunctionDef) and node.name in names], type_ignores=[])
        namespace = {'json': json, 'math': math, '_LOG': logging.getLogger('isolated_recovery_probe'),
                     '_POSITION_STATE_NAMES': ('entry_price', 'trailing_peak', 'bars_held', 'last_held_bar_ts')}
        exec(compile(selected, str(runner_path), 'exec'), namespace)
        self.recover = namespace['_reconcile_exit_events_from_queue']
        self.venue_permission = namespace['_venue_and_entry_permission']

    def recovery_fixture(self, rows):
        values = {}
        state = types.SimpleNamespace(get=lambda key: values.get(key), set=lambda key, value: values.__setitem__(key, value),
                                      keys_ending=lambda suffix: sorted(key for key in values if key.endswith(suffix)))
        queue = types.SimpleNamespace(strategy_sell_intents_after=lambda symbol, after=0:
                                     [dict(row) for row in rows if row['rowid'] > after])
        return state, queue, values

    def test_second_historical_kill_remains_after_first_clears(self):
        state, queue, values = self.recovery_fixture([])
        cfg = {'strategy_id': 's', 'venue': 'new'}
        values['kill_remaining:old1:BTC:s'] = '49'
        values['kill_remaining:old2:BTC:s'] = '49'
        with self.assertLogs('isolated_recovery_probe', level='WARNING'):
            venue, block = self.venue_permission(state, self.journal, cfg, 'BTC', 'new', queue)
        self.assertEqual(venue, 'old1')
        self.assertTrue(block.startswith('other_venue_hold:'))
        values['kill_remaining:old1:BTC:s'] = '0'
        with self.assertLogs('isolated_recovery_probe', level='WARNING'):
            venue, block = self.venue_permission(state, self.journal, cfg, 'BTC', 'new', queue)
        self.assertEqual(venue, 'old2')

    def test_queue_only_exit_holds_old_venue_before_move(self):
        rows = [{'rowid': 1, 'intent_id': 'third-loss', 'venue': 'old', 'symbol': 'BTC',
                 'strategy_id': 's', 'meta': {'exit_event': {'scope': 'old:BTC:s',
                                                          'pnl_pct': -3.85, 'is_loss': True}}}]
        state, queue, values = self.recovery_fixture(rows)
        values['active_venue:BTC:s'] = 'old'
        with self.assertLogs('isolated_recovery_probe', level='WARNING'):
            venue, block = self.venue_permission(state, self.journal, {'strategy_id': 's'}, 'BTC', 'new', queue)
        self.assertEqual(venue, 'old')
        self.assertTrue(self.journal.has_unresolved('old:BTC:s'))
        self.assertTrue(self.journal.status_of('third-loss')['confirmed'])

    def test_unreadable_history_refuses_entries_even_if_venue_returned(self):
        state, queue, values = self.recovery_fixture([])
        def broken(suffix):
            raise OSError('injected history failure')
        state.keys_ending = broken
        with self.assertLogs('isolated_recovery_probe', level='WARNING'):
            venue, block = self.venue_permission(state, self.journal, {'strategy_id': 's'}, 'BTC', 'new', queue)
        self.assertEqual(venue, 'new')
        self.assertTrue(block.startswith('venue_history_unreadable:'))
        self.assertNotIn('active_venue:BTC:s', values)

    def test_malformed_event_is_quarantined_not_silently_skipped(self):
        rows = [{'rowid': 1, 'intent_id': 'a', 'venue': 'v', 'symbol': 'BTC',
                 'strategy_id': 's', 'meta': {'exit_event': None}}]
        state, queue, values = self.recovery_fixture(rows)
        self.assertEqual(self.recover(self.journal, state, queue, 'v:BTC:s', 'BTC'), 1)
        row = self.journal.unresolved('v:BTC:s')[0]
        self.assertTrue(row['quarantined'])
        self.assertTrue(row['confirmed'])
        self.assertEqual(row['raw'], 'null')
        self.assertEqual(values['exit_reconciled_position:v:BTC:s'], '1|a')
        self.assertEqual(self.recover(self.journal, state, queue, 'v:BTC:s', 'BTC'), 0)

    def test_anchor_replacement_rereads_without_duplicate_journal_identity(self):
        def row(index, identity):
            return {'rowid': index, 'intent_id': identity, 'venue': 'v', 'symbol': 'BTC',
                    'strategy_id': 's', 'meta': {'exit_event': {'scope': 'v:BTC:s',
                                                              'pnl_pct': -1.0, 'is_loss': True}}}
        rows = [row(1, 'a'), row(2, 'b')]
        state, queue, values = self.recovery_fixture(rows)
        self.assertEqual(self.recover(self.journal, state, queue, 'v:BTC:s', 'BTC'), 2)
        rows[1] = row(2, 'c')
        with self.assertLogs('isolated_recovery_probe', level='WARNING'):
            self.assertEqual(self.recover(self.journal, state, queue, 'v:BTC:s', 'BTC'), 1)
        self.assertEqual([r['intent_id'] for r in self.journal.unresolved('v:BTC:s')], ['a', 'b', 'c'])
        self.assertEqual(values['exit_reconciled_position:v:BTC:s'], '2|c')

    def counter(self):
        with sqlite3.connect(self.path) as con:
            row = con.execute("SELECT v FROM strategy_state WHERE k='streak'").fetchone()
        return None if row is None else row[0]

    def apply(self, identity, reducer=None):
        return self.journal.apply('s', identity, allowed_keys=['streak'],
                                  reduce=reducer or (lambda event, get: {'streak': int(get('streak') or 0) + 1}))

    def test_later_confirmation_survives_reopen_and_applies_in_order_once(self):
        for identity in ('a', 'b'):
            self.journal.prepare('s', identity, {})
        self.journal.confirm('s', 'b')
        reopened = type(self.journal)()
        self.assertTrue(reopened.status_of('b')['confirmed'])
        with self.assertRaisesRegex(ValueError, 'earlier_exit_unresolved'):
            self.apply('b')
        self.journal.confirm('s', 'a')
        self.assertTrue(self.apply('a'))
        self.assertTrue(self.apply('b'))
        self.assertFalse(self.apply('a'))
        self.assertEqual(self.counter(), '2')

    def test_unconfirmed_production_apply_is_refused(self):
        self.journal.prepare('s', 'a', {})
        with self.assertRaisesRegex(ValueError, 'unconfirmed'):
            self.apply('a')
        self.assertIsNone(self.counter())

    def test_legacy_schema_upgrade_preserves_rows_and_requires_confirmation(self):
        with sqlite3.connect(self.path) as con:
            con.execute('CREATE TABLE exit_events (seq INTEGER PRIMARY KEY AUTOINCREMENT,'
                        'scope TEXT NOT NULL,intent_id TEXT NOT NULL UNIQUE,payload TEXT NOT NULL,'
                        "status TEXT NOT NULL CHECK(status IN ('pending','applied','unwritten')))")
            con.execute("INSERT INTO exit_events(scope,intent_id,payload,status) VALUES('s','a','{}','pending')")
            con.execute("INSERT INTO exit_events(scope,intent_id,payload,status) VALUES('s','old','{}','applied')")
        rows = self.journal.unresolved('s')
        self.assertEqual([row['intent_id'] for row in rows], ['a'])
        self.assertFalse(rows[0]['confirmed'])
        self.assertEqual(self.journal.status_of('old')['status'], 'applied')
        with self.assertRaisesRegex(ValueError, 'unconfirmed'):
            self.apply('a')
        self.journal.confirm('s', 'a')
        self.assertTrue(self.apply('a'))
        self.assertFalse(type(self.journal)().has_unresolved('s'))

    def test_invalid_utf8_payload_is_preserved_without_reader_failure(self):
        self.journal.prepare('s', 'a', {})
        with sqlite3.connect(self.path) as con:
            con.execute("UPDATE exit_events SET payload=CAST(x'ff7b' AS TEXT) WHERE intent_id='a'")
        row = self.journal.unresolved('s')[0]
        self.assertEqual(row['raw'], b'\xff{')
        self.assertIsNone(row['payload'])
        self.journal.quarantine('s', 'a', 'bad_text')
        self.assertEqual(self.journal.unresolved('s')[0]['raw'], b'\xff{')

    def test_damaged_scope_refuses_application_in_other_scope(self):
        self.journal.prepare('bad', 'a', {})
        self.journal.prepare('s', 'b', {})
        self.journal.confirm('s', 'b')
        with sqlite3.connect(self.path) as con:
            con.execute("UPDATE exit_events SET scope=CAST(x'ff' AS TEXT) WHERE intent_id='a'")
        self.assertTrue(self.journal.has_unresolved('s'))
        self.assertTrue(self.journal.has_unresolved('other'))
        with self.assertRaisesRegex(ValueError, 'scope_damaged'):
            self.apply('b')
        self.assertIsNone(self.counter())

    def test_quarantine_preserves_evidence_and_blocks_overtaking(self):
        self.journal.quarantine_raw('s', 'a', '{bad', 'unreadable', confirmed=True)
        self.journal.prepare('s', 'b', {})
        self.journal.confirm('s', 'b')
        rows = self.journal.unresolved('s')
        self.assertEqual(rows[0]['raw'], '{bad')
        self.assertTrue(rows[0]['quarantined'])
        with self.assertRaisesRegex(ValueError, 'earlier_exit_unresolved'):
            self.apply('b')
        with self.assertRaisesRegex(ValueError, 'quarantined'):
            self.journal.settle('s', 'a', written=False, reduce=lambda event, get: {})
        self.assertTrue(self.journal.has_unresolved('s'))

    def test_production_reducer_cannot_write_stop_keys(self):
        self.journal.prepare('s', 'a', {})
        self.journal.confirm('s', 'a')
        with self.assertRaisesRegex(ValueError, 'not_allowed'):
            self.apply('a', lambda event, get: {'entry_price': '0'})
        self.assertEqual(self.journal.status_of('a')['status'], 'pending')
        self.assertIsNone(self.counter())

    def test_partial_write_failure_rolls_back_counter_and_event(self):
        self.journal.prepare('s', 'a', {})
        self.journal.confirm('s', 'a')
        with sqlite3.connect(self.path) as con:
            con.execute("CREATE TRIGGER reject_second BEFORE INSERT ON strategy_state "
                        "WHEN NEW.k='second' BEGIN SELECT RAISE(ABORT,'injected second write'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.journal.apply('s', 'a', allowed_keys=['streak', 'second'],
                               reduce=lambda event, get: {'streak': '1', 'second': '2'})
        self.assertIsNone(self.counter())
        self.assertEqual(self.journal.status_of('a')['status'], 'pending')


if __name__ == '__main__':
    unittest.main(verbosity=2)
