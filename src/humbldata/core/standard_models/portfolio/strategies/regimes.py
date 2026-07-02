"""Regime-to-position mapping models for backtesting strategies.

This module defines Pydantic models to validate and structure regime-based
trading rules, enabling HumblCompass backtests to map regime labels to specific
long and short asset positions.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ValidationError, model_validator


class HumblCompassPositionSideList(BaseModel):
    """Define long and short position lists for a single market regime.

    This Pydantic model encapsulates the trading rules for a specific regime by
    specifying which assets should be held long and which should be held short.
    It enforces strict validation to prevent configuration errors such as
    duplicate symbols or conflicting long-short assignments for the same asset.

    Parameters
    ----------
    long : list[str], optional
        Asset symbols to target with long exposure when this regime is active.
        Each symbol must be unique within this list. Default is empty list.
    short : list[str], optional
        Asset symbols to target with short exposure when this regime is active.
        Each symbol must be unique within this list and cannot appear in the
        ``long`` list. Default is empty list.

    Raises
    ------
    ValidationError
        If duplicate symbols are found in either ``long`` or ``short`` lists,
        or if any symbol appears in both lists simultaneously.

    Notes
    -----
    This model is designed to work within the HumblCompass backtesting framework
    to define regime-specific trading strategies.

    **Validation Rules**:

    1. **No Duplicates**: Each list (``long`` and ``short``) must contain unique
       symbols only. Duplicate entries will trigger a ValidationError.
    2. **Disjoint Sets**: The ``long`` and ``short`` sets must be completely
       disjoint - no symbol can appear in both lists simultaneously.
    3. **Symbol Existence**: Asset symbol validation against the actual returns
       universe occurs at strategy initialization time in
       ``HumblCompassSimpleBacktest``, not at model construction.

    **Design Philosophy**:

    The model uses Pydantic's ``mode="after"`` validation to enforce business
    rules after field assignment. This ensures data integrity at the schema
    level before any trading logic is applied.

    Examples
    --------
    >>> # Create regime rules for a growth/bullish regime
    >>> boom_regime = HumblCompassPositionSideList(
    ...     long=["SPY", "QQQ", "XLY"],
    ...     short=["TLT", "GLD"]
    ... )
    >>> print(boom_regime.long)
    ['SPY', 'QQQ', 'XLY']
    >>>
    >>> # Invalid: duplicate in long list raises ValidationError
    >>> try:
    ...     invalid = HumblCompassPositionSideList(long=["SPY", "SPY", "QQQ"])
    ... except ValidationError as e:
    ...     print("Duplicate symbols detected")
    Duplicate symbols detected
    >>>
    >>> # Invalid: same symbol in both long and short raises ValidationError
    >>> try:
    ...     invalid = HumblCompassPositionSideList(long=["SPY"], short=["SPY"])
    ... except ValidationError as e:
    ...     print("Long-short conflict detected")
    Long-short conflict detected

    See Also
    --------
    HumblCompassPositionLogic : Container mapping regime names to position lists
    humbldata.portfolio.strategies.humbl_compass_simple_backtest.HumblCompassSimpleBacktest : Strategy that consumes these mappings
    """

    long: list[str] = Field(default_factory=list)
    short: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _no_dupes_and_no_overlap(self) -> HumblCompassPositionSideList:
        # Raise plain ValueError, not pydantic.ValidationError: Pydantic v2's
        # ValidationError is constructed internally via
        # `pydantic_core.ValidationError.from_exception_data(...)`, not this
        # public-looking (list[dict], model) signature. Model validators are
        # expected to raise ValueError/AssertionError/TypeError, which
        # Pydantic automatically wraps into a proper ValidationError for the
        # caller.
        long_set: set[str] = set(self.long)
        short_set: set[str] = set(self.short)
        if len(long_set) != len(self.long):  # duplicates in long
            msg = "Duplicate symbols in long list"
            raise ValueError(msg)
        if len(short_set) != len(self.short):  # duplicates in short
            msg = "Duplicate symbols in short list"
            raise ValueError(msg)
        if long_set.intersection(short_set):
            msg = "Long and short lists must be disjoint"
            raise ValueError(msg)
        return self


class HumblCompassPositionLogic(BaseModel):
    """Map market regime labels to their corresponding position strategies.

    This model serves as the primary configuration container for regime-based
    trading strategies in the HumblCompass backtesting framework. It maps each
    regime label (e.g., "humblBOOM", "humblBUST") to a specific set of long and
    short position rules, enabling systematic regime-rotation strategies.

    Parameters
    ----------
    humblBOOM : HumblCompassPositionSideList, optional
        Position lists for the humblBOOM regime. Default is empty lists.
    humblBOUNCE : HumblCompassPositionSideList, optional
        Position lists for the humblBOUNCE regime. Default is empty lists.
    humblBLOAT : HumblCompassPositionSideList, optional
        Position lists for the humblBLOAT regime. Default is empty lists.
    humblBUST : HumblCompassPositionSideList, optional
        Position lists for the humblBUST regime. Default is empty lists.

    Returns
    -------
    None

    Notes
    -----
    This model is consumed by ``HumblCompassSimpleBacktest`` to determine daily
    trading positions based on the active regime for each asset.

    **Symbol Validation Strategy**:

    1. **Construction Time**: This model does NOT validate whether symbols
       actually exist in the trading universe. It only validates the structure
       and internal consistency of the mappings.
    2. **Strategy Initialization**: Symbol existence is validated when
       ``HumblCompassSimpleBacktest`` is initialized, cross-checking against
       the ``actual_returns`` DataFrame columns.
    3. **Unknown Asset Handling**: The strategy offers two policies via
       ``unknown_asset_policy``: ``"error"`` (raise ValueError) or ``"clip"``
       (silently remove unknown symbols using ``clip_to_universe()``).

    **Use Cases**:

    - Define multi-regime rotation strategies for systematic trading
    - Configure defensive vs. aggressive positioning based on market conditions
    - Create regime-specific long-short portfolios with automated rebalancing
    - Validate and sanitize regime configuration from external sources

    The model provides helper methods for introspection (``all_symbols()``) and
    filtering (``clip_to_universe()``) to facilitate integration with trading
    systems.

    Examples
    --------
    >>> # Create a simple two-regime strategy
    >>> logic = HumblCompassPositionLogic(
    ...     humblBOOM=HumblCompassPositionSideList(long=["SPY", "QQQ"], short=["TLT"]),
    ...     humblBUST=HumblCompassPositionSideList(long=["TLT", "GLD"], short=["SPY"]),
    ... )
    >>> sorted(logic.all_symbols())
    ['GLD', 'QQQ', 'SPY', 'TLT']
    >>>
    >>> # Clip to available universe
    >>> available = {"SPY", "TLT", "GLD"}
    >>> clipped = logic.clip_to_universe(available)
    >>> clipped.humblBOOM.long
    ['SPY']

    See Also
    --------
    HumblCompassPositionSideList : Individual regime position definition
    humbldata.portfolio.strategies.humbl_compass_simple_backtest.HumblCompassSimpleBacktest : Strategy using these mappings
    coerce_humbl_compass_position_logic : Helper to construct from raw dicts
    create_example_position_logic : Factory for standard four-regime configuration
    """

    humblBOOM: HumblCompassPositionSideList = Field(  # noqa: N815
        default_factory=HumblCompassPositionSideList
    )
    humblBOUNCE: HumblCompassPositionSideList = Field(  # noqa: N815
        default_factory=HumblCompassPositionSideList
    )
    humblBLOAT: HumblCompassPositionSideList = Field(  # noqa: N815
        default_factory=HumblCompassPositionSideList
    )
    humblBUST: HumblCompassPositionSideList = Field(  # noqa: N815
        default_factory=HumblCompassPositionSideList
    )

    def all_symbols(self) -> set[str]:
        """Extract the complete set of unique symbols across all regimes.

        This method aggregates all asset symbols referenced in any long or short
        position across all defined regimes, returning a deduplicated set. It is
        useful for validating symbol availability against a trading universe or
        for constructing data fetch requests.

        Returns
        -------
        set[str]
            Unique set of asset symbols appearing in either ``long`` or ``short``
            lists across all regimes. Empty set if no regimes are defined or all
            regime lists are empty.

        Notes
        -----
        **Implementation Details**:

        1. **Aggregation Strategy**: Iterates through all regime values and
           unions the ``long`` and ``short`` lists into an accumulator set.
        2. **Deduplication**: Set semantics automatically handle duplicates if
           the same symbol appears in multiple regimes or in both long and short
           lists across different regimes.
        3. **Performance**: O(n) where n is total symbols across all regimes;
           suitable for typical regime configuration sizes (10-100 symbols).

        This method is frequently used internally by ``HumblCompassSimpleBacktest``
        during initialization to validate that all configured symbols exist in
        the returns universe.

        Examples
        --------
        The example below predates this model's current field structure
        (``humblBOOM``/``humblBOUNCE``/``humblBLOAT``/``humblBUST``, see
        `HumblCompassPositionLogic`'s own docstring for a runnable example)
        and is illustrative only - not asserted as a doctest.

        >>> mappings = HumblRegimePositionMappings(  # doctest: +SKIP
        ...     regimes={
        ...         "regime_a": RegimeSideLists(long=["SPY", "TLT"]),
        ...         "regime_b": RegimeSideLists(short=["GLD"], long=["SPY"])
        ...     }
        ... )
        >>> mappings.all_symbols()  # doctest: +SKIP
        {'SPY', 'TLT', 'GLD'}
        >>>
        >>> # Empty mappings return empty set
        >>> empty = HumblRegimePositionMappings()  # doctest: +SKIP
        >>> empty.all_symbols()  # doctest: +SKIP
        set()

        See Also
        --------
        clip_to_universe : Filter symbols to match an available universe
        humbldata.portfolio.strategies.humbl_compass_simple_backtest.HumblCompassSimpleBacktest : Consumer of this method during validation
        """
        acc: set[str] = set()
        for side_lists in (
            self.humblBOOM,
            self.humblBOUNCE,
            self.humblBLOAT,
            self.humblBUST,
        ):
            acc.update(side_lists.long)
            acc.update(side_lists.short)
        return acc

    def clip_to_universe(self, universe: set[str]) -> HumblCompassPositionLogic:
        """Filter position mappings to retain only symbols present in the universe.

        This method creates a new ``HumblRegimePositionMappings`` instance with
        all symbol lists filtered to include only those symbols that exist in the
        provided universe set. Symbols not present in the universe are silently
        removed from both long and short lists across all regimes.

        Parameters
        ----------
        universe : set[str]
            Set of allowed asset symbols, typically derived from the columns of
            an ``actual_returns`` DataFrame or a broker's available instruments.
            Only symbols present in this set will be retained in the output.

        Returns
        -------
        HumblCompassPositionLogic
            A new mappings instance with identical regime structure but filtered
            symbol lists. Empty regimes (with both long and short lists empty
            after filtering) are preserved to maintain regime structure.

        Notes
        -----
        **Filtering Strategy**:

        1. **Non-Destructive**: The original mappings instance is unchanged; a
           new instance is returned with filtered lists.
        2. **Regime Preservation**: All regime keys are preserved even if their
           position lists become empty after filtering. This maintains consistent
           regime structure for downstream processing.
        3. **Use Case**: Typically invoked automatically by
           ``HumblCompassSimpleBacktest`` when ``unknown_asset_policy="clip"`` is
           set, allowing graceful handling of configuration files that reference
           symbols not available in the current trading universe.

        **Performance Considerations**:

        - Time complexity: O(n*m) where n is total symbols and m is universe size
        - Space complexity: O(n) for the new mappings structure
        - For typical regime configs (10-50 symbols) performance is negligible

        The method is called during strategy initialization by
        ``HumblCompassSimpleBacktest`` to sanitize user-provided mappings against
        the actual available data.

        Examples
        --------
        The example below predates this model's current field structure
        (``humblBOOM``/``humblBOUNCE``/``humblBLOAT``/``humblBUST``) and is
        illustrative only - not asserted as a doctest.

        >>> # Create mappings with symbols that may not all be available
        >>> mappings = HumblRegimePositionMappings(  # doctest: +SKIP
        ...     regimes={
        ...         "risk_on": RegimeSideLists(
        ...             long=["SPY", "QQQ", "ARKK"],
        ...             short=["TLT"]
        ...         )
        ...     }
        ... )
        >>>
        >>> # Clip to available universe (ARKK not available)
        >>> available = {"SPY", "QQQ", "TLT", "GLD"}
        >>> clipped = mappings.clip_to_universe(available)  # doctest: +SKIP
        >>> clipped.regimes["risk_on"].long  # doctest: +SKIP
        ['SPY', 'QQQ']
        >>> clipped.regimes["risk_on"].short  # doctest: +SKIP
        ['TLT']
        >>>
        >>> # Original is unchanged
        >>> mappings.regimes["risk_on"].long  # doctest: +SKIP
        ['SPY', 'QQQ', 'ARKK']

        See Also
        --------
        all_symbols : Get all symbols referenced across regimes
        humbldata.portfolio.strategies.humbl_compass_simple_backtest.HumblCompassSimpleBacktest : Calls this when unknown_asset_policy="clip"
        coerce_humbl_compass_position_logic : Construct mappings from raw dicts
        """
        return HumblCompassPositionLogic(
            humblBOOM=HumblCompassPositionSideList(
                long=[s for s in self.humblBOOM.long if s in universe],
                short=[s for s in self.humblBOOM.short if s in universe],
            ),
            humblBOUNCE=HumblCompassPositionSideList(
                long=[s for s in self.humblBOUNCE.long if s in universe],
                short=[s for s in self.humblBOUNCE.short if s in universe],
            ),
            humblBLOAT=HumblCompassPositionSideList(
                long=[s for s in self.humblBLOAT.long if s in universe],
                short=[s for s in self.humblBLOAT.short if s in universe],
            ),
            humblBUST=HumblCompassPositionSideList(
                long=[s for s in self.humblBUST.long if s in universe],
                short=[s for s in self.humblBUST.short if s in universe],
            ),
        )


def coerce_humbl_compass_position_logic(
    obj: dict[str, dict[str, list[str]]] | HumblCompassPositionLogic,
) -> HumblCompassPositionLogic:
    """Convert raw dictionary or existing model into validated position logic.

    This utility function accepts either a plain nested dictionary or an existing
    ``HumblRegimePositionMappings`` instance and ensures it is returned as a
    fully validated Pydantic model. It serves as the primary entry point for
    converting user-provided configuration into type-safe regime mappings.

    Parameters
    ----------
    obj : dict[str, dict[str, list[str]]] | HumblCompassPositionLogic
        Input to coerce into a validated mappings model. Accepts:

        - **dict**: Nested dictionary with structure
          ``{regime_name: {"long": [symbols], "short": [symbols]}}``.
          Each regime key must map to a dict with optional ``"long"`` and
          ``"short"`` keys containing lists of symbol strings.
        - **HumblCompassPositionLogic**: Existing validated instance, which
          is returned unchanged (pass-through for convenience).

    Returns
    -------
    HumblCompassPositionLogic
        Validated Pydantic model instance with all regime position rules
        properly structured and validated.

    Raises
    ------
    ValidationError
        If the input dictionary contains invalid structure, such as:

        - Duplicate symbols within a long or short list
        - Same symbol appearing in both long and short for a regime
        - Missing or malformed ``long``/``short`` keys in regime dicts

    Notes
    -----
    **Coercion Process**:

    1. **Type Check**: If input is already a ``HumblRegimePositionMappings``,
       return it immediately (no-op for efficiency).
    2. **Dict Conversion**: For dictionary input, iterate through regime keys
       and construct ``RegimeSideLists`` instances using Pydantic's ``**kwargs``
       unpacking, which validates structure and content.
    3. **Validation**: Each ``RegimeSideLists`` construction triggers the
       ``_no_dupes_and_no_overlap`` validator, ensuring data integrity.

    **Usage Patterns**:

    This function is used extensively by ``HumblCompassSimpleBacktest`` during
    initialization to normalize user input, allowing users to provide either
    convenience dicts or pre-validated model instances.

    **Design Rationale**:

    Accepting both types allows flexibility: users can provide simple dicts for
    quick prototyping, while production code can pre-validate and pass model
    instances for type safety.

    Examples
    --------
    >>> # Coerce a raw dictionary keyed by the four HumblCompass regimes
    >>> raw_config = {
    ...     "humblBOOM": {"long": ["SPY", "QQQ"], "short": ["TLT"]},
    ...     "humblBUST": {"long": ["TLT"], "short": ["SPY"]}
    ... }
    >>> mappings = coerce_humbl_compass_position_logic(raw_config)
    >>> mappings.humblBOOM.long
    ['SPY', 'QQQ']
    >>>
    >>> # Pass-through existing model
    >>> same = coerce_humbl_compass_position_logic(mappings)
    >>> same is mappings
    True
    >>>
    >>> # Invalid dict raises ValidationError
    >>> invalid = {"humblBOOM": {"long": ["A", "A"]}}  # duplicate
    >>> try:
    ...     coerce_humbl_compass_position_logic(invalid)
    ... except ValidationError:
    ...     print("Validation failed")
    Validation failed

    See Also
    --------
    HumblCompassPositionLogic : Target model class
    HumblCompassPositionSideList : Component model for individual regimes
    humbldata.portfolio.strategies.humbl_compass_simple_backtest.HumblCompassSimpleBacktest : Primary consumer of this function
    create_example_position_logic : Factory for standard configurations
    """
    if isinstance(obj, HumblCompassPositionLogic):
        return obj

    # Accept partial dicts; default missing regimes to empty lists
    def _to_side(
        d: dict[str, list[str]] | None,
    ) -> HumblCompassPositionSideList:
        d = d or {}
        return HumblCompassPositionSideList(
            long=list(d.get("long", [])), short=list(d.get("short", []))
        )

    return HumblCompassPositionLogic(
        humblBOOM=_to_side(obj.get("humblBOOM")),
        humblBOUNCE=_to_side(obj.get("humblBOUNCE")),
        humblBLOAT=_to_side(obj.get("humblBLOAT")),
        humblBUST=_to_side(obj.get("humblBUST")),
    )


def create_example_position_logic() -> HumblCompassPositionLogic:
    """Generate a pre-configured four-regime position strategy for HumblCompass.

    This factory function returns a ready-to-use ``HumblRegimePositionMappings``
    instance configured with standard positions for all four HumblCompass market
    regimes: BOOM, BLOAT, BUST, and BOUNCE. It serves as both a quick-start
    template for new strategies and a reference implementation of regime-based
    positioning logic.

    Returns
    -------
    HumblCompassPositionLogic
        Validated mappings instance with long and short positions defined for:

        - **humblBOOM**: Growth-oriented, risk-on positioning
        - **humblBLOAT**: Defensive, late-cycle positioning
        - **humblBUST**: Risk-off, preservation-focused positioning
        - **humblBOUNCE**: Early-cycle recovery positioning

    Notes
    -----
    **Regime Positioning Logic**:

    1. **humblBOOM (Risk-On Expansion)**:
       - Long: Growth equities (SPY, QQQ), cyclicals (XLY, IWM)
       - Short: Bonds (TLT), defensives (GLD), volatility (VIX)
       - Rationale: Maximum exposure to economic growth and risk assets

    2. **humblBLOAT (Late-Cycle Caution)**:
       - Long: Defensives (GLD, XLP, XLU), commodities
       - Short: Equities (SPY), financials (XLF), small-caps (IWM)
       - Rationale: Reduce equity risk, favor stability and inflation hedges

    3. **humblBUST (Risk-Off Contraction)**:
       - Long: Safe havens (TLT, BIL, GLD)
       - Short: Risk assets (SPY, QQQ), energy (XLE)
       - Rationale: Capital preservation, flight to quality

    4. **humblBOUNCE (Early Recovery)**:
       - Long: Cyclicals (SPY, XLI, XLB)
       - Short: Bonds (TLT), utilities (XLU)
       - Rationale: Capture early-cycle rotation into risk assets

    **Customization**:

    This is a reference configuration. Users should modify symbols based on their
    available universe, risk preferences, and investment thesis. The function is
    used internally by the HumblCompass backtesting framework for documentation
    and testing purposes.

    Examples
    --------
    >>> # Get standard four-regime configuration
    >>> logic = create_example_position_logic()
    >>> logic.humblBOOM.long
    ['SPY', 'QQQ', 'XLY', 'IWM']
    >>> logic.humblBOOM.short
    ['TLT', 'GLD', 'VIX']
    >>>
    >>> # Available regimes: humblBOOM, humblBLOAT, humblBUST, humblBOUNCE
    >>>
    >>> # Get all symbols for data fetching
    >>> sorted(logic.all_symbols())
    ['BIL', 'GLD', 'IWM', 'QQQ', 'SPY', 'TLT', 'VIX', 'XLB', 'XLE', 'XLF', 'XLI', 'XLP', 'XLU', 'XLY']
    >>>
    >>> # Use directly in backtest (illustrative - returns_df/compass_monthly
    >>> # are placeholders for real DataFrames, not asserted as a doctest)
    >>> from humbldata.portfolio.strategies.humbl_compass_simple_backtest import HumblCompassSimpleBacktest
    >>> backtest = HumblCompassSimpleBacktest(  # doctest: +SKIP
    ...     actual_returns=returns_df,
    ...     compass_metric=compass_monthly,
    ...     humbl_compass_position_logic=create_example_position_logic(),
    ...     allow_shorts=True
    ... )

    See Also
    --------
    HumblCompassPositionLogic : Model class for regime mappings
    coerce_humbl_compass_position_logic : Construct from custom dicts
    humbldata.portfolio.strategies.humbl_compass_simple_backtest.HumblCompassSimpleBacktest : Consumer strategy
    """
    return HumblCompassPositionLogic(
        humblBOOM=HumblCompassPositionSideList(
            long=["SPY", "QQQ", "XLY", "IWM"],
            short=["TLT", "GLD", "VIX"],
        ),
        humblBLOAT=HumblCompassPositionSideList(
            long=["GLD", "XLP", "XLU"],
            short=["SPY", "XLF", "IWM"],
        ),
        humblBUST=HumblCompassPositionSideList(
            long=["TLT", "BIL", "GLD"],
            short=["SPY", "QQQ", "XLE"],
        ),
        humblBOUNCE=HumblCompassPositionSideList(
            long=["SPY", "XLI", "XLB"],
            short=["TLT", "XLU"],
        ),
    )
