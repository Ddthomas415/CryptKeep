"""Check reported trade arithmetic, not market provenance or strategy validity."""
import json
from pathlib import Path

source = Path('/private/tmp/cryptkeep-shared-unique-20261005/02031bde9876221a-result.json')
data = json.loads(source.read_text())
rate = data['fee_bps'] / 10000
arm = data['arms']['sma200_signal_only']
cash = data['initial_cash_usd']
entry = None
closed = []
for trade in arm['trades']:
    notional = trade['qty'] * trade['price']
    fee = notional * rate
    if trade['side'] == 'buy':
        if entry is not None:
            raise ValueError('Unexpected overlapping buys in signal-only artifact')
        entry = notional + fee
        cash -= entry
    elif trade['side'] == 'sell':
        if entry is None:
            raise ValueError('Sell has no preceding buy')
        proceeds = notional - fee
        cash += proceeds
        closed.append(proceeds - entry)
        entry = None
    else:
        raise ValueError('Unknown trade side')
report = {
    'scope': 'SUPPLIED_PRICE_ARITHMETIC_ONLY',
    'closed_net': closed, 'closed_net_total': sum(closed),
    'closed_net_winners': sum(value > 0 for value in closed), 'remaining_cash': cash,
    'open_position': entry is not None,
    'reported_terminal_net': arm['net_after_terminal_liquidation'],
    'reported_terminal_equity_less_initial': arm['terminal_liquidation_equity'] - data['initial_cash_usd'],
    'limitations': 'Recorded modeled prices only; no fresh fees, archive source or live fills verified',
}
Path(__file__).with_name('supplied_economic_arithmetic.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
