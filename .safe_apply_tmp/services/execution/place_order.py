from __future__ import annotations

from typing import Any, Optional, Dict

# The ONLY file allowed to call `.create_order(` directly.
# Everything else must call place_order/place_order_async.

def place_order(ex: Any, *args: Any, **kwargs: Any) -> Any:
    return ex.create_order(*args, **kwargs)

async def place_order_async(ex: Any, *args: Any, **kwargs: Any) -> Any:
    return await ex.create_order(*args, **kwargs)
