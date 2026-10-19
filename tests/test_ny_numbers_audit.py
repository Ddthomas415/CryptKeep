from datetime import date, timedelta
import math

import pytest

from scripts.research.ny_numbers_audit import audit, binomial_lower, chi_square_survival, normalize, summarize, walk_forward


def plan(window=3):
    return {'window_draws': window, 'smoothing': 1, 'validation_start': '2020-01-01',
            'test_start': '2020-01-08', 'data_end_exclusive': '2020-01-12',
            'reference_prize': 500, 'reference_stake': 1}


def table():
    return {date(2020, 1, 1) + timedelta(days=i): '000' for i in range(11)}


def test_leading_zeros_preserved_and_bad_values_refused():
    assert normalize('7') == '007'
    assert normalize('057') == '057'
    assert normalize('0') == '000'
    assert normalize(None) is None
    with pytest.raises(ValueError):
        normalize('1000')
    with pytest.raises(ValueError):
        normalize('2-3')


def test_conflicting_dates_not_silently_selected():
    rows = [{'draw_date': '2020-01-01', 'midday_daily': '001', 'evening_daily': '003'},
            {'draw_date': '2020-01-01', 'midday_daily': '002', 'evening_daily': '3'},
            {'draw_date': '2020-01-02', 'midday_daily': '000', 'evening_daily': '004'}]
    tables, summary = audit(rows, '2021-01-01')
    assert date(2020, 1, 1) not in tables['midday']
    assert summary['sessions']['midday']['ambiguous_dates'] == ['2020-01-01']
    assert summary['sessions']['evening']['identical_duplicate_session_records'] == 1


def test_forecast_precedes_actual_and_future_draw_cannot_change_it():
    data = table()
    before = walk_forward(data, plan())
    data[date(2020, 1, 4)] = '999'
    after = walk_forward(data, plan())
    assert before[3]['prediction'] == after[3]['prediction'] == '000'
    assert after[3]['hit'] is False
    assert before[:3] == after[:3]


def test_missing_draw_preserved_and_history_reset():
    data = table()
    del data[date(2020, 1, 5)]
    rows = walk_forward(data, plan())
    assert rows[4]['status'] == 'OUTCOME_UNKNOWN'
    assert rows[4]['prediction'] == '000'
    assert rows[5]['prediction'] is None
    assert rows[8]['prediction'] == '000'


def test_lower_interval_exact_special_cases_and_known_one_success():
    assert binomial_lower(0, 100) == 0
    assert binomial_lower(10, 10) == pytest.approx(.05 ** .1)
    assert binomial_lower(1, 100) == pytest.approx(1 - .95 ** .01, abs=1e-12)


def test_chi_square_tail_against_reference_cases():
    assert chi_square_survival(0, 9) == 1
    assert chi_square_survival(10, 2) == pytest.approx(math.exp(-5), rel=1e-12)
    assert chi_square_survival(16.9189776046, 9) == pytest.approx(.05, abs=1e-10)


def test_reference_payout_is_not_actual_wager_and_unknown_not_loss():
    rows = [{'status': 'OBSERVED', 'prediction': '000', 'hit': True, 'log_score_delta': 0},
            {'status': 'OBSERVED', 'prediction': '000', 'hit': False, 'log_score_delta': 0}]
    result = summarize(rows, plan())
    assert result['current_payout_reference_net'] == 498
    assert result['fair_expected_reference_net'] == -1
    rows.append({'status': 'OUTCOME_UNKNOWN', 'prediction': '000'})
    assert summarize(rows, plan())['current_payout_reference_net'] is None
