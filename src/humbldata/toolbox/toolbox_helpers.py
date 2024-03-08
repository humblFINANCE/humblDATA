"""
Context: Toolbox || **Category: Helpers**.

These `Toolbox()` helpers are used in various calculations in the toolbox
context. Most of the helpers will be mathematical transformations of data. These
functions should be **DUMB** functions.
"""

from datetime import UTC, datetime, timedelta, timezone

import polars as pl
from dateutil.relativedelta import relativedelta

from humbldata.core.standard_models.abstract.errors import HumblDataError


# Private Functions Used in toolbox_helpers.py functions =======================
def _window_format(
    window: str,
    start_date: str | datetime | None = None,
    end_date: str | datetime | None = None,
    _return_timedelta: bool = True,
    _avg_trading_days: bool = False,
) -> str | timedelta:
    """
    Context: Toolbox || Category: Helpers || **Command: _window_format**.

    This function formats a window string into a standard format (e.g. "1d" for 1
    day, "1w" for 1 week, "1mo" for 1 month, "1q" for 1 quarter, "1y" for 1 year).

    Parameters
    ----------
    window : str
        The window string to format. It should contain a number followed by a
        window part. The window part can be 'day', 'week', 'month', 'quarter', or
        'year'. The window part can be in singular or plural form and can be
        abbreviated. For example, '2 weeks', '2week', '2wks', '2wk', '2w' are
        all valid.
    start_date : str | datetime | None, optional
        The start date of the window. If not provided, it is assumed to be None.
    end_date : str | datetime | None, optional
        The end date of the window. If not provided, the current UTC date is used.
    _return_timedelta : bool, optional
        A flag to determine if the return type should be a timedelta object.
        Default is True.
    _avg_trading_days : bool, optional
        A flag to determine if the average trading days should be considered in
        the calculation conversion from the window to days. If it is True,
        then the number of days returned will be equal to the number of trading
        days in that time period. Default is False.

    Returns
    -------
    str | timedelta
        The formatted window string or a timedelta object representing the
        window. The format of the string is a number followed by an abbreviation
        of the window part ('d' for day, 'w' for week, 'mo' for month, 'q' for
        quarter, 'y' for year). For example, '2 weeks' is formatted as '2w'.
        If _return_timedelta is True, a timedelta object is returned based on
        the window and _avg_trading_days flag.

    Raises
    ------
    HumblDataError
        If an invalid window part is provided.

    Notes
    -----
    This function has two parameters: `_return_timedelta` and `_avg_trading_days`.
    The point of having these two arguments are to control the output of the
    number of days that the function outputs. When using Polars `rolling_map()`,
    you can only pass an `int` to the parameter `window_size`. This will roll
    your function over a window of `n: int` size. BUT...when using
    `.rolling_std()` or `.rolling().agg() + map_elements()` logic, you can pass
    a `str | timedelta | int`. This allows for dynamic time based grouping.

    This allows for rolling based on an integer index in Polars functions by
    using the `1i` syntax.
    """  # noqa: W505
    # Determine the 'latest' date if not provided. This is used to correctly calculate the  number of days in a window
    if not end_date:
        end_date = datetime.utcnow()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=UTC)

    # Separate the number and window part
    num = "".join(filter(str.isdigit, window))
    # Find the first character after the number in the window string
    window_part = next((char for char in window if char.isalpha()), None)

    # Check if the window part is a valid abbreviation
    if window_part not in {"d", "w", "m", "y", "q"}:
        msg = (
            f"`{window}` could not be formatted; needs to include d, w, m, y, q"
        )
        raise HumblDataError(msg)

    # If the window part is "m", replace it with "mo" to represent "month"
    if window_part == "m":
        window_part = "mo"

    # Return the formatted window string
    if not _return_timedelta:
        out = num + window_part

    elif _return_timedelta:
        num = int(num)
        if not _avg_trading_days:
            if window_part == "d":
                out = relativedelta(days=num)
            elif window_part == "w":
                out = relativedelta(weeks=num)
            elif window_part == "mo":
                out = relativedelta(months=num)
            elif window_part == "q":
                out = relativedelta(months=num * 3)
            elif window_part == "y":
                out = relativedelta(years=num)
            else:
                msg = f"Invalid window part: {window_part}"
                raise HumblDataError(msg)
        elif _avg_trading_days:
            window_periods = {"d": 1, "w": 5, "mo": 21, "q": 63, "y": 252}
            out = timedelta(days=window_periods[window_part] * num)

        # Conversion to datetime object, to get days
        then = end_date - out
        out = end_date - then
    return out


def _window_format_monthly(window: str) -> int:
    """
    Context: Toolbox || Category: Helpers || **Command: _window_format_monthly**.

    This function returns the number of months in a window.

    Parameters
    ----------
    window : str
        The window string to format. It should contain a number followed by a
        window part. The window part can be 'day', 'week', 'month', 'quarter', or
        'year'. The window part can be in singular or plural form and can be
        abbreviated. For example, '2 weeks', '2week', '2wks', '2wk', '2w' are
        all valid.

    Returns
    -------
    int
        The number of months as an integer.

    Raises
    ------
    ValueError
        If the time string format is unrecognized.
    """
    # Extract the quantity and the unit from the string
    quantity = int("".join(filter(str.isdigit, window)))
    unit = "".join(filter(str.isalpha, window))

    # Define a mapping from units to their equivalent in months
    unit_to_months = {
        "d": 1 / 30,  # Approximate a day to 1/30th of a month
        "w": 1 / 4,  # Approximate a week to 1/4th of a month
        "mo": 1,  # A month is exactly 1 month
        "q": 3,  # A quarter is 3 months
        "y": 12,  # A year is 12 months
    }

    if unit not in unit_to_months:
        msg = f"Unrecognized time unit: '{unit}' in '{window}'"
        raise HumblDataError(msg)

    # Calculate the number of months
    months = quantity * unit_to_months[unit]

    # Return the number of months, rounded to the nearest whole number
    return round(months)


def _cumsum_check(
    data: pl.DataFrame | pl.LazyFrame | pl.Series | None = None,
    _column_name: str = "cumdev",
) -> bool:
    """
    Context: Toolbox || Category: Helpers || **Command: _cumsum_check**.

    Check if the last value of a column in a DataFrame is 0 for each symbol and window.

    This function returns True if the last value is 0 for all groups, otherwise it raises
    a HumblDataError and stops code execution.

    Parameters
    ----------
    data : Union[pl.DataFrame, pl.LazyFrame, pl.Series]
        The data to check. It should have 'symbol' and 'window_index' columns for grouping.
    _column_name : str
        The name of the column to check.

    Returns
    -------
    bool
        True if the last value of the column is 0 for all groups, otherwise raises an error.

    Raises
    ------
    HumblDataError
        If the last value of the column is not close to 0 for any group.

    Notes
    -----
    This function is used in `cum_sum()`
    """
    from numpy import isclose

    if isinstance(data, pl.DataFrame | pl.LazyFrame):
        # Ensure data is a DataFrame for processing
        if isinstance(data, pl.LazyFrame):
            data = data.collect()

        # Check if 'symbol' and 'window_index' columns exist
        group_cols = _set_over_cols(data, "symbol", "window_index")

        # Group by 'symbol' and 'window_index', then check the last value of each group
        if group_cols:
            grouped = data.group_by(group_cols).agg(
                [pl.last(_column_name).alias("last_value")]
            )
        else:
            grouped = data.with_columns(last_value=pl.last(_column_name))

        # Check if the last value is close to 0 for each group
        if not all(isclose(grouped["last_value"], 0, atol=1e-6)):
            msg = "Not all groups' last value is close to 0 in `cum_sum()`"
            raise HumblDataError(msg)

    elif isinstance(data, pl.Series):
        # For a Series, just check the last value
        if not isclose(data.tail(1)[0], 0, atol=1e-6):
            msg = (
                "The value is not close to 0, there was an error in `cum_sum()`"
            )
            raise HumblDataError(msg)
    else:
        msg = "No DataFrame/LazyFrame or Series was provided."
        raise HumblDataError(msg)

    return True


def _check_required_columns(data: pl.DataFrame | pl.LazyFrame, *columns: str):
    """
    Context: Toolbox || Category: Technical || Sub-Category: Volatility Helpers || **Command: check_required_columns**.

    Checks if all required columns are present in the DataFrame.

    Parameters
    ----------
    data : pl.DataFrame | pl.LazyFrame
        The DataFrame to check.
    *args
        Variable length argument list for required column names.

    Raises
    ------
    HumblDataError
        If any of the required columns are missing.

    Examples
    --------
    >>> check_required_columns(data, "open", "close", "high", "low")
    """
    missing_columns = [col for col in columns if col not in data.columns]
    if missing_columns:
        msg = f"Missing required columns: {', '.join(missing_columns)}"
        raise HumblDataError(msg)


def _set_sort_cols(
    data: pl.DataFrame | pl.LazyFrame, *columns: str
) -> list[str] | None:
    """
    Context: Toolbox || Category: Helpers || **Command: _set_sort_cols**.

    This function returns only present columns in a DataFrame.
    It is used to set the columns to use for the `sort` parameter in Polars
    DataFrame operations.

    If the DataFrame has a 'symbol' column, it will be used as the first column in the list.
    If the DataFrame has a 'window_index' column, it will be used as the second column in the list.
    If the DataFrame has neither of these columns, the list will be empty.

    Parameters
    ----------
    data : pl.DataFrame
        The DataFrame to check for column presence.
    *columns : str
        Variable number of string arguments representing column names to check
        in the DataFrame.

    Returns
    -------
    Optional[List[str]]
        A list containing the names of the columns that are present in the
        DataFrame,
        in the order they were specified. Returns None if none of the specified
        columns are present.

    Examples
    --------
    >>> df = pl.DataFrame({"symbol": [1, 2, 3], "price": [100, 101, 102]})
    >>> _set_sort_cols(df, "symbol", "window_index")
    ['symbol']
    """
    present_columns = [col for col in columns if col in data.columns]
    return present_columns if present_columns else None


def _set_over_cols(
    data: pl.DataFrame | pl.LazyFrame, *columns: str
) -> list[str] | None:
    """
    Context: Toolbox || Category: Helpers || **Command: _set_over_cols**.

    This function returns only present columns in a DataFrame.
    It is used to set the columns to use for the `over` parameter in Polars
    DataFrame operations.
    If the DataFrame has a 'symbol' column, it will be used as the first column
    in the list.
    If the DataFrame has a 'window_index' column, it will be used as the second
    column in the list.
    If the DataFrame has neither of these columns, the list will be empty.

    Parameters
    ----------
    data : pl.DataFrame
        The DataFrame to check for column presence.
    *columns : str
        Variable number of string arguments representing column names to check
        in the DataFrame.

    Returns
    -------
    Optional[List[str]]
        A list containing the names of the columns that are present in the
        DataFrame,
        in the order they were specified. Returns None if none of the specified
        columns are present.

    Examples
    --------
    >>> df = pl.DataFrame({"symbol": [1, 2, 3], "price": [100, 101, 102]})
    >>> _set_over_cols(df, "symbol", "window_index")
    ['symbol']
    """
    present_columns = [col for col in columns if col in data.columns]
    return present_columns if present_columns else None


# Public Functions =============================================================
def log_returns(
    data: pl.Series | pl.DataFrame | pl.LazyFrame | None = None,
    _column_name: str = "adj_close",
    *,
    _drop_nulls: bool = True,
    _sort: bool = True,
) -> pl.Series | pl.DataFrame | pl.LazyFrame:
    """
    Context: Toolbox || Category: Helpers || **Command: log_returns**.

    This is a DUMB command. It can be used in any CONTEXT or CATEGORY.
    Calculates the logarithmic returns for a given Polars Series, DataFrame, or
    LazyFrame. Logarithmic returns are widely used in the financial
    industry to measure the rate of return on investments over time. This
    function supports calculations on both individual series and dataframes
    containing financial time series data.

    Parameters
    ----------
    data : pl.Series | pl.DataFrame | pl.LazyFrame, optional
        The input data for which to calculate the log returns. Default is None.
    _drop_nulls : bool, optional
        Whether to drop null values from the result. Default is True.
    _column_name : str, optional
        The column name to use for log return calculations in DataFrame or
        LazyFrame. Default is "adj_close".
    _sort : bool, optional
        If True, sorts the DataFrame or LazyFrame by `date` and `symbol` before
        calculation. If you want a DUMB function, set to False.
        Default is True.

    Returns
    -------
    pl.Series | pl.DataFrame | pl.LazyFrame
        The original `data`, with an extra column of `log returns` of the input
        data. The return type matches the input type.

    Raises
    ------
    HumblDataError
        If neither a series, DataFrame, nor LazyFrame is provided as input.

    Examples
    --------
    >>> series = pl.Series([100, 105, 103])
    >>> log_returns(data=series)
    series([-inf, 0.048790, -0.019418])

    >>> df = pl.DataFrame({"adj_close": [100, 105, 103]})
    >>> log_returns(data=df)
    shape: (3, 2)
    ┌───────────┬────────────┐
    │ adj_close ┆ log_returns│
    │ ---       ┆ ---        │
    │ f64       ┆ f64        │
    ╞═══════════╪════════════╡
    │ 100.0     ┆ NaN        │
    ├───────────┼────────────┤
    │ 105.0     ┆ 0.048790   │
    ├───────────┼────────────┤
    │ 103.0     ┆ -0.019418  │
    └───────────┴────────────┘

    Improvements
    -----------
    Add a parameter `_sort_cols: list[str] | None = None` to make the function even
    dumber. This way you could specify certain columns to sort by instead of
    using default `date` and `symbol`. If `_sort_cols=None` and `_sort=True`,
    then the function will use the default `date` and `symbol` columns for
    sorting.

    """
    # Calculation for Polars Series
    if isinstance(data, pl.Series):
        out = data.log().diff()
        if _drop_nulls:
            out = out.drop_nulls()
    # Calculation for Polars DataFrame or LazyFrame
    elif isinstance(data, pl.DataFrame | pl.LazyFrame):
        sort_cols = _set_sort_cols(data, "symbol", "date")
        if _sort and sort_cols:
            data = data.sort(sort_cols)
        elif _sort and not sort_cols:
            msg = "Data must contain 'symbol' and 'date' columns for sorting."
            raise HumblDataError(msg)

        if "log_returns" not in data.columns:
            out = data.set_sorted(sort_cols).with_columns(
                pl.col(_column_name).log().diff().alias("log_returns")
            )
        else:
            out = data
        if _drop_nulls:
            out = out.drop_nulls(subset="log_returns")
    else:
        msg = "No valid data type was provided for `log_returns()` calculation."
        raise HumblDataError(msg)

    return out


def detrend(
    data: pl.DataFrame | pl.LazyFrame | pl.Series,
    _detrend_col: str = "log_returns",
    _detrend_value_col: str | pl.Series | None = "window_mean",
    *,
    _sort: bool = False,
) -> pl.DataFrame | pl.LazyFrame | pl.Series:
    """
    Context: Toolbox || Category: Helpers || **Command: detrend**.

    This is a DUMB command. It can be used in any CONTEXT or CATEGORY.

    Detrends a column in a DataFrame, LazyFrame, or Series by subtracting the
    values of another column from it. Optionally sorts the data by 'symbol' and
    'date' before detrending if _sort is True.

    Parameters
    ----------
    data : Union[pl.DataFrame, pl.LazyFrame, pl.Series]
        The data structure containing the columns to be processed.
    _detrend_col : str
        The name of the column from which values will be subtracted.
    _detrend_value_col : str | pl.Series | None, optional
        The name of the column whose values will be subtracted OR if you
        pass a pl.Series to the `data` parameter, then you can use this to
        pass a second `pl.Series` to subtract from the first.
    _sort : bool, optional
        If True, sorts the data by 'symbol' and 'date' before detrending.
        Default is False.

    Returns
    -------
    Union[pl.DataFrame, pl.LazyFrame, pl.Series]
        The detrended data structure with the same type as the input,
        with an added column named `f"detrended_{_detrend_col}"`.

    Notes
    -----
    Function doesn't use `.over()` in calculation. Once the data is sorted,
    subtracting _detrend_value_col from _detrend_col is a simple operation
    that doesn't need to be grouped, because the sorting has already aligned
    the rows for subtraction
    """
    if isinstance(data, pl.DataFrame | pl.LazyFrame):
        sort_cols = _set_sort_cols(data, "symbol", "date")
        if _sort and sort_cols:
            data = data.sort(sort_cols)
        elif _sort and not sort_cols:
            msg = "Data must contain 'symbol' and 'date' columns for sorting."
            raise HumblDataError(msg)

    if isinstance(data, pl.DataFrame | pl.LazyFrame):
        if (
            _detrend_value_col not in data.columns
            or _detrend_col not in data.columns
        ):
            msg = f"Both {_detrend_value_col} and {_detrend_col} must be columns in the data."
            raise HumblDataError(msg)
        detrended = data.set_sorted(sort_cols).with_columns(
            (pl.col(_detrend_col) - pl.col(_detrend_value_col)).alias(
                f"detrended_{_detrend_col}"
            )
        )
    elif isinstance(data, pl.Series):
        if not isinstance(_detrend_value_col, pl.Series):
            msg = "When 'data' is a Series, '_detrend_value_col' must also be a Series."
            raise HumblDataError(msg)
        detrended = data - _detrend_value_col
        detrended.rename(f"detrended_{_detrend_col}")

    return detrended


def cum_sum(
    data: pl.DataFrame | pl.LazyFrame | pl.Series | None = None,
    _column_name: str = "detrended_returns",
    *,
    _sort: bool = True,
    _mandelbrot_usage: bool = True,
) -> pl.LazyFrame | pl.DataFrame | pl.Series:
    """
    Context: Toolbox || Category: Helpers || **Command: cum_sum**.

    This is a DUMB command. It can be used in any CONTEXT or CATEGORY.

    Calculate the cumulative sum of a series or column in a DataFrame or
    LazyFrame.

    Parameters
    ----------
    data : pl.DataFrame | pl.LazyFrame | pl.Series | None
        The data to process.
    _column_name : str
        The name of the column to calculate the cumulative sum on,
        applicable if df is provided.
    _sort : bool, optional
        If True, sorts the DataFrame or LazyFrame by date and symbol before
        calculation. Default is True.
    _mandelbrot_usage : bool, optional
        If True, performs additional checks specific to the Mandelbrot Channel
        calculation. This should be set to True when you have a cumulative
        deviate series, and False when not. Please check 'Notes' for more
        information. Default is True.

    Returns
    -------
    pl.DataFrame | pl.LazyFrame | pl.Series
        The DataFrame or Series with the cumulative deviate series added as a
        new column or as itself.

    Notes
    -----
    This function is used to calculate the cumulative sum for the deviate series
    of detrended returns for the data in the pipeline for
    `calc_mandelbrot_channel`.

    So, although it is calculating a cumulative sum, it is known as a cumulative
    deviate because it is a cumulative sum on a deviate series, meaning that the
    cumulative sum should = 0 for each window. The _mandelbrot_usage parameter
    allows for checks to ensure the data is suitable for Mandelbrot Channel
    calculations, i.e that the deviate series was calculated correctly by the
    end of each series being 0, meaning the trend (the mean over the
    window_index) was successfully removed from the data.
    """
    if isinstance(data, pl.DataFrame | pl.LazyFrame):
        sort_cols = _set_sort_cols(data, "symbol", "date")
        if _sort:
            data = data.sort(sort_cols)

        over_cols = _set_over_cols(data, "symbol", "window_index")
        if over_cols:
            out = data.set_sorted(sort_cols).with_columns(
                pl.col(_column_name).cum_sum().over(over_cols).alias("cum_sum")
            )
        else:
            out = data.with_columns(
                pl.col(_column_name).cum_sum().alias("cum_sum")
            )
    elif isinstance(data, pl.Series):
        out = data.cum_sum().alias("cum_sum")
    else:
        msg = "No DataFrame/LazyFrame/Series was provided."
        raise HumblDataError(msg)

    if _mandelbrot_usage:
        _cumsum_check(out, _column_name="cum_sum")

    return out


def std(
    data: pl.LazyFrame | pl.DataFrame | pl.Series, _column_name: str = "cum_sum"
) -> pl.LazyFrame | pl.DataFrame | pl.Series:
    """
    Context: Toolbox || Category: Helpers || **Command: std**.

    Calculate the standard deviation of the cumulative deviate series within
    each window of the dataset.

    Parameters
    ----------
    df : pl.LazyFrame
        The LazyFrame from which to calculate the standard deviation.
    _column_name : str, optional
        The name of the column from which to calculate the standard deviation,
        with "cumdev" as the default value.

    Returns
    -------
    pl.LazyFrame
        A LazyFrame with the standard deviation of the specified column for each
        window, added as a new column named "S".

    Improvements
    -----------
    Just need to parametrize `.over()` call in the function if want an even
    dumber function, that doesn't calculate each `window_index`.
    """
    if isinstance(data, pl.Series):
        out = data.std()
    elif isinstance(data, pl.DataFrame | pl.LazyFrame):
        sort_cols = _set_sort_cols(data, "symbol", "date")
        over_cols = _set_over_cols(data, "symbol", "window_index")

        if over_cols:
            out = data.set_sorted(sort_cols).with_columns(
                [
                    pl.col(_column_name)
                    .std()
                    .over(over_cols)
                    .alias(f"{_column_name}_std"),  # used to be 'S'
                ]
            )
        else:
            out = data.with_columns(
                pl.col(_column_name).std().alias("S"),
            )

    return out


def mean(
    data: pl.DataFrame | pl.LazyFrame | pl.Series,
    _column_name: str = "log_returns",
    *,
    _sort: bool = True,
) -> pl.DataFrame | pl.LazyFrame:
    """
    Context: Toolbox || Category: Helpers || **Function: mean**.

    This is a DUMB command. It can be used in any CONTEXT or CATEGORY.

    This function calculates the mean of a column (<_column_name>) over a
    each window in the dataset, if there are any.
    This window is intended to be the `window` that is passed in the
    `calc_mandelbrot_channel()` function. The mean calculated is meant to be
    used as the mean of each `window` within the time series. This
    way, each block of windows has their own mean, which can then be used to
    normalize the data (i.e remove the mean) from each window section.

    Parameters
    ----------
    data : pl.DataFrame | pl.LazyFrame
        The DataFrame or LazyFrame to calculate the mean on.
    _column_name : str
        The name of the column to calculate the mean on.
    _sort : bool
        If True, sorts the DataFrame or LazyFrame by date before calculation.
        Default is False.

    Returns
    -------
    pl.DataFrame | pl.LazyFrame
        The original DataFrame or LazyFrame with a `window_mean` & `date` column,
        which contains the mean of 'log_returns' per range/window.


    Notes
    -----
    Since this function is an aggregation function, it reduces the # of
    observations in the dataset,thus, unless I take each value and iterate each
    window_mean value to correlate to the row in the original dataframe, the
    function will return a dataframe WITHOUT the original data.

    """
    if isinstance(data, pl.Series):
        out = data.mean()
    else:
        if data is None:
            msg = "No DataFrame was passed to the `mean()` function."
            raise HumblDataError(msg)
        sort_cols = _set_sort_cols(data, "symbol", "date")
        over_cols = _set_over_cols(data, "symbol", "window_index")
        if _sort and sort_cols:  # Check if _sort is True
            data = data.sort(sort_cols).set_sorted(sort_cols)
        if over_cols:
            out = data.with_columns(
                pl.col(_column_name).mean().over(over_cols).alias("window_mean")
            )
        else:
            out = data.with_columns(pl.col(_column_name).mean().alias("mean"))
        if sort_cols:
            out = out.sort(sort_cols)
    return out


def range_(
    data: pl.LazyFrame | pl.DataFrame | pl.Series,
    _column_name: str = "cum_sum",
    *,
    _sort: bool = True,
) -> pl.LazyFrame | pl.DataFrame | pl.Series:
    """
    Context: Toolbox || Category: Technical || Sub-Category: MandelBrot Channel || Sub-Category: Helpers || **Function: mandelbrot_range**.

    Calculate the range (max - min) of the cumulative deviate values of a
    specified column in a DataFrame for each window in the dataset, if there are any.

    Parameters
    ----------
    data : pl.LazyFrame
        The DataFrame to calculate the range from.
    _column_name : str, optional
        The column to calculate the range from, by default "cumdev".

    Returns
    -------
    pl.LazyFrame | pl.DataFrame
        A DataFrame with the range of the specified column for each window.
    """
    if isinstance(data, pl.Series):
        out = data.max() - data.min()

    if isinstance(data, pl.LazyFrame | pl.DataFrame):
        sort_cols = _set_sort_cols(data, "symbol", "date")
    over_cols = _set_over_cols(data, "symbol", "window_index")
    if _sort:
        data = data.sort(sort_cols)
    if over_cols:
        out = (
            data.set_sorted(sort_cols)
            .with_columns(
                [
                    pl.col(_column_name)
                    .min()
                    .over(over_cols)
                    .alias(f"{_column_name}_min"),
                    pl.col(_column_name)
                    .max()
                    .over(over_cols)
                    .alias(f"{_column_name}_max"),
                ]
            )
            .sort(sort_cols)
            .with_columns(
                (
                    pl.col(f"{_column_name}_max")
                    - pl.col(f"{_column_name}_min")
                ).alias(f"{_column_name}_range"),  # used to be 'R'
            )
        )
    else:
        out = (
            data.with_columns(
                [
                    pl.col(_column_name).min().alias(f"{_column_name}_min"),
                    pl.col(_column_name).max().alias(f"{_column_name}_max"),
                ]
            )
            .sort(sort_cols)
            .with_columns(
                (
                    pl.col(f"{_column_name}_max")
                    - pl.col(f"{_column_name}_min")
                ).alias(f"{_column_name}_range"),
            )
        )

    return out
