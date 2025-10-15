"""Helper orchestration for adding TimeGPT forecasts to humblCOMPASS.

This module remains feature-specific glue. Nixtla-agnostic utilities live in
`humbldata.core.utils.timegpt`.
"""

from __future__ import annotations

import polars as pl

from humbldata.core.standard_models.abstract.warnings import HumblDataWarning
from humbldata.core.utils.env import Env
from humbldata.core.utils.timegpt import HumblDataNixtlaClient


def timepgt_humbl_compass_engine(
    combined_df: pl.DataFrame | pl.LazyFrame,
    *,
    country: str,
    h: int,
    freq: str | None,
    env: Env,
    model: str | None = None,
) -> pl.LazyFrame:
    """Append CPI and CLI TimeGPT forecasts to combined dataset.

    Parameters
    ----------
    combined_df : pl.DataFrame
        Dataframe containing columns: ``date_month_start``, ``country``,
        ``cpi``, and ``cli`` at minimum, sorted by date.
    country : str
        Country identifier to embed in unique_id and annotate in outputs.
    h : int
        Forecast horizon (steps) to request from TimeGPT.
    freq : str, optional
        Optional frequency override for TimeGPT (e.g., ``'MS'``). If ``None``,
        TimeGPT will infer.
    env : Env
        Environment accessor containing NIXTLA_API_KEY.
    model : str, optional
        Optional model name passed through to TimeGPT.

    Returns
    -------
    pl.DataFrame
        The input frame with future rows appended and a boolean ``is_forecast``
        column (True for appended rows, False for historical).
    """
    lf = (
        combined_df.lazy()
        if isinstance(combined_df, pl.DataFrame)
        else combined_df
    )
    # Validate required columns lazily by schema introspection
    required_cols = {"date_month_start", "country", "cpi", "cli"}
    if not required_cols.issubset(set(lf.columns)):
        message = f"Missing required columns for forecasting: {required_cols}"
        raise HumblDataWarning(message)

    client = HumblDataNixtlaClient(env=env)
    if not client.is_available:
        # Graceful exit if API key is missing
        return lf.with_columns(pl.lit(value=False).alias("is_forecast"))

    # Prepare long frames
    date_col = "date_month_start"
    cpi_long = client.prepare_long_frame(
        lf,
        time_col=date_col,
        target_col="cpi",
        unique_id=f"{country}:cpi",
    )
    cli_long = client.prepare_long_frame(
        lf,
        time_col=date_col,
        target_col="cli",
        unique_id=f"{country}:cli",
    )

    # Forecast each series
    try:
        cpi_fcst = client.forecast_series(
            cpi_long,
            h=h,
            time_col=date_col,
            target_col="cpi",
            freq=freq,
            model=model,
        )
        cli_fcst = client.forecast_series(
            cli_long,
            h=h,
            time_col=date_col,
            target_col="cli",
            freq=freq,
            model=model,
        )
    except HumblDataWarning:
        # On any failure, return original with flag False
        return lf.with_columns(pl.lit(value=False).alias("is_forecast"))

    # Join forecasts on date and keep only dates strictly greater than last observed
    last_date = lf.select(pl.col(date_col).max()).collect().item()
    fcst_joined = (
        cpi_fcst.join(cli_fcst, on=date_col, how="inner")
        .filter(pl.col(date_col) > last_date)
        .with_columns(
            [
                pl.lit(country).alias("country"),
                pl.lit(value=True).alias("is_forecast"),
            ]
        )
        .select([date_col, "country", "cpi", "cli", "is_forecast"])
    )

    base = lf.with_columns(pl.lit(value=False).alias("is_forecast"))
    # Append
    # For safety, left-join forecast extras (if any) are ignored here; downstream steps will compute deltas/regimes
    appended = pl.concat([base, fcst_joined], how="diagonal_relaxed")
    return appended.lazy()
