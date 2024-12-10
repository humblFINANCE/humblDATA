from datetime import datetime
from typing import Any, ClassVar

from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader

from humbldata.core.utils.env import Env


class BuyCloseSellOpen(Strategy):
    """
    Strategy that buys 10 minutes before market close and sells 10 minutes after market open.
    Goes all in on buys and all out on sells.
    """

    parameters: ClassVar[dict[str, Any]] = {
        "symbol": "SPY",  # Default trading symbol
    }

    def initialize(self):
        # Set to execute 10 minutes before close and after open
        self.minutes_before_closing = 10
        self.minutes_after_opening = 10
        self.sleeptime = "1M"
        self.last_trade_date = None

    def position_sizing(self, price):
        """Calculate maximum shares we can buy with available cash"""
        cash = self.get_cash()
        return int(cash / price)

    def before_market_opens(self):
        """Reset the last trade date at the start of each trading day"""
        self.last_trade_date = None

    def on_market_open(self):
        """Sell all positions 10 minutes after market open"""
        symbol = self.parameters["symbol"]
        position = self.get_position(symbol)

        if position is not None:
            current_price = self.get_last_price(symbol)
            self.sell_all()
            self.last_trade_date = self.get_datetime().date()
            self.log_message(f"Sold all {symbol} positions at {current_price}")

    def before_market_closes(self):
        """Buy positions 10 minutes before market close"""
        symbol = self.parameters["symbol"]
        current_dt = self.get_datetime()
        position = self.get_position(symbol)

        # Prevent multiple trades on the same day
        if self.last_trade_date == current_dt.date():
            return

        if position is None:
            current_price = self.get_last_price(symbol)
            quantity = self.position_sizing(current_price)

            if quantity > 0:
                order = self.create_order(symbol, quantity, "buy")
                self.submit_order(order)
                self.last_trade_date = current_dt.date()
                self.log_message(
                    f"Bought {quantity} shares of {symbol} at {current_price}"
                )

    def on_abrupt_closing(self):
        """Sell all positions if the strategy is stopped"""
        self.sell_all()


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

        strategy = BuyCloseSellOpen(
            broker=broker,
            parameters={
                "symbol": "SPY",
            },
        )

        trader.add_strategy(strategy)
        strategy_executors = trader.run_all()

    else:
        # Run backtest
        backtesting_start = datetime(2023, 1, 1)
        backtesting_end = datetime(2024, 1, 1)

        results = BuyCloseSellOpen.backtest(
            YahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={
                "symbol": "SPY",
            },
            benchmark_asset="SPY",
        )
