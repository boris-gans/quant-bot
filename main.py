from exchange.exchange_wrapper import ExchangeWrapper
from data.data_handler import DataHandler
from strategies.moving_average import MovingAverageStrategy
from trader.trader import Trader
from config.settings import SYMBOL, TIMEFRAME

def main():
    # Init exchange + data
    exchange = ExchangeWrapper()
    data_handler = DataHandler(exchange)
    df = data_handler.get_historical_data(SYMBOL, TIMEFRAME, limit=200)

    # Apply strategy
    strategy = MovingAverageStrategy(short_window=10, long_window=30)
    df = strategy.generate_signals(df)
    last_signal = df.iloc[-1]["signal"]

    # Execute trade
    trader = Trader(exchange)
    trader.execute_signal(SYMBOL, last_signal)

if __name__ == "__main__":
    main()

# COMPONENTS
# exchange_wrapper
"""Uses ccxt to connect to whatever exchange is configured in settings.py"""

# data_handler
"""Converts the raw OHLCV (open, high, low, close and volume) into a clean df"""

# strategies/*
"""Apply logic to data to produce signals"""

# trader
"""Takes a signal (+ additional rules) and decides whether to place an order via exchange_wrapper"""

# backtester
"""Runs strategies on historical data offline without exchange"""
