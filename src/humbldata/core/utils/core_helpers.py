"""A module to contain core helper functions for the program."""

__docformat__ = "numpy"

from concurrent.futures import ThreadPoolExecutor
import asyncio
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


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


def run_async(coro):
    """Run an async function in a new thread and return the result."""
    with ThreadPoolExecutor() as executor:
        future = executor.submit(lambda: asyncio.run(coro))
        return future.result()
