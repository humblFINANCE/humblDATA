from datetime import datetime
from typing import Any, ClassVar

import polars as pl
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.entities.position import Position
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader

from humbldata.core.utils.env import Env
from humbldata.toolbox.toolbox_controller import Toolbox


class HumblChannelSingleLong(Strategy):
    """Strategy that trades based on HumblChannel indicators."""

    parameters: ClassVar[dict[str, Any]] = {
        "symbol": "SPY",
        "quantity": 1,
        "buy_threshold_pct": 0.005,  # 2% threshold
        "sell_threshold_pct": 0.001,  # 2% threshold
    }

    def initialize(self):
        self.sleeptime = "1D"

    def before_market_opens(self):
        current_date = self.get_round_day()
        # current_date = self.get_datetime().strftime("%Y-%m-%d")
        # self.log_message(f"Current Trading Day: {current_date}", color="blue")

        # Calculates the humblCHANNEL from 2000-01-01 to current date, returns only one observation
        self.vars.daily_humbl_channel = (
            Toolbox(
                symbols=self.parameters["symbol"],
                interval="1d",
                start_date="2000-01-01",
                end_date=current_date,
                membership="admin",
            )
            .technical.humbl_channel(
                historical=False,
                window="1mo",
                _boundary_group_down=False,
                chart=False,
                live_price=False,
            )
            .to_polars()
        )

        # self.log_message(
        #     f"HumblChannel Bottom Price: {self.vars.daily_humbl_channel.select('bottom_price')}",
        #     color="blue",
        # )
        # self.log_message(
        #     f"HumblChannel Top Price: {self.vars.daily_humbl_channel.select('top_price')}",
        #     color="blue",
        # )

    def on_trading_iteration(self):
        symbol = self.parameters["symbol"]
        cash = self.get_cash()

        # Get current price and position
        current_price = self.get_last_price(symbol)
        position = self.get_position(symbol)

        # Get bottom and top prices from HumblChannel
        bottom_price = self.vars.daily_humbl_channel.select("bottom_price").row(
            0
        )[0]
        top_price = self.vars.daily_humbl_channel.select("top_price").row(0)[0]

        # Calculate price differences as percentages
        bottom_diff_pct = abs(current_price - bottom_price) / bottom_price
        top_diff_pct = abs(current_price - top_price) / top_price

        # First check sell condition - if we have a position and price is near top
        if (
            position is not None
            and abs(top_diff_pct) <= self.parameters["sell_threshold_pct"]
        ):
            # Sell all shares
            order = self.create_order(symbol, position.quantity, "sell")
            self.submit_order(order)
            return  # Exit to prevent buy on same day

        # Then check buy condition - if we have no position and price is near bottom
        if (
            position is None
            and abs(bottom_diff_pct) <= self.parameters["buy_threshold_pct"]
        ):
            # Calculate maximum shares we can buy with available cash
            max_shares = int(cash / current_price)
            if max_shares > 0:
                order = self.create_order(symbol, max_shares, "buy")
                self.submit_order(order)


if __name__ == "__main__":
    is_live = False

    if is_live:
        env = Env()
        ALPACA_CONFIG = {
            "API_KEY": env.ALPACA_API_KEY,
            "API_SECRET": env.ALPACA_API_SECRET,
            "PAPER": True,
        }

        trader = Trader()
        broker = Alpaca(ALPACA_CONFIG)

        strategy = HumblChannelSingleLong(
            broker=broker,
            parameters={
                "symbol": "SPY",
                "quantity": 1,
            },
        )

        trader.add_strategy(strategy)
        strategy_executors = trader.run_all()

    else:
        # Run backtest
        backtesting_start = datetime(2010, 1, 1)
        backtesting_end = datetime(2024, 12, 10)

        results = HumblChannelSingleLong.backtest(
            YahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={
                "symbol": "SPY",
            },
            benchmark_asset="SPY",
        )
