import pytest

from scripts.research.liquidation_data_probe import MINUTE, completed_candles, coverage, records


def event(t=1):
    return {'timestamp': t, 'position_side': 'long', 'side': 'sell'}


def test_direction_identity_and_bankruptcy_price_not_market_price():
    group = {'instId': 'BTC-USDT-SWAP', 'instType': 'SWAP',
             'details': [{'ts': '1', 'posSide': 'long', 'side': 'sell', 'bkPx': '1'}]}
    rows = records([group], 'BTC-USDT-SWAP', 100)
    assert rows[0]['raw']['bkPx'] == '1'
    assert 'entry_price' not in rows[0]
    assert 'return' not in rows[0]
    with pytest.raises(ValueError, match='instrument'):
        records([group], 'ETH-USDT-SWAP', 100)
    group['details'][0]['side'] = 'buy'
    with pytest.raises(ValueError, match='direction'):
        records([group], 'BTC-USDT-SWAP', 100)


def test_post_cutoff_events_do_not_enter_frozen_sample():
    group = {'instId': 'BTC-USDT-SWAP', 'instType': 'SWAP',
             'details': [{'ts': '100', 'posSide': 'long', 'side': 'sell'}]}
    assert records([group], 'BTC-USDT-SWAP', 100) == []


def test_match_starts_after_event_and_needs_all_minutes():
    bars = {i * MINUTE: ['available'] for i in range(1, 16)}
    assert coverage([event()], bars, bars, 20 * MINUTE, [1, 5, 15])['matched_long_sell_records'] == 1
    del bars[7 * MINUTE]
    result = coverage([event()], bars, bars, 20 * MINUTE, [1, 5, 15])
    assert result['matched_long_sell_records'] == 0
    assert result['missing_price_records'] == 1


def test_incomplete_forward_window_is_immature_not_failed_recovery():
    result = coverage([event()], {}, {}, MINUTE, [1, 5, 15])
    assert result['immature_records'] == 1
    assert result['missing_price_records'] == 0


def test_price_grid_refuses_unconfirmed_or_invalid_values():
    candle = [MINUTE, '100', '101', '99', '100', '1', '1', '1', '0']
    assert completed_candles([candle], 3 * MINUTE) == {}
    candle[-1] = '1'
    assert MINUTE in completed_candles([candle], 3 * MINUTE)
    candle[1] = 'nan'
    with pytest.raises(ValueError, match='invalid_candle'):
        completed_candles([candle], 3 * MINUTE)


def test_many_records_in_one_minute_are_not_independent_episodes():
    result = coverage([event(1), event(2), event(3)], {}, {}, 20 * MINUTE, [1, 5, 15])
    assert result['long_sell_records'] == 3
    assert result['long_sell_minute_bins'] == 1
