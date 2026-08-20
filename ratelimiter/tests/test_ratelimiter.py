import time

import pytest

from ratelimiter.limiters.fixedwindow import FixedWindow
from ratelimiter.limiters.slidingwindow import SlidingWindow
from ratelimiter.limiters.tokenbucket import TokenBucket
from ratelimiter.models.tier import Tier
from ratelimiter.models.user import User
from ratelimiter.utils.service import RateLimitService


class TestFixedWindow:
    def test_allows_within_limit(self):
        fw = FixedWindow(limit=3, window=60.0)
        assert fw.is_allowed("user1") is True
        assert fw.is_allowed("user1") is True
        assert fw.is_allowed("user1") is True

    def test_blocks_over_limit(self):
        fw = FixedWindow(limit=2, window=60.0)
        assert fw.is_allowed("user1") is True
        assert fw.is_allowed("user1") is True
        assert fw.is_allowed("user1") is False

    def test_per_key_isolation(self):
        fw = FixedWindow(limit=1, window=60.0)
        assert fw.is_allowed("user1") is True
        assert fw.is_allowed("user2") is True
        assert fw.is_allowed("user1") is False
        assert fw.is_allowed("user2") is False

    def test_window_reset(self):
        fw = FixedWindow(limit=1, window=0.1)
        assert fw.is_allowed("user1") is True
        assert fw.is_allowed("user1") is False
        time.sleep(0.15)
        assert fw.is_allowed("user1") is True


class TestSlidingWindow:
    def test_allows_within_limit(self):
        sw = SlidingWindow(max_requests=3, time_window=60.0)
        assert sw.is_allowed("user1") is True
        assert sw.is_allowed("user1") is True
        assert sw.is_allowed("user1") is True

    def test_blocks_over_limit(self):
        sw = SlidingWindow(max_requests=2, time_window=60.0)
        assert sw.is_allowed("user1") is True
        assert sw.is_allowed("user1") is True
        assert sw.is_allowed("user1") is False

    def test_per_key_isolation(self):
        sw = SlidingWindow(max_requests=1, time_window=60.0)
        assert sw.is_allowed("user1") is True
        assert sw.is_allowed("user2") is True
        assert sw.is_allowed("user1") is False

    def test_window_expiry(self):
        sw = SlidingWindow(max_requests=1, time_window=0.1)
        assert sw.is_allowed("user1") is True
        assert sw.is_allowed("user1") is False
        time.sleep(0.15)
        assert sw.is_allowed("user1") is True


class TestTokenBucket:
    def test_allows_within_capacity(self):
        tb = TokenBucket(capacity=3, refill_rate=100.0)
        assert tb.is_allowed("user1") is True
        assert tb.is_allowed("user1") is True
        assert tb.is_allowed("user1") is True

    def test_blocks_when_empty(self):
        tb = TokenBucket(capacity=1, refill_rate=0.0)
        assert tb.is_allowed("user1") is True
        assert tb.is_allowed("user1") is False

    def test_refill(self):
        tb = TokenBucket(capacity=1, refill_rate=100.0)
        assert tb.is_allowed("user1") is True
        assert tb.is_allowed("user1") is False
        time.sleep(0.05)
        assert tb.is_allowed("user1") is True

    def test_per_key_isolation(self):
        tb = TokenBucket(capacity=1, refill_rate=0.0)
        assert tb.is_allowed("user1") is True
        assert tb.is_allowed("user2") is True
        assert tb.is_allowed("user1") is False
        assert tb.is_allowed("user2") is False


class TestRateLimitService:
    def test_routes_to_correct_limiter(self):
        limiters = {
            Tier.BASIC: FixedWindow(limit=1, window=60.0),
            Tier.PREMIUM: FixedWindow(limit=2, window=60.0),
        }
        service = RateLimitService(limiters)
        basic_user = User(user_id="u1", tier=Tier.BASIC)
        premium_user = User(user_id="u2", tier=Tier.PREMIUM)

        assert service.is_request_allowed(basic_user) is True
        assert service.is_request_allowed(basic_user) is False
        assert service.is_request_allowed(premium_user) is True
        assert service.is_request_allowed(premium_user) is True
        assert service.is_request_allowed(premium_user) is False

    def test_unknown_tier_defaults_to_allowed(self):
        service = RateLimitService({})
        user = User(user_id="u1", tier=Tier.BASIC)
        assert service.is_request_allowed(user) is True
