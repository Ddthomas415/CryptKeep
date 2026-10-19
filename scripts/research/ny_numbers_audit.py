"""One frozen public-data lottery study. No wagers, purchases or account access."""

import argparse
import base64
from collections import deque
from datetime import date, datetime, timedelta, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import re

import numpy as np
import requests

FIELDS = {'midday': 'midday_daily', 'evening': 'evening_daily'}
URL = 'https://data.ny.gov/resource/hsys-3def.json'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def freeze(output):
    save(output, {'registered_utc': datetime.now(timezone.utc).isoformat(),
                  'source_sha256': digest(__file__), 'source_url': URL,
                  'data_end_exclusive': '2026-10-01', 'validation_start': '2016-01-01',
                  'test_start': '2022-01-01', 'window_draws': 1000, 'smoothing': 1.0,
                  'tie_rule': 'lowest digit independently per position',
                  'prediction_rule': 'product of three Laplace-smoothed positional frequencies from previous 1000 consecutive known daily draws of the same session; predict before current outcome; no fitting or threshold selection',
                  'unknown_rule': 'missing/ambiguous session outcome resets its history; eligible prediction with unknown outcome remains unresolved, never a loss or zero return',
                  'reference_stake': 1.0, 'reference_prize': 500.0,
                  'reference_payout_policy': 'current base straight-play reference only, not historical payout reconstruction; no bonuses, add-ons or taxes; no tickets purchased',
                  'fair_null_probability': .001, 'break_even_probability': .002,
                  'primary': 'pooled final held-out mean log-score improvement over uniform; lower 95% paired-calendar-day circular block-bootstrap bound above zero for both 14-day and 90-day blocks, and positive validation mean',
                  'economic_gate': 'at least 1000 observed final predictions, no eligible unknown outcomes, and pooled one-sided 95% binomial lower bound for selected-number hit probability strictly above .002',
                  'bootstrap_repetitions': 2000, 'bootstrap_seed': 20261013,
                  'exploratory_tests': 'positional uniformity, within-draw positional independence, same-position lag-one dependence, midday/evening same-day dependence, digit-sum distribution; one Bonferroni family across all tests',
                  'assumptions': ['numeric strings shorter than three digits represent omitted leading zeroes in a three-digit game',
                                  'fair iid draws define the null; binomial intervals assume independent equal-probability successes, not demonstrated properties of actual draws'],
                  'limits': ['one_fixed_model_does_not_test_every_possible_bias', 'historical_not_live_prospective_validation',
                             'drawing_equipment_and_procedure_history_unverified', 'bootstrap_is_block_length_dependent',
                             'no_capital_or_wager_authorization', 'no_claim_that_p_values_are_profit_probabilities']})


def collect(plan_path, output):
    plan = json.loads(Path(plan_path).read_text())
    if digest(__file__) != plan['source_sha256']:
        raise ValueError('source_changed')
    raw = {'plan_sha256': digest(plan_path), 'receipts': [], 'rows': None, 'status': 'INCOMPLETE'}
    where = "draw_date < '" + plan['data_end_exclusive'] + "T00:00:00.000'"
    try:
        with requests.Session() as session:
            session.trust_env = False

            def get(params):
                receipt = {'url': URL, 'params': params, 'requested_utc': datetime.now(timezone.utc).isoformat()}
                raw['receipts'].append(receipt)
                response = session.get(URL, params=params, timeout=45, allow_redirects=False)
                receipt.update(http_status=response.status_code, received_utc=datetime.now(timezone.utc).isoformat(),
                               response_base64=base64.b64encode(response.content).decode(),
                               response_sha256=hashlib.sha256(response.content).hexdigest())
                response.raise_for_status()
                return response.json()

            count = get({'$select': 'count(*) as n', '$where': where})
            expected = int(count[0]['n'])
            raw['rows'] = get({'$where': where, '$order': 'draw_date ASC', '$limit': 50000})
            raw['expected_rows'] = expected
            if not isinstance(raw['rows'], list) or len(raw['rows']) != expected or expected >= 50000:
                raise ValueError('incomplete_or_unexpected_download')
            if digest(__file__) != plan['source_sha256']:
                raise ValueError('source_changed_during_fetch')
            raw['status'] = 'COMPLETE'
    except Exception as exc:
        raw['error'] = str(exc)
        save(output, raw)
        raise
    save(output, raw)
    print(json.dumps({'rows': len(raw['rows']), 'receipts': len(raw['receipts']), 'status': raw['status']}))


def normalize(value):
    if value is None or str(value).strip() == '':
        return None
    value = str(value).strip()
    if not re.fullmatch(r'[0-9]{1,3}', value):
        raise ValueError('invalid_three_digit_value')
    return value.zfill(3)


def audit(rows, end):
    values = {session: {} for session in FIELDS}
    problems, shortened = [], 0
    dates = []
    for index, row in enumerate(rows):
        day = date.fromisoformat(row['draw_date'][:10])
        if day >= date.fromisoformat(end):
            raise ValueError('post_cutoff_row')
        dates.append(day)
        for session, field in FIELDS.items():
            try:
                value = normalize(row.get(field))
            except ValueError:
                problems.append({'row': index, 'date': day.isoformat(), 'session': session, 'value': row.get(field)})
                value = 'INVALID'
            if value is not None:
                shortened += int(value != 'INVALID' and len(str(row[field]).strip()) < 3)
                values[session].setdefault(day, []).append(value)
    tables, summary = {}, {}
    for session, days in values.items():
        table, duplicates, ambiguous = {}, 0, []
        for day, items in days.items():
            distinct = set(items)
            if len(distinct) == 1 and 'INVALID' not in distinct:
                table[day] = items[0]
                duplicates += len(items) - 1
            else:
                ambiguous.append(day.isoformat())
        tables[session] = table
        first, last = min(table), max(table)
        missing = [d.isoformat() for d in day_grid(first, last + timedelta(days=1)) if d not in table]
        summary[session] = {'valid_draws': len(table), 'first': first.isoformat(), 'last': last.isoformat(),
                            'identical_duplicate_session_records': duplicates, 'ambiguous_dates': ambiguous,
                            'missing_calendar_dates_between_first_and_last': missing}
    return tables, {'source_rows': len(rows), 'first_date': min(dates).isoformat(), 'last_date': max(dates).isoformat(),
                    'short_numeric_values_zero_padded': shortened, 'malformed_values': problems, 'sessions': summary}


def day_grid(start, end):
    while start < end:
        yield start
        start += timedelta(days=1)


def chi_square_survival(statistic, degrees):
    """Regularized upper gamma, avoiding a new scientific-package dependency."""
    if statistic <= 0 or degrees <= 0:
        return 1.0
    a, x = degrees / 2, statistic / 2
    factor = math.exp(a * math.log(x) - x - math.lgamma(a))
    if x < a + 1:
        term = total = 1 / a
        for i in range(1, 10000):
            term *= x / (a + i)
            total += term
            if abs(term) < abs(total) * 1e-14:
                return min(1.0, max(0.0, 1 - total * factor))
    else:
        tiny = 1e-300
        b, c = x + 1 - a, 1 / tiny
        d = 1 / (b if abs(b) > tiny else tiny)
        h = d
        for i in range(1, 10000):
            numerator = -i * (i - a)
            b += 2
            d = numerator * d + b
            c = b + numerator / c
            d = 1 / (d if abs(d) > tiny else tiny)
            c = c if abs(c) > tiny else tiny
            change = d * c
            h *= change
            if abs(change - 1) < 1e-14:
                return min(1.0, max(0.0, factor * h))
    raise ValueError('gamma_convergence_failure')


def categorical_test(name, counts, expected):
    mask = expected > 0
    statistic = float(np.sum((counts[mask] - expected[mask]) ** 2 / expected[mask]))
    if counts.ndim == 1:
        degrees = int(mask.sum()) - 1
    else:
        degrees = (int(np.count_nonzero(counts.sum(axis=0))) - 1) * (int(np.count_nonzero(counts.sum(axis=1))) - 1)
    return {'name': name, 'statistic': statistic, 'degrees': degrees,
            'minimum_expected_count': float(expected[mask].min()),
            'p': chi_square_survival(statistic, degrees) if expected[mask].min() >= 5 else None}


def anomaly_tests(tables):
    tests, frequencies = [], {}
    sums = np.bincount([sum(x) for x in itertools.product(range(10), repeat=3)], minlength=28)
    for session, table in tables.items():
        ordered = sorted(table)
        digits = np.array([[int(c) for c in table[d]] for d in ordered])
        n = len(digits)
        frequencies[session] = []
        for position in range(3):
            counts = np.bincount(digits[:, position], minlength=10)
            frequencies[session].append(counts.tolist())
            tests.append(categorical_test(f'{session}:position{position+1}:uniform', counts, np.full(10, n/10)))
        total_counts = np.bincount(digits.sum(axis=1), minlength=28)
        tests.append(categorical_test(f'{session}:sum_distribution', total_counts, n * sums / 1000))
        for left, right in ((0, 1), (0, 2), (1, 2)):
            pairs = np.zeros((10, 10))
            np.add.at(pairs, (digits[:, left], digits[:, right]), 1)
            tests.append(categorical_test(f'{session}:within_positions{left+1}{right+1}', pairs,
                                         np.outer(pairs.sum(axis=1), pairs.sum(axis=0)) / pairs.sum()))
        for position in range(3):
            pairs = np.zeros((10, 10))
            for previous, current in zip(ordered, ordered[1:]):
                if current - previous == timedelta(days=1):
                    pairs[int(table[previous][position]), int(table[current][position])] += 1
            tests.append(categorical_test(f'{session}:lag1_position{position+1}', pairs,
                                         np.outer(pairs.sum(axis=1), pairs.sum(axis=0)) / pairs.sum()))
    common = sorted(set(tables['midday']) & set(tables['evening']))
    for position in range(3):
        pairs = np.zeros((10, 10))
        for day in common:
            pairs[int(tables['midday'][day][position]), int(tables['evening'][day][position])] += 1
        tests.append(categorical_test(f'midday_evening:position{position+1}', pairs,
                                     np.outer(pairs.sum(axis=1), pairs.sum(axis=0)) / pairs.sum()))
    for test in tests:
        test['bonferroni_p'] = min(1.0, test['p'] * len(tests)) if test['p'] is not None else None
    return {'family_size': len(tests), 'tests': tests, 'position_digit_counts': frequencies,
            'fair_sum_counts_per_1000': sums.tolist()}


def walk_forward(table, plan):
    counts = np.zeros((3, 10), dtype=int)
    history, ledger = deque(), []
    start, end = min(table), date.fromisoformat(plan['data_end_exclusive'])
    validation, final = date.fromisoformat(plan['validation_start']), date.fromisoformat(plan['test_start'])
    for day in day_grid(start, end):
        prediction = None
        if len(history) == plan['window_draws']:
            probabilities = (counts + plan['smoothing']) / (len(history) + 10 * plan['smoothing'])
            prediction = ''.join(str(x) for x in np.argmax(probabilities, axis=1))
        actual = table.get(day)
        if day >= validation:
            row = {'date': day.isoformat(), 'period': 'validation' if day < final else 'final',
                   'prediction': prediction, 'actual': actual, 'status': 'WARMUP_OR_UNKNOWN_HISTORY'}
            if prediction is not None:
                row['status'] = 'OUTCOME_UNKNOWN' if actual is None else 'OBSERVED'
                if actual is not None:
                    prob = float(np.prod([probabilities[pos, int(c)] for pos, c in enumerate(actual)]))
                    row.update(log_score_delta=math.log(prob) + math.log(1000), hit=prediction == actual)
            ledger.append(row)
        if actual is None:
            history.clear()
            counts[:] = 0
            continue
        digits = tuple(map(int, actual))
        history.append(digits)
        for pos, digit in enumerate(digits):
            counts[pos, digit] += 1
        if len(history) > plan['window_draws']:
            old = history.popleft()
            for pos, digit in enumerate(old):
                counts[pos, digit] -= 1
    return ledger


def binomial_lower(hits, n, alpha=.05):
    if hits == 0 or n == 0:
        return 0.0
    if hits == n:
        return alpha ** (1/n)

    def tail(p):
        if p == 0:
            return 0.0
        term = math.exp(n * math.log1p(-p))
        cdf = term
        for k in range(hits - 1):
            term *= (n - k) * p / ((k + 1) * (1 - p))
            cdf += term
        return max(0.0, min(1.0, 1 - cdf))

    low, high = 0.0, hits/n
    for _ in range(80):
        middle = (low + high) / 2
        if tail(middle) < alpha:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def summarize(ledger, plan):
    observed = [row for row in ledger if row['status'] == 'OBSERVED']
    n, hits = len(observed), sum(row['hit'] for row in observed)
    unknown = sum(row['status'] == 'OUTCOME_UNKNOWN' for row in ledger)
    return {'calendar_session_days': len(ledger), 'scored_predictions': n, 'hits': hits,
            'unknown_eligible_outcomes': unknown,
            'unscored_due_to_history': sum(row['prediction'] is None for row in ledger),
            'mean_log_score_delta_vs_uniform': float(np.mean([row['log_score_delta'] for row in observed])) if n else None,
            'hit_rate': hits/n if n else None, 'binomial_one_sided_95_lower': binomial_lower(hits, n),
            'fair_expected_hits': n/1000,
            'current_payout_reference_net': hits * plan['reference_prize'] - n * plan['reference_stake'] if not unknown else None,
            'fair_expected_reference_net': -.5 * n}


def bootstrap(ledger, plan, block):
    by_day = {}
    for row in ledger:
        values = by_day.setdefault(row['date'], [0.0, 0])
        if row['status'] == 'OBSERVED':
            values[0] += row['log_score_delta']
            values[1] += 1
    if not by_day or sum(v[1] for v in by_day.values()) == 0:
        return {'status': 'INSUFFICIENT_OBSERVATIONS'}
    values = np.array([by_day[d] for d in sorted(by_day)])
    rng = np.random.default_rng(plan['bootstrap_seed'])
    means = []
    length = len(values)
    for _ in range(plan['bootstrap_repetitions']):
        starts = rng.integers(0, length, size=math.ceil(length/block))
        indices = ((starts[:, None] + np.arange(block)) % length).ravel()[:length]
        sampled = values[indices].sum(axis=0)
        if sampled[1] > 0:
            means.append(sampled[0]/sampled[1])
    if len(means) != plan['bootstrap_repetitions']:
        return {'status': 'INSUFFICIENT_BOOTSTRAP_REPLICATES'}
    return {'status': 'COMPLETE', 'block_calendar_days': block,
            'lower95': float(np.quantile(means, .025)), 'upper95': float(np.quantile(means, .975))}


def analyze(plan_path, raw_path, output):
    plan = json.loads(Path(plan_path).read_text())
    raw = json.loads(Path(raw_path).read_text())
    if digest(__file__) != plan['source_sha256'] or raw['plan_sha256'] != digest(plan_path) or raw['status'] != 'COMPLETE':
        raise ValueError('binding_or_download_failure')
    for receipt in raw['receipts']:
        if hashlib.sha256(base64.b64decode(receipt['response_base64'])).hexdigest() != receipt['response_sha256']:
            raise ValueError('raw_receipt_corruption')
    tables, data_audit = audit(raw['rows'], plan['data_end_exclusive'])
    ledgers = {session: walk_forward(table, plan) for session, table in tables.items()}
    periods = {}
    for period in ('validation', 'final'):
        pooled = []
        summaries = {}
        for session, ledger in ledgers.items():
            part = [row for row in ledger if row['period'] == period]
            summaries[session] = summarize(part, plan)
            pooled.extend(part)
        periods[period] = {'sessions': summaries, 'pooled': summarize(pooled, plan),
                           'log_score_intervals': {str(b): bootstrap(pooled, plan, b) for b in (14, 90)}}
    final, validation = periods['final'], periods['validation']
    evidence_complete = final['pooled']['scored_predictions'] >= 1000 and final['pooled']['unknown_eligible_outcomes'] == 0
    score_pass = (validation['pooled']['mean_log_score_delta_vs_uniform'] is not None
                  and validation['pooled']['mean_log_score_delta_vs_uniform'] > 0
                  and all(x['status'] == 'COMPLETE' and x['lower95'] > 0 for x in final['log_score_intervals'].values()))
    economic_pass = final['pooled']['binomial_one_sided_95_lower'] > plan['break_even_probability']
    result = {'plan_sha256': digest(plan_path), 'raw_sha256': digest(raw_path), 'data_audit': data_audit,
              'exploratory_anomaly_tests': anomaly_tests(tables), 'periods': periods,
              'predictive_gate': 'PASS_CANDIDATE' if evidence_complete and score_pass else 'NOT_DEMONSTRATED' if evidence_complete else 'INCOMPLETE',
              'economic_gate': 'PASS_CANDIDATE' if evidence_complete and score_pass and economic_pass else 'NOT_DEMONSTRATED' if evidence_complete else 'INCOMPLETE',
              'ledgers': ledgers, 'limits': plan['limits'], 'acceptance': 'READY_FOR_INDEPENDENT_REVIEW',
              'money_spent_on_wagers': 0, 'reference_outcomes_not_actual_money': True}
    if digest(__file__) != plan['source_sha256'] or raw['plan_sha256'] != digest(plan_path):
        raise ValueError('source_or_plan_changed')
    save(output, result)
    compact = {session: {k: v for k, v in info.items() if not isinstance(v, list)}
               for session, info in data_audit['sessions'].items()}
    print(json.dumps({'source_rows': data_audit['source_rows'], 'audit_sessions': compact,
                      'malformed_values': len(data_audit['malformed_values']), 'periods': periods,
                      'predictive_gate': result['predictive_gate'], 'economic_gate': result['economic_gate']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['freeze', 'collect', 'analyze'])
    parser.add_argument('paths', nargs='+')
    args = parser.parse_args()
    {'freeze': freeze, 'collect': collect, 'analyze': analyze}[args.action](*args.paths)
