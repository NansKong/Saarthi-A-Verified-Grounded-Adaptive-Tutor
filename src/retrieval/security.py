"""Small, dependency-free protections for a demo server that holds a paid API key."""
from __future__ import annotations

import hmac
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class RateLimiter:
    """Sliding-window limiter per client key. In-memory and per-process: fine for one demo server."""

    def __init__(self, max_calls: int, window_s: float = 60.0, clock=time.monotonic):
        self.max, self.window, self._clock = max_calls, window_s, clock
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        if self.max <= 0:
            return
        now = self._clock()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.max:
                retry = max(1, int(self.window - (now - q[0])))
                raise HTTPException(status_code=429, detail="rate limit exceeded", headers={"Retry-After": str(retry)})
            q.append(now)
            if len(self._hits) > 10_000:  # bound memory: forget idle clients
                for k in [k for k, v in self._hits.items() if not v or now - v[-1] > self.window]:
                    del self._hits[k]


def make_admin_guard(token: str):
    """Dependency for endpoints that change state or spend money. No token configured => open (local dev)."""
    def guard(request: Request) -> None:
        if token and not hmac.compare_digest(request.headers.get("x-admin-token", ""), token):
            raise HTTPException(status_code=401, detail="admin token required (header X-Admin-Token)")
    return guard
