"""
HumblData cache utilities.

This module provides custom cache plugins and serializers for HumblData.
"""

import json
import pickle
from typing import Any
from urllib.parse import urlparse

from aiocache.plugins import BasePlugin
from aiocache.serializers import BaseSerializer

from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import setup_logger

env = Env()
logger = setup_logger("LogCacheHitPlugin", level=env.LOGGER_LEVEL)


def build_cache_key(self: Any, command_param_fields: list[str] = []) -> str:
    """
    Build a cache key from specified command parameters and context dates.

    Parameters
    ----------
    self : Any
        The instance containing context_params and command_params
    command_param_fields : list[str], optional
        list of field names from command_params to include in the key, by default empty list

    Returns
    -------
    str
        JSON string of the key data, sorted for consistency

    Notes
    -----
    Always includes start_date and end_date from context_params.
    Additional fields from command_params can be specified via command_param_fields.
    """
    # Convert dates to strings if they're datetime objects
    start_date = self.context_params.start_date
    if not isinstance(start_date, str):
        start_date = start_date.strftime("%Y-%m-%d")

    end_date = self.context_params.end_date
    if not isinstance(end_date, str):
        end_date = end_date.strftime("%Y-%m-%d")

    # Initialize key data with required context dates
    key_data = {
        "start_date": start_date,
        "end_date": end_date,
    }

    # Add specified command params if they exist
    if command_param_fields:
        for field in command_param_fields:
            if hasattr(self.command_params, field):
                key_data[field] = getattr(self.command_params, field)

    return json.dumps(key_data, sort_keys=True)


def get_redis_location(env: Env) -> str:
    """
    Helper to determine if Redis is local or remote.
    Returns 'remote' if REDIS_URL is set and not localhost/127.0.0.1, else 'local'.
    """
    redis_url = env.REDIS_URL
    if redis_url:
        parsed = urlparse(redis_url)
        host = parsed.hostname
        if host and host not in ("localhost", "127.0.0.1"):
            return "remote"
        return "local"
    # Fallback to REDIS_HOST
    host = getattr(env, "REDIS_HOST", "localhost")
    if host not in ("localhost", "127.0.0.1"):
        return "remote"
    return "local"


class LogCacheHitPlugin(BasePlugin):
    """Log cache hit and return value."""

    def __init__(self, name="humbl_compass"):
        super().__init__()
        self.name = name
        self.env = Env()
        self.redis_location = get_redis_location(self.env)

    async def post_get(self, cache, key, *args, **kwargs):
        """Log cache hit and return value."""
        value = kwargs.get("ret")
        if value is not None:
            info_msg = f"{self.name} cache HIT & RETURNED [{self.redis_location} redis]"
            debug_msg = (
                f"{self.name} cache key: {key} [{self.redis_location} redis]"
            )
            logger.info(info_msg)
            logger.debug(debug_msg)
        return value


class CustomPickleSerializer(BaseSerializer):
    """Custom aiocache serializer using pickle and latin‑1 safe decoding."""

    def __init__(self, *args, encoding="latin1", **kwargs):
        """Initialize the custom pickle serializer with latin-1 encoding.

        The latin-1 encoding is required to ensure RedisCache._get can properly
        decode bytes without UnicodeDecodeError while preserving the original
        pickle byte-stream.

        Parameters
        ----------
        encoding : str, optional
            The encoding to use for serialization, by default "latin1"
        *args
            Variable length argument list passed to parent class
        **kwargs
            Arbitrary keyword arguments passed to parent class
        """
        super().__init__(encoding=encoding, *args, **kwargs)

    def dumps(self, value):
        """Serialize any Python object to raw pickle bytes."""
        return pickle.dumps(value)

    def loads(self, value):
        """Deserialize bytes (or latin‑1 string) back to the original object."""
        if value is None:
            return None
        # aiocache's Redis backend decodes with latin‑1 and hands us str
        if isinstance(value, str):
            value = value.encode("latin1")
        return pickle.loads(value)


def get_redis_cache_config(namespace: str = "default"):
    """
    Returns a dict of aiocache.RedisCache config based on environment.
    """
    env = Env()
    if env.REDIS_URL:
        parsed = urlparse(env.REDIS_URL)
        password = parsed.password
        host = parsed.hostname
        port = parsed.port
        scheme = parsed.scheme
        if not host or not port:
            raise ValueError(f"Invalid REDIS_URL: {env.REDIS_URL}")
        config = {
            "endpoint": host,
            "port": port,
            "password": password,
            "namespace": namespace,
        }
        if scheme == "rediss":
            config["ssl"] = True
        return config
    # Fallback to host/port vars (for local/dev)
    return {
        "endpoint": getattr(env, "REDIS_HOST", "localhost"),
        "port": getattr(env, "REDIS_PORT", 6379),
        "namespace": namespace,
    }
