from ratelimiter.models.user import User
from ratelimiter.models.tier import Tier
from ratelimiter.utils.rlconfig import RLConfig
from ratelimiter.limiters.fixedwindow import FixedWindow
from ratelimiter.limiters.slidingwindow import SlidingWindow
from ratelimiter.limiters.tokenbucket import TokenBucket
from ratelimiter.utils.service import RateLimitService


def main():
    basic_config = RLConfig(window_size=60.0, max_requests=100)
    premium_config = RLConfig(window_size=60.0, max_requests=200)
    enterprise_config = RLConfig(window_size=60.0, max_requests=500)

    basic_limiter = FixedWindow(limit=basic_config.max_requests, window=basic_config.window_size)
    premium_limiter = SlidingWindow(max_requests=premium_config.max_requests, time_window=premium_config.window_size)
    enterprise_limiter = TokenBucket(capacity=enterprise_config.max_requests, refill_rate=10)

    rate_limiters = {
        Tier.BASIC: basic_limiter,
        Tier.PREMIUM: premium_limiter,
        Tier.ENTERPRISE: enterprise_limiter,
    }
    service = RateLimitService(rate_limiters)

    basic_user = User(user_id="user1", tier=Tier.BASIC)
    premium_user = User(user_id="user2", tier=Tier.PREMIUM)
    enterprise_user = User(user_id="user3", tier=Tier.ENTERPRISE)

    for user in [basic_user, premium_user, enterprise_user]:
        results = [service.is_request_allowed(user) for _ in range(5)]
        print(f"{user.tier.value} ({user.user_id}): {results}")


if __name__ == "__main__":
    main()