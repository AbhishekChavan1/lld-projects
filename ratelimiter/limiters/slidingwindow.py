import time
import threading
from .rate_limiter import RateLimiter
from collections import deque,defaultdict

class SlidingWindow(RateLimiter):
    def __init__(self, max_requests: int, time_window: float):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(deque)
        self.lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        with self.lock:
            current_time = time.time()
            request_times = self.requests[key]

            # Remove timestamps that are outside the time window
            while request_times and request_times[0] <= current_time - self.time_window:
                request_times.popleft()

            if len(request_times) < self.max_requests:
                request_times.append(current_time)
                return True
            else:
                return False
