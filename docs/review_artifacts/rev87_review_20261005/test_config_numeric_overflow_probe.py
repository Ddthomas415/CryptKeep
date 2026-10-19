"""Isolated config-function probe; no production imports or operator state."""
import ast
import math
from pathlib import Path
import unittest


SOURCE = Path('/private/tmp/cryptkeep-rev87-candidate-20261005/services/execution/paper_engine.py')


def isolated_config(value):
    tree = ast.parse(SOURCE.read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_cfg')
    namespace = {
        'math': math,
        '_NOT_MAPPING': frozenset({'config_not_mapping', 'paper_trading_not_mapping'}),
        '_CONFIG_ERRORS_LOGGED': set(),
        '_LOG': type('QuietLogger', (), {'warning': lambda *args, **kwargs: None})(),
        'load_user_yaml': lambda **kwargs: {'paper_trading': value},
    }
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), 'exec'), namespace)
    return namespace['_cfg']()


class NumericConfigProbe(unittest.TestCase):
    def test_normal_config(self):
        self.assertEqual(isolated_config({'fee_bps': 7.5})['fee_bps'], 7.5)

    def assert_controlled_refusal(self, setting):
        try:
            config = isolated_config({setting: 10 ** 1000})
        except Exception as error:
            self.fail(f'{setting}: config creation escaped with {type(error).__name__}')
        self.assertIn(setting, config['config_error'])

    def test_fee_overflow(self):
        self.assert_controlled_refusal('fee_bps')

    def test_slippage_overflow(self):
        self.assert_controlled_refusal('slippage_bps')

    def test_cash_overflow(self):
        self.assert_controlled_refusal('starting_cash_quote')

    def test_quantity_overflow(self):
        self.assert_controlled_refusal('max_order_qty')


if __name__ == '__main__':
    unittest.main()
