"""HumblCompass SimpleBacktest with publication-lag-aware alignment options."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd
import polars as pl

from humbldata.core.backtesting.simple_backtest import (
    SimpleBacktest,
    SimpleBacktestResult,
)


class HumblCompassBacktestResult(SimpleBacktestResult):
    """Placeholder subclass for potential future extensions.

    This is currently equivalent to :class:`SimpleBacktestResult`. We keep the
    name to allow downstream code to switch on result type later without
    changing call-sites.
    """


class HumblCompassSimpleBacktest(SimpleBacktest):
    """HumblCompass-tailored SimpleBacktest.

    Parameters
    ----------
    actual_returns
        Daily realized returns, indexed by trading-day ``DatetimeIndex`` and
        columns as assets. A ``cash`` column is optional and will be handled by
        the base engine.
    compass_metric
        Monthly HumblCompass regime labels. Accepted types:
        ``pandas.DataFrame``, ``polars.DataFrame``, or ``polars.LazyFrame``.
        Schema is flexible:
        - Either columns per asset (preferred), indexed by the month start,
          or
        - A single column named ``humbl_regime`` with a date column or
          index representing month starts. In this case the series will be
          expanded to all assets present in ``actual_returns``.
    other_metrics
        Optional additional metric DataFrames to include alongside
        HumblCompass for cross-regime comparisons. Must be pandas
        DataFrames already aligned to daily dates.
    regime_alignment
        Alignment logic for monthly regimes onto trading days. Options:
        - ``"month_attribution"``: attribute each day of a labeled month to
          that month, but mask dates beyond the last fully known month
          (no carry into later unknown months).
        - ``"tradable_asof"``: assign a regime to a day only after it
          becomes knowable based on publication lag or a provided
          effective-start calendar (no lookahead; causal analysis).
    lag_months
        Integer month lag to apply when ``regime_alignment='tradable_asof'`` and
        no ``effective_start_calendar`` is provided. Example: ``2`` means the
        August regime becomes tradable starting October 1.
    effective_start_calendar
        Optional calendar with columns ``date_month_start`` and
        ``effective_start`` specifying the first date a given month label
        is known. Accepted as pandas, ``polars.DataFrame`` or
        ``polars.LazyFrame``. If provided, overrides ``lag_months``.
    carry_past_last_known
        If True, allow forward-fill of ``month_attribution`` beyond the
        last fully-known month. Defaults to False (recommended for
        descriptive attribution without implying knowledge of future
        months).

    Notes
    -----
    - Internally, monthly alignment is executed in Polars for performance
      and clarity, then converted to pandas before handing off to the base
      engine.
    - Output metric passed to the base class is a daily pandas DataFrame
      with columns matching the asset universe of ``actual_returns``
      (excluding cash by default).

    Choosing an alignment
    ---------------------
    - Use ``tradable-asof`` for any performance you might present as a
      strategy or imply tradability.
    - Use ``month_attribution`` for descriptive regime analytics and
      validation - "what happens inside a HumblBounce month".

    Quick reference
    ---------------
    Month attribution
      - Pros: clean regime-vs-behavior view; aligns with the human idea
        that "August was HumblBounce".
      - Cons: not tradable unless labels are known intra-month; do not
        carry into future months - mask after ``last_known_month_end``.
      - Answers: "In months classified as HumblBounce, what happened
        inside those months?"
      - Good for: attribution, characterization, sanity checks.

    Tradable-as-of
      - Pros: no lookahead; reflects decision timing; realistic PnL.
      - Cons: labels appear later due to lag (e.g., August behavior shows
        up starting Oct 1 for a two-month lag); less intuitive to read.
      - Answers: "Given only information known that day, what is
        performance?"
      - Good for: signal realism, causal backtests, live expectations.
      - Requires: either ``lag_months`` or an ``effective_start_calendar``.
    """

    def __init__(  # noqa: PLR0913
        self,
        actual_returns: pd.DataFrame,
        compass_metric: pd.DataFrame | pl.DataFrame | pl.LazyFrame,
        other_metrics: dict[str, pd.DataFrame] | None = None,
        *,
        regime_alignment: Literal[
            "month_attribution", "tradable_asof"
        ] = "tradable_asof",
        lag_months: int = 2,
        effective_start_calendar: (
            pd.DataFrame | pl.DataFrame | pl.LazyFrame | None
        ) = None,
        carry_past_last_known: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize the HumblCompass backtest with regime alignment.

        This prepares a daily regime metric from a monthly HumblCompass input
        using either simple month attribution or a tradable-as-of alignment
        that respects publication lag or an effective-start calendar.

        Parameters
        ----------
        actual_returns : pandas.DataFrame
            Daily realized returns indexed by trading-day ``DatetimeIndex``.
            Columns are asset symbols. A ``cash`` column is optional.
        compass_metric : pandas.DataFrame | polars.DataFrame | polars.LazyFrame
            Monthly HumblCompass labels. Either per-asset columns or a single
            ``humbl_regime`` column with a date/index representing month
            starts.
        other_metrics : dict[str, pandas.DataFrame], optional
            Additional daily metric frames to include alongside
            ``humblCOMPASS``. Must be aligned to trading days.
        regime_alignment : {"month_attribution", "tradable_asof"}
            Alignment mode. ``month_attribution`` forward-fills within the
            month. ``tradable_asof`` assigns labels only when they become
            known (no lookahead).
        lag_months : int
            Publication lag in months when using ``tradable_asof`` and no
            effective-start calendar is provided. Default is 2.
        effective_start_calendar : pandas.DataFrame | polars.DataFrame | None
            Optional calendar with ``date_month_start`` and ``effective_start``
            columns. Overrides ``lag_months`` when provided.
        carry_past_last_known : bool
            If True, allows forward-fill past the last fully-known month in
            ``month_attribution`` mode. Default is False.
        **kwargs : Any
            Passed to the base strategy. Notable keys: ``cash_column_name``,
            ``log_returns`` (defaults to True in the base class).

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If the monthly ``compass_metric`` cannot be coerced to a valid
            schema with a date column.

        See Also
        --------
        humbldata.core.backtesting.simple_backtest.SimpleBacktest
            Base class providing regime bucket analytics.
        """
        # Determine assets to expand regime for when needed
        cash_col = kwargs.get("cash_column_name", "cash")
        all_assets: list[str] = list(actual_returns.columns)
        assets: list[str] = [a for a in all_assets if a != cash_col]

        # Coerce, normalize, and align monthly regimes to trading days in Polars
        comp_pl = self._coerce_to_polars(compass_metric)
        comp_pl = self._normalize_compass_schema(comp_pl, assets)

        if regime_alignment == "month_attribution":
            aligned_pl = self._align_month_attribution(
                comp_pl=comp_pl,
                trading_index=pd.DatetimeIndex(actual_returns.index),
                carry_past_last_known=carry_past_last_known,
            )
        else:
            aligned_pl = self._align_tradable_asof(
                comp_pl=comp_pl,
                trading_index=pd.DatetimeIndex(actual_returns.index),
                lag_months=lag_months,
                effective_calendar=effective_start_calendar,
            )

        compass_daily_pd = self._polars_to_pandas_daily(aligned_pl)

        metrics: dict[str, pd.DataFrame] = {"humblCOMPASS": compass_daily_pd}
        if other_metrics:
            metrics.update(other_metrics)

        super().__init__(
            actual_returns=actual_returns, metrics=metrics, **kwargs
        )

    # If we need to return a specialized result later, we can override the
    # public API method to wrap the parent result into our subclass. For now,
    # we keep the same behavior and type for maximum compatibility.
    def generate_hisotrical_performance_backtest(
        self, *args, **kwargs
    ) -> SimpleBacktestResult:
        """Run regime analysis and augment with HumblCompass instance stats.

        This delegates to the base backtest to compute per-bucket performance
        and then adds instance-aware statistics for ``humblCOMPASS`` such as
        contiguous instance counts, average instance length, and drawdowns.

        Parameters
        ----------
        *args
            Positional arguments passed through to the base implementation.
        **kwargs
            Keyword arguments passed through to the base implementation.

        Returns
        -------
        SimpleBacktestResult
            Result with nested per-bucket metrics and a tidy ``summary``.

        See Also
        --------
        humbldata.core.backtesting.simple_backtest.SimpleBacktest
            Base computation of per-bucket performance metrics.
        """
        result = super().generate_hisotrical_performance_backtest(
            *args, **kwargs
        )

        # Augment with instance-based stats for humblCOMPASS buckets
        self._calculate_instance_stats(result)
        return result

    # -------------------------------------------------
    # Internals - instance analytics
    # -------------------------------------------------
    def _calculate_instance_stats(self, result: SimpleBacktestResult) -> None:
        """Compute instance-level statistics for HumblCompass buckets.

        For each asset and regime bucket under ``humblCOMPASS``, compute the
        number of contiguous instances, average instance length, average
        per-instance max drawdown, and the worst per-instance drawdown.

        Parameters
        ----------
        result : SimpleBacktestResult
            Result whose nested metrics will be updated in place.

        Returns
        -------
        None
        """
        metric_name = "humblCOMPASS"
        if metric_name not in self.metrics:
            return

        metric_df = self.metrics[metric_name]
        returns_df = self.actual_returns

        nested = result.regime_metrics
        assets = [a for a in nested if metric_name in nested.get(a, {})]

        for asset in assets:
            self._calculate_instance_stats_for_asset(
                nested=nested,
                asset=asset,
                metric_name=metric_name,
                metric_df=metric_df,
                returns_df=returns_df,
            )

        # Rebuild the summary table to include the new fields
        result.rebuild_summary()

    def _calculate_instance_stats_for_asset(
        self,
        *,
        nested: dict,
        asset: str,
        metric_name: str,
        metric_df: pd.DataFrame,
        returns_df: pd.DataFrame,
    ) -> None:
        """Compute instance statistics for one asset and update nested metrics.

        Parameters
        ----------
        nested : dict
            Nested regime metrics mapping to update in place.
        asset : str
            Asset symbol being processed.
        metric_name : str
            Metric key (expected ``"humblCOMPASS"`` here).
        metric_df : pandas.DataFrame
            Monthly HumblCompass labels for all assets.
        returns_df : pandas.DataFrame
            Daily returns used to compute instance drawdowns and counts.

        Returns
        -------
        None
        """
        if asset not in metric_df.columns or asset not in returns_df.columns:
            return

        m_series = metric_df[asset]
        common_idx = returns_df.index.intersection(m_series.index)
        asset_returns = returns_df.loc[common_idx, asset].dropna()
        asset_metric = m_series.loc[common_idx]

        for bucket in nested[asset][metric_name]:
            bucket_mask = asset_metric.astype(str) == bucket
            if not bucket_mask.any():
                nested[asset][metric_name][bucket].update(
                    {
                        "num_instances": 0.0,
                        "avg_instance_length": None,
                        "average_drawdown": None,
                        "max_drawdown": None,
                    }
                )
                continue

            run_change = bucket_mask.ne(bucket_mask.shift(fill_value=False))
            run_id = run_change.cumsum()
            true_runs = run_id[bucket_mask]

            instance_lengths: list[int] = []
            instance_drawdowns: list[float] = []

            for _, idx_vals in true_runs.groupby(true_runs):
                sub_idx = idx_vals.index
                sub_returns = asset_returns.reindex(sub_idx).dropna()
                if sub_returns.empty:
                    continue
                instance_lengths.append(len(sub_returns))

                if getattr(self, "log_returns", True):
                    wealth = (sub_returns.cumsum()).apply(np.exp)
                else:
                    wealth = (1.0 + sub_returns).cumprod()
                drawdown = (wealth / wealth.cummax()) - 1.0
                instance_dd = (
                    float(drawdown.min()) if not drawdown.empty else 0.0
                )
                instance_drawdowns.append(instance_dd)

            if getattr(self, "log_returns", True):
                bucket_idx = asset_metric.index[bucket_mask]
                bucket_returns = asset_returns.reindex(bucket_idx).dropna()
                if not bucket_returns.empty:
                    sum_log = float(bucket_returns.sum())
                    total_ret = float(np.exp(sum_log) - 1.0)
                    ppy = self._infer_ppy(bucket_returns.index)  # type: ignore[arg-type]
                    years_float = (
                        float(len(bucket_returns)) / float(ppy)
                        if ppy > 0
                        else 0.0
                    )
                    ann_ret = (
                        float(np.exp(sum_log / years_float) - 1.0)
                        if years_float > 0
                        else None
                    )
                    nested[asset][metric_name][bucket].update(
                        {
                            "total_return": total_ret,
                            "cumulative_return": total_ret,
                            "annualized_return": ann_ret,
                        }
                    )

            num_instances = float(len(instance_lengths))
            avg_len = (
                float(pd.Series(instance_lengths).mean())
                if instance_lengths
                else None
            )
            avg_dd = (
                float(pd.Series(instance_drawdowns).mean())
                if instance_drawdowns
                else None
            )
            worst_dd = (
                float(min(instance_drawdowns)) if instance_drawdowns else None
            )

            nested[asset][metric_name][bucket].update(
                {
                    "num_instances": num_instances,
                    "avg_instance_length": avg_len,
                    "average_drawdown": avg_dd,
                    "max_drawdown": worst_dd,
                }
            )

    # -------------------------------------------------
    # Internals - Polars alignment helpers
    # -------------------------------------------------
    @staticmethod
    def _coerce_to_polars(
        df_like: pd.DataFrame | pl.DataFrame | pl.LazyFrame,
    ) -> pl.DataFrame:
        """Coerce pandas/Polars input into a Polars frame with a date column.

        Parameters
        ----------
        df_like : pandas.DataFrame | polars.DataFrame | polars.LazyFrame
            Frame with either a date-like index or a date column.

        Returns
        -------
        polars.DataFrame
            Polars frame sorted by ``date`` with ``Datetime(us)`` type.

        Raises
        ------
        ValueError
            If a ``date`` or ``date_month_start`` column or index is not
            present.

        Notes
        -----
        - If the index comes from pandas, it is promoted to ``date``.
        - ``date_month_start`` is normalized to ``date``.
        - Time unit is forced to microseconds to avoid join mismatches.
        """
        if isinstance(df_like, pl.LazyFrame):
            out = df_like.collect()
        elif isinstance(df_like, pl.DataFrame):
            out = df_like
        else:
            out = pl.from_pandas(df_like)

        # Bring index over as a column if it exists (pandas-origin frames)
        if "index" in out.columns and "date" not in out.columns:
            out = out.rename({"index": "date"})

        # Normalize date column name
        if "date" not in out.columns and "date_month_start" in out.columns:
            out = out.rename({"date_month_start": "date"})

        # If still no date, attempt to detect a likely date column by name
        if "date" not in out.columns:
            candidate = next(
                (c for c in out.columns if "date" in c.lower()), None
            )
            if candidate is not None:
                out = out.rename({candidate: "date"})

        if "date" not in out.columns:
            msg = "compass_metric requires a 'date' or 'date_month_start' column or index"
            raise ValueError(msg)

        # Ensure datetime type and unify time unit for asof joins
        # Always cast to microseconds to avoid unit mismatches during joins
        out = out.with_columns(
            pl.col("date").cast(pl.Datetime(time_unit="us"), strict=False)
        )

        return out.sort("date")

    @staticmethod
    def _normalize_compass_schema(
        comp_pl: pl.DataFrame, assets: list[str]
    ) -> pl.DataFrame:
        """Normalize monthly labels to per-asset columns for all assets.

        Parameters
        ----------
        comp_pl : polars.DataFrame
            Polars frame with ``date`` and either per-asset columns or a
            single ``humbl_regime`` column.
        assets : list[str]
            Target asset universe for expansion and filtering.

        Returns
        -------
        polars.DataFrame
            Frame with ``date`` and per-asset label columns for ``assets``.
        """
        cols = [c for c in comp_pl.columns if c != "date"]
        if cols == ["humbl_regime"]:
            base = comp_pl.select(["date", "humbl_regime"]).rename(
                {"humbl_regime": assets[0] if assets else "humbl_regime"}
            )
            if assets:
                # Replicate regime across all asset columns
                exprs = [pl.col(assets[0]).alias(a) for a in assets]
                base = base.with_columns(exprs)
            return base

        # If there are non-asset columns, keep only those that intersect
        keep_cols = ["date"] + [c for c in cols if c in assets]
        if (
            len(keep_cols) == 1
        ):  # no matching asset columns, fall back to broadcast
            if "humbl_regime" in cols:
                tmp = comp_pl.select(["date", "humbl_regime"]).rename(
                    {"humbl_regime": assets[0] if assets else "humbl_regime"}
                )
            else:
                # take first non-date column and broadcast
                first = cols[0]
                tmp = comp_pl.select(["date", first]).rename(
                    {first: assets[0] if assets else first}
                )
            exprs = (
                [pl.col(tmp.columns[1]).alias(a) for a in assets]
                if assets
                else []
            )
            return tmp.with_columns(exprs)

        return comp_pl.select(keep_cols).sort("date")

    @staticmethod
    def _trading_index_to_polars(
        trading_index: pd.DatetimeIndex,
    ) -> pl.DataFrame:
        """Convert a trading-day ``DatetimeIndex`` into a Polars date frame.

        Parameters
        ----------
        trading_index : pandas.DatetimeIndex
            Trading-day index to convert.

        Returns
        -------
        polars.DataFrame
            Polars frame with a single ``date`` column, typed ``Datetime``.
        """
        trading_df = pd.DataFrame(
            {"date": pd.DatetimeIndex(trading_index).sort_values()}
        )
        return pl.from_pandas(trading_df).with_columns(
            pl.col("date").cast(pl.Datetime(time_unit="us"))
        )

    # Note: EOM helper removed - not required by current alignment paths.

    def _align_month_attribution(
        self,
        *,
        comp_pl: pl.DataFrame,
        trading_index: pd.DatetimeIndex,
        carry_past_last_known: bool,
    ) -> pl.DataFrame:
        """Forward-attribute monthly labels to each trading day in-month.

        Parameters
        ----------
        comp_pl : polars.DataFrame
            Monthly labels with a ``date`` month-start column.
        trading_index : pandas.DatetimeIndex
            Trading-day index to map to monthly labels.
        carry_past_last_known : bool
            If False, mask days beyond the end of the last fully-known month.

        Returns
        -------
        polars.DataFrame
            Daily-aligned labels with a ``date`` column and per-asset labels.
        """
        daily = self._trading_index_to_polars(trading_index)
        # asof join backward maps each day to the most recent month start
        joined = daily.join_asof(comp_pl, on="date", strategy="backward")

        if carry_past_last_known:
            return joined

        # mask dates beyond end-of-month of last known month
        last_known = comp_pl.select(pl.col("date").max()).item()
        last_known_pd = pd.Timestamp(last_known)
        cutoff = (last_known_pd + pd.offsets.MonthEnd(0)).to_pydatetime()
        # Apply mask to all regime columns
        regime_cols = [c for c in joined.columns if c != "date"]
        exprs = [
            pl.when(pl.col("date") <= pl.lit(cutoff))
            .then(pl.col(c))
            .otherwise(pl.lit(None))
            .alias(c)
            for c in regime_cols
        ]
        return joined.with_columns(exprs)

    def _align_tradable_asof(
        self,
        *,
        comp_pl: pl.DataFrame,
        trading_index: pd.DatetimeIndex,
        lag_months: int,
        effective_calendar: pd.DataFrame | pl.DataFrame | pl.LazyFrame | None,
    ) -> pl.DataFrame:
        """Assign labels after they become knowable (causal alignment).

        Parameters
        ----------
        comp_pl : polars.DataFrame
            Monthly labels with a ``date`` month-start column.
        trading_index : pandas.DatetimeIndex
            Trading-day index to align.
        lag_months : int
            Publication lag to apply when ``effective_calendar`` is None.
        effective_calendar : pandas.DataFrame | polars.DataFrame | None
            Optional calendar with ``date_month_start`` and
            ``effective_start`` columns.

        Returns
        -------
        polars.DataFrame
            Daily-aligned labels as of their effective start dates.
        """
        base = comp_pl

        if effective_calendar is not None:
            cal_pl = self._coerce_to_polars(effective_calendar)
            # Try to normalize column names
            if (
                "date_month_start" not in cal_pl.columns
                and "date" in cal_pl.columns
            ):
                cal_pl = cal_pl.rename({"date": "date_month_start"})
            if "effective_start" not in cal_pl.columns:
                # If absent, require lag fallback - we will construct below
                cal_pl = cal_pl.with_columns(
                    pl.col("date_month_start")
                    .dt.offset_by(f"{lag_months}mo")
                    .alias("effective_start")
                )
            cal = (
                cal_pl.select(["date_month_start", "effective_start"])
                .with_columns(
                    [
                        pl.col("date_month_start").cast(
                            pl.Datetime(time_unit="us")
                        ),
                        pl.col("effective_start").cast(
                            pl.Datetime(time_unit="us")
                        ),
                    ]
                )
                .sort("date_month_start")
            )

            # Join the calendar onto monthly labels; fall back to lag if missing
            base = (
                base.join(
                    cal, left_on="date", right_on="date_month_start", how="left"
                )
                .with_columns(
                    pl.when(pl.col("effective_start").is_null())
                    .then(pl.col("date").dt.offset_by(f"{lag_months}mo"))
                    .otherwise(pl.col("effective_start"))
                    .alias("effective_start")
                )
                .select(
                    ["effective_start"]
                    + [c for c in base.columns if c != "date"]
                )
                .with_columns(
                    pl.col("effective_start").cast(pl.Datetime(time_unit="us"))
                )
            )
        else:
            base = (
                base.with_columns(
                    pl.col("date")
                    .dt.offset_by(f"{lag_months}mo")
                    .alias("effective_start")
                )
                .select(
                    ["effective_start"]
                    + [c for c in base.columns if c != "date"]
                )
                .with_columns(
                    pl.col("effective_start").cast(pl.Datetime(time_unit="us"))
                )
            )

        daily = self._trading_index_to_polars(trading_index)
        base = base.sort("effective_start")
        # asof on effective_start
        aligned = daily.join_asof(
            base,
            left_on="date",
            right_on="effective_start",
            strategy="backward",
        )
        return aligned.drop("effective_start")

    @staticmethod
    def _polars_to_pandas_daily(df: pl.DataFrame) -> pd.DataFrame:
        """Convert a Polars daily frame into a pandas DataFrame with index.

        Parameters
        ----------
        df : polars.DataFrame
            Polars frame with a ``date`` column and per-asset label columns.

        Returns
        -------
        pandas.DataFrame
            Pandas DataFrame indexed by ``DatetimeIndex`` sorted ascending.
        """
        pdf = df.to_pandas()
        pdf = pdf.set_index("date")
        # Ensure index type
        if not isinstance(pdf.index, pd.DatetimeIndex):
            pdf.index = pd.to_datetime(pdf.index)
        return pdf.sort_index()
