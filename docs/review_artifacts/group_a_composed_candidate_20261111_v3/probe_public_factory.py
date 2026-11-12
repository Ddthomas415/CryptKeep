"""Construct a fake public client from composed source; no network or keys."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import types


def run(tree):
    tree = Path(tree).resolve()
    if not tree.is_relative_to('/private/tmp'):
        raise ValueError('scratch_tree_required')
    with tempfile.TemporaryDirectory(prefix='cbp-public-factory-', dir='/private/tmp') as directory:
        os.environ.clear()
        os.environ.update(PATH='/usr/bin:/bin', LC_ALL='C', HOME=directory, CBP_STATE_DIR=directory)
        sys.path.insert(0, str(tree))
        created = []
        class FakeCoinbase:
            def __init__(self, settings):
                self.settings = settings
                created.append(self)
            def set_sandbox_mode(self, enabled):
                self.sandbox = enabled
        ccxt = types.ModuleType('ccxt')
        ccxt.coinbase = FakeCoinbase
        sys.modules['ccxt'] = ccxt
        from services.security import exchange_factory
        expected = tree/'services/security/exchange_factory.py'
        assert Path(exchange_factory.__file__).resolve() == expected
        client = exchange_factory.make_exchange('coinbase', {}, enable_rate_limit=True)
        assert len(created) == 1 and client.settings == {
            'enableRateLimit': True, 'apiKey': None, 'secret': None}
        assert client.sandbox is False
        return {'scope': 'synthetic_public_constructor_not_market_or_account_access',
                'factory_sha256': hashlib.sha256(expected.read_bytes()).hexdigest(),
                'client_constructors': len(created), 'credentials_supplied': False,
                'network_calls': 0, 'publisher_call_signature_compatible': True}


if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1]), sort_keys=True, indent=2))
