import time
from dataclasses import dataclass, field


@dataclass
class WindowData:
    count: int = 0
    window_start: float = field(default_factory=time.time)


class RateLimitStore:

    def __init__(self):
        self._store: dict[str, WindowData] = {}

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """
        Checks if request is allowed.
        Returns (is_allowed, retry_after_seconds)

        Logic:
        1. Get or create window for this key
        2. Check if window has expired → reset if yes
        3. Check if count < limit → allow and increment
        4. If count >= limit → block and return retry_after
        """
        now = time.time()
        
        # Get existing window or create fresh one
        if key not in self._store:
            self._store[key] = WindowData(count=0, window_start=now)

        window = self._store[key]
        elapsed = now - window.window_start

        # Window expired → reset it
        if elapsed >= window_seconds:
            window.count = 0
            window.window_start = now

        # Under limit → allow
        if window.count < limit:
            window.count += 1
            return True, 0

        # Over limit → block
        retry_after = int(window_seconds - elapsed)
        return False, retry_after

    def get_remaining(self, key: str, limit: int) -> int:
        """How many requests left in current window."""
        if key not in self._store:
            return limit
        return max(0, limit - self._store[key].count)

    def get_reset_time(self, key: str, window_seconds: int) -> int:
        """Unix timestamp when window resets."""
        if key not in self._store:
            return int(time.time() + window_seconds)
        return int(self._store[key].window_start + window_seconds)


# Single instance shared across all requests
rate_limit_store = RateLimitStore()