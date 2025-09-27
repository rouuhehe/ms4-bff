import time
from typing import Callable, Coroutine, Any

class CircuitOpen(Exception):
    pass

class CircuitBreaker:
    def __init__(self, fail_max: int = 5, reset_timeout: int = 30):
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self._failures = 0
        self._state = "CLOSED"  # CLOSED, OPEN, HALF
        self._opened_at = 0.0

    async def call(self, coro_fn: Callable[[], Coroutine[Any, Any, Any]]):
        now = time.time()
        if self._state == "OPEN":
            if now - self._opened_at < self.reset_timeout:
                raise CircuitOpen("circuit open")
            else:
                self._state = "HALF"

        try:
            result = await coro_fn()
        except Exception:
            self._record_failure()
            raise
        else:
            self._record_success()
            return result

    def _record_failure(self):
        self._failures += 1
        if self._failures >= self.fail_max:
            self._state = "OPEN"
            self._opened_at = time.time()

    def _record_success(self):
        self._failures = 0
        self._state = "CLOSED"