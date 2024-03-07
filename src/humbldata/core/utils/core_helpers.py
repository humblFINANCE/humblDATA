"""A module to contain core helper functions for the program."""

__docformat__ = "numpy"
import functools
import logging
from collections.abc import Callable
from typing import Any, Optional


# Assuming get_current_system() and DEBUG_MODE are defined elsewhere
# Placeholder for get_current_system().DEBUG_MODE check
def is_debug_mode() -> bool:
    """
    Check if the current system is in debug mode.

    Returns
    -------
    bool
        True if the system is in debug mode, False otherwise.
    """
    return False


def log_start_end(
    func: Callable | None = None, *, log: logging.Logger | None = None
) -> Callable:
    """
    Add logging at the start and end of any function it decorates, including time tracking.

    Handles exceptions by logging them and modifies behavior based on the
    system's debug mode. Logs the total time taken by the function.

    Parameters
    ----------
    func : Optional[Callable]
        The function to decorate.
    log : Optional[logging.Logger]
        The logger to use for logging.

    Returns
    -------
    Callable
        The decorated function.
    """
    assert callable(func) or func is None

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import time  # lazy import

            nonlocal log
            if log is None:
                log = logging.getLogger(func.__module__)

            start_time = time.time()
            log.info("START", extra={"func_name": func.__name__})

            try:
                result = func(*args, **kwargs)
            except KeyboardInterrupt:
                end_time = time.time()
                total_time = end_time - start_time
                log.info(
                    "Interrupted by user",
                    extra={
                        "func_name": func.__name__,
                        "total_time": total_time,
                    },
                )
                return []
            except Exception as e:
                end_time = time.time()
                total_time = end_time - start_time
                log.exception(
                    "Exception in:",
                    extra={
                        "func_name": func.__name__,
                        "exception": e,
                        "total_time": total_time,
                    },
                )
                return []
            else:
                end_time = time.time()
                total_time = end_time - start_time
                log.info(
                    "END ",
                    extra={
                        "func_name": func.__name__,
                        "total_time": total_time,
                    },
                )
                return result

        return wrapper

    return decorator(func) if callable(func) else decorator
