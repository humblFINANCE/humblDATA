import base64
import io
from typing import Any, ClassVar, Generic, Literal, Optional, TypeVar, overload

import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializeAsAny,
)

from humbldata.core.standard_models.abstract.chart import Chart
from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.abstract.tagged import Tagged
from humbldata.core.standard_models.abstract.warnings import Warning_
from humbldata.core.standard_models.portfolio import PortfolioQueryParams
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.utils.env import Env
from humbldata.core.utils.logger import setup_logger

env = Env()
logger = setup_logger("HumblObject", env.LOGGER_LEVEL)

T = TypeVar("T")


def extract_subclass_dict(self, attribute_name: str, items: list):
    """
    Extract the dictionary representation of the specified attribute.

    Parameters
    ----------
    attribute_name : str
        The name of the attribute to update in the items list.
    """
    # Check if the attribute exists and has a value
    attribute_value = getattr(self, attribute_name, None)
    if attribute_value:
        # Assuming the attribute has a method called 'model_dump' to get its dictionary representation
        add_item = attribute_value.model_dump()
        add_item_str = str(add_item)
        if len(add_item_str) > 80:
            add_item_str = add_item_str[:80] + "..."
        for i, item in enumerate(items):
            if item.startswith(f"{attribute_name}:"):
                items[i] = f"{attribute_name}: {add_item_str}"
                break

    return items


class HumblObject(Tagged, Generic[T]):
    """HumblObject is the base class for all data returned from the Toolbox."""

    _user_settings: ClassVar[BaseModel | None] = None
    _system_settings: ClassVar[BaseModel | None] = None

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    results: T | None = Field(
        default=None,
        description="Serializable Logical Plan of the pl.LazyFrame results.",
    )
    equity_data: T | None = Field(
        default=None,
        description="Serialized raw data used in the command calculations.",
    )
    provider: str | None = Field(
        default=None,
        description="Provider name.",
    )
    warnings: list[Warning_] | None = Field(
        default=None,
        description="List of warnings.",
    )
    chart: Chart | list[Chart] | None = Field(
        default=None,
        description="Chart object.",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Extra info.",
    )
    context_params: ToolboxQueryParams | PortfolioQueryParams | None = Field(
        default=None,
        title="Context Parameters",
        description="Context parameters.",
    )
    command_params: Optional[SerializeAsAny[QueryParams]] = Field(
        default=None,
        title="Command Parameters",
        description="Command-specific parameters.",
    )

    # @field_validator("command_params")
    # def validate_command_params(cls, v):
    #     class_name = v.__class__.__name__
    #     if "QueryParams" in class_name:
    #         return v
    #     msg = "Wrong type for 'command_params', must be subclass of QueryParams"
    #     raise TypeError(msg)

    def __repr__(self) -> str:
        """Human readable representation of the object."""
        items = [
            f"{k}: {v}"[:83] + ("..." if len(f"{k}: {v}") > 83 else "")
            for k, v in self.model_dump().items()
        ]

        # Needed to extract subclass dict correctly
        # items = extract_subclass_dict(self, "command_params", items)

        return f"{self.__class__.__name__}\n\n" + "\n".join(items)

    @overload
    def to_polars(
        self, collect: Literal[True] = True, equity_data: bool = False
    ) -> pl.DataFrame: ...
    @overload
    def to_polars(
        self, collect: Literal[False], equity_data: bool = False
    ) -> pl.LazyFrame: ...

    def to_polars(
        self, collect: bool = True, equity_data: bool = False
    ) -> pl.LazyFrame | pl.DataFrame:
        """
        Deserialize the stored results or return the LazyFrame, and optionally collect them into a Polars DataFrame.

        Parameters
        ----------
        collect : bool, optional
            If True, collects the deserialized LazyFrame into a DataFrame.
            Default is True.
        equity_data : bool, optional
            If True, processes equity_data instead of results.
            Default is False.

        Returns
        -------
        pl.LazyFrame | pl.DataFrame
            The results as a Polars LazyFrame or DataFrame,
            depending on the collect parameter.

        Raises
        ------
        HumblDataError
            If no results or equity data are found to process
        """
        data = self.equity_data if equity_data else self.results

        if data is None:
            raise HumblDataError("No data found.")

        if isinstance(data, pl.LazyFrame):
            out = data
        elif isinstance(data, str):
            with io.StringIO(data) as data_io:
                out = pl.LazyFrame.deserialize(data_io, format="json")
        elif isinstance(data, bytes):
            with io.BytesIO(data) as data_io:
                out = pl.read_ipc(data_io).lazy()
        else:
            raise HumblDataError(
                "Invalid data type. Expected LazyFrame or serialized string."
            )

        if collect:
            out = out.collect()

        return out

    def to_df(
        self, collect: bool = True, equity_data: bool = False
    ) -> pl.LazyFrame | pl.DataFrame:
        """
        Alias for the `to_polars` method.

        Parameters
        ----------
        collect : bool, optional
            If True, collects the deserialized LazyFrame into a DataFrame.
            Default is True.

        Returns
        -------
        pl.LazyFrame | pl.DataFrame
            The deserialized results as a Polars LazyFrame or DataFrame,
            depending on the collect parameter.
        """
        return self.to_polars(collect=collect, equity_data=equity_data)

    def to_pandas(self, equity_data: bool = False) -> pd.DataFrame:
        """
        Convert the results to a Pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            The results as a Pandas DataFrame.
        """
        return self.to_polars(collect=True, equity_data=equity_data).to_pandas()

    def to_numpy(self, equity_data: bool = False) -> np.ndarray:
        """
        Convert the results to a NumPy array.

        Returns
        -------
        np.ndarray
            The results as a NumPy array.
        """
        return self.to_polars(collect=True, equity_data=equity_data).to_numpy()

    def to_dict(
        self,
        row_wise: bool = False,
        equity_data: bool = False,
        as_series: bool = True,
    ) -> dict | list[dict]:
        """
        Transform the stored data into a dictionary or a list of dictionaries.

        This method allows for the conversion of the internal data
        representation into a more universally accessible format, either
        aggregating the entire dataset into a single dictionary (column-wise)
        or breaking it down into a list of dictionaries, each representing a
        row in the dataset.

        Parameters
        ----------
        row_wise : bool, optional
            Determines the format of the output. If set to True, the method
            returns a list of dictionaries, with each dictionary representing a
            row and its corresponding data as key-value pairs. If set to False,
            the method returns a single dictionary, with column names as keys
            and lists of column data as values. Default is False.

        equity_data : bool, optional
            A flag to specify whether to use equity-specific data for the
            conversion. This parameter allows for flexibility in handling
            different types of data stored within the object. Default is
            False.
        as_series : bool, optional
            If True, the method returns a pl.Series with values as Series. If
            False, the method returns a dict with values as List[Any].
            Default is True.

        Returns
        -------
        dict | list[dict]
            Depending on the `row_wise` parameter, either a dictionary mapping column names to lists of values (if `row_wise` is False) or a list of dictionaries, each representing a row in the dataset (if `row_wise` is True).
        """
        if row_wise:
            return self.to_polars(
                collect=True, equity_data=equity_data
            ).to_dicts()
        return self.to_polars(collect=True, equity_data=equity_data).to_dict(
            as_series=as_series
        )

    def to_arrow(self, equity_data: bool = False) -> pa.Table:
        """
        Convert the results to an Arrow Table.

        Returns
        -------
        pa.Table
            The results as an Arrow Table.
        """
        return self.to_polars(collect=True, equity_data=equity_data).to_arrow()

    def to_struct(
        self, name: str = "results", equity_data: bool = False
    ) -> pl.Series:
        """
        Convert the results to a struct.

        Parameters
        ----------
        name : str, optional
            The name of the struct. Default is "results".

        Returns
        -------
        pl.Struct
            The results as a struct.
        """
        return self.to_polars(collect=True, equity_data=equity_data).to_struct(
            name=name
        )

    def to_json(
        self,
        equity_data: bool = False,
        chart: bool = False,
        object_dump: bool = False,
    ) -> str | list[str]:
        """
        Convert the results to a JSON string.

        Parameters
        ----------
        equity_data : bool, optional
            If True, return equity data instead of results. Default is False.
        chart : bool, optional
            If True, return all generated charts as a JSON string instead of
            returning the results. Default is False.
        object_dump : bool, optional
            If True, serialize the entire HumblObject model to JSON. Default is False.

        Returns
        -------
        str | list[str]
            The results, charts, or entire object as a JSON string or list of JSON strings.

        Raises
        ------
        HumblDataError
            If chart is True but no charts are available.
        """
        import json
        from datetime import date, datetime

        from humbldata.core.standard_models.abstract.errors import (
            HumblDataError,
        )

        def json_serial(obj):
            """JSON serializer for objects not serializable by default json code."""
            logger.debug("Serializing object of type: %s", type(obj))
            if isinstance(obj, (datetime, date)):
                logger.debug("Converting datetime/date to ISO format")
                return obj.isoformat()
            elif isinstance(obj, bytes):
                logger.debug("Converting bytes to base64 encoded string")
                return base64.b64encode(obj).decode("utf-8")
            elif isinstance(obj, pl.LazyFrame):
                logger.debug("Serializing LazyFrame to binary format")
                return obj.serialize(format="binary")
            msg = f"Type {type(obj)} not serializable"
            logger.debug("Serialization failed: %s", msg)
            raise TypeError(msg)

        def decode_base64_numpy_arrays(chart_json: str) -> str:
            """
            Decode base64-encoded numpy arrays in Plotly chart JSON.

            Parameters
            ----------
            chart_json : str
                The JSON string containing the chart data

            Returns
            -------
            str
                The JSON string with decoded numpy arrays
            """
            # Parse the JSON to a Python dict
            if not chart_json:
                return chart_json

            chart_data = json.loads(chart_json)

            # Function to recursively process the chart data
            def process_dict(
                d: dict | list | Any,
            ) -> dict | list | Any:
                if isinstance(d, dict):
                    for key, value in d.items():
                        if (
                            isinstance(value, dict)
                            and "dtype" in value
                            and "bdata" in value
                        ):
                            # This looks like a base64-encoded numpy array
                            try:
                                dtype = value.get("dtype")
                                b64_data = value.get("bdata")

                                if isinstance(b64_data, str):
                                    # Decode the base64 data
                                    binary_data = base64.b64decode(b64_data)

                                    # Convert to numpy array
                                    array = np.frombuffer(
                                        binary_data, dtype=dtype
                                    )

                                    # Replace the encoded data with the actual array values
                                    d[key] = array.tolist()
                            except Exception:
                                # If decoding fails, leave as is
                                pass
                        elif isinstance(value, (dict, list)):
                            process_dict(value)
                elif isinstance(d, list):
                    for i, item in enumerate(d):
                        if isinstance(item, (dict, list)):
                            process_dict(item)
                return d

            # Process the chart data
            processed_data = process_dict(chart_data)

            # Convert back to JSON string with compact formatting (no spaces)
            return json.dumps(processed_data, separators=(",", ":"))

        if object_dump:
            # Serialize the entire HumblObject to JSON using Pydantic's model_dump
            return json.dumps(
                self.model_dump(), default=json_serial, separators=(",", ":")
            )
        elif chart:
            if self.chart is None:
                msg = f"You set `.to_json(chart=True)` but there were no charts. Make sure `chart=True` in {self.command_params.__class__.__name__}"
                raise HumblDataError(msg)

            if isinstance(self.chart, list):
                return [
                    decode_base64_numpy_arrays(chart.content)
                    if chart and chart.content
                    else ""
                    for chart in self.chart
                    if chart
                ]
            else:
                return (
                    decode_base64_numpy_arrays(self.chart.content)
                    if self.chart.content
                    else ""
                )
        else:
            data = self.to_polars(
                collect=True, equity_data=equity_data
            ).to_dict(as_series=False)
            return json.dumps(data, default=json_serial, separators=(",", ":"))

    def is_empty(self, equity_data: bool = False) -> bool:
        """
        Check if the results are empty.

        Returns
        -------
        bool
            True if the results are empty, False otherwise.
        """
        return self.to_polars(collect=True, equity_data=equity_data).is_empty()

    def show(self) -> None:
        """Show the chart."""
        if isinstance(self.chart, list):
            for chart in self.chart:
                if chart and chart.fig:
                    chart.fig.show()
                else:
                    msg = "Chart object is missing or incomplete."
                    raise HumblDataError(msg)
        elif not self.chart or not self.chart.fig:
            msg = "Chart not found."
            raise HumblDataError(msg)
