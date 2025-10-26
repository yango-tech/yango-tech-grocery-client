import asyncio
import time
import unittest

from yango_tech_grocery_client.rate_limiter import MethodRateLimiter


# TODO: make working tests environment
class TestRateLimiter(unittest.IsolatedAsyncioTestCase):
    """
    Test suite for MethodRateLimiter class.
    Run `python -m unittest -v <test_path>` to run the test.
    For example: `python -m unittest -v src.services.yango.tests.test_rate_limiter`
    """

    async def test_rate_limiter_basic(self) -> None:
        """
        Test that rate limiter allows up to max_rps requests per second.
        """
        max_rps = 5
        limiter = MethodRateLimiter(max_rps)
        endpoint = '/test/endpoint'
        token = 'test_token'

        # Make max_rps requests - should all pass immediately
        start_time = time.time()
        for _ in range(max_rps):
            await limiter.acquire(endpoint, token)

        elapsed = time.time() - start_time
        # Should be almost immediate (less than 0.1 seconds)
        self.assertLess(elapsed, 0.1, 'Expected immediate execution')

        # Check current RPS
        current_rps = limiter.get_current_rps(endpoint, token)
        self.assertEqual(current_rps, max_rps, f'Expected {max_rps} RPS')

    async def test_rate_limiter_exceed_limit(self) -> None:
        """Test that rate limiter waits when exceeding the limit"""
        max_rps = 2
        limiter = MethodRateLimiter(max_rps)
        endpoint = '/test/endpoint'
        token = 'test_token'

        # Make max_rps requests - should pass immediately
        start_time = time.time()
        for _ in range(max_rps):
            await limiter.acquire(endpoint, token)

        # Make max_rps + 1 request - should wait for the oldest request to expire
        await limiter.acquire(endpoint, token)
        elapsed = time.time() - start_time

        # Should wait about 1 second (between 0.9 and 1.1 seconds is reasonable)
        self.assertGreaterEqual(elapsed, 0.9, 'Expected to wait at least 0.9 seconds')
        self.assertLessEqual(elapsed, 1.1, 'Expected to wait at most 1.1 seconds')

    async def test_rate_limiter_multiple_endpoints(self) -> None:
        """Test that rate limiter works independently for different endpoints"""
        max_rps = 3
        limiter = MethodRateLimiter(max_rps)
        endpoint1 = '/endpoint/1'
        endpoint2 = '/endpoint/2'
        token = 'test_token'

        # Make max_rps requests for endpoint1 - should pass immediately
        start_time = time.time()
        for _ in range(max_rps):
            await limiter.acquire(endpoint1, token)

        # Make max_rps requests for endpoint2 - should also pass immediately
        for _ in range(max_rps):
            await limiter.acquire(endpoint2, token)

        elapsed = time.time() - start_time
        # Should be almost immediate since they're different endpoints
        self.assertLess(elapsed, 0.1, 'Expected immediate execution')

        # Check RPS for both endpoints
        rps1 = limiter.get_current_rps(endpoint1, token)
        rps2 = limiter.get_current_rps(endpoint2, token)
        self.assertEqual(rps1, max_rps, f'Expected {max_rps} RPS for endpoint1')
        self.assertEqual(rps2, max_rps, f'Expected {max_rps} RPS for endpoint2')

    async def test_rate_limiter_multiple_tokens(self) -> None:
        """Test that rate limiter works independently for different tokens on same endpoint"""
        max_rps = 3
        limiter = MethodRateLimiter(max_rps)
        endpoint = '/test/endpoint'
        token1 = 'token1'
        token2 = 'token2'

        # Make max_rps requests for token1 - should pass immediately
        start_time = time.time()
        for _ in range(max_rps):
            await limiter.acquire(endpoint, token1)

        # Make max_rps requests for token2 - should also pass immediately
        for _ in range(max_rps):
            await limiter.acquire(endpoint, token2)

        elapsed = time.time() - start_time
        # Should be almost immediate since they're different tokens
        self.assertLess(elapsed, 0.1, 'Expected immediate execution')

        # Check RPS for both tokens
        rps1 = limiter.get_current_rps(endpoint, token1)
        rps2 = limiter.get_current_rps(endpoint, token2)
        self.assertEqual(rps1, max_rps, f'Expected {max_rps} RPS for token1')
        self.assertEqual(rps2, max_rps, f'Expected {max_rps} RPS for token2')

    async def test_rate_limiter_cleanup_old_requests(self) -> None:
        """Test that old requests are cleaned up properly"""
        max_rps = 2
        limiter = MethodRateLimiter(max_rps)
        endpoint = '/test/endpoint'
        token = 'test_token'

        # Make max_rps requests
        for _ in range(max_rps):
            await limiter.acquire(endpoint, token)

        # Wait for more than 1 second
        await asyncio.sleep(1.1)

        # Make another request - should pass immediately since old requests are cleaned up
        start_time = time.time()
        await limiter.acquire(endpoint, token)
        elapsed = time.time() - start_time

        self.assertLess(elapsed, 0.1, 'Expected immediate execution after cleanup')

        # Check RPS - should be 1 (only the new request)
        current_rps = limiter.get_current_rps(endpoint, token)
        self.assertEqual(current_rps, 1, 'Expected 1 RPS after cleanup')

    async def test_rate_limiter_concurrent_access(self) -> None:
        """Test that rate limiter works correctly under concurrent access"""
        max_rps = 3
        limiter = MethodRateLimiter(max_rps)
        endpoint = '/test/endpoint'
        token = 'test_token'

        # Start 5 concurrent requests
        start_time = time.time()
        tasks = [limiter.acquire(endpoint, token) for _ in range(max_rps + 2)]
        await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        # First max_rps requests should be immediate, last 2 should wait
        # The wait time should be around 1 second
        self.assertGreaterEqual(elapsed, 0.9, 'Expected to wait at least 0.9 seconds for concurrent access')
        self.assertLessEqual(elapsed, 1.1, 'Expected to wait at most 1.1 seconds for concurrent access')

    async def test_rate_limiter_precise_waiting(self) -> None:
        """Test that rate limiter waits precisely based on request timing"""
        max_rps = 2
        limiter = MethodRateLimiter(max_rps)
        endpoint = '/test/endpoint'
        token = 'test_token'

        # Make max_rps requests at different times
        start_time = time.time()
        await limiter.acquire(endpoint, token)  # Request 1 at time 0

        await asyncio.sleep(0.3)  # Wait 0.3 seconds
        await limiter.acquire(endpoint, token)  # Request max_rps at time 0.3

        # Make max_rps request - should wait for the first request to expire (0.7 seconds from now)
        await limiter.acquire(endpoint, token)
        elapsed = time.time() - start_time

        # Should wait about 1 second total (0.3 + 0.7)
        self.assertGreaterEqual(elapsed, 0.9, 'Expected to wait at least 0.9 seconds')
        self.assertLessEqual(elapsed, 1.1, 'Expected to wait at most 1.1 seconds')

    async def test_rate_limiter_immediate_execution_after_partial_window(self) -> None:
        """Test that requests execute immediately if previous second didn't hit RPS limit"""
        max_rps = 5
        limiter = MethodRateLimiter(max_rps)
        endpoint = '/test/endpoint'
        token = 'test_token'

        # Make only max_rps - 3 requests (well below the max_rps limit)
        start_time = time.time()
        for _ in range(max_rps - 3):
            await limiter.acquire(endpoint, token)

        # Wait 0.5 seconds (not a full second)
        await asyncio.sleep(0.5)

        # Make another request - should execute immediately since we're still within limits
        request_start_time = time.time()
        await limiter.acquire(endpoint, token)
        request_elapsed = time.time() - request_start_time

        # This request should execute immediately (less than 0.01 seconds)
        self.assertLess(request_elapsed, 0.01, 'Expected immediate execution')

        # Total time should be around 0.5 seconds (the wait time)
        total_elapsed = time.time() - start_time
        self.assertGreaterEqual(total_elapsed, 0.4, 'Expected total time at least 0.4 seconds')
        self.assertLessEqual(total_elapsed, 0.6, 'Expected total time at most 0.6 seconds')

    async def test_rate_limiter_sliding_window_behavior(self) -> None:
        """Test that rate limiter properly handles sliding window behavior"""
        max_rps = 3
        limiter = MethodRateLimiter(max_rps)
        endpoint = '/test/endpoint'
        token = 'test_token'

        # Make max_rps requests at different times within a 1-second window
        await limiter.acquire(endpoint, token)  # Request 1 at time 0

        await asyncio.sleep(0.4)  # Wait 0.4 seconds
        await limiter.acquire(endpoint, token)  # Request 2 at time 0.4

        await asyncio.sleep(0.4)  # Wait 0.4 seconds
        await limiter.acquire(endpoint, token)  # Request max_rps at time 0.8

        # Wait a bit more (0.3 seconds) - total time is 1.1 seconds
        await asyncio.sleep(0.3)  # Total time: 1.1 seconds

        # The first request (at time 0) should now be outside the 1-second window
        # So we should be able to make another request immediately
        request_start_time = time.time()
        await limiter.acquire(endpoint, token)
        request_elapsed = time.time() - request_start_time

        # This request should execute immediately since the oldest request expired
        self.assertLess(request_elapsed, 0.01, 'Expected immediate execution due to sliding window')

    async def test_rate_limiter_wait_until_next_second(self) -> None:
        """Test that when there are already max_rps requests in the last second, we wait until the next second"""
        max_rps = 3
        limiter = MethodRateLimiter(max_rps)
        endpoint = '/test/endpoint'
        token = 'test_token'

        # Make exactly max_rps requests at the same time (or very close)
        start_time = time.time()
        for _ in range(max_rps):
            await limiter.acquire(endpoint, token)

        # The next request should wait until the oldest request expires (1 second from when it was made)
        await limiter.acquire(endpoint, token)
        elapsed = time.time() - start_time

        # Should wait approximately 1 second
        self.assertGreaterEqual(elapsed, 0.9, 'Expected to wait at least 0.9 seconds')
        self.assertLessEqual(elapsed, 1.1, 'Expected to wait at most 1.1 seconds')
