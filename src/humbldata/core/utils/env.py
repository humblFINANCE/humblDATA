"""The Env Module, to control a single instance of environment variables."""

import os
from pathlib import Path

import dotenv

from humbldata.core.standard_models.abstract.singleton import SingletonMeta


class Env(metaclass=SingletonMeta):
    """A singleton environment to hold all Environment variables."""

    _environ: dict[str, str]

    def __init__(self) -> None:
        env_path = dotenv.find_dotenv()
        dotenv.load_dotenv(Path(env_path))

        self._environ = os.environ.copy()

    @property
    def OBB_PAT(self) -> str | None:  # noqa: N802
        """OpenBB Personal Access Token."""
        return self._environ.get("OBB_PAT", None)

    @property
    def LOGGER_LEVEL(self) -> int:
        """
        Get the global logger level.

        Returns
        -------
        int
            The numeric logging level (default: 20 for INFO).

        Notes
        -----
        Mapping of string levels to numeric values:
        DEBUG: 10, INFO: 20, WARNING: 30, ERROR: 40, CRITICAL: 50
        """
        level_map = {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50,
        }
        return level_map.get(
            self._environ.get("LOGGER_LEVEL", "INFO").upper(), 20
        )

    @property
    def OBB_LOGGED_IN(self) -> bool:
        return self.str2bool(self._environ.get("OBB_LOGGED_IN", False))

    @staticmethod
    def str2bool(value: str | bool) -> bool:
        """Match a value to its boolean correspondent.

        Args:
            value (str): The string value to be converted to a boolean.

        Returns
        -------
            bool: The boolean value corresponding to the input string.

        Raises
        ------
            ValueError: If the input string does not correspond to a boolean
            value.
        """
        if isinstance(value, bool):
            return value
        if value.lower() in {"false", "f", "0", "no", "n"}:
            return False
        if value.lower() in {"true", "t", "1", "yes", "y"}:
            return True
        msg = f"Failed to cast '{value}' to bool."
        raise ValueError(msg)
