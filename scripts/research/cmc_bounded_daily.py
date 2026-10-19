"""Isolated parallel bounded-score arithmetic, with no market-scoring authority."""
import hashlib
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


CAP = 0.05
ALPHA = 0.05
START = date(2026, 11, 10)
DAYS = 90
CONTRACT = Path(__file__).resolve().parents[2] / 'docs/research/cmc_trending_log/bounded_daily_parallel_contract_20261010.md'


def boundary_ms(day):
    # Latest entry is before next midnight, followed by seven days plus tolerance.
    boundary = datetime.combine(day + timedelta(days=8), datetime.min.time(), timezone.utc)
    return int((boundary + timedelta(hours=12)).timestamp() * 1000)


def half_width(t):
    if type(t) is not int or t < 1:
        raise ValueError('positive integer day count required')
    return 2 * CAP * math.sqrt(math.log(2 * t * (t + 1) / ALPHA) / (2 * t))


def _time(value, *, upper):
    if type(value) is not int or not 0 <= value <= upper:
        raise ValueError('invalid or late evidence time')


def evaluate(audit, *, now_ms):
    """Calculate only a complete declared window; input qualification is not certified."""
    if type(now_ms) is not int or now_ms < boundary_ms(START + timedelta(days=DAYS-1)):
        raise ValueError('declared window not mature')
    if audit.get('status') != 'COMPLETE_FULL_COHORT':
        raise ValueError('complete cohort required')
    calendar = audit.get('calendar')
    if not isinstance(calendar, list) or len(calendar) != DAYS:
        raise ValueError('exact declared calendar required')
    input_hash = hashlib.sha256(json.dumps(audit, sort_keys=True, separators=(',', ':'),
                                          allow_nan=False).encode()).hexdigest()
    scores, raw_days, raw_events, clipped_events = [], [], [], []
    ids = set()
    rows = []
    for index, row in enumerate(calendar):
        day = START + timedelta(days=index)
        boundary = boundary_ms(day)
        if (row.get('day') != day.isoformat() or row.get('status') != 'COMPLETE_DAY'
                or row.get('list_observed') is not True
                or row.get('maturity_boundary_ms') != boundary):
            raise ValueError('invalid calendar or maturity boundary')
        for key in ('eligible', 'unknown', 'missing_outcomes'):
            if type(row.get(key)) is not int or row[key] < 0:
                raise ValueError('invalid count metadata')
        if row['unknown'] or row['missing_outcomes']:
            raise ValueError('unresolved day')
        _time(row.get('list_available_at_ms'), upper=boundary)
        events = row.get('events')
        if not isinstance(events, list) or len(events) != row['eligible']:
            raise ValueError('event count mismatch')
        values, clipped = [], []
        for event in events:
            identifier = event.get('event_id')
            if not isinstance(identifier, str) or not identifier or identifier in ids:
                raise ValueError('invalid or duplicate event identity')
            ids.add(identifier)
            value = event.get('net_excess')
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError('finite excess return required')
            if event.get('qualification') != 'QUALIFIED_PAIRED_ENDPOINTS':
                raise ValueError('qualified endpoint input required')
            _time(event.get('evidence_available_at_ms'), upper=boundary)
            values.append(value)
            clipped.append(max(-CAP, min(CAP, value)))
        try:
            raw_sum = math.fsum(values)
            clip_sum = math.fsum(clipped)
        except OverflowError as exc:
            raise ValueError('nonfinite aggregate') from exc
        score = clip_sum / len(events) if events else 0.0
        raw_day = raw_sum / len(events) if events else 0.0
        scores.append(score)
        raw_days.append(raw_day)
        raw_events.extend(values)
        clipped_events.extend(clipped)
        rows.append({'day': day.isoformat(), 'raw_values': values, 'bounded_values': clipped,
                     'bounded_daily_score': score, 'raw_daily_mean': raw_day,
                     'maturity_boundary_ms': boundary})
    try:
        mean = math.fsum(scores) / DAYS
        raw_sum = math.fsum(raw_events)
        raw_daily_mean = math.fsum(raw_days) / DAYS
        adjustment = math.fsum(clipped_events) - raw_sum
        negative_tail = math.fsum(v for v in raw_events if v < -CAP)
        positive_tail = math.fsum(v for v in raw_events if v > CAP)
    except OverflowError as exc:
        raise ValueError('nonfinite aggregate') from exc
    numbers = (mean, raw_sum, raw_daily_mean, adjustment, negative_tail, positive_tail)
    if not all(math.isfinite(v) for v in numbers):
        raise ValueError('nonfinite aggregate')
    h = half_width(DAYS)
    return {'status': 'DESCRIPTIVE_PARALLEL_RESULT', 'scoring_authorized': False,
            'target': 'TIME_AVERAGE_CONDITIONAL_BOUNDED_DAILY_SCORE',
            'coverage': 'CONDITIONAL_ON_DECLARED_CHRONOLOGICAL_INPUT_CONTRACT',
            'qualification_verified': False, 'calendar_days': DAYS,
            'bounded_daily_mean': mean, 'half_width': h,
            'conditional_average_interval': [max(-CAP, mean-h), min(CAP, mean+h)],
            'raw_event_weighted_mean': raw_sum / len(raw_events) if raw_events else None,
            'raw_daily_mean': raw_daily_mean, 'eligible_events': len(raw_events),
            'zero_event_days': sum(not row['raw_values'] for row in rows),
            'clipped_events': sum(a != b for a, b in zip(raw_events, clipped_events)),
            'raw_negative_tail_sum': negative_tail, 'raw_positive_tail_sum': positive_tail,
            'clipped_minus_raw_sum': adjustment, 'calendar': rows,
            'input_sha256': input_hash, 'implementation_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'contract_sha256': hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
            'limits': ['not_original_mean_inference', 'not_portfolio_profit',
                       'not_future_profitability', 'input_provenance_not_certified']}
