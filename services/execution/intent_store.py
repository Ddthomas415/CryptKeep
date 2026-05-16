"""Compatibility shim for legacy services.execution.intent_store imports.

Canonical implementation now lives in services.execution.compat.intent_store.
This aliases the module object so private test-patched names like _connect remain available.
"""

import sys
from services.execution.compat import intent_store as _impl

sys.modules[__name__] = _impl
