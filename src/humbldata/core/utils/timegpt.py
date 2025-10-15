"""TimeGPT utilities and thin client wrapper.

This module centralizes Nixtla TimeGPT interactions behind a small wrapper
that is agnostic to humblDATA features. It exposes utilities to:

- Build a clean long-format frame for one series using a last contiguous
  monthly segment without gaps or nulls
- Call TimeGPT using explicit ``time_col`` and ``target_col`` without
  renaming columns

The wrapper can convert between Polars and Pandas as needed to satisfy the
TimeGPT client while returning Polars dataframes for consistency in the
codebase.
"""

from __future__ import annotations

import polars as pl
from nixtla import NixtlaClient

from humbldata.core.standard_models.abstract.warnings import HumblDataWarning
from humbldata.core.utils.env import Env


class HumblDataNixtlaClient:
    """Thin wrapper around Nixtla TimeGPT client.

    Parameters
    ----------
    env : Env, optional
        Environment accessor. If not provided, a new ``Env`` instance is used.
    api_key : str, optional
        Explicit API key override. If not provided, ``env.NIXTLA_API_KEY`` is
        used.

    Notes
    -----
    - The underlying Nixtla client is created lazily to avoid import costs
      when forecasting is disabled.
    - Methods return Polars DataFrames for consistency.
    """

    def __init__(
        self, env: Env | None = None, api_key: str | None = None
    ) -> None:
        self._env = env or Env()
        self._api_key = api_key or self._env.NIXTLA_API_KEY
        self._client: NixtlaClient | None = None

    @property
    def is_available(self) -> bool:
        """Whether the client can be instantiated (API key present)."""
        return bool(self._api_key)

    def _ensure_client(self) -> None:
        """Instantiate the Nixtla client if possible, otherwise raise a warning."""
        if self._client is not None:
            return
        if not self._api_key:
            msg = "NIXTLA_API_KEY not set - skipping TimeGPT forecast. Set Env.NIXTLA_API_KEY."
            raise HumblDataWarning(msg)

        self._client = NixtlaClient(api_key=self._api_key)

    def prepare_long_frame(
        self,
        df: pl.DataFrame | pl.LazyFrame,
        *,
        time_col: str,
        target_col: str,
        unique_id: str,
    ) -> pl.LazyFrame:
        """Prepare a single-series long-format dataframe for TimeGPT.

        The function sorts by ``time_col``, filters to the last contiguous
        monthly segment (no gaps larger than ~40 days), drops nulls in
        ``target_col``, and returns ``[unique_id, time_col, target_col]``.

        Parameters
        ----------
        df : pl.DataFrame
            Input wide or long dataframe containing ``time_col`` and
            ``target_col``.
        time_col : str
            Name of the timestamp column to pass to TimeGPT via ``time_col``.
        target_col : str
            Name of the numeric series to forecast, passed via ``target_col``.
        unique_id : str
            Series identifier required by TimeGPT when multiple series are
            present.

        Returns
        -------
        pl.DataFrame
            Clean long-format dataframe suitable for TimeGPT.
        """
        if isinstance(df, pl.LazyFrame):
            df = df.collect()
        if time_col not in df.columns or target_col not in df.columns:
            msg = f"Missing required columns for TimeGPT: {time_col!r}, {target_col!r}."
            raise HumblDataWarning(msg)

        work = (
            df.select([time_col, target_col])
            .sort(time_col)
            .drop_nulls([time_col, target_col])
        )

        # Identify last contiguous monthly segment based on day gaps
        # Allow small calendar irregularities by using a 40-day threshold
        if work.height > 1:
            diffs = (
                work.select(
                    pl.col(time_col).diff().dt.total_days().alias("_gap_days")
                )
                .with_row_index(name="_row")
                .filter(pl.col("_gap_days") > 40)
                .select("_row")
                .to_series()
            )
            start_idx = int(diffs.item(-1) + 1) if diffs.len() > 0 else 0
            work = work.slice(start_idx)

        work = work.with_columns(pl.lit(unique_id).alias("unique_id"))
        return work.select(["unique_id", time_col, target_col]).lazy()

    def forecast_series(
        self,
        df_long: pl.DataFrame | pl.LazyFrame,
        *,
        h: int,
        time_col: str,
        target_col: str,
        freq: str | None = None,
        model: str | None = None,
    ) -> pl.LazyFrame:
        """Forecast a single series using TimeGPT.

        Parameters
        ----------
        df_long : pl.DataFrame
            Long-format dataframe with columns ``unique_id``, ``time_col``,
            and ``target_col``.
        h : int
            Forecast horizon (number of future steps).
        time_col : str
            Name of the timestamp column.
        target_col : str
            Name of the numeric series column.
        freq : str, optional
            Optional frequency override (e.g., ``'MS'``). If ``None``, TimeGPT
            infers frequency.
        model : str, optional
            Optional model identifier for TimeGPT.

        Returns
        -------
        pl.DataFrame
            Dataframe with columns ``time_col`` and ``target_col`` containing
            the forecasted values for the next ``h`` steps.
        """
        if isinstance(df_long, pl.LazyFrame):
            df_long = df_long.collect()

        self._ensure_client()
        assert self._client is not None  # for type checkers)

        # Call Nixtla client forecast passing a Polars DataFrame directly
        if model is None:
            fcst_any = self._client.forecast(
                df=df_long,
                h=h,
                time_col=time_col,
                target_col=target_col,
                freq=freq,
            )
        else:
            fcst_any = self._client.forecast(
                df=df_long,
                h=h,
                time_col=time_col,
                target_col=target_col,
                freq=freq,
                model=model,
            )

        # Coerce output to Polars
        if isinstance(fcst_any, pl.DataFrame):
            fcst_pl = fcst_any
        else:
            try:
                fcst_pl = pl.from_pandas(fcst_any)  # type: ignore[arg-type]
            except Exception as exc:
                msg = "TimeGPT forecast output not convertible to Polars"
                raise HumblDataWarning(msg) from exc

        # The returned value column may be named 'TimeGPT'; normalize to target_col
        cols = set(fcst_pl.columns)
        value_col = target_col if target_col in cols else None
        if value_col is None:
            for candidate in ("TimeGPT", "timegpt", "yhat", "y"):
                if candidate in cols:
                    value_col = candidate
                    break
        if value_col is None:
            message = (
                "Could not locate forecast value column in TimeGPT response."
            )
            raise HumblDataWarning(message)

        # Normalize column names
        rename_map_pl: dict[str, str] = {}
        if value_col != target_col:
            rename_map_pl[value_col] = target_col
        if time_col not in cols and "ds" in cols:
            rename_map_pl["ds"] = time_col
        if rename_map_pl:
            fcst_pl = fcst_pl.rename(rename_map_pl)

        out_pl = fcst_pl.select([time_col, target_col])
        return out_pl.lazy()
