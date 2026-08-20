# python-ratelimiter

A lightweight, thread-safe Python rate-limiting library that supports **multiple algorithms** and **per-user tiers**. Drop it into any service to throttle requests by user, IP, API key, or any identifier you choose.

## Features

- **Three classic rate-limiting algorithms** behind a single interface:
  - `FixedWindow` — simple counter per fixed time window.
  - `SlidingWindow` — precise rolling window using per-key timestamp deques.
  - `TokenBucket` — leaky-bucket style with continuous fractional refills.
- **Tier-based routing** — map users (or any subjects) to a limiter based on their tier (`BASIC`, `PREMIUM`, `ENTERPRISE`).
- **Thread-safe** — all limiters use internal locks, safe for concurrent use.
- **Pluggable** — implement `RateLimiter` to plug in your own algorithm.
- **Zero external dependencies** — pure Python stdlib.

## Installation

```bash
git clone https://github.com/AbhishekChavan1/python-ratelimiter.git
cd python-ratelimiter
```

No external dependencies are required. Just `import` the package.

## Quick Start

```python
from ratelimiter.utils.rlconfig import RLConfig
from ratelimiter.models.user import User
from ratelimiter.models.tier import Tier
from ratelimiter.limiters.fixedwindow import FixedWindow
from ratelimiter.limiters.slidingwindow import SlidingWindow
from ratelimiter.limiters.tokenbucket import TokenBucket
from ratelimiter.utils.service import RateLimitService

# Configure a different limiter per tier
limiters = {
    Tier.BASIC:      FixedWindow(limit=100, window=60.0),       # 100 req/min
    Tier.PREMIUM:    SlidingWindow(max_requests=200, time_window=60.0),  # 200 req/min
    Tier.ENTERPRISE: TokenBucket(capacity=500, refill_rate=10),  # burst 500, +10/sec
}

service = RateLimitService(limiters)

user = User(user_id="u1", tier=Tier.PREMIUM)
if service.is_request_allowed(user):
    # serve the request
    ...
else:
    # reject (HTTP 429, etc.)
    ...
```

A ready-to-run demo is included in `smoke.py`:

```bash
python smoke.py
```

## Algorithms

| Algorithm       | Best for                                              | Memory            | Burst behavior            |
|-----------------|-------------------------------------------------------|-------------------|---------------------------|
| `FixedWindow`   | Simple quota enforcement; cheap, predictable          | O(1)              | Allows up to `2*limit` across a window boundary |
| `SlidingWindow` | Smooth, accurate throttling                           | O(n) per key      | Strict — never exceeds `max_requests` |
| `TokenBucket`   | Bursty traffic with steady long-term rate             | O(k) keys         | Smooth bursts up to `capacity` |

### `FixedWindow`

Counts requests within fixed, non-overlapping time windows. Resets when the window expires.

```python
FixedWindow(limit=100, window=60.0)  # 100 requests per 60 seconds
```

### `SlidingWindow`

Stores per-key timestamp deques and evicts entries older than the time window. Guarantees no more than `max_requests` in any rolling `time_window`.

```python
SlidingWindow(max_requests=200, time_window=60.0)
```

### `TokenBucket`

Each key has a bucket that refills at `refill_rate` tokens/second up to `capacity`. One token is consumed per request.

```python
TokenBucket(capacity=500, refill_rate=10)  # 500 burst, +10/sec sustained
```

## Project Structure

```
ratelimiter/
├── __init__.py
├── main.py                       # wiring example (per-tier limiter map)
├── smoke.py                      # runnable demo
├── limiters/
│   ├── rate_limiter.py           # abstract base class
│   ├── fixedwindow.py
│   ├── slidingwindow.py
│   └── tokenbucket.py
├── models/
│   ├── __init__.py
│   ├── tier.py                   # Tier enum
│   └── user.py                   # User dataclass
└── utils/
    ├── rlconfig.py               # RLConfig dataclass
    └── service.py                # RateLimitService facade
```

## Extending

Implement the `RateLimiter` interface to add a custom algorithm:

```python
from ratelimiter.limiters.rate_limiter import RateLimiter

class MyLimiter(RateLimiter):
    def is_allowed(self, key: str) -> bool:
        # your logic here
        ...
```

Then register it in the service:

```python
limiters = {Tier.BASIC: MyLimiter(...), ...}
```

## Thread Safety

All bundled limiters use `threading.Lock` around their internal state, so they are safe to share across threads in a single process. For multi-process or distributed rate limiting, wrap a limiter with an external store (Redis, etc.) — not included in this library.

## License

MIT — see `LICENSE` (add one before publishing if needed).

## Author

[AbhishekChavan1](https://github.com/AbhishekChavan1)
