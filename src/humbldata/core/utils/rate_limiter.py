from datetime import datetime

from limits import parse
from limits.aio.storage import (
    MemoryStorage as AsyncMemoryStorage,
)  # Use AsyncRedisStorage for prod
from limits.aio.strategies import (
    FixedWindowRateLimiter as AsyncFixedWindowRateLimiter,
)
from limits.storage import MemoryStorage  # Use RedisStorage for prod
from limits.strategies import FixedWindowRateLimiter

from humbldata.core.utils.logger import setup_logger

logger = setup_logger("RateLimiter")


class RateLimitExceeded(Exception):
    pass


class ProviderRateLimiter:
    """
    A rate limiter for API providers.

    Parameters
    ----------
    default_limit : str, optional
        The default rate limit.
    provider_limits : dict, optional
    """

    def __init__(
        self,
        default_limit: str = "10/minute",
        provider_limits: dict | None = None,
    ):
        self.storage = MemoryStorage()  # swap for RedisStorage(url) in prod
        self.limiter = FixedWindowRateLimiter(self.storage)
        self.default_limit = parse(default_limit)
        self.provider_limits = provider_limits or {}

    def get_limit(self, provider: str, endpoint: str | None = None):
        # endpoint-specific override
        if endpoint and (provider, endpoint) in self.provider_limits:
            limit_str = self.provider_limits[(provider, endpoint)]
            logger.debug(
                f"get_limit: provider={provider}, endpoint={endpoint}, key=({provider}, {endpoint}), value={limit_str}"
            )
            return parse(limit_str)
        # provider-wide override
        if provider in self.provider_limits:
            limit_str = self.provider_limits[provider]
            logger.debug(
                f"get_limit: provider={provider}, endpoint={endpoint}, key={provider}, value={limit_str}"
            )
            return parse(limit_str)
        logger.debug(
            f"get_limit: provider={provider}, endpoint={endpoint}, using default {self.default_limit}"
        )
        return self.default_limit

    def _rate_limit_key(self, provider: str, endpoint: str | None = None):
        if endpoint:
            return f"rate_limit:{provider}:{endpoint}"
        return f"rate_limit:{provider}"

    def hit(self, provider: str, endpoint: str | None = None):
        """
        Hit the rate limit for a provider and endpoint.

        Parameters
        ----------
        provider : str
        endpoint : str | None, optional
        """
        limit = self.get_limit(provider, endpoint)
        key = self._rate_limit_key(provider, endpoint)
        if not self.limiter.hit(limit, key):
            msg = f"Rate limit exceeded for {provider} {endpoint or ''}"
            raise RateLimitExceeded(msg)

    def test(self, provider: str, endpoint: str | None = None):
        """
        Test the rate limit for a provider and endpoint.

        Parameters
        ----------
        provider : str
        endpoint : str | None, optional
        """
        limit = self.get_limit(provider, endpoint)
        key = self._rate_limit_key(provider, endpoint)
        return self.limiter.test(limit, key)

    def get_usage(self, provider: str, endpoint: str | None = None):
        limit = self.get_limit(provider, endpoint)
        key = self._rate_limit_key(provider, endpoint)
        logger.debug(
            f"get_usage: provider={provider}, endpoint={endpoint}, key={key}, limit_item={limit}"
        )
        reset_time, remaining = self.limiter.get_window_stats(limit, key)
        reset_time_str = (
            datetime.fromtimestamp(reset_time).isoformat()
            if reset_time
            else "unknown"
        )
        usage_str = f"{remaining} remaining out of {limit.amount} per {str(limit)} (resets at {reset_time_str})"
        return remaining, str(limit), usage_str, reset_time_str


class AsyncProviderRateLimiter:
    def __init__(
        self,
        default_limit: str = "10/minute",
        provider_limits: dict | None = None,
    ):
        self.storage = AsyncMemoryStorage()
        self.limiter = AsyncFixedWindowRateLimiter(self.storage)
        self.default_limit = parse(default_limit)
        self.provider_limits = provider_limits or {}

    def get_limit(self, provider: str, endpoint: str | None = None):
        if endpoint and (provider, endpoint) in self.provider_limits:
            return parse(self.provider_limits[(provider, endpoint)])
        if provider in self.provider_limits:
            return parse(self.provider_limits[provider])
        return self.default_limit

    def _rate_limit_key(self, provider: str, endpoint: str | None = None):
        if endpoint:
            return f"rate_limit:{provider}:{endpoint}"
        return f"rate_limit:{provider}"

    async def hit(self, provider: str, endpoint: str | None = None):
        limit_item = self.get_limit(provider, endpoint)
        key = self._rate_limit_key(provider, endpoint)
        if not await self.limiter.hit(limit_item, key):
            msg = f"Rate limit exceeded for {provider} {endpoint or ''}"
            raise RateLimitExceeded(msg)

    async def test(self, provider: str, endpoint: str | None = None):
        limit_item = self.get_limit(provider, endpoint)
        key = self._rate_limit_key(provider, endpoint)
        return await self.limiter.test(limit_item, key)

    def context(self, provider: str, endpoint: str | None = None):
        return _AsyncRateLimitContext(self, provider, endpoint)

    async def get_usage(self, provider: str, endpoint: str | None = None):
        limit_item = self.get_limit(provider, endpoint)
        key = self._rate_limit_key(provider, endpoint)
        logger.debug(
            f"get_usage: provider={provider}, endpoint={endpoint}, key={key}, limit_item={limit_item}"
        )
        reset_time, remaining = await self.limiter.get_window_stats(
            limit_item, key
        )
        reset_time_str = (
            datetime.fromtimestamp(reset_time).isoformat()
            if reset_time
            else "unknown"
        )
        usage_str = f"{remaining} remaining out of {limit_item.amount} per {str(limit_item)} (resets at {reset_time_str})"
        return remaining, str(limit_item), usage_str, reset_time_str


class _AsyncRateLimitContext:
    def __init__(
        self,
        async_provider_limiter: AsyncProviderRateLimiter,
        provider: str,
        endpoint: str | None,
    ):
        self.async_provider_limiter = async_provider_limiter
        self.provider = provider
        self.endpoint = endpoint
        self.extra = {}

    async def __aenter__(self):
        limit_item = self.async_provider_limiter.get_limit(
            self.provider, self.endpoint
        )
        key = self.async_provider_limiter._rate_limit_key(
            self.provider, self.endpoint
        )

        strategy_limiter = self.async_provider_limiter.limiter

        reset_time, remaining = await strategy_limiter.get_window_stats(
            limit_item, key
        )
        reset_time_str = (
            datetime.fromtimestamp(reset_time).isoformat()
            if reset_time
            else "unknown"
        )
        route = self.endpoint or ""
        logger.info(
            f"Checking Rate Limits for Provider: {self.provider} Route: {route} | {remaining}/{limit_item.amount} remaining (resets at {reset_time_str})"
        )
        self.extra = {
            "rate_limit_usage_before_hit": f"{remaining}/{limit_item.amount}",
            "rate_limit_remaining_before_hit": remaining,
            "rate_limit_limit_str": str(limit_item),
            "rate_limit_reset_time": reset_time_str,
        }

        allowed = await strategy_limiter.test(limit_item, key)
        if not allowed:
            raise RateLimitExceeded(
                f"Rate limit exceeded for {self.provider} {self.endpoint or ''}. Usage: {f'{remaining}/{limit_item.amount}'}"
            )

        await strategy_limiter.hit(limit_item, key)

        # After hit, remaining should decrease by 1
        logger.info(
            f"Updating Rate Limit - Provider: {self.provider} Route: {route} | {remaining - 1}/{limit_item.amount} remaining (resets at {reset_time_str})"
        )
        self.extra["rate_limit_usage_after_hit"] = (
            f"{remaining - 1}/{limit_item.amount}"
        )
        self.extra["rate_limit_remaining_after_hit"] = remaining - 1
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass
