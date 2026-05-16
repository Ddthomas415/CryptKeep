"""Compatibility shim for legacy services.execution.intent_executor imports.

Canonical implementation now lives in services.execution.compat.intent_executor.
This aliases the module object so private test-patched names like _killswitch_state remain available.
"""

import sys
from services.execution.compat import intent_executor as _impl

sys.modules[__name__] = _impl
