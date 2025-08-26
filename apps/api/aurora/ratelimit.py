from __future__ import annotations

from typing import Dict, Tuple
import time

from .config import settings

# Tiny in-memory rate limiter (best-effort; replace with Redis in prod)
_BUCKETS: Dict[Tuple[str, str], Tuple[int, float]] = {}


def allow(key: str, route: str) -> bool:
    if not settings.rate_limit_enabled:
        return True
    limit = max(1, int(settings.rate_limit_per_minute))
    now = time.time()
    k = (key, route)
    count, ts = _BUCKETS.get(k, (0, now))
    if now - ts > 60:
        _BUCKETS[k] = (1, now)
        return True
    if count < limit:
        _BUCKETS[k] = (count + 1, ts)
        return True
    return False
