from tests.test_live_reconciler_tracks_every_open_intent import (
    _seed_tracked, _status, _Venue, _reload_live_stack, _wire_reconciler, _run_reconciler,
)


def test_repeated_passes_eventually_reconcile_oldest_beyond_cap(monkeypatch, tmp_path):
    queue, trading, dedupe, consumer, reconciler = _reload_live_stack(monkeypatch, tmp_path)
    venue = _Venue()
    ids = _seed_tracked(queue, venue, 7)
    _wire_reconciler(monkeypatch, reconciler, venue)
    monkeypatch.setattr(reconciler, 'TRACKED_SCAN_LIMIT', 5)
    venue.close_with_trade(f'cid-{ids[0]}', 'oldest-fill')
    for _ in range(3):
        _run_reconciler(reconciler)
    assert _status(queue, ids[0]) == 'filled'
