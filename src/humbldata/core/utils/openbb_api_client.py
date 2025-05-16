"""Client for interacting with an external OpenBB-like API."""

import warnings
from typing import TYPE_CHECKING, cast

import polars as pl
from pydantic import BaseModel

from humbldata.core.standard_models.abstract.humblobject import HumblObject
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.abstract.warnings import (
    HumblDataWarning,
    Warning_,  # Keep for type hinting if necessary, though self.warnings will store these
    collect_warnings,
)
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import log_start_end, setup_logger
from humbldata.core.utils.network_helpers import (
    amake_request,
    get_querystring,
)

if TYPE_CHECKING:
    pass

logger = setup_logger("OpenBBAPIClient")


class OpenBBAPIClient:
    """Asynchronous client to fetch data from the external OpenBB API."""

    def __init__(self):
        """Initialize the client with environment configuration."""
        self.env = Env()
        self.warnings: list[Warning_] = []
        self.obb_path: str | None = None
        self.api_query_params: QueryParams | None = None
        self.full_url: str | None = None
        self.raw_api_response: dict | list[dict] | None = None
        self.extra: dict = {}

    async def _get_base_url(self) -> str:
        """Determine the base API URL based on the environment."""
        api_suffix = self.env.OPENBB_API_PREFIX
        if self.env.ENVIRONMENT == "production":
            url = self.env.OPENBB_API_PROD_URL
            if not url:
                msg = "OPENBB_API_PROD_URL is not set in the environment."
                raise ValueError(msg)
            return f"{url.rstrip('/')}{api_suffix}"
        else:
            url = self.env.OPENBB_API_DEV_URL
            if not url:
                msg = "OPENBB_API_DEV_URL is not set in the environment."
                raise ValueError(msg)
            return f"{url.rstrip('/')}{api_suffix}"

    def _translate_path(self, obb_path: str) -> str:
        """
        Translate an OpenBB-style path to an API endpoint segment.

        Parameters
        ----------
        obb_path : str
            The OpenBB-style path (e.g. 'equity.price.historical')

        Returns
        -------
        str
            The API endpoint segment (e.g. '/equity/price/historical')

        Examples
        --------
        >>> client = OpenBBAPIClient(env)
        >>> client._translate_path('equity.price.historical')
        '/equity/price/historical'
        >>> client._translate_path('crypto.ohlcv')
        '/crypto/ohlcv'
        """
        return "/" + obb_path.replace(".", "/")

    async def _build_url(
        self,
        obb_path: str,
        api_query_params: BaseModel,
        base_url: str | None = None,
    ) -> str:
        """
        Build the full URL for the API request.

        Parameters
        ----------
        obb_path : str
            The OpenBB-style path for the API resource.
        api_query_params : BaseModel
            The Pydantic model instance containing the query parameters.
        base_url : Optional[str], optional
            The base URL of the API. If not provided, will be determined from
            environment.

        Returns
        -------
        str
            The full URL including query string if present.
        """
        if base_url is None:
            base_url = await self._get_base_url()
        url_path = self._translate_path(obb_path)
        url_without_query = f"{base_url}{url_path}"
        query_params_dict = api_query_params.model_dump(exclude_none=True)
        querystring = get_querystring(query_params_dict)
        if querystring:
            return f"{url_without_query}?{querystring}"
        return url_without_query

    @collect_warnings
    async def transform_query(
        self,
        obb_path: str,
        api_query_params: BaseModel,
    ):
        """
        Build the full URL and stores parameters for the API request.

        Parameters
        ----------
        obb_path : str
            The OpenBB-style path for the API resource
            (e.g., 'equity.price.historical').
        api_query_params : BaseModel
            A Pydantic model instance containing the query parameters for the
            API request.
        """
        self.obb_path = obb_path
        self.api_query_params = api_query_params

        if not self.api_query_params:
            # Or handle as an error, depending on expected behavior
            warnings.warn(
                "API query parameters are not provided.",
                HumblDataWarning,
                stacklevel=2,
            )
            # Potentially set a default or raise an error
            # For now, we assume it might be valid for some calls to have no params
            # and _build_url handles empty dict correctly.

        self.full_url = await self._build_url(
            self.obb_path, self.api_query_params
        )
        msg = f"Prepared request for: {self.full_url}"
        logger.info(msg)
        return self

    @collect_warnings
    async def extract_data(self):
        """Make the network request to the previously built URL."""
        if not self.full_url or not self.obb_path:
            message = "URL or obb_path not set. Run transform_query first."
            logger.error(message)
            warnings.warn(message, HumblDataWarning, stacklevel=2)
            # Store error details in self.extra to be picked up by transform_data
            self.extra["error_details"] = message
            self.raw_api_response = (
                None  # Ensure it's None so transform_data handles it
            )
            return self

        msg = f"Fetching data from: {self.full_url}"
        logger.info(msg)
        self.raw_api_response = await amake_request(
            url=self.full_url, method="GET"
        )
        return self

    async def _validate_client_state_for_transform(self) -> str | None:
        """Validate if the client is ready for data transformation."""
        if self.obb_path is None:
            message = "Client not properly initialized with obb_path before transforming data."
            logger.error(message)
            return message
        return None

    async def _validate_api_response(self) -> str | None:
        """Validate the raw API response, including API error messages (e.g., rate limiting)."""
        error_message = self.extra.get("error_details")
        # Handle None response
        if self.raw_api_response is None and not error_message:
            error_message = (
                f"API request to {self.full_url} failed with no data."
            )
            logger.error(error_message)
            warnings.warn(error_message, HumblDataWarning, stacklevel=2)
        # Handle non-dict/list response
        elif (
            not isinstance(self.raw_api_response, dict | list)
            and not error_message
        ):
            error_message = f"API response for {self.obb_path} from {self.full_url} was not a dictionary or list as expected. Type: {type(self.raw_api_response)}."
            logger.error(error_message)
            warnings.warn(error_message, HumblDataWarning, stacklevel=2)
        # Handle API error message in dict response (e.g., rate limiting)
        elif isinstance(self.raw_api_response, dict):
            detail = self.raw_api_response.get("detail")
            if detail:
                error_message = f"API error for {self.obb_path} from {self.full_url}: {detail}"
                logger.error(error_message)
                warnings.warn(error_message, HumblDataWarning, stacklevel=2)
                self.warnings.append(
                    Warning_(
                        message=error_message,
                        category="OpenBBAPIError",
                    )
                )
        # Handle API error message in list response (rare, but possible)
        elif isinstance(self.raw_api_response, list):
            for item in self.raw_api_response:
                if isinstance(item, dict) and "detail" in item:
                    detail = item["detail"]
                    error_message = f"API error for {self.obb_path} from {self.full_url}: {detail}"
                    logger.error(error_message)
                    warnings.warn(error_message, HumblDataWarning, stacklevel=2)
                    self.warnings.append(
                        Warning_(
                            message=error_message,
                            category="OpenBBAPIError",
                        )
                    )
                    break
        return error_message

    def _parse_api_response_json(self) -> dict:
        """Parse the raw API response, defaulting to dict."""
        if isinstance(self.raw_api_response, list):
            msg = f"API response for {self.obb_path} was a list. Expected dict. Processing as empty."
            logger.warning(msg)
            warnings.warn(msg, HumblDataWarning, stacklevel=2)
            return {}  # Treat as empty dict
        # Cast is safe due to _validate_api_response checks or the list handling above
        return cast("dict", self.raw_api_response)

    def _extract_results_to_lazyframe(
        self, api_response_json: dict
    ) -> pl.LazyFrame:
        """Extract 'results' from API response and converts to Polars LazyFrame."""
        data_list = api_response_json.get("results", [])
        if not isinstance(data_list, list):
            msg = f"API response 'results' for {self.obb_path} is not a list: {type(data_list)}. Treating as empty list."
            logger.warning(msg)
            warnings.warn(msg, HumblDataWarning, stacklevel=2)
            data_list = []

        results_lf = pl.LazyFrame()
        if data_list:
            try:
                results_lf = pl.from_dicts(data_list).lazy()
            except Exception as e:
                msg = f"Error converting API response 'results' to Polars LazyFrame for {self.obb_path}: {e}"
                logger.exception(msg)
                warnings.warn(msg, HumblDataWarning, stacklevel=2)
        return results_lf

    def _process_api_warnings(self, api_response_json: dict):
        """Process warnings from the API response."""
        api_warnings_raw = api_response_json.get("warnings")
        if not api_warnings_raw:
            return

        if isinstance(api_warnings_raw, list):
            for warn_data in api_warnings_raw:
                if isinstance(warn_data, dict):
                    try:
                        api_message = warn_data.get(
                            "message", "Unknown API warning"
                        )
                        api_category = warn_data.get(
                            "category", "HumblDataWarning"
                        )
                        warnings.warn(
                            f"API Reported [{api_category}]: {api_message}",
                            HumblDataWarning,
                            stacklevel=2,
                        )
                    except Exception as e:
                        malformed_warning_message = f"Could not parse API warning: {warn_data}, Error: {e}"
                        logger.warning(malformed_warning_message)
                        warnings.warn(
                            malformed_warning_message,
                            HumblDataWarning,
                            stacklevel=2,
                        )
                else:
                    non_dict_warning_message = (
                        f"API warning was not a dict: {warn_data}"
                    )
                    warnings.warn(
                        non_dict_warning_message,
                        HumblDataWarning,
                        stacklevel=2,
                    )
        else:
            non_list_warning_message = (
                f"API returned non-list warnings structure: {api_warnings_raw}"
            )
            warnings.warn(
                non_list_warning_message, HumblDataWarning, stacklevel=2
            )

    @collect_warnings
    async def transform_data(self) -> HumblObject:
        """Process the API response and wraps it in a HumblObject."""
        client_state_error = await self._validate_client_state_for_transform()
        if client_state_error:
            return HumblObject(
                results=pl.LazyFrame().serialize(format="binary"),
                provider=self.api_query_params.provider,
                warnings=[
                    *self.warnings,
                    Warning_(
                        message=client_state_error,
                        category="HumblDataCriticalError",
                    ),
                ],
                extra={
                    "original_api_response": self.raw_api_response,
                    **self.extra,
                },
            )

        api_response_error = await self._validate_api_response()
        if api_response_error:
            return HumblObject(
                results=pl.LazyFrame().serialize(format="binary"),
                provider=self.api_query_params.provider,
                warnings=self.warnings,
                extra={
                    "original_api_response": self.raw_api_response,
                    **self.extra,
                },
            )

        api_response_json = self._parse_api_response_json()
        results_lf = self._extract_results_to_lazyframe(api_response_json)

        # --- Convert 'date' columns from string to pl.Date or pl.Datetime if needed ---
        if "date" in results_lf.collect_schema():
            dtype = results_lf.collect_schema()["date"]
            if dtype == pl.Utf8:
                # Try to parse as date, fallback to datetime if needed
                try:
                    results_lf = results_lf.with_columns(
                        pl.col("date").str.to_date().alias("date")
                    )
                except Exception:
                    results_lf = results_lf.with_columns(
                        pl.col("date").str.to_datetime().alias("date")
                    )
        # --------------------------------------------------------------------------

        self._process_api_warnings(api_response_json)

        extra_info_from_api = api_response_json.get("extra", {})
        final_extra = {**self.extra, **extra_info_from_api}

        return HumblObject(
            results=results_lf.serialize(format="binary"),
            provider=self.api_query_params.provider,
            warnings=self.warnings,
            chart=None,
            extra={
                "original_api_response": self.raw_api_response,
                **final_extra,
            },
        )

    @log_start_end(logger=logger)
    async def fetch_data(
        self,
        obb_path: str,
        api_query_params: QueryParams,
    ) -> HumblObject:
        """
        Execute the TET pattern: Transform Query, Extract Data, Transform Data.

        Parameters
        ----------
        obb_path : str
            The OpenBB-style path for the API resource.
        api_query_params : QueryParams
            Pydantic model for API query parameters.

        Returns
        -------
        HumblObject
            A HumblObject containing the fetched and processed data.
        """
        await self.transform_query(obb_path, api_query_params)
        await self.extract_data()
        return await self.transform_data()
