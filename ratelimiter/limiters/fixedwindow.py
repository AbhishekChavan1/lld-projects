import threading
import time
from collections import defaultdict

from .rate_limiter import RateLimiter


class FixedWindow(RateLimiter):
    def __init__(self, limit: int, window: float):
        super().__init__()
        self.lock = threading.Lock()
        self.limit = limit
        self.window = window
        self.windows: dict[str, dict] = {}

    def is_allowed(self, key: str) -> bool:
        with self.lock:
            current_time = time.time()
            if key not in self.windows:
                self.windows[key] = {"start": current_time, "count": 0}

            entry = self.windows[key]
            if current_time - entry["start"] >= self.window:
                entry["start"] = current_time
                entry["count"] = 0

            if entry["count"] < self.limit:
                entry["count"] += 1
                return True
            return False

