from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def retry(
    fn: Callable[[], T],
    *,
    retries: int = 3,
    base_delay_sec: float = 0.2,
    backoff: float = 2.0,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    last: BaseException | None = None
    for attempt in range(max(1, int(retries))):
        try:
            return fn()
        except retry_on as e:
            last = e
            if attempt >= int(retries) - 1:
                raise
            delay = float(base_delay_sec) * (float(backoff) ** attempt)
            time.sleep(max(0.0, delay))
    if last is not None:
        raise last
    raise RuntimeError("retry failed without exception")


async def retry_async(
    fn: Callable[[], "asyncio.Future[T] | Any"],
    *,
    retries: int = 3,
    base_delay_sec: float = 0.2,
    backoff: float = 2.0,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    last: BaseException | None = None
    for attempt in range(max(1, int(retries))):
        try:
            out = fn()
            if asyncio.iscoroutine(out):
                return await out  # type: ignore[return-value]
            return out
        except retry_on as e:
            last = e
            if attempt >= int(retries) - 1:
                raise
            delay = float(base_delay_sec) * (float(backoff) ** attempt)
            await asyncio.sleep(max(0.0, delay))
    if last is not None:
        raise last
    raise RuntimeError("retry_async failed without exception")
