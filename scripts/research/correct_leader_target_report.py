"""Correct reporting omissions without modifying the frozen test or results."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from scripts.research.leader_target_test import DAY, summary


def corrected_summary(events):
    result = summary(events)
    result['average_closed_net_usd'] = result.pop('average_net_usd')
    result['worst_closed_net_usd'] = result.pop('worst_net_usd')
    result['closed_net_winners'] = result.pop('net_winners')
    entered = [e for e in events if 'entry_time' in e]
    unresolved = [e for e in entered if 'net_pnl_usd' not in e]
    marks = [e['last_mark_net_pnl_usd'] for e in unresolved if 'last_mark_net_pnl_usd' in e]
    result['unresolved_entered_events'] = len(unresolved)
    result['unresolved_without_mark'] = len(unresolved)-len(marks)
    result['unresolved_last_mark_sum_usd'] = sum(marks)
    result['closed_plus_last_marks_sum_usd_not_portfolio'] = result['sum_closed_net_usd_not_portfolio']+sum(marks)
    result['marked_event_denominator'] = result['closed_trades']+len(marks)
    result['average_closed_plus_last_marks_usd'] = (
        result['closed_plus_last_marks_sum_usd_not_portfolio']/result['marked_event_denominator']
        if result['marked_event_denominator'] else None)
    return result


def correct(original, raw):
    result = deepcopy(original)
    series = {s: {int(b['start']): b for b in value['raw']['candles']}
              for s, value in raw['markets'].items() if 'raw' in value}
    for run in result['runs']:
        for segment in run['segments']:
            t = segment['end']-DAY
            candidates = [(s, float(bars[t]['close'])/float(bars[t-DAY]['close'])-1)
                          for s, bars in series.items() if t in bars and t-DAY in bars
                          and float(bars[t-DAY]['close']) > 0 and float(bars[t]['volume']) > 0]
            symbol, gain = max(candidates, key=lambda x: x[1])
            events = segment['events']+[{'leader_bar': t, 'symbol': symbol,
                                        'leader_gain': gain, 'status': 'WAITING_AT_SEGMENT_END'}]
            segment.update(corrected_summary(events))
            for key in ('average_net_usd', 'worst_net_usd', 'net_winners'):
                segment.pop(key, None)
        run['combined'] = corrected_summary([e for segment in run['segments'] for e in segment['events']])
    return result


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[2]
    source = root/'research/leader_target_results_20261012.json'
    dataset = root/'research/coinbase_leader_daily_repaired_20261012.json'
    result = correct(json.loads(source.read_text()), json.loads(dataset.read_text()))
    result['report_correction_source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    result['report_correction_script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['correction'] = 'Terminal leaders restored; closed-only labels explicit; unresolved marks not realized PnL'
    with (root/'research/leader_target_results_corrected_20261012.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    for row in result['runs']:
        c = row['combined']
        print(row['pullback'], row['target'], row['hold'], c['leader_events'],
              round(c['average_closed_net_usd'], 2), round(c['average_closed_plus_last_marks_usd'], 2))
