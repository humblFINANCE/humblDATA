import io
from typing import Any, ClassVar, Generic, TypeVar

import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    SerializeAsAny,
    field_validator,
)

from humbldata.core.standard_models.abstract.chart import Chart
from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.standard_models.abstract.query_params import QueryParams
from humbldata.core.standard_models.abstract.tagged import Tagged
from humbldata.core.standard_models.abstract.warnings import Warning_
from humbldata.core.standard_models.portfolio import PortfolioQueryParams
from humbldata.core.standard_models.toolbox import ToolboxQueryParams

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
    """HumblObject is the base class for all dta returned from the Toolbox."""

    _user_settings: ClassVar[BaseModel | None] = None
    _system_settings: ClassVar[BaseModel | None] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

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
        default_factory=ToolboxQueryParams,
        title="Context Parameters",
        description="Context parameters.",
    )
    command_params: SerializeAsAny[QueryParams] | None = Field(
        default=QueryParams,
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
                out = pl.LazyFrame.deserialize(data_io, format="binary")
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
        self, equity_data: bool = False, chart: bool = False
    ) -> str | list[str]:
        """
        Convert the results to a JSON string.

        Parameters
        ----------
        equity_data : bool, optional
            A flag to specify whether to use equity-specific data for the
            conversion. Default is False.
        chart : bool, optional
            If True, return all generated charts as a JSON string instead of
            returning the results. Default is False.

        Returns
        -------
        str
            The results or charts as a JSON string.

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
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            msg = f"Type {type(obj)} not serializable"
            raise TypeError(msg)

        if chart:
            if self.chart is None:
                msg = f"You set `.to_json(chart=True)` but there were no charts. Make sure `chart=True` in {self.command_params.__class__.__name__}"
                raise HumblDataError(msg)

            if isinstance(self.chart, list):
                return [
                    chart.fig.to_json()
                    for chart in self.chart
                    if chart and chart.fig
                ]
            else:
                return self.chart.fig.to_json()
        else:
            data = self.to_polars(
                collect=True, equity_data=equity_data
            ).to_dict(as_series=False)
            return json.dumps(data, default=json_serial)

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
