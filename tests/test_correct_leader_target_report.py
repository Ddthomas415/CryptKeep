import json
from pathlib import Path
from scripts.research.correct_leader_target_report import correct, corrected_summary


def test_labels_and_marks_are_not_realized_profit():
    result = corrected_summary([{'status': 'TARGET_EXIT', 'entry_time': 1, 'net_pnl_usd': 20},
                                {'status': 'OPEN_AT_SEGMENT_END', 'entry_time': 2, 'last_mark_net_pnl_usd': -60}])
    assert result['average_closed_net_usd'] == 20
    assert result['average_closed_plus_last_marks_usd'] == -20
    assert result['unresolved_entered_events'] == 1
    assert 'average_net_usd' not in result


def test_terminal_leaders_restored_without_changing_closed_results():
    root = Path(__file__).resolve().parents[1]
    original = json.loads((root/'research/leader_target_results_20261012.json').read_text())
    raw = json.loads((root/'research/coinbase_leader_daily_repaired_20261012.json').read_text())
    revised = correct(original, raw)
    for old, new in zip(original['runs'], revised['runs']):
        assert new['combined']['leader_events'] == 181
        assert new['combined']['sum_closed_net_usd_not_portfolio'] == old['combined']['sum_closed_net_usd_not_portfolio']
        assert new['combined']['closed_trades'] == old['combined']['closed_trades']
        assert new['combined']['average_closed_net_usd'] == old['combined']['average_net_usd']
