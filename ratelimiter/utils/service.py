from typing import Mapping

from ratelimiter.models.tier import Tier
from ratelimiter.models.user import User
from ratelimiter.limiters.rate_limiter import RateLimiter


class RateLimitService:
    def __init__(self, rate_limiters: Mapping[Tier, RateLimiter]):
        self.rate_limiters = rate_limiters

    def is_request_allowed(self, user: User) -> bool:
        """
        Check if the request for the given user is allowed based on their tier's rate limiting rules.

        :param user: The User object containing user information and tier.
        :return: True if the request is allowed, False otherwise.
        """
        key = f"{user.tier.value}:{user.user_id}"
        limiter = self.rate_limiters.get(user.tier)
        if limiter is None:
            # no limiter configured for this tier — default to allowed
            return True
        return limiter.is_allowed(key)
    