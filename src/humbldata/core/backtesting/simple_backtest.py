from __future__ import annotations

import datetime as dt
from collections.abc import Iterable, Mapping
from typing import Any, cast

import numpy as np
import pandas as pd
from investos.portfolio.result.base_result import BaseResult
from investos.portfolio.strategy import BaseStrategy


class SimpleBacktestResult(BaseResult):
    """Result object for SimpleBacktest regime analysis.

    Parameters
    ----------
    start_date
        First timestamp present in the input universe.
    end_date
        Last timestamp present in the input universe.
    actual_returns
        DataFrame of realized returns for assets. Index must be ``DatetimeIndex``.
    regime_metrics
        Nested dictionary with structure: ``asset -> metric_name -> bucket_value -> metrics_dict``.
    cash_column_name
        Optional name of the cash column in ``actual_returns`` if present. Defaults to ``"cash"``.

    Notes
    -----
    This class extends investos ``BaseResult`` to store a nested structure of
    per-asset, per-metric, per-regime performance statistics. It maintains
    compatibility with investos workflows by keeping the standard properties
    available (e.g., ``h``, ``u``, portfolio-level metrics) when used in a
    traditional backtest. For pure regime analysis, only ``regime_metrics`` is
    populated.
    """

    def __init__(
        self,
        start_date: dt.datetime,
        end_date: dt.datetime,
        actual_returns: pd.DataFrame,
        regime_metrics: dict[
            str, dict[str, dict[str, dict[str, float | None]]]
        ],
        cash_column_name: str = "cash",
    ) -> None:
        super().__init__(
            start_date=start_date,
            end_date=end_date,
            cash_column_name=cash_column_name,
            actual_returns=actual_returns,
        )
        self.regime_metrics: dict[
            str, dict[str, dict[str, dict[str, float | None]]]
        ] = regime_metrics

        # A tidy, analysis-friendly summary table (stored privately)
        # Columns: [symbol, metric, bucket, <metrics...>]
        self._summary: pd.DataFrame = self._build_summary_dataframe()

    def to_dict(self) -> dict[str, Any]:
        """Return the nested regime metrics as a JSON-serializable dict."""
        return self.regime_metrics

    # Public hook for subclasses to rebuild their summary after mutation
    def rebuild_summary(self) -> None:
        """Rebuild the tidy summary table from current ``regime_metrics``."""
        self._summary = self._build_summary_dataframe()

    @property
    def summary(self) -> pd.DataFrame:  # type: ignore[override]
        """Return a tidy DataFrame summary of regime metrics.

        Overrides the base result's read-only property with one that
        returns the per-symbol, per-metric, per-bucket flattened table.
        """
        return self._summary

    # -----------------------
    # Internals - formatting
    # -----------------------
    def _build_summary_dataframe(self) -> pd.DataFrame:
        """Flatten nested regime metrics into a tidy pandas DataFrame.

        The resulting DataFrame contains one row per
        (symbol, metric, bucket) with all computed statistics as columns.
        Missing buckets are skipped.
        """
        rows: list[dict[str, Any]] = []
        for symbol, metric_dict in self.regime_metrics.items():
            for metric_name, bucket_dict in metric_dict.items():
                for bucket, metrics in bucket_dict.items():
                    if not metrics:
                        continue
                    row: dict[str, Any] = {
                        "symbol": symbol,
                        "metric": metric_name,
                        "bucket": bucket,
                    }
                    row.update(metrics)
                    rows.append(row)

        if not rows:
            return pd.DataFrame(
                columns=pd.Index(
                    [
                        "symbol",
                        "metric",
                        "bucket",
                        "num_instances",
                        "avg_instance_length",
                        "average_drawdown",
                        "total_return",
                        "annualized_return",
                        "annualized_excess_return",
                        "excess_risk_annualized",
                        "information_ratio",
                        "risk_over_cash_annualized",
                        "sharpe_ratio",
                        "max_drawdown",
                        "annual_turnover",
                        "portfolio_hit_rate",
                        "cumulative_return",
                        "annualized_volatility",
                        "num_periods",
                    ]
                )
            )

        df = pd.DataFrame(rows)
        # Ensure expected column ordering when present
        preferred_order = [
            "symbol",
            "metric",
            "bucket",
            "num_periods",
            "num_instances",
            "avg_instance_length",
            "total_return",
            "cumulative_return",
            "annualized_return",
            "annualized_excess_return",
            "annualized_volatility",
            "risk_over_cash_annualized",
            "excess_risk_annualized",
            "sharpe_ratio",
            "information_ratio",
            "average_drawdown",
            "max_drawdown",
            "portfolio_hit_rate",
            "annual_turnover",
        ]
        cols = [c for c in preferred_order if c in df.columns] + [
            c for c in df.columns if c not in preferred_order
        ]
        df = df[cols]
        # Stable sort for readability
        return df.sort_values(by=["metric", "symbol", "bucket"]).reset_index(  # type: ignore[call-arg]
            drop=True
        )


class SimpleBacktest(BaseStrategy):
    """Strategy for categorical regime analysis without active trading.

    This strategy computes performance metrics for each asset across regime
    buckets for one or more metric DataFrames. It returns a nested result
    object that is compatible with investos workflows.

    Examples
    --------
    The example below is illustrative pseudocode (not asserted as a
    doctest): `actual_returns`/`metrics` and the resulting values are
    placeholders, not runnable in isolation.

    >>> # actual_returns: DataFrame [dates x assets]
    >>> # metrics: {"humblCOMPASS": df1, "humblMOMENTUM": df2}
    >>> strat = SimpleBacktest(actual_returns=actual_returns, metrics=metrics)  # doctest: +SKIP
    >>> result = strat.generate_hisotrical_performance_backtest()  # doctest: +SKIP
    >>> nested = result.to_dict()  # doctest: +SKIP
    >>> nested["SPY"]["humblCOMPASS"]["humblBOOM"]  # doctest: +SKIP
    {'cumulative_return': 0.12, 'annualized_return': 0.10, 'max_drawdown': -0.05, 'annualized_volatility': 0.16, 'sharpe_ratio': 0.62}
    """

    def __init__(
        self,
        actual_returns: pd.DataFrame,
        metrics: Mapping[str, pd.DataFrame],
        costs: list | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            actual_returns=actual_returns, costs=costs or [], **kwargs
        )
        self.metrics: dict[str, pd.DataFrame] = {
            name: df.copy() for name, df in metrics.items()
        }

        # Whether input returns are log returns. If True, wealth and
        # compounding use exp(cumsum(log_returns)). Defaults to True.
        self.log_returns: bool = bool(kwargs.get("log_returns", True))

        # Ensure indices are DatetimeIndex and aligned universe-wise (intersection)
        self._normalize_inputs()

        # Metadata for investos result saving
        self.metadata_properties = [
            "metrics_names",
        ]

    @property
    def metrics_names(self) -> list[str]:
        return list(self.metrics.keys())

    # -----------------------------------------------
    # Strategy required method - zero-trade behavior
    # -----------------------------------------------
    def generate_trade_list(
        self, holdings: pd.Series, t: dt.datetime
    ) -> pd.Series:
        """Return a zero-trade vector to remain flat.

        This keeps compatibility with ``BacktestController`` if used, while this
        class is primarily intended for regime analysis outside of a trading
        optimization loop.
        """
        return pd.Series(index=holdings.index, data=0.0)

    # -----------------------------------------------
    # Public API
    # -----------------------------------------------
    def generate_hisotrical_performance_backtest(
        self,
        assets: Iterable[str] | None = None,
        risk_free_rate_annual: float = 0.0,
        include_cash: bool = False,
    ) -> SimpleBacktestResult:
        """Compute metrics for all (asset, metric, bucket) combinations.

        Parameters
        ----------
        assets
            Optional iterable of assets to include. Defaults to all assets in
            ``actual_returns`` (excluding cash if present and ``include_cash`` is False).
        risk_free_rate_annual
            Annualized risk free rate to use for Sharpe ratio. If zero, excess
            returns equal raw returns.
        include_cash
            If True, include the cash column (if present) as an asset in the
            analysis. Defaults to False.

        Returns
        -------
        SimpleBacktestResult
            Result containing nested regime analytics in ``result.to_dict()``.
        """
        returns_df = self.actual_returns.copy()

        # Determine assets universe
        cash_col = getattr(self, "cash_column_name", "cash")
        all_assets = list(returns_df.columns)
        if not include_cash and cash_col in all_assets:
            all_assets.remove(cash_col)
        asset_list = list(assets) if assets is not None else all_assets

        # Construct benchmark/rf series - use cash if present else 0
        benchmark_full = (
            returns_df[cash_col].astype(float)
            if cash_col in returns_df.columns
            else pd.Series(0.0, index=returns_df.index, dtype=float)
        )
        # Use cash as risk-free by default (mirrors BaseResult behavior)
        risk_free_full = benchmark_full

        # Precompute per-metric global bucket sets (as strings for JSON keys)
        metric_to_buckets: dict[str, list[str]] = {}
        for metric_name, metric_df in self.metrics.items():
            uniques = pd.unique(pd.Series(metric_df.values.ravel()).dropna())
            # Normalize to strings for JSON keys while preserving human readability
            bucket_names = sorted([str(v) for v in uniques])
            metric_to_buckets[metric_name] = bucket_names

        nested: dict[str, dict[str, dict[str, dict[str, float | None]]]] = {}

        # Compute metrics per (asset, metric, bucket)
        for asset in asset_list:
            nested[asset] = {}
            for metric_name, metric_df in self.metrics.items():
                nested[asset][metric_name] = {}

                # Skip assets absent from a metric DataFrame
                if asset not in metric_df.columns:
                    # Still need to mark all buckets as missing for completeness
                    for bucket in metric_to_buckets[metric_name]:
                        nested[asset][metric_name][bucket] = {}
                    continue

                # Align index with returns
                m_series = metric_df[asset]
                common_idx = returns_df.index.intersection(m_series.index)
                asset_returns = returns_df.loc[common_idx, asset].dropna()
                asset_metric = m_series.loc[common_idx]

                # For completeness, iterate the global set of buckets
                for bucket in metric_to_buckets[metric_name]:
                    # Match on the original values, not the str key
                    bucket_mask = asset_metric.astype(str) == bucket
                    candidate_idx = asset_metric.index[bucket_mask]
                    sub_idx = asset_returns.index.intersection(candidate_idx)
                    sub_returns = asset_returns.loc[sub_idx].dropna()

                    if sub_returns.empty:
                        nested[asset][metric_name][bucket] = {}
                        continue

                    bench_sub = cast(
                        "pd.Series",
                        benchmark_full.reindex(sub_returns.index).astype(float),
                    )
                    rf_sub = cast(
                        "pd.Series",
                        risk_free_full.reindex(sub_returns.index).astype(float),
                    )
                    metrics = self._compute_stats(
                        returns=sub_returns,
                        benchmark_returns=bench_sub,
                        risk_free_returns=rf_sub,
                    )
                    nested[asset][metric_name][bucket] = metrics

        # Validate completeness and self-correct to ensure all combinations present
        nested = self._validate_and_fill(
            nested=nested,
            metric_to_buckets=metric_to_buckets,
            assets=asset_list,
        )

        idx = pd.DatetimeIndex(returns_df.index)
        if idx.size > 0:
            start_dt = idx[0].to_pydatetime()  # type: ignore[assignment]
            end_dt = idx[-1].to_pydatetime()  # type: ignore[assignment]
        else:
            now_ts = pd.Timestamp.utcnow()
            start_dt = now_ts.to_pydatetime()
            end_dt = now_ts.to_pydatetime()

        result = SimpleBacktestResult(
            start_date=start_dt,
            end_date=end_dt,
            actual_returns=returns_df,
            regime_metrics=nested,
            cash_column_name=cash_col,
        )

        return result

    # -----------------------------------------------
    # Internals
    # -----------------------------------------------
    def _normalize_inputs(self) -> None:
        """Ensure DatetimeIndex and intersect indices across inputs.

        This keeps analysis aligned across ``actual_returns`` and all metric
        DataFrames, clipping to the common date range and sorting the index.
        """

        # Ensure datetime index
        def _ensure_dtindex(df: pd.DataFrame) -> pd.DataFrame:
            out = df.copy()
            if not isinstance(out.index, pd.DatetimeIndex):
                out.index = pd.to_datetime(out.index)
            out = out.sort_index()
            return out

        self.actual_returns = _ensure_dtindex(self.actual_returns)
        for k, df in self.metrics.items():
            self.metrics[k] = _ensure_dtindex(df)

        # Intersect all indices
        common_idx = self.actual_returns.index
        for df in self.metrics.values():
            common_idx = common_idx.intersection(df.index)

        self.actual_returns = self.actual_returns.loc[common_idx]
        for k, df in self.metrics.items():
            self.metrics[k] = df.loc[common_idx]

    @staticmethod
    def _infer_ppy(index: pd.DatetimeIndex) -> float:
        """Infer periods per year from index spacing.

        Uses pandas frequency inference when available; falls back to average
        delta heuristic. Returns a float for generality.
        """
        if index.size < 2:
            return 252.0

        freq = pd.infer_freq(index)
        if freq:
            f = freq.upper()
            if f.startswith(("B", "D")):
                return 252.0
            if f.startswith("W"):
                return 52.0
            if f.startswith("M"):
                return 12.0
            if f.startswith("Q"):
                return 4.0
            if f.startswith(("A", "Y")):
                return 1.0

        # Heuristic based on average days per step
        ns = np.asarray(index.asi8, dtype=np.int64)
        deltas = np.diff(ns) / 86_400_000_000_000  # to days
        avg_days = float(np.mean(deltas))
        if avg_days <= 2.0:
            return 252.0
        if avg_days <= 10.0:
            return 52.0
        if avg_days <= 25.0:
            return 12.0
        if avg_days <= 80.0:
            return 4.0
        return 1.0

    def _compute_stats(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series,
        risk_free_returns: pd.Series,
    ) -> dict[str, float | None]:
        """Compute required metrics for a returns series.

        Mirrors BaseResult key names for compatibility and downstream expectations.
        Returned keys:
        - total_return
        - annualized_return
        - annualized_excess_return
        - excess_risk_annualized
        - information_ratio
        - risk_over_cash_annualized
        - sharpe_ratio
        - max_drawdown
        - annual_turnover (always None here)
        - portfolio_hit_rate
        - cumulative_return (alias for total_return)
        - annualized_volatility (alias for risk_over_cash_annualized using returns over cash)
        """
        returns = returns.dropna().astype(float)
        if returns.empty:
            return {}

        # Align series
        idx = returns.index
        benchmark_returns = (
            benchmark_returns.reindex(idx).fillna(0.0).astype(float)
        )
        risk_free_returns = (
            risk_free_returns.reindex(idx).fillna(0.0).astype(float)
        )
        excess = (returns - benchmark_returns).dropna()
        over_cash = (returns - risk_free_returns).dropna()

        # Infer ppy and annualization based on trading days
        idx = cast("pd.DatetimeIndex", returns.index)
        ppy = SimpleBacktest._infer_ppy(idx)

        n = len(returns)
        years_float = float(n) / float(ppy) if ppy > 0 and n > 0 else 0.0

        # Cumulative and annualized return
        if self.log_returns:
            sum_log = float(returns.sum())
            cum_ret = float(np.exp(sum_log) - 1.0)
            ann_ret = (
                float(np.exp(sum_log / years_float) - 1.0)
                if years_float > 0
                else float("nan")
            )
        else:
            cum_ret = float((1.0 + returns).prod() - 1.0)
            ann_ret = (
                float(((1.0 + cum_ret) ** (ppy / max(n, 1))) - 1.0)
                if n > 0
                else float("nan")
            )

        # Annualized volatility (over cash as in BaseResult.risk_over_cash_annualized)
        vol = (
            float(over_cash.std(ddof=1) * np.sqrt(ppy))
            if len(over_cash) > 1
            else float("nan")
        )

        # Sharpe ratio (over cash) and Information ratio (over benchmark)
        over_cash_std = over_cash.std(ddof=1)
        sharpe = (
            float(np.sqrt(ppy) * over_cash.mean() / over_cash_std)
            if len(over_cash) > 1 and over_cash_std > 0
            else float("nan")
        )

        excess_std = excess.std(ddof=1)
        information_ratio = (
            float(np.sqrt(ppy) * excess.mean() / excess_std)
            if len(excess) > 1 and excess_std > 0
            else float("nan")
        )

        # Max drawdown on wealth curve
        if self.log_returns:
            wealth = np.exp(returns.cumsum())
        else:
            wealth = (1.0 + returns).cumprod()
        rolling_max = wealth.cummax()
        drawdown = (wealth / rolling_max) - 1.0
        max_dd = float(drawdown.min()) if not drawdown.empty else float("nan")

        # Annualized excess return (geometric like BaseResult when geometric=True)
        if self.log_returns:
            sum_bench_log = float(benchmark_returns.sum())
            total_benchmark = float(np.exp(sum_bench_log) - 1.0)
            ann_bench = (
                float(np.exp(sum_bench_log / years_float) - 1.0)
                if years_float > 0
                else float("nan")
            )
            # Log-excess annualization: use log domain difference
            ann_excess = (
                float(
                    np.exp((float(returns.sum()) - sum_bench_log) / years_float)
                    - 1.0
                )
                if years_float > 0
                else float("nan")
            )
        else:
            total_benchmark = float((1.0 + benchmark_returns).prod() - 1.0)
            ann_bench = (
                float(((1.0 + total_benchmark) ** (ppy / max(n, 1))) - 1.0)
                if n > 0
                else float("nan")
            )
            # Match BaseResult default behavior (non-geometric)
            ann_excess = ann_ret - ann_bench

        # Portfolio hit rate (proportion of positive raw returns)
        hit_rate = float((returns > 0).mean()) if n > 0 else float("nan")

        # Convert NaNs to None for JSON cleanliness
        def _nan_to_none(x: float) -> float | None:
            return (
                None
                if (
                    x is None
                    or (isinstance(x, float) and (np.isnan(x) or np.isinf(x)))
                )
                else float(x)
            )

        out: dict[str, float | None] = {
            # BaseResult-style keys
            "total_return": _nan_to_none(cum_ret),
            "annualized_return": _nan_to_none(ann_ret),
            "annualized_excess_return": _nan_to_none(ann_excess),
            "excess_risk_annualized": _nan_to_none(
                excess_std * np.sqrt(ppy) if len(excess) > 1 else float("nan")
            ),
            "information_ratio": _nan_to_none(information_ratio),
            "risk_over_cash_annualized": _nan_to_none(vol),
            "sharpe_ratio": _nan_to_none(sharpe),
            "max_drawdown": _nan_to_none(max_dd),
            "annual_turnover": None,  # Not defined for this static bucket analysis
            "portfolio_hit_rate": _nan_to_none(hit_rate),
            # Convenience aliases requested
            "cumulative_return": _nan_to_none(cum_ret),
            "annualized_volatility": _nan_to_none(vol),
        }

        # Add count of periods for richer summaries
        # Kept outside of _nan_to_none for integer fidelity
        # Number of observations in this bucket (as float for JSON compatibility)
        out["num_periods"] = float(n)

        # Type ignore to satisfy return type, keeping None values when needed
        return out  # type: ignore[return-value]

    @staticmethod
    def _validate_and_fill(
        nested: dict[str, dict[str, dict[str, dict[str, float | None]]]],
        metric_to_buckets: dict[str, list[str]],
        assets: Iterable[str],
    ) -> dict[str, dict[str, dict[str, dict[str, float | None]]]]:
        """Ensure every (asset, metric, bucket) exists; fill missing with None."""
        out = nested
        for asset in assets:
            if asset not in out:
                out[asset] = {}
            for metric_name, buckets in metric_to_buckets.items():
                if metric_name not in out[asset]:
                    out[asset][metric_name] = {}
                for bucket in buckets:
                    if bucket not in out[asset][metric_name]:
                        out[asset][metric_name][bucket] = {}
        return out
