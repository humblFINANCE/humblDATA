import contextlib
import functools
from typing import Any, Callable, List, Optional, Type, Union
from warnings import WarningMessage, catch_warnings

from pydantic import BaseModel


class Warning_(BaseModel):  # noqa: N801, D101
    category: str
    message: str


def cast_warning(w: WarningMessage) -> Warning_:  # noqa: D103
    return Warning_(
        category=w.category.__name__,
        message=str(w.message),
    )


class HumblDataWarning(Warning):  # noqa: D101
    """Base warning class for HumblData warnings."""

    pass


# Create a function to convert a Warning to a Warning_ object
def warning_to_warning_(warning_obj: Warning) -> Warning_:
    """Convert a Warning object to a Warning_ object."""
    return Warning_(
        category=warning_obj.__class__.__name__,
        message=str(warning_obj),
    )


class WarningCollector:
    """Context manager and decorator for collecting warnings."""

    def __init__(self):
        self.warnings: list[Warning_] = []

    def __enter__(self):
        self._recorded = []
        self._showwarning_orig = None
        self._catch_ctx = catch_warnings(record=True)
        self._warnings = self._catch_ctx.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._catch_ctx.__exit__(exc_type, exc_val, exc_tb)
        self.warnings.extend([cast_warning(w) for w in self._warnings])
        return False

    def collect_warnings(self, func: Callable) -> Callable:
        """
        Collect warnings from a function.

        Parameters
        ----------
        func : Callable
            The function to wrap

        Returns
        -------
        Callable
            The wrapped function that collects warnings
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                result = func(*args, **kwargs)
            return result

        return wrapper


# Global collector for use in decorators
warning_collector = WarningCollector()


def collect_warnings(func: Callable) -> Callable:
    """
    Collect warnings from a function and store them in the global collector.

    Parameters
    ----------
    func : Callable
        The function to wrap

    Returns
    -------
    Callable
        The wrapped function that collects warnings
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with warning_collector:
            result = func(*args, **kwargs)

        # If this is a method of a class that has a warnings attribute, add the warnings
        if args and hasattr(args[0], "warnings"):
            if not isinstance(args[0].warnings, list):
                args[0].warnings = []

            # Only add warnings that don't already exist in the list
            for warning in warning_collector.warnings:
                if not any(
                    w.message == warning.message for w in args[0].warnings
                ):
                    args[0].warnings.append(warning)

        return result

    return wrapper


@contextlib.contextmanager
def collect_warnings_context():
    """
    Context manager to collect warnings.

    Yields
    ------
    List[Warning_]
        The list of collected warnings
    """
    collector = WarningCollector()
    with collector:
        yield collector.warnings


# Helper function to create a Warning_ object directly
def create_warning(category: str, message: str) -> Warning_:
    """
    Create a Warning_ object directly.

    Parameters
    ----------
    category : str
        The category of the warning
    message : str
        The warning message

    Returns
    -------
    Warning_
        The created Warning_ object
    """
    return Warning_(category=category, message=message)
