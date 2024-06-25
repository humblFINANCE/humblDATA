"""Common descriptions for model fields."""

QUERY_DESCRIPTIONS = {
    "symbol": "Symbol to get data for.",
    "start_date": "Start date of the data, in YYYY-MM-DD format.",
    "end_date": "End date of the data, in YYYY-MM-DD format.",
    "interval": "Time interval of the data to return.",
    "period": "Time period of the data to return.",
    "date": "A specific date to get data for.",
    "limit": "The number of data entries to return.",
    "countries": "The country or countries to get data.",
    "units": "The unit of measurement for the data.",
    "frequency": "The frequency of the data.",
    "symbol_list_warning": "Lists of symbols are not allowed for this function. "
    "Multiple symbols will be ignored in favour of the first symbol.",
    "provider": "The provider of the data.",
    "user_role": "The role of a user in supabase.",
}

DATA_DESCRIPTIONS = {
    "symbol": "Symbol representing the entity requested in the data.",
    "cik": "Central Index Key (CIK) for the requested entity.",
    "date": "The date of the data as a Date object, the returned data's original dtype",
    "open": "The open price.",
    "high": "The high price.",
    "low": "The low price.",
    "close": "The close price.",
    "volume": "The trading volume.",
    "adj_close": "The adjusted close price.",
    "vwap": "Volume Weighted Average Price over the period.",
    "last_price": "The most recent price of the asset",
    "sector": "The sector of the asset",
    "mandelbrot_channel": "The Mandelbrot channel of the asset",
    "buy_price": "The recommended buy price for the asset",
    "sell_price": "The recommended sell price for the asset",
    "upside": "The potential upside of the asset",
    "downside": "The potential downside of the asset",
    "risk_reward_ratio": "The risk-reward ratio for the asset",
    "asset_class": "The class of the asset (e.g., equity, bond, commodity)",
    "humbl_suggestion": "humbl's recommendation for the asset",
}
