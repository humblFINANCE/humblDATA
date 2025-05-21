import asyncio
import logging
import time

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
                f"[RateLimiter] get_limit: provider={provider}, endpoint={endpoint}, key=({provider}, {endpoint}), value={limit_str}"
            )
            return parse(limit_str)
        # provider-wide override
        if provider in self.provider_limits:
            limit_str = self.provider_limits[provider]
            logger.debug(
                f"[RateLimiter] get_limit: provider={provider}, endpoint={endpoint}, key={provider}, value={limit_str}"
            )
            return parse(limit_str)
        logger.debug(
            f"[RateLimiter] get_limit: provider={provider}, endpoint={endpoint}, using default {self.default_limit}"
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
            f"[RateLimiter] get_usage: provider={provider}, endpoint={endpoint}, key={key}, limit_item={limit}"
        )
        count, _ = self.limiter.get_window_stats(limit, key)
        remaining_calls = max(0, limit.amount - count)
        parts = str(limit).split("/")
        limit_period_str = parts[1] if len(parts) > 1 else "unknown"
        usage_str = f"{count} / {limit.amount} per {limit_period_str}"
        return count, remaining_calls, str(limit), usage_str


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
            f"[RateLimiter] get_usage: provider={provider}, endpoint={endpoint}, key={key}, limit_item={limit_item}"
        )
        count, _ = await self.limiter.get_window_stats(limit_item, key)
        remaining_calls = max(0, limit_item.amount - count)
        parts = str(limit_item).split("/")
        limit_period_str = parts[1] if len(parts) > 1 else "unknown"
        usage_str = f"{count} / {limit_item.amount} per {limit_period_str}"
        return count, remaining_calls, str(limit_item), usage_str


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

        current_hits, _ = await strategy_limiter.get_window_stats(
            limit_item, key
        )
        remaining_calls = max(0, limit_item.amount - current_hits)

        parts = str(limit_item).split("/")
        limit_period_str = parts[1] if len(parts) > 1 else "unknown"
        usage_str_before_hit = (
            f"{current_hits} / {limit_item.amount} per {limit_period_str}"
        )

        logging.info(
            f"[RateLimiter] Check {self.provider} {self.endpoint or ''}: {usage_str_before_hit}. Remaining: {remaining_calls}"
        )
        self.extra = {
            "rate_limit_usage_before_hit": usage_str_before_hit,
            "rate_limit_remaining_before_hit": remaining_calls,
            "rate_limit_limit_str": str(limit_item),
        }

        allowed = await strategy_limiter.test(limit_item, key)
        if not allowed:
            raise RateLimitExceeded(
                f"Rate limit exceeded for {self.provider} {self.endpoint or ''}. Usage: {usage_str_before_hit}"
            )

        await strategy_limiter.hit(limit_item, key)

        usage_after_hit_str = (
            f"{current_hits + 1} / {limit_item.amount} per {limit_period_str}"
        )
        logging.info(
            f"[RateLimiter] HIT {self.provider} {self.endpoint or ''}: {usage_after_hit_str}. Remaining: {remaining_calls - 1}"
        )
        self.extra["rate_limit_usage_after_hit"] = usage_after_hit_str
        self.extra["rate_limit_remaining_after_hit"] = remaining_calls - 1
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass
