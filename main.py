from exchange.exchange_wrapper import ExchangeWrapper
from data.data_handler import DataHandler
from strategies.moving_average import MovingAverageStrategy
from trader.trader import Trader
from config.settings import SYMBOL, TIMEFRAME, DATABASE_URL
from utils.logger import Logger
import sys


def initialize_database(data_handler, exchange, log):
    """
    Initialization pipeline:
    1. Get instruments
    2. Get instrument status
    3. Get tickers
    4. Get trades
    5. Get order books
    """
    log.info("Starting database initialization...")

    # 1. Instruments
    try:
        instruments = exchange.get_instruments()
        if not instruments or "instruments" not in instruments:
            log.error("No instruments returned by exchange")
            sys.exit(1)  # Stop early
        data_handler.init_instruments(instruments["instruments"])
        log.info(f"Saved {len(instruments['instruments'])} instruments")
    except Exception as e:
        log.exception(f"Failed to save instruments: {e}")
        sys.exit(1)

    # 2. Instrument status
    try:
        status = exchange.get_instrument_status_list()
        # status = exchange.get_instrument_status('PI_XBTUSD')
        # print(status)
        data_handler.save_instrument_status(status)
    except Exception as e:
        log.warning(f"Failed to fetch statuses: {e}")
        # continue
    
    # for inst in instruments["instruments"]:
    #     symbol = inst.get("symbol")
    #     try:
    #         status = exchange.get_instrument_status(symbol)
    #         data_handler.save_instrument_status(symbol, status)
    #     except Exception as e:
    #         log.warning(f"Failed to fetch status for {symbol}: {e}")
    #         continue

    # 3. Tickers
    for inst in instruments["instruments"]:
        symbol = inst.get("symbol")
        try:
            ticker = exchange.get_ticker(symbol)
            data_handler.save_ticker(symbol, ticker)
        except Exception as e:
            log.warning(f"Failed to fetch ticker for {symbol}: {e}")
            continue

    # 4. Trades
    for inst in instruments["instruments"]:
        symbol = inst.get("symbol")
        try:
            trades = exchange.get_trade_history(symbol)
            data_handler.save_trades(symbol, trades)
        except Exception as e:
            log.warning(f"Failed to fetch trades for {symbol}: {e}")
            continue

    # 5. Order books
    for inst in instruments["instruments"]:
        symbol = inst.get("symbol")
        try:
            order_book = exchange.get_order_book(symbol)
            data_handler.save_order_book(symbol, order_book)
        except Exception as e:
            log.warning(f"Failed to fetch order book for {symbol}: {e}")
            continue

    log.info("Database initialization completed successfully.")


def main():
    # Init logger
    log = Logger().get_logger()

    # Init exchange + data
    exchange = ExchangeWrapper(log)
    data_handler = DataHandler(DATABASE_URL, log)

    initialize_database(data_handler, exchange, log)

    # df = data_handler.get_historical_data(SYMBOL, TIMEFRAME, limit=200)

    # Apply strategy
    # strategy = MovingAverageStrategy(short_window=10, long_window=30, logger=log)
    # df = strategy.generate_signals(df)
    # last_signal = df.iloc[-1]["signal"]

    # # Execute trade
    # trader = Trader(exchange, log)
    # trader.execute_signal(SYMBOL, last_signal)

if __name__ == "__main__":
    main()


# -----------------------------
# DATA COLLECTION PIPELINE

# Initialization: no data in the db or a daily init
# 1. Get instruments
# 2. get instrument status list
# 3. Get tickers
# 4. Get trades --> this will be refreshed often
# 5. Get order book --> this will be refreshed often

# Live trading polling: Refresh only neccecesary data, minmize latency
# 1. Instrument status: poll frequently for dislocations / volatility
# 2. Tickers: poll frequently for live prices, funding rates, etc.
# 3. Order books: poll less frequently (unless depth is needed); overwrite each time
# 4. Trades: poll frequently, only append new ones (time + symbol as uniqueness)

# Historical data collection / backtesting: Build a large dataset for research
# 1. Trades: append all
# 2. Tickers
# 3. Order books: only needed for depth/liquidity analysis
# 4. Instrument status: rarely needed unless simulating trading restrictions
#   loop through all of these per instrument for a massive dataset


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
