import copy
import math
from datetime import timedelta

import pytest

from scripts.research import cmc_bounded_daily as study


def fixture():
    rows = []
    for index in range(study.DAYS):
        day = study.START + timedelta(days=index)
        b = study.boundary_ms(day)
        rows.append({'day': day.isoformat(), 'status': 'COMPLETE_DAY', 'list_observed': True,
                     'maturity_boundary_ms': b, 'list_available_at_ms': b-1,
                     'eligible': 0, 'unknown': 0, 'missing_outcomes': 0, 'events': []})
    return {'status': 'COMPLETE_FULL_COHORT', 'calendar': rows}


def add(audit, index, values):
    row = audit['calendar'][index]
    row['eligible'] = len(values)
    row['events'] = [{'event_id': f'{index}-{i}', 'net_excess': value,
                      'qualification': 'QUALIFIED_PAIRED_ENDPOINTS',
                      'evidence_available_at_ms': row['maturity_boundary_ms']}
                     for i, value in enumerate(values)]


def run(audit):
    return study.evaluate(audit, now_ms=study.boundary_ms(study.START + timedelta(days=89)))


def test_clipping_retains_raw_and_no_mutation():
    audit = fixture()
    add(audit, 0, [-20.0, 0.01, 2.0])
    original = copy.deepcopy(audit)
    result = run(audit)
    assert audit == original
    assert result['calendar'][0]['raw_values'] == [-20.0, 0.01, 2.0]
    assert result['calendar'][0]['bounded_values'] == [-0.05, 0.01, 0.05]
    assert result['clipped_events'] == 2
    assert result['raw_negative_tail_sum'] == -20
    assert result['raw_positive_tail_sum'] == 2
    assert result['raw_event_weighted_mean'] < 0
    assert result['scoring_authorized'] is False
    assert result['qualification_verified'] is False


def test_daily_not_event_weighting():
    audit = fixture()
    add(audit, 0, [0.04]*10)
    add(audit, 1, [-0.04])
    result = run(audit)
    assert result['bounded_daily_mean'] == pytest.approx(0)
    assert result['raw_event_weighted_mean'] > 0
    assert result['zero_event_days'] == 88


def test_width_and_known_range():
    assert study.half_width(90) == pytest.approx(0.026561823723115024)
    assert study.half_width(1) == pytest.approx(0.1*math.sqrt(math.log(80)/2))
    result = run(fixture())
    assert result['raw_event_weighted_mean'] is None
    assert result['conditional_average_interval'] == pytest.approx([-result['half_width'], result['half_width']])
    assert len(result['input_sha256']) == 64


@pytest.mark.parametrize('field,value', [('unknown', 1), ('missing_outcomes', 1),
                                        ('list_observed', False), ('eligible', True),
                                        ('maturity_boundary_ms', 0), ('day', '2026-11-11')])
def test_bad_calendar_refuses(field, value):
    audit = fixture()
    audit['calendar'][0][field] = value
    with pytest.raises(ValueError):
        run(audit)


@pytest.mark.parametrize('value', [True, float('inf'), float('nan'), '0.1'])
def test_invalid_returns(value):
    audit = fixture()
    add(audit, 0, [value])
    with pytest.raises(ValueError):
        run(audit)


def test_late_receipts_duplicate_ids_missing_day_and_early_run():
    audit = fixture()
    add(audit, 0, [0.01])
    audit['calendar'][0]['events'][0]['evidence_available_at_ms'] += 1
    with pytest.raises(ValueError, match='late evidence'):
        run(audit)
    audit = fixture()
    add(audit, 0, [0.01, 0.01])
    audit['calendar'][0]['events'][1]['event_id'] = '0-0'
    with pytest.raises(ValueError, match='duplicate'):
        run(audit)
    with pytest.raises(ValueError, match='calendar'):
        run({'status': 'COMPLETE_FULL_COHORT', 'calendar': audit['calendar'][:-1]})
    with pytest.raises(ValueError, match='not mature'):
        study.evaluate(fixture(), now_ms=0)
