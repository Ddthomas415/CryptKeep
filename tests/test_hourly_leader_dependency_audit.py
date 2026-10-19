from scripts.research.hourly_leader_dependency_audit import audit


def test_repeated_entries_and_open_marks_do_not_disappear():
    events = [{'symbol': 'X', 'entry_time': 1, 'net_usd': 20},
              {'symbol': 'X', 'entry_time': 1, 'net_usd': 20},
              {'symbol': 'Y', 'entry_time': 2, 'last_mark_net_usd': -40},
              {'symbol': 'Z', 'entry_time': 3}]
    result = audit(events)
    assert result['distinct_entry_count'] == 3
    assert result['distinct_closed_count'] == 1
    assert result['distinct_closed_plus_marks_mean_usd'] == -10
    assert result['unpriced_entries'] == 1
