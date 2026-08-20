# smoke.py
from ratelimiter.limiters.fixedwindow import FixedWindow
from ratelimiter.limiters.slidingwindow import SlidingWindow
from ratelimiter.limiters.tokenbucket import TokenBucket
from ratelimiter.utils.rlconfig import RLConfig
from ratelimiter.models.tier import Tier
from ratelimiter.models.user import User
from ratelimiter.utils.service import RateLimitService

basicCfg = RLConfig(window_size=60.0, max_requests=5)
fw = FixedWindow(limit=basicCfg.max_requests, window=basicCfg.window_size)
sw = SlidingWindow(max_requests=5, time_window=60.0)
tb = TokenBucket(capacity=5, refill_rate=1.0)

limiters = {Tier.BASIC: fw, Tier.PREMIUM: sw, Tier.ENTERPRISE: tb}
service = RateLimitService(limiters)

user = User(user_id="u1", tier=Tier.BASIC)
for i in range(7):
    print(i, service.is_request_allowed(user))