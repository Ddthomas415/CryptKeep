"""Synthetic counterexamples for audit claims, not a corrected market simulator."""

import math
import unittest


class DiagnosticCounterexamples(unittest.TestCase):
    def test_one_way_cost_threshold_does_not_cover_round_trip(self):
        gross = 0.0044865
        cost = 0.0035
        net_per_entry_notional = gross - cost - (1 + gross) * cost
        self.assertLess(net_per_entry_notional, 0)
        break_even_fee = gross / (2 + gross)
        self.assertLess(break_even_fee, 0.00225)

    def test_post_open_holdings_misclassify_opening_gaps(self):
        closes = [100, 200, 100]
        post_open_holdings = [True, False]
        returns = [math.log(closes[i] / closes[i - 1]) for i in (1, 2)]
        old_in = sum(r for r, held in zip(returns, post_open_holdings) if held)
        old_out = sum(r for r, held in zip(returns, post_open_holdings) if not held)
        # Buy at 200 after the first gap; sell at 100 after the second gap.
        actual_held_return = math.log(100 / 200)
        self.assertGreater(old_in, 0)
        self.assertLess(old_out, 0)
        self.assertLess(actual_held_return, 0)
        self.assertNotEqual(old_in, actual_held_return)

    def test_delayed_exit_dollars_need_original_position_quantity(self):
        notional, entry, blocked_exit, actual_exit = 100, 50, 80, 60
        old_dollars = (actual_exit / blocked_exit - 1) * notional
        quantity = notional / entry
        actual_delay_effect = quantity * (actual_exit - blocked_exit)
        self.assertEqual(old_dollars, -25)
        self.assertEqual(actual_delay_effect, -40)
        self.assertNotEqual(old_dollars, actual_delay_effect)


if __name__ == "__main__":
    unittest.main()
