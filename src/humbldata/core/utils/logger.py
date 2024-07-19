import asyncio
import functools
import logging
import sys
import time
import uuid
from collections.abc import Callable
from typing import Any

import coloredlogs

from humbldata.core.utils.env import Env


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with the specified name and logging level.

    Parameters
    ----------
    name : str
        The name of the logger.
    level : int, optional
        The logging level, by default logging.INFO.

    Returns
    -------
    logging.Logger
        A configured logger instance.

    Notes
    -----
    This function creates a logger with a StreamHandler that outputs to sys.stdout.
    It uses a formatter that includes timestamp, logger name, log level, and message.
    If the logger already has handlers, it skips the setup to avoid duplicate logging.
    The logger is configured not to propagate messages to the root logger.

    Examples
    --------
    >>> logger = setup_logger("my_logger", logging.DEBUG)
    >>> logger.debug("This is a debug message")
    2023-05-20 10:30:45,123 - my_logger - DEBUG - This is a debug message
    """
    logger = logging.getLogger(name)

    # Check if the logger already has handlers to avoid duplicate logging
    if not logger.handlers:
        logger.setLevel(level)

        # Install coloredlogs
        coloredlogs.install(
            level=level,
            logger=logger,
            fmt="%(levelname)s: %(name)s || %(message)s",
            level_styles={
                "debug": {"color": "green"},
                "info": {"color": "blue"},
                "warning": {"color": "yellow", "bold": True},
                "error": {"color": "red", "bold": True},
                "critical": {
                    "color": "red",
                    "bold": True,
                    "background": "white",
                },
            },
            field_styles={
                "asctime": {"color": "blue"},
                "levelname": {"color": "magenta", "bold": True},
                "name": {"color": "cyan"},
            },
        )

    # Prevent the logger from propagating messages to the root logger
    logger.propagate = False

    return logger


# # Create package-wide logger
# env = Env()
# logger = setup_logger("humbldata", level=env.LOGGER_LEVEL)


def log_start_end(
    func: Callable | None = None, *, logger: logging.Logger | None = None
) -> Callable:
    """
    Log the start and end of any function, including time tracking.

    This decorator works with both synchronous and asynchronous functions.
    It logs the start and end of the function execution, as well as the total
    execution time. If an exception occurs, it logs the exception details.

    Parameters
    ----------
    func : Callable | None, optional
        The function to be decorated. If None, the decorator can be used with parameters.
    logger : logging.Logger | None, optional
        The logger to use. If None, a logger will be created using the function's module name.

    Returns
    -------
    Callable
        The wrapped function.

    Notes
    -----
    - For asynchronous functions, the decorator uses an async wrapper.
    - For synchronous functions, it uses a sync wrapper.
    - If a KeyboardInterrupt occurs, it logs the interruption and returns an empty list.
    - If any other exception occurs, it logs the exception and re-raises it.

    Examples
    --------
    >>> @log_start_end
    ... def example_function():
    ...     print("This is an example function")
    ...
    >>> example_function()
    START: example_function (sync)
    This is an example function
    END: example_function (sync) - Total time: 0.0001s

    >>> @log_start_end(logger=custom_logger)
    ... async def async_example():
    ...     await asyncio.sleep(1)
    ...
    >>> asyncio.run(async_example())
    START: async_example (async)
    END: async_example (async) - Total time: 1.0012s
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
