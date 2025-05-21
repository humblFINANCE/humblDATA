"""Networking helper functions for asynchronous requests and utility functions."""

import asyncio
import random
import re
import warnings
import zlib
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Type,
    Union,
)

import aiohttp
from multidict import CIMultiDict, CIMultiDictProxy, MultiDict

# Regex to filter sensitive query parameters for obfuscation
FILTER_QUERY_REGEX = r".*key.*|.*token.*|.*auth.*|(c$)"


def obfuscate(
    params: Union[CIMultiDict[str], MultiDict[str]],
) -> dict[str, Any]:
    """Obfuscate sensitive information in request parameters."""
    return {
        param: "********"
        if re.match(FILTER_QUERY_REGEX, param, re.IGNORECASE)
        else val
        for param, val in params.items()
    }


def get_user_agent() -> str:
    """Get a pseudo-random user agent string."""
    user_agent_strings = [
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.10; rv:86.1) Gecko/20100101 Firefox/86.1",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:86.1) Gecko/20100101 Firefox/86.1",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:82.1) Gecko/20100101 Firefox/82.1",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:86.0) Gecko/20100101 Firefox/86.0",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:86.0) Gecko/20100101 Firefox/86.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.10; rv:83.0) Gecko/20100101 Firefox/83.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:84.0) Gecko/20100101 Firefox/84.0",
    ]
    return random.choice(user_agent_strings)  # nosec B311: Not used for cryptographic purposes


class ClientResponse(aiohttp.ClientResponse):
    """Custom ClientResponse to obfuscate sensitive request info."""

    def __init__(self, *args, **kwargs):
        """Initialize the response, obfuscating request_info."""
        # Check if 'request_info' is in kwargs before trying to modify it
        if "request_info" in kwargs and kwargs["request_info"] is not None:
            kwargs["request_info"] = self.obfuscate_request_info(
                kwargs["request_info"]
            )
        super().__init__(*args, **kwargs)

    @classmethod
    def obfuscate_request_info(
        cls, request_info: aiohttp.RequestInfo
    ) -> aiohttp.RequestInfo:
        """Remove sensitive information from request info URL and headers."""
        if request_info.url:
            query = obfuscate(request_info.url.query.copy())
            url = request_info.url.with_query(query)
        else:
            url = request_info.url

        headers = CIMultiDictProxy(
            CIMultiDict(obfuscate(request_info.headers.copy()))
        )

        # real_url is read-only, so we pass the modified url for both original and real_url if needed.
        # The constructor for RequestInfo expects: method, url, *, headers, real_url.
        # We are essentially reconstructing it with obfuscated parts.
        return aiohttp.RequestInfo(
            url=url,
            method=request_info.method,
            headers=headers,
            real_url=url,  # Using the obfuscated url for real_url as well
        )

    async def json(self, **kwargs) -> Union[dict, list]:
        """Return the json response, ensuring content type is appropriate."""
        # Add content_type=None to allow parsing of non-application/json types if needed by API
        kwargs.setdefault("content_type", None)
        return await super().json(**kwargs)


class ClientSession(aiohttp.ClientSession):
    """Custom ClientSession with default configurations and custom ClientResponse."""

    _response_class: Type[ClientResponse] = (
        ClientResponse  # Set default response class
    )

    def __init__(self, *args, **kwargs):
        """Initialize the session with defaults."""
        kwargs.setdefault("connector", aiohttp.TCPConnector(ttl_dns_cache=300))
        kwargs.setdefault("response_class", self._response_class)
        kwargs.setdefault(
            "auto_decompress", False
        )  # Explicitly set based on provided code
        super().__init__(*args, **kwargs)

    def __del__(self, _warnings: Any = warnings) -> None:
        """Attempt to close the session on deletion if not already closed."""
        if not self.closed:
            try:
                asyncio.create_task(self.close())
            except (
                RuntimeError
            ):  # Handles cases where event loop might be closed
                pass

    async def get(self, url: str, **kwargs) -> ClientResponse:  # type: ignore
        """Send GET request."""
        return await self.request(
            "GET", str(url), **kwargs
        )  # Ensure URL is string

    async def post(self, url: str, **kwargs) -> ClientResponse:  # type: ignore
        """Send POST request."""
        return await self.request(
            "POST", str(url), **kwargs
        )  # Ensure URL is string

    async def get_json(self, url: str, **kwargs) -> Union[dict, list]:
        """Send GET request and return json."""
        response = await self.request(
            "GET", str(url), **kwargs
        )  # Ensure URL is string
        return await response.json()

    async def get_one(self, url: str, **kwargs) -> Dict[str, Any]:
        """Send GET request and return first item in json if list."""
        response = await self.request(
            "GET", str(url), **kwargs
        )  # Ensure URL is string
        data = await response.json()

        if isinstance(data, list):
            return data[0] if data else {}  # Handle empty list
        return (
            data if isinstance(data, dict) else {}
        )  # Handle non-dict response

    async def request(  # type: ignore
        self,
        method: str,
        url: str,
        *args,
        raise_for_status: bool = False,
        **kwargs,
    ) -> ClientResponse:
        """Send request with default headers and optional gzip/deflate handling."""

        headers = kwargs.pop("headers", CIMultiDict())
        headers.setdefault("Accept", "application/json")
        headers.setdefault("Accept-Encoding", "gzip, deflate")
        headers.setdefault("Connection", "keep-alive")
        headers.setdefault("User-Agent", get_user_agent())
        kwargs["headers"] = headers

        response = await super().request(
            method, str(url), *args, **kwargs
        )  # Ensure URL is string

        if raise_for_status:
            response.raise_for_status()

        encoding = response.headers.get("Content-Encoding", "")
        if encoding.lower() in ("gzip", "deflate") and not self.auto_decompress:
            response_body = await response.read()
            if response_body:  # Ensure body is not empty before decompressing
                wbits = (
                    16 + zlib.MAX_WBITS
                    if encoding.lower() == "gzip"
                    else -zlib.MAX_WBITS
                )
                # Use a new _body attribute as original _body might be protected or managed internally
                response._body = zlib.decompress(response_body, wbits)  # type: ignore
            else:
                response._body = b""  # type: ignore

        return response  # type: ignore


async def get_async_requests_session(**kwargs) -> ClientSession:
    """Helper function to get an instance of ClientSession."""
    return ClientSession(**kwargs)


async def amake_request(
    url: str,
    method: Literal["GET", "POST"] = "GET",
    timeout: int = 10,
    response_callback: Optional[
        Callable[
            [ClientResponse, ClientSession], Awaitable[Union[dict, List[dict]]]
        ]
    ] = None,
    **kwargs,
) -> Union[dict, List[dict], None]:
    """
    Abstract helper to make a single asynchronous request.
    """
    if method.upper() not in ["GET", "POST"]:
        raise ValueError("Method must be GET or POST")

    # User preferences for timeout can be passed in kwargs via 'preferences' dict
    request_timeout = kwargs.pop("preferences", {}).get(
        "request_timeout", timeout
    )

    # Ensure a ClientTimeout object is created for aiohttp
    timeout_obj = aiohttp.ClientTimeout(total=request_timeout)
    kwargs["timeout"] = timeout_obj

    # Default response callback parses JSON
    async def default_callback(r: ClientResponse, _: ClientSession):
        return await r.json()

    effective_response_callback = response_callback or default_callback

    # Session management: use provided session or create a new one
    session_provided = "session" in kwargs
    session = kwargs.pop("session", None)

    if not session:
        session = await get_async_requests_session()

    try:
        response = await session.request(method.upper(), url, **kwargs)
        # Ensure response is processed by the callback
        # The callback should handle potential errors or non-JSON responses if necessary
        return await effective_response_callback(response, session)
    except aiohttp.ClientError as e:
        warnings.warn(f"Request to {url} failed: {e}", UserWarning)
        return None  # Return None on client errors
    finally:
        if (
            not session_provided and session
        ):  # Close session only if created locally
            await session.close()


async def amake_requests(
    urls: Union[str, List[str]],
    response_callback: Optional[
        Callable[
            [ClientResponse, ClientSession], Awaitable[Union[dict, List[dict]]]
        ]
    ] = None,
    **kwargs,
):
    """Make multiple requests asynchronously using a shared session."""

    # Pop 'session' to avoid passing it to individual amake_request calls if we create one here.
    # If a session is provided in kwargs, it will be used.
    session_from_kwargs = kwargs.pop("session", None)
    session = session_from_kwargs or await get_async_requests_session(
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "method",
                "timeout",
                "response_callback",
                "raise_for_status",
            ]
        }
    )

    # Ensure method is correctly passed if specified, otherwise amake_request default is 'GET'
    method = kwargs.get("method", "GET")
    timeout = kwargs.get("timeout", 10)  # Default timeout for each request

    # Prepare tasks
    urls_list = urls if isinstance(urls, list) else [urls]
    tasks = []
    for url in urls_list:
        # Pass the shared session to each amake_request call
        # Individual kwargs for amake_request can be passed if needed,
        # but here we use the common ones.
        task_kwargs = kwargs.copy()
        task_kwargs["session"] = session  # Pass the shared session
        task_kwargs["method"] = method
        task_kwargs["timeout"] = timeout  # Use the already prepared timeout
        # response_callback is passed directly to amake_request
        tasks.append(
            amake_request(
                url, response_callback=response_callback, **task_kwargs
            )
        )

    results: list = []
    try:
        # asyncio.gather collects results or exceptions
        gathered_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in gathered_results:
            is_exception = isinstance(result, Exception)

            if is_exception and kwargs.get("raise_for_status", False):
                # If raise_for_status is true, and an exception occurred, re-raise it.
                raise result

            if (
                is_exception or result is None
            ):  # Skip exceptions (if not raising) and None results
                continue

            # Extend results list
            if isinstance(result, list):
                results.extend(result)
            else:
                results.append(result)

        return results

    finally:
        # Close the session only if it was created by this function
        if not session_from_kwargs and session:
            await session.close()


def get_querystring(items: dict, exclude: Optional[List[str]] = None) -> str:
    """Turn a dictionary into a querystring, excluding specified keys.

    Parameters
    ----------
    items: dict
        The dictionary to be turned into a querystring.
    exclude: List[str], optional
        The keys to be excluded from the querystring. Defaults to None.

    Returns
    -------
    str
        The querystring.
    """
    if exclude is None:
        exclude = []

    # Create a copy to avoid modifying the original dict
    filtered_items = items.copy()
    for key in exclude:
        filtered_items.pop(key, None)

    query_items = []
    for key, value in filtered_items.items():
        if value is None:
            continue
        if isinstance(value, list):
            # Join list values with commas (e.g., symbol=AAPL,AMD)
            query_items.append(f"{key}={','.join(map(str, value))}")
        elif isinstance(
            value, bool
        ):  # Handle boolean values correctly for URLs
            query_items.append(f"{key}={str(value).lower()}")
        else:
            query_items.append(f"{key}={value}")

    querystring = "&".join(query_items)
    return f"{querystring}" if querystring else ""
