import asyncio
import time
from collections import defaultdict, deque

from .constants import MAX_RPS


class MethodRateLimiter:
    """
    A rate limiter that tracks requests per auth_token and endpoint combination.
    Each (auth_token, endpoint) pair has its own rate limit counter using a sliding window approach
    """

    def __init__(self, max_rps: int = 5):
        """
        Initialize the rate limiter

        Args:
            max_rps: Maximum requests per second per auth_token-endpoint combination
        """
        self.max_rps = max_rps
        self.request_timestamps: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def acquire(self, endpoint: str, auth_token: str) -> None:
        """
        Acquire permission to make a request for the specified endpoint and auth_token.

        This method will wait if necessary to stay within rate limits.
        If rate limiting is disabled, this method returns immediately

        Args:
            endpoint: The endpoint URL being requested
            auth_token: The authentication auth_token being used
        """

        async with self._lock:
            key = (auth_token, endpoint)

            current_rps = self.get_current_rps(endpoint, auth_token)

            if current_rps >= self.max_rps:
                # Add small buffer to ensure window moves
                wait_time = 1.001 - self.get_difference_with_first_request(key, time.time())

                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            self.request_timestamps[key].append(time.time())

    def get_current_rps(self, endpoint: str, auth_token: str) -> int:
        """
        Get the current RPS for a specific auth_token and endpoint combination

        Args:
            endpoint: The endpoint URL to check
            auth_token: The authentication auth_token to check

        Returns:
            Number of requests in the last second
        """
        key = (auth_token, endpoint)
        self.clean_up_old_timestamps(key)

        return len(self.request_timestamps[key])

    def get_difference_with_first_request(self, key: tuple[str, str], timestamp: float) -> float:
        """
        Get a difference in seconds between the first timestamp and a timestamp passed in parameters
        for a specific auth_token and endpoint combination
        """
        return timestamp - self.request_timestamps[key][0]

    def clean_up_old_timestamps(self, key: tuple[str, str]) -> None:
        """
        Clean up old timestamps older than 1 second
        """
        now = time.time()
        while self.request_timestamps[key] and self.get_difference_with_first_request(key, now) >= 1.0:
            self.request_timestamps[key].popleft()


yango_rate_limiter = MethodRateLimiter(max_rps=MAX_RPS)
