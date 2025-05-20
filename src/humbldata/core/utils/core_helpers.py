"""A module to contain core helper functions for the program."""

__docformat__ = "numpy"

import asyncio
import io
from concurrent.futures import ThreadPoolExecutor

import polars as pl
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


def serialize_lazyframe_to_ipc(frame: pl.LazyFrame | pl.DataFrame) -> bytes:
    """
    Serialize a Polars LazyFrame or DataFrame to Arrow IPC format using write_ipc.

    Parameters
    ----------
    frame : pl.LazyFrame | pl.DataFrame
        The frame to serialize. If a LazyFrame is passed, it will be collected
        to a DataFrame.

    Returns
    -------
    bytes
        The serialized IPC byte stream.
    """
    if isinstance(frame, pl.LazyFrame):
        frame = frame.collect()
    buffer = io.BytesIO()
    frame.write_ipc(buffer)
    return buffer.getvalue()
