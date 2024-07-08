import asyncio
import functools
import logging
import sys
import time
import uuid
from collections.abc import Callable
from typing import Any


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)

    # Check if the logger already has handlers to avoid duplicate logging
    if not logger.handlers:
        logger.setLevel(level)

        # Create console handler and set level
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Add formatter to handler
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

    # Prevent the logger from propagating messages to the root logger
    logger.propagate = False

    return logger


# Create package-wide logger
logger = setup_logger("humbldata")


def log_start_end(
    func: Callable | None = None, *, logger: logging.Logger | None = None
) -> Callable:
    """
    Add logging at the start and end of any function it decorates, including time tracking.
    Works with both synchronous and asynchronous functions.
    """
    assert callable(func) or func is None

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            start_time = time.time()
            logger.info(f"START: {func.__name__} (async)")

            try:
                result = await func(*args, **kwargs)
            except KeyboardInterrupt:
                end_time = time.time()
                total_time = end_time - start_time
                logger.info(
                    f"INTERRUPTED: {func.__name__} (async) - Total time: {total_time:.4f}s"
                )
                return []
            except Exception as e:
                end_time = time.time()
                total_time = end_time - start_time
                logger.exception(
                    f"EXCEPTION in {func.__name__} (async) - Total time: {total_time:.4f}s"
                )
                raise
            else:
                end_time = time.time()
                total_time = end_time - start_time
                logger.info(
                    f"END: {func.__name__} (async) - Total time: {total_time:.4f}s"
                )
                return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            start_time = time.time()
            logger.info(f"START: {func.__name__} (sync)")

            try:
                result = func(*args, **kwargs)
            except KeyboardInterrupt:
                end_time = time.time()
                total_time = end_time - start_time
                logger.info(
                    f"INTERRUPTED: {func.__name__} (sync) - Total time: {total_time:.4f}s"
                )
                return []
            except Exception as e:
                end_time = time.time()
                total_time = end_time - start_time
                logger.exception(
                    f"EXCEPTION in {func.__name__} (sync) - Total time: {total_time:.4f}s"
                )
                raise
            else:
                end_time = time.time()
                total_time = end_time - start_time
                logger.info(
                    f"END: {func.__name__} (sync) - Total time: {total_time:.4f}s"
                )
                return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator(func) if callable(func) else decorator
