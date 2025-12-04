"""
Tests for Rate Limiting functionality
"""

import time
import pytest
from autopr.security.rate_limiting import RateLimiter, rate_limit, get_rate_limiter


@pytest.fixture(autouse=True)
def reset_global_rate_limiter():
    """Reset the global rate limiter before each test to ensure test isolation."""
    import autopr.security.rate_limiting as rate_limiting_module
    rate_limiting_module._rate_limiter = None
    yield
    rate_limiting_module._rate_limiter = None


class TestRateLimiter:
    """Test RateLimiter class."""
    
    def test_basic_rate_limiting(self):
        """Test basic rate limiting functionality."""
        limiter = RateLimiter(default_limit=5, window_seconds=60)
        
        # First 5 requests should be allowed
        for i in range(5):
            allowed, info = limiter.is_allowed("test_key")
            assert allowed, f"Request {i+1} should be allowed"
            assert info["remaining"] == 4 - i
        
        # 6th request should be blocked
        allowed, info = limiter.is_allowed("test_key")
        assert not allowed, "6th request should be blocked"
        assert info["remaining"] == 0
        assert info["retry_after"] > 0
    
    def test_different_keys(self):
        """Test rate limiting with different keys."""
        limiter = RateLimiter(default_limit=5, window_seconds=60)
        
        # Use up limit for key1
        for _ in range(5):
            allowed, _ = limiter.is_allowed("key1")
            assert allowed
        
        # key1 should be blocked
        allowed, _ = limiter.is_allowed("key1")
        assert not allowed
        
        # key2 should still be allowed
        allowed, _ = limiter.is_allowed("key2")
        assert allowed
    
    def test_tiered_limits(self):
        """Test tiered rate limiting."""
        limiter = RateLimiter(default_limit=100, window_seconds=60)
        
        # Anonymous tier (10/min)
        allowed, info = limiter.is_allowed("user1", tier="anonymous")
        assert allowed
        assert info["limit"] == 10
        
        # Authenticated tier (100/min)
        allowed, info = limiter.is_allowed("user2", tier="authenticated")
        assert allowed
        assert info["limit"] == 100
        
        # Premium tier (1000/min)
        allowed, info = limiter.is_allowed("user3", tier="premium")
        assert allowed
        assert info["limit"] == 1000
    
    def test_custom_limit(self):
        """Test custom limit override."""
        limiter = RateLimiter(default_limit=100, window_seconds=60)
        
        # Custom limit should override default
        allowed, info = limiter.is_allowed("test_key", limit=3)
        assert allowed
        assert info["limit"] == 3
        
        # Use up custom limit
        limiter.is_allowed("test_key", limit=3)
        limiter.is_allowed("test_key", limit=3)
        
        # Should be blocked now
        allowed, info = limiter.is_allowed("test_key", limit=3)
        assert not allowed
    
    def test_window_expiry(self):
        """Test that old requests expire."""
        limiter = RateLimiter(default_limit=2, window_seconds=1)
        
        # Use up limit
        limiter.is_allowed("test_key")
        limiter.is_allowed("test_key")
        
        # Should be blocked
        allowed, _ = limiter.is_allowed("test_key")
        assert not allowed
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again
        allowed, info = limiter.is_allowed("test_key")
        assert allowed
        assert info["remaining"] == 1
    
    def test_reset(self):
        """Test rate limit reset."""
        limiter = RateLimiter(default_limit=2, window_seconds=60)
        
        # Use up limit
        limiter.is_allowed("test_key")
        limiter.is_allowed("test_key")
        
        # Should be blocked
        allowed, _ = limiter.is_allowed("test_key")
        assert not allowed
        
        # Reset limit
        limiter.reset("test_key")
        
        # Should be allowed again
        allowed, _ = limiter.is_allowed("test_key")
        assert allowed
    
    def test_rate_limit_info(self):
        """Test rate limit info dictionary."""
        limiter = RateLimiter(default_limit=10, window_seconds=60)
        
        allowed, info = limiter.is_allowed("test_key")
        
        # Check all required fields
        assert "limit" in info
        assert "remaining" in info
        assert "reset" in info
        assert "retry_after" in info
        
        # Check values
        assert info["limit"] == 10
        assert info["remaining"] == 9  # 1 used
        assert info["reset"] > time.time()
        assert info["retry_after"] == 0  # Allowed, so no retry


class TestRateLimitDecorator:
    """Test rate_limit decorator."""
    
    @pytest.mark.asyncio
    async def test_async_decorator(self):
        """Test decorator on async function."""
        call_count = 0
        
        @rate_limit(limit=3, window=60)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        # First 3 calls should succeed
        for i in range(3):
            result = await test_func()
            assert result == "success"
            assert call_count == i + 1
        
        # 4th call should raise exception
        with pytest.raises(Exception, match="Rate limit exceeded"):
            await test_func()
    
    def test_sync_decorator(self):
        """Test decorator on sync function."""
        call_count = 0
        
        @rate_limit(limit=3, window=60)
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        # First 3 calls should succeed
        for i in range(3):
            result = test_func()
            assert result == "success"
            assert call_count == i + 1
        
        # 4th call should raise exception
        with pytest.raises(Exception, match="Rate limit exceeded"):
            test_func()


class TestGlobalRateLimiter:
    """Test global rate limiter instance."""
    
    def test_get_rate_limiter(self):
        """Test getting global rate limiter."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        # Should be same instance
        assert limiter1 is limiter2
    
    def test_shared_state(self):
        """Test that global limiter maintains state."""
        limiter = get_rate_limiter()
        
        # Use some requests
        limiter.is_allowed("shared_key", limit=5)
        limiter.is_allowed("shared_key", limit=5)
        
        # Get limiter again
        limiter2 = get_rate_limiter()
        
        # Should have same state
        allowed, info = limiter2.is_allowed("shared_key", limit=5)
        assert allowed
        assert info["remaining"] == 2  # 3 used (including this one)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
