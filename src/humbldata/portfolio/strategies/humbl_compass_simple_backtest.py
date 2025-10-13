"""HumblCompass SimpleBacktest with publication-lag-aware alignment options."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

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

    def __init__(
        self,
        actual_returns: pd.DataFrame,
        compass_metric: pd.DataFrame | pl.DataFrame | pl.LazyFrame,
        other_metrics: Mapping[str, pd.DataFrame] | None = None,
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
        """Run the base regime analysis and return the result.

        This intentionally returns the base ``SimpleBacktestResult`` to
        avoid unnecessary object copying. The result type remains
        compatible with any downstream handling.
        """
        return super().generate_hisotrical_performance_backtest(*args, **kwargs)

    # -------------------------------------------------
    # Internals - Polars alignment helpers
    # -------------------------------------------------
    @staticmethod
    def _coerce_to_polars(
        df_like: pd.DataFrame | pl.DataFrame | pl.LazyFrame,
    ) -> pl.DataFrame:
        """Coerce pandas/Polars input to a Polars DataFrame with a date column.

        Accepted schemas:
        - Index is date-like OR a column in {"date", "date_month_start"}
        - Values are either a single ``humbl_regime`` column or per-asset columns
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
        """Ensure the Polars frame has per-asset columns; expand if single column.

        If a single column named ``humbl_regime`` exists, replicate to each asset
        column. Otherwise, assume provided columns already match assets.
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
        # Keep exact dates from the trading calendar (not a range), ordered
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

        Days strictly after the last fully-known month are masked to null unless
        ``carry_past_last_known`` is True.
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
        """Assign labels only after they become knowable (causal alignment)."""
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
        pdf = df.to_pandas()
        pdf = pdf.set_index("date")
        # Ensure index type
        if not isinstance(pdf.index, pd.DatetimeIndex):
            pdf.index = pd.to_datetime(pdf.index)
        return pdf.sort_index()
