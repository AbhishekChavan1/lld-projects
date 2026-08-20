import threading
import time
from dataclasses import dataclass
from .rate_limiter import RateLimiter


@dataclass
class _BucketState:
    tokens: float
    capacity: int
    refill_rate: float
    last_refill_timestamp: float


class TokenBucket(RateLimiter):
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = float(refill_rate)
        self.buckets: dict[str, _BucketState] = {}
        self.lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        with self.lock:
            now = time.time()
            if key not in self.buckets:
                self.buckets[key] = _BucketState(tokens=float(self.capacity), capacity=self.capacity, refill_rate=self.refill_rate, last_refill_timestamp=now)

            bucket = self.buckets[key]
            elapsed = now - bucket.last_refill_timestamp
            # refill fractional tokens
            bucket.tokens = min(bucket.capacity, bucket.tokens + elapsed * bucket.refill_rate)
            bucket.last_refill_timestamp = now

            if bucket.tokens >= 1.0:
                bucket.tokens -= 1.0
                return True
            return False