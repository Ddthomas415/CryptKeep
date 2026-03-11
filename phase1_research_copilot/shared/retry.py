from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


def retry_sync(
    fn: Callable[[], T],
    *,
    retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
) -> T:
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except Exception:
            if attempt > retries:
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay = delay + random.random() * 0.1
            time.sleep(delay)


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
) -> T:
    attempt = 0
    while True:
        attempt += 1
        try:
            return await fn()
        except Exception:
            if attempt > retries:
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay = delay + random.random() * 0.1
            await asyncio.sleep(delay)
